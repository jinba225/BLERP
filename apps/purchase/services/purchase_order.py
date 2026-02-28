from django.db import transaction
from purchase.models import PurchaseOrder, PurchaseOrderItem

from common.utils import DocumentNumberGenerator


class PurchaseOrderService:
    @staticmethod
    @transaction.atomic
    def create_order(user, order_data, items_data):
        if "order_number" not in order_data:
            order_data["order_number"] = DocumentNumberGenerator.generate(
                "purchase_order",
                model_class=PurchaseOrder,  # 使用完整的键名  # 传递模型类以支持重用已删除订单编号
            )

        order = PurchaseOrder(**order_data)
        order.created_by = user
        order.save()

        for idx, item_data in enumerate(items_data):
            if not item_data.get("product_id") and not item_data.get("product"):
                continue

            PurchaseOrderItem.objects.create(
                purchase_order=order, created_by=user, sort_order=idx, **item_data
            )

        order.calculate_totals()
        order.save()

        return order

    @staticmethod
    @transaction.atomic
    def update_order(order, user, order_data, items_data):
        for key, value in order_data.items():
            setattr(order, key, value)

        order.updated_by = user
        order.save()

        if items_data is not None:
            order.items.all().delete()
            for idx, item_data in enumerate(items_data):
                if not item_data.get("product_id") and not item_data.get("product"):
                    continue

                PurchaseOrderItem.objects.create(
                    purchase_order=order, created_by=user, sort_order=idx, **item_data
                )

        order.calculate_totals()
        order.save()

        return order
