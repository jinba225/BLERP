"""
Sales Order Service
封装销售订单的业务逻辑
"""

from decimal import Decimal, InvalidOperation

from core.models import Notification
from django.contrib import messages
from django.db import transaction

from ..models import SalesOrder, SalesOrderItem


class SalesOrderService:
    """销售订单服务类"""

    @staticmethod
    def create_order(user, data):
        """
        创建销售订单

        Args:
            user: 当前用户
            data: 订单数据（字典）
                {
                    'customer_id': 客户ID,
                    'items': [
                        {
                            'product_id': 产品ID,
                            'quantity': 数量,
                            'unit_price': 单价,
                            'discount_rate': 折扣率,
                        }
                    ],
                    'order_date': 订单日期,
                    'delivery_date': 交货日期,
                    'payment_terms': 付款条件,
                    'notes': 备注,
                }

        Returns:
            SalesOrder: 创建的销售订单实例
        """
        from common.utils import DocumentNumberGenerator

        with transaction.atomic():
            # 生成订单号
            order_number = DocumentNumberGenerator.generate("SO")

            # 创建订单主表
            order = SalesOrder.objects.create(
                order_number=order_number,
                customer_id=data.get("customer_id"),
                order_date=data.get("order_date"),
                delivery_date=data.get("delivery_date"),
                payment_terms=data.get("payment_terms"),
                notes=data.get("notes", ""),
                status="draft",
                created_by=user,
            )

            # 创建订单明细
            total_amount = Decimal("0")
            for item_data in data.get("items", []):
                try:
                    # 计算明细金额
                    unit_price = Decimal(str(item_data.get("unit_price", "0")))
                    quantity = int(item_data.get("quantity", 0))
                    discount_rate = (
                        Decimal(str(item_data.get("discount_rate", "0"))) / 100
                    )
                    discount_amount = unit_price * quantity * discount_rate
                    line_total = (unit_price * quantity) - discount_amount

                    SalesOrderItem.objects.create(
                        order=order,
                        product_id=item_data.get("product_id"),
                        quantity=quantity,
                        unit_price=unit_price,
                        discount_rate=discount_rate,
                        discount_amount=discount_amount,
                        line_total=line_total,
                        created_by=user,
                    )

                    total_amount += line_total

                except (ValueError, InvalidOperation, KeyError) as e:
                    messages.error(user, f"订单明细数据错误：{str(e)}")
                    raise ValueError(f"订单明细数据错误：{str(e)}")

            # 更新订单总金额
            order.subtotal = total_amount
            order.total_amount = total_amount
            order.save()

            # 创建通知
            Notification.create_notification(
                recipient=user,
                title=f"销售订单 {order_number} 已创建",
                message=f'订单包含 {len(data.get("items", []))} 个商品，总金额：{total_amount}',
                notification_type="info",
                category="sales_order",
                reference_type="SalesOrder",
                reference_id=str(order.id),
                reference_url=reverse("sales:detail", kwargs={"pk": order.id}),
            )

            return order

    @staticmethod
    def calculate_total(items):
        """
        计算订单总额

        Args:
            items: 订单明细列表

        Returns:
            Decimal: 订单总金额
        """
        total = Decimal("0")
        for item in items:
            try:
                unit_price = Decimal(str(item.get("unit_price", "0")))
                quantity = int(item.get("quantity", 0))
                discount_rate = Decimal(str(item.get("discount_rate", "0"))) / 100
                line_total = (unit_price * quantity) * (1 - discount_rate)
                total += line_total
            except (ValueError, InvalidOperation):
                pass
        return total

    @staticmethod
    def check_inventory(order_id):
        """
        检查库存是否充足

        Args:
            order_id: 订单ID

        Returns:
            dict: {
                'is_sufficient': True/False,
                'insufficient_items': [库存不足的商品列表]
            }
        """
        from products.models import Product

        order = SalesOrder.objects.get(id=order_id)
        insufficient_items = []

        for item in order.items.all():
            try:
                product = Product.objects.get(id=item.product_id)

                # 检查产品库存是否充足
                # 这里简化处理，实际应该检查多个仓库的总库存
                # TODO: 实现完整的库存检查逻辑
                if item.quantity > product.stock_available:
                    insufficient_items.append(
                        {
                            "product_id": item.product_id,
                            "product_name": product.name,
                            "requested_quantity": item.quantity,
                            "available_quantity": product.stock_available,
                        }
                    )
            except Product.DoesNotExist:
                continue

        return {
            "is_sufficient": len(insufficient_items) == 0,
            "insufficient_items": insufficient_items,
        }

    @staticmethod
    def update_status(order_id, status, user):
        """
        更新订单状态

        Args:
            order_id: 订单ID
            status: 新状态
            user: 操作用户

        Returns:
            bool: 更新是否成功
        """
        try:
            order = SalesOrder.objects.get(id=order_id)
            old_status = order.status
            order.status = status
            order.updated_by = user
            order.save()

            # 状态变更通知
            if old_status != status:
                status_messages = {
                    "draft": "草稿",
                    "pending": "待审核",
                    "confirmed": "已确认",
                    "in_production": "生产中",
                    "ready_to_ship": "待发货",
                    "shipped": "已发货",
                    "delivered": "已交付",
                    "completed": "已完成",
                    "cancelled": "已取消",
                }
                Notification.create_notification(
                    recipient=order.customer,
                    title=f"订单 {order.order_number} 状态已更新",
                    message=f"订单状态：{
                        status_messages.get(
                            old_status,
                            old_status)} → {
                        status_messages.get(
                            status,
                            status)}",
                    notification_type="info",
                    category="sales_order",
                    reference_type="SalesOrder",
                    reference_id=str(order.id),
                    reference_url=reverse("sales:detail", kwargs={"pk": order.id}),
                )

            return True

        except SalesOrder.DoesNotExist:
            return False
