"""
销售模块创建工具

提供销售业务的创建功能，包括发货、退货、借货等
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from customers.models import Customer
from django.db import transaction
from django.utils import timezone
from products.models import Product
from sales.models import Delivery, Quote, SalesLoan, SalesOrder, SalesReturn

from common.utils import DocumentNumberGenerator

from .base_tool import BaseTool, ToolResult


class CreateDeliveryTool(BaseTool):
    """创建发货单工具"""

    name = "create_delivery"
    display_name = "创建发货单"
    description = "为销售订单创建发货单"
    category = "sales"
    risk_level = "medium"
    require_permission = "sales.add_delivery"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer", "description": "销售订单ID"},
                "items": {
                    "type": "array",
                    "description": "发货明细列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"},
                            "quantity": {"type": "number", "description": "发货数量"},
                        },
                        "required": ["product_id", "quantity"],
                    },
                },
                "delivery_date": {"type": "string", "description": "发货日期（YYYY-MM-DD，默认今天）"},
                "tracking_number": {"type": "string", "description": "快递单号"},
                "shipping_address": {"type": "string", "description": "收货地址"},
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["order_id", "items"],
        }

    def execute(
        self,
        order_id: int,
        items: list,
        delivery_date: str = None,
        tracking_number: str = "",
        shipping_address: str = "",
        notes: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行创建发货单"""
        try:
            from sales.models import DeliveryItem, SalesOrder

            # 获取订单
            try:
                order = SalesOrder.objects.get(id=order_id, is_deleted=False)
            except SalesOrder.DoesNotExist:
                return ToolResult(success=False, error=f"订单ID {order_id} 不存在")

            # 验证订单状态
            if order.status not in ["confirmed", "in_production", "ready_to_ship"]:
                return ToolResult(success=False, error=f"订单状态为 {order.get_status_display()}，不能发货")

            # 验证明细并计算
            validated_items = []
            for item in items:
                try:
                    product = Product.objects.get(id=item["product_id"], is_deleted=False)
                except Product.DoesNotExist:
                    return ToolResult(success=False, error=f"产品ID {item['product_id']} 不存在")

                quantity = float(item["quantity"])

                # 检查订单明细中的剩余数量
                order_item = order.items.filter(product_id=product.id).first()
                if not order_item:
                    return ToolResult(success=False, error=f"订单中不包含产品 {product.name}")

                remaining = order_item.remaining_quantity
                if quantity > remaining:
                    return ToolResult(
                        success=False, error=f"产品 {product.name} 发货数量 {quantity} 超过剩余数量 {remaining}"
                    )

                validated_items.append(
                    {
                        "product": product,
                        "quantity": quantity,
                    }
                )

            # 创建发货单
            with transaction.atomic():
                delivery_number = DocumentNumberGenerator.generate("delivery")
                delivery_date_obj = (
                    datetime.strptime(delivery_date, "%Y-%m-%d").date()
                    if delivery_date
                    else timezone.now().date()
                )

                delivery = Delivery.objects.create(
                    delivery_number=delivery_number,
                    sales_order=order,
                    delivery_date=delivery_date_obj,
                    tracking_number=tracking_number,
                    shipping_address=shipping_address
                    or order.delivery_address
                    or order.customer.address,
                    status="pending",
                    notes=notes,
                    created_by=self.user,
                )

                # 创建明细
                for item_data in validated_items:
                    DeliveryItem.objects.create(
                        delivery=delivery,
                        product=item_data["product"],
                        quantity=item_data["quantity"],
                        created_by=self.user,
                    )

            return ToolResult(
                success=True,
                data={
                    "delivery_id": delivery.id,
                    "delivery_number": delivery.delivery_number,
                    "order_number": order.order_number,
                    "customer_name": order.customer.name,
                    "delivery_date": delivery.delivery_date.strftime("%Y-%m-%d"),
                    "items_count": len(validated_items),
                },
                message=f"发货单 {delivery.delivery_number} 创建成功，包含 {len(validated_items)} 个明细",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"创建发货单失败: {str(e)}")


class CreateSalesReturnTool(BaseTool):
    """创建销售退货单工具"""

    name = "create_sales_return"
    display_name = "创建退货单"
    description = "为客户创建销售退货单"
    category = "sales"
    risk_level = "medium"
    require_permission = "sales.add_salesreturn"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer", "description": "销售订单ID（可选）"},
                "delivery_id": {"type": "integer", "description": "发货单ID（可选）"},
                "customer_id": {"type": "integer", "description": "客户ID"},
                "items": {
                    "type": "array",
                    "description": "退货明细列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"},
                            "quantity": {"type": "number", "description": "退货数量"},
                            "refund_amount": {"type": "number", "description": "退款金额"},
                        },
                        "required": ["product_id", "quantity"],
                    },
                },
                "return_reason": {
                    "type": "string",
                    "description": "退货原因（quality/wrong/damaged/customer_other）",
                    "enum": ["quality", "wrong", "damaged", "customer_other"],
                },
                "request_date": {"type": "string", "description": "退货申请日期（YYYY-MM-DD，默认今天）"},
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["customer_id", "items", "return_reason"],
        }

    def execute(
        self,
        customer_id: int,
        items: list,
        return_reason: str,
        order_id: int = None,
        delivery_id: int = None,
        request_date: str = None,
        notes: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行创建退货单"""
        try:
            from sales.models import SalesReturnItem

            # 获取客户
            try:
                customer = Customer.objects.get(id=customer_id, is_deleted=False)
            except Customer.DoesNotExist:
                return ToolResult(success=False, error=f"客户ID {customer_id} 不存在")

            # 获取订单或发货单（可选）
            order = None
            delivery = None

            if order_id:
                try:
                    order = SalesOrder.objects.get(id=order_id, is_deleted=False)
                except SalesOrder.DoesNotExist:
                    return ToolResult(success=False, error=f"订单ID {order_id} 不存在")

            if delivery_id:
                try:
                    delivery = Delivery.objects.get(id=delivery_id, is_deleted=False)
                except Delivery.DoesNotExist:
                    return ToolResult(success=False, error=f"发货单ID {delivery_id} 不存在")

            # 验证明细并计算
            validated_items = []
            total_refund = 0

            for item in items:
                try:
                    product = Product.objects.get(id=item["product_id"], is_deleted=False)
                except Product.DoesNotExist:
                    return ToolResult(success=False, error=f"产品ID {item['product_id']} 不存在")

                quantity = float(item["quantity"])
                refund_amount = float(item.get("refund_amount", 0))
                total_refund += refund_amount

                validated_items.append(
                    {
                        "product": product,
                        "quantity": quantity,
                        "refund_amount": refund_amount,
                    }
                )

            # 创建退货单
            with transaction.atomic():
                return_number = DocumentNumberGenerator.generate("sales_return")
                request_date_obj = (
                    datetime.strptime(request_date, "%Y-%m-%d").date()
                    if request_date
                    else timezone.now().date()
                )

                sales_return = SalesReturn.objects.create(
                    return_number=return_number,
                    sales_order=order,
                    delivery=delivery,
                    customer=customer,
                    return_reason=return_reason,
                    request_date=request_date_obj,
                    refund_amount=total_refund,
                    status="pending",
                    notes=notes,
                    created_by=self.user,
                )

                # 创建明细
                for item_data in validated_items:
                    SalesReturnItem.objects.create(
                        sales_return=sales_return,
                        product=item_data["product"],
                        quantity=item_data["quantity"],
                        refund_amount=item_data["refund_amount"],
                        created_by=self.user,
                    )

            return ToolResult(
                success=True,
                data={
                    "return_id": sales_return.id,
                    "return_number": sales_return.return_number,
                    "customer_name": customer.name,
                    "request_date": sales_return.request_date.strftime("%Y-%m-%d"),
                    "return_reason": sales_return.get_return_reason_display(),
                    "refund_amount": float(total_refund),
                    "items_count": len(validated_items),
                },
                message=f"退货单 {sales_return.return_number} 创建成功，退款金额 {total_refund:.2f} 元",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"创建退货单失败: {str(e)}")


class CreateSalesLoanTool(BaseTool):
    """创建借货单工具"""

    name = "create_sales_loan"
    display_name = "创建借货单"
    description = "为客户创建借货单"
    category = "sales"
    risk_level = "medium"
    require_permission = "sales.add_salesloan"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer", "description": "客户ID"},
                "items": {
                    "type": "array",
                    "description": "借货明细列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"},
                            "quantity": {"type": "number", "description": "借货数量"},
                        },
                        "required": ["product_id", "quantity"],
                    },
                },
                "loan_date": {"type": "string", "description": "借货日期（YYYY-MM-DD，默认今天）"},
                "expected_return_date": {"type": "string", "description": "预计归还日期（YYYY-MM-DD）"},
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["customer_id", "items"],
        }

    def execute(
        self,
        customer_id: int,
        items: list,
        loan_date: str = None,
        expected_return_date: str = "",
        notes: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行创建借货单"""
        try:
            from sales.models import SalesLoanItem

            # 获取客户
            try:
                customer = Customer.objects.get(id=customer_id, is_deleted=False)
            except Customer.DoesNotExist:
                return ToolResult(success=False, error=f"客户ID {customer_id} 不存在")

            # 验证明细
            validated_items = []

            for item in items:
                try:
                    product = Product.objects.get(id=item["product_id"], is_deleted=False)
                except Product.DoesNotExist:
                    return ToolResult(success=False, error=f"产品ID {item['product_id']} 不存在")

                quantity = float(item["quantity"])

                validated_items.append(
                    {
                        "product": product,
                        "quantity": quantity,
                    }
                )

            # 创建借货单
            with transaction.atomic():
                loan_number = DocumentNumberGenerator.generate("sales_loan")
                loan_date_obj = (
                    datetime.strptime(loan_date, "%Y-%m-%d").date()
                    if loan_date
                    else timezone.now().date()
                )

                # 默认预计归还日期为30天后
                expected_return_date_obj = None
                if expected_return_date:
                    expected_return_date_obj = datetime.strptime(
                        expected_return_date, "%Y-%m-%d"
                    ).date()
                else:
                    expected_return_date_obj = loan_date_obj + timedelta(days=30)

                loan = SalesLoan.objects.create(
                    loan_number=loan_number,
                    customer=customer,
                    loan_date=loan_date_obj,
                    expected_return_date=expected_return_date_obj,
                    status="pending",
                    notes=notes,
                    created_by=self.user,
                )

                # 创建明细
                for item_data in validated_items:
                    SalesLoanItem.objects.create(
                        sales_loan=loan,
                        product=item_data["product"],
                        quantity=item_data["quantity"],
                        created_by=self.user,
                    )

            return ToolResult(
                success=True,
                data={
                    "loan_id": loan.id,
                    "loan_number": loan.loan_number,
                    "customer_name": customer.name,
                    "loan_date": loan.loan_date.strftime("%Y-%m-%d"),
                    "expected_return_date": loan.expected_return_date.strftime("%Y-%m-%d"),
                    "items_count": len(validated_items),
                },
                message=f"借货单 {
                    loan.loan_number} 创建成功，预计归还日期 {
                    loan.expected_return_date.strftime('%Y-%m-%d')}",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"创建借货单失败: {str(e)}")


class ConvertQuoteToOrderTool(BaseTool):
    """报价单转订单工具"""

    name = "convert_quote_to_order"
    display_name = "报价单转订单"
    description = "将报价单转换为销售订单"
    category = "sales"
    risk_level = "medium"
    require_permission = "sales.add_order"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "quote_id": {"type": "integer", "description": "报价单ID"},
                "delivery_address": {"type": "string", "description": "交付地址（可选）"},
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["quote_id"],
        }

    def execute(
        self, quote_id: int, delivery_address: str = "", notes: str = "", **kwargs
    ) -> ToolResult:
        """执行转换"""
        try:
            from sales.models import SalesOrder, SalesOrderItem

            # 获取报价单
            try:
                quote = Quote.objects.get(id=quote_id, is_deleted=False)
            except Quote.DoesNotExist:
                return ToolResult(success=False, error=f"报价单ID {quote_id} 不存在")

            # 检查报价单状态
            if quote.status != "accepted":
                return ToolResult(
                    success=False, error=f"报价单状态为 {quote.get_status_display()}，只有已接受的报价单才能转为订单"
                )

            # 检查是否已转换
            if hasattr(quote, "converted_to_order") and quote.converted_to_order:
                return ToolResult(
                    success=False, error=f"该报价单已转换为订单 {quote.converted_to_order.order_number}"
                )

            # 获取报价明细
            quote_items = quote.items.filter(is_deleted=False)

            # 创建订单
            with transaction.atomic():
                order_number = DocumentNumberGenerator.generate("sales_order")
                order_date = timezone.now().date()
                delivery_date = order_date + timedelta(days=30)  # 默认30天后交货

                order = SalesOrder.objects.create(
                    order_number=order_number,
                    customer=quote.customer,
                    quote=quote,
                    order_date=order_date,
                    required_date=quote.valid_until,
                    delivery_date=delivery_date,
                    total_amount=quote.total_amount,
                    delivery_address=delivery_address or quote.customer.address,
                    notes=notes,
                    status="pending",
                    created_by=self.user,
                )

                # 创建订单明细
                for i, quote_item in enumerate(quote_items, 1):
                    SalesOrderItem.objects.create(
                        order=order,
                        product=quote_item.product,
                        product_code=quote_item.product.code,
                        quantity=quote_item.quantity,
                        unit_price=quote_item.unit_price,
                        line_total=quote_item.line_total,
                        sequence=i,
                        created_by=self.user,
                    )

                # 更新报价单状态
                quote.status = "converted"
                quote.save()

            return ToolResult(
                success=True,
                data={
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "quote_number": quote.quote_number,
                    "customer_name": quote.customer.name,
                    "total_amount": float(order.total_amount),
                    "items_count": len(quote_items),
                    "delivery_date": delivery_date.strftime("%Y-%m-%d"),
                },
                message=f"报价单 {quote.quote_number} 已成功转换为订单 {order.order_number}",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"报价单转订单失败: {str(e)}")
