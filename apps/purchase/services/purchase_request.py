from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from purchase.models import PurchaseOrder, PurchaseOrderItem, PurchaseRequest, PurchaseRequestItem

from common.utils import DocumentNumberGenerator


class PurchaseRequestService:
    @staticmethod
    @transaction.atomic
    def create_request(user, request_data, items_data):
        if "request_number" not in request_data:
            request_data["request_number"] = DocumentNumberGenerator.generate("purchase_request")

        purchase_request = PurchaseRequest(**request_data)
        purchase_request.created_by = user
        purchase_request.save()

        total = Decimal("0")
        for idx, item_data in enumerate(items_data):
            if not item_data.get("product_id") and not item_data.get("product"):
                continue

            item = PurchaseRequestItem.objects.create(
                purchase_request=purchase_request,
                created_by=user,
                sort_order=idx,
                **item_data,
            )
            total += item.estimated_total

        purchase_request.estimated_total = total
        purchase_request.save()

        return purchase_request

    @staticmethod
    @transaction.atomic
    def update_request(purchase_request, user, request_data, items_data):
        for key, value in request_data.items():
            setattr(purchase_request, key, value)

        purchase_request.updated_by = user
        purchase_request.save()

        if items_data is not None:
            purchase_request.items.all().delete()
            total = Decimal("0")
            for idx, item_data in enumerate(items_data):
                if not item_data.get("product_id") and not item_data.get("product"):
                    continue

                item = PurchaseRequestItem.objects.create(
                    purchase_request=purchase_request,
                    created_by=user,
                    sort_order=idx,
                    **item_data,
                )
                total += item.estimated_total

            purchase_request.estimated_total = total
            purchase_request.save()

        return purchase_request

    @staticmethod
    @transaction.atomic
    def convert_request_to_order(
        purchase_request, user, supplier_id, warehouse_id=None, items_prices=None
    ):
        """
        Convert a purchase request to a purchase order.

        Args:
            purchase_request: The purchase request to convert
            user: The current user
            supplier_id: The supplier ID (required)
            warehouse_id: The warehouse ID (optional)
            items_prices: Dictionary of item prices {item_id: price} (optional)

        Returns:
            PurchaseOrder: The created purchase order

        Raises:
            ValueError: If validation fails
        """
        # Validate supplier
        if not supplier_id:
            raise ValueError("供应商不能为空")

        order = PurchaseOrder.objects.create(
            order_number=DocumentNumberGenerator.generate(
                "purchase_order",
                model_class=PurchaseOrder,  # 传递模型类以支持重用已删除订单编号
            ),
            supplier_id=supplier_id,
            order_date=timezone.now().date(),
            required_date=purchase_request.required_date,
            buyer=user,
            warehouse_id=warehouse_id,
            reference_number=purchase_request.request_number,
            notes=f"由采购申请单 {purchase_request.request_number} 转换",
            internal_notes=(
                f'申请部门：{purchase_request.department.name if purchase_request.department else "无"}\n'
                f"申请人：{purchase_request.requester.get_full_name() or purchase_request.requester.username}\n"
                f"申请理由：{purchase_request.justification or '无'}"
            ),
            created_by=user,
            status="draft",
        )

        # Copy request items to order items with prices
        for request_item in purchase_request.items.all():
            # Determine unit price with priority:
            # 1. Provided price from items_prices
            # 2. Estimated price from request item
            # 3. Product cost price
            # 4. Default to 0
            if items_prices and request_item.id in items_prices:
                unit_price = items_prices[request_item.id]
            elif request_item.estimated_price:
                unit_price = request_item.estimated_price
            elif request_item.product.cost_price:
                unit_price = request_item.product.cost_price
            else:
                unit_price = Decimal("0")

            PurchaseOrderItem.objects.create(
                purchase_order=order,
                product=request_item.product,
                quantity=request_item.quantity,
                unit_price=unit_price,
                required_date=request_item.required_date,
                specifications=request_item.specifications,
                notes=request_item.notes,
                sort_order=request_item.sort_order,
                created_by=user,
            )

        # Calculate totals
        order.calculate_totals()
        order.save()

        # Update request status
        purchase_request.status = "ordered"
        purchase_request.converted_order = order
        purchase_request.save()

        return order
