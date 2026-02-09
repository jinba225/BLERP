"""
销售模块扩展工具

提供销售业务的高级查询和操作工具，包括发货、退货、借货等功能
"""

from typing import Any, Dict

from customers.models import Customer
from django.db.models import Q
from sales.models import Delivery, SalesLoan, SalesReturn

from .base_tool import BaseTool, ToolResult


class QueryDeliveriesTool(BaseTool):
    """查询发货单工具"""

    name = "query_deliveries"
    display_name = "查询发货单"
    description = "查询发货单列表，支持按状态、客户、日期范围筛选"
    category = "sales"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "发货状态（draft/pending/shipped/delivered/cancelled）",
                    "enum": ["draft", "pending", "shipped", "delivered", "cancelled"],
                },
                "customer_id": {"type": "integer", "description": "客户ID"},
                "date_from": {"type": "string", "description": "开始日期（YYYY-MM-DD）"},
                "date_to": {"type": "string", "description": "结束日期（YYYY-MM-DD）"},
                "keyword": {"type": "string", "description": "搜索关键词（发货单号）"},
                "limit": {"type": "integer", "description": "返回结果数量限制（默认20）", "default": 20},
            },
        }

    def execute(
        self,
        status: str = None,
        customer_id: int = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            deliveries = Delivery.objects.filter(is_deleted=False)

            if status:
                deliveries = deliveries.filter(status=status)

            if customer_id:
                deliveries = deliveries.filter(sales_order__customer_id=customer_id)

            if date_from:
                deliveries = deliveries.filter(delivery_date__gte=date_from)

            if date_to:
                deliveries = deliveries.filter(delivery_date__lte=date_to)

            if keyword:
                deliveries = deliveries.filter(delivery_number__icontains=keyword)

            deliveries = deliveries.select_related("sales_order__customer").order_by(
                "-delivery_date"
            )[:limit]

            # 格式化结果
            results = []
            for delivery in deliveries:
                results.append(
                    {
                        "id": delivery.id,
                        "delivery_number": delivery.delivery_number,
                        "order_number": delivery.sales_order.order_number
                        if delivery.sales_order
                        else "",
                        "customer_name": delivery.sales_order.customer.name
                        if delivery.sales_order
                        else "",
                        "delivery_date": delivery.delivery_date.strftime("%Y-%m-%d")
                        if delivery.delivery_date
                        else None,
                        "tracking_number": delivery.tracking_number or "",
                        "status": delivery.status,
                        "status_display": delivery.get_status_display(),
                        "items_count": delivery.items.count() if hasattr(delivery, "items") else 0,
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个发货单")

        except Exception as e:
            return ToolResult(success=False, error=f"查询发货单失败: {str(e)}")


class QuerySalesReturnsTool(BaseTool):
    """查询销售退货单工具"""

    name = "query_sales_returns"
    display_name = "查询退货单"
    description = "查询销售退货单列表，支持按状态、客户、日期范围筛选"
    category = "sales"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "退货状态（pending/approved/rejected/received/processed/cancelled）",
                    "enum": [
                        "pending",
                        "approved",
                        "rejected",
                        "received",
                        "processed",
                        "cancelled",
                    ],
                },
                "customer_id": {"type": "integer", "description": "客户ID"},
                "date_from": {"type": "string", "description": "开始日期（YYYY-MM-DD）"},
                "date_to": {"type": "string", "description": "结束日期（YYYY-MM-DD）"},
                "keyword": {"type": "string", "description": "搜索关键词（退货单号）"},
                "limit": {"type": "integer", "description": "返回结果数量限制（默认20）", "default": 20},
            },
        }

    def execute(
        self,
        status: str = None,
        customer_id: int = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            returns = SalesReturn.objects.filter(is_deleted=False)

            if status:
                returns = returns.filter(status=status)

            if customer_id:
                returns = returns.filter(sales_order__customer_id=customer_id)

            if date_from:
                returns = returns.filter(request_date__gte=date_from)

            if date_to:
                returns = returns.filter(request_date__lte=date_to)

            if keyword:
                returns = returns.filter(return_number__icontains=keyword)

            returns = returns.select_related("sales_order__customer").order_by("-request_date")[
                :limit
            ]

            # 格式化结果
            results = []
            for ret in returns:
                results.append(
                    {
                        "id": ret.id,
                        "return_number": ret.return_number,
                        "order_number": ret.sales_order.order_number if ret.sales_order else "",
                        "customer_name": ret.sales_order.customer.name if ret.sales_order else "",
                        "request_date": ret.request_date.strftime("%Y-%m-%d")
                        if ret.request_date
                        else None,
                        "return_reason": ret.return_reason,
                        "return_reason_display": ret.get_return_reason_display(),
                        "status": ret.status,
                        "status_display": ret.get_status_display(),
                        "refund_amount": float(ret.refund_amount) if ret.refund_amount else 0,
                        "items_count": ret.items.count() if hasattr(ret, "items") else 0,
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个退货单")

        except Exception as e:
            return ToolResult(success=False, error=f"查询退货单失败: {str(e)}")


class QuerySalesLoansTool(BaseTool):
    """查询借货单工具"""

    name = "query_sales_loans"
    display_name = "查询借货单"
    description = "查询销售借货单列表，支持按状态、客户、日期范围筛选"
    category = "sales"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "借货状态（pending/approved/rejected/borrowed/returned/cancelled）",
                    "enum": [
                        "pending",
                        "approved",
                        "rejected",
                        "borrowed",
                        "returned",
                        "cancelled",
                    ],
                },
                "customer_id": {"type": "integer", "description": "客户ID"},
                "date_from": {"type": "string", "description": "开始日期（YYYY-MM-DD）"},
                "date_to": {"type": "string", "description": "结束日期（YYYY-MM-DD）"},
                "keyword": {"type": "string", "description": "搜索关键词（借货单号）"},
                "limit": {"type": "integer", "description": "返回结果数量限制（默认20）", "default": 20},
            },
        }

    def execute(
        self,
        status: str = None,
        customer_id: int = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            loans = SalesLoan.objects.filter(is_deleted=False)

            if status:
                loans = loans.filter(status=status)

            if customer_id:
                loans = loans.filter(customer_id=customer_id)

            if date_from:
                loans = loans.filter(loan_date__gte=date_from)

            if date_to:
                loans = loans.filter(loan_date__lte=date_to)

            if keyword:
                loans = loans.filter(loan_number__icontains=keyword)

            loans = loans.select_related("customer").order_by("-loan_date")[:limit]

            # 格式化结果
            results = []
            for loan in loans:
                results.append(
                    {
                        "id": loan.id,
                        "loan_number": loan.loan_number,
                        "customer_name": loan.customer.name if loan.customer else "",
                        "loan_date": loan.loan_date.strftime("%Y-%m-%d")
                        if loan.loan_date
                        else None,
                        "expected_return_date": loan.expected_return_date.strftime("%Y-%m-%d")
                        if loan.expected_return_date
                        else None,
                        "status": loan.status,
                        "status_display": loan.get_status_display(),
                        "items_count": loan.items.count() if hasattr(loan, "items") else 0,
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个借货单")

        except Exception as e:
            return ToolResult(success=False, error=f"查询借货单失败: {str(e)}")


class GetDeliveryDetailTool(BaseTool):
    """获取发货单详情工具"""

    name = "get_delivery_detail"
    display_name = "获取发货单详情"
    description = "获取指定发货单的完整详情，包括明细、物流信息等"
    category = "sales"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"delivery_id": {"type": "integer", "description": "发货单ID"}},
            "required": ["delivery_id"],
        }

    def execute(self, delivery_id: int, **kwargs) -> ToolResult:
        """执行获取详情"""
        try:
            # 获取发货单
            try:
                delivery = Delivery.objects.get(id=delivery_id, is_deleted=False)
            except Delivery.DoesNotExist:
                return ToolResult(success=False, error=f"发货单ID {delivery_id} 不存在")

            # 获取发货明细
            items = []
            if hasattr(delivery, "items"):
                for item in delivery.items.filter(is_deleted=False):
                    items.append(
                        {
                            "product_name": item.product.name if item.product else "",
                            "product_code": item.product.code if item.product else "",
                            "quantity": float(item.quantity) if hasattr(item, "quantity") else 0,
                        }
                    )

            # 构建完整信息
            result = {
                "delivery_number": delivery.delivery_number,
                "sales_order": {
                    "id": delivery.sales_order.id,
                    "order_number": delivery.sales_order.order_number,
                }
                if delivery.sales_order
                else None,
                "customer": {
                    "id": delivery.sales_order.customer.id,
                    "name": delivery.sales_order.customer.name,
                }
                if delivery.sales_order and delivery.sales_order.customer
                else None,
                "delivery_date": delivery.delivery_date.strftime("%Y-%m-%d")
                if delivery.delivery_date
                else None,
                "tracking_number": delivery.tracking_number or "",
                "shipping_address": delivery.shipping_address or "",
                "status": delivery.status,
                "status_display": delivery.get_status_display(),
                "items": items,
                "created_at": delivery.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }

            return ToolResult(
                success=True, data=result, message=f"发货单 {delivery.delivery_number} 详情获取成功"
            )

        except Exception as e:
            return ToolResult(success=False, error=f"获取发货单详情失败: {str(e)}")
