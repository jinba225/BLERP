"""
报表模块工具

提供AI生成各类业务报表的工具集
"""

from typing import Dict, Any
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from apps.sales.models import SalesOrder
from apps.purchase.models import PurchaseOrder
from apps.inventory.models import InventoryStock, InventoryTransaction
from .base_tool import BaseTool, ToolResult


class GenerateSalesReportTool(BaseTool):
    """生成销售报表工具"""

    name = "generate_sales_report"
    display_name = "生成销售报表"
    description = "生成指定时间段的销售报表，包含销售额、订单数等统计"
    category = "report"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）"
                },
                "date_to": {
                    "type": "string",
                    "description": "结束日期（YYYY-MM-DD）"
                },
                "group_by": {
                    "type": "string",
                    "description": "分组方式（day/month/customer）",
                    "enum": ["day", "month", "customer"],
                    "default": "day"
                }
            },
            "required": ["date_from", "date_to"]
        }

    def execute(self, date_from: str, date_to: str,
                group_by: str = "day", **kwargs) -> ToolResult:
        """执行生成报表"""
        try:
            # 验证日期格式
            try:
                start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                return ToolResult(
                    success=False,
                    error="日期格式错误，应为 YYYY-MM-DD"
                )

            # 查询订单
            orders = SalesOrder.objects.filter(
                order_date__gte=start_date,
                order_date__lte=end_date,
                is_deleted=False
            ).exclude(status='cancelled')

            # 总体统计
            total_orders = orders.count()
            total_amount = orders.aggregate(total=Sum('total_amount'))['total'] or 0

            # 按状态统计
            status_stats = {}
            for status_choice in SalesOrder.STATUS_CHOICES:
                status = status_choice[0]
                count = orders.filter(status=status).count()
                amount = orders.filter(status=status).aggregate(
                    total=Sum('total_amount'))['total'] or 0
                status_stats[status] = {
                    "count": count,
                    "amount": float(amount),
                    "display": status_choice[1]
                }

            # 分组统计
            grouped_data = []
            if group_by == "customer":
                customer_stats = orders.values('customer__name').annotate(
                    order_count=Count('id'),
                    total_amount=Sum('total_amount')
                ).order_by('-total_amount')[:10]

                for stat in customer_stats:
                    grouped_data.append({
                        "customer_name": stat['customer__name'],
                        "order_count": stat['order_count'],
                        "total_amount": float(stat['total_amount']),
                    })

            elif group_by == "day":
                # 按天统计（简化版）
                current_date = start_date
                while current_date <= end_date:
                    day_orders = orders.filter(order_date=current_date)
                    day_count = day_orders.count()
                    day_amount = day_orders.aggregate(
                        total=Sum('total_amount'))['total'] or 0

                    grouped_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "order_count": day_count,
                        "total_amount": float(day_amount),
                    })

                    current_date += timedelta(days=1)

            return ToolResult(
                success=True,
                data={
                    "period": {
                        "start_date": date_from,
                        "end_date": date_to,
                    },
                    "summary": {
                        "total_orders": total_orders,
                        "total_amount": float(total_amount),
                    },
                    "status_breakdown": status_stats,
                    "grouped_data": grouped_data,
                },
                message=f"销售报表生成成功，共 {total_orders} 个订单，总金额 {float(total_amount)} 元"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"生成销售报表失败: {str(e)}"
            )


class GeneratePurchaseReportTool(BaseTool):
    """生成采购报表工具"""

    name = "generate_purchase_report"
    display_name = "生成采购报表"
    description = "生成指定时间段的采购报表，包含采购额、订单数等统计"
    category = "report"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）"
                },
                "date_to": {
                    "type": "string",
                    "description": "结束日期（YYYY-MM-DD）"
                },
                "group_by": {
                    "type": "string",
                    "description": "分组方式（day/month/supplier）",
                    "enum": ["day", "month", "supplier"],
                    "default": "day"
                }
            },
            "required": ["date_from", "date_to"]
        }

    def execute(self, date_from: str, date_to: str,
                group_by: str = "day", **kwargs) -> ToolResult:
        """执行生成报表"""
        try:
            # 验证日期格式
            try:
                start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                return ToolResult(
                    success=False,
                    error="日期格式错误，应为 YYYY-MM-DD"
                )

            # 查询订单
            orders = PurchaseOrder.objects.filter(
                order_date__gte=start_date,
                order_date__lte=end_date,
                is_deleted=False
            ).exclude(status='cancelled')

            # 总体统计
            total_orders = orders.count()
            total_amount = orders.aggregate(total=Sum('total_amount'))['total'] or 0

            # 按状态统计
            status_stats = {}
            for status_choice in PurchaseOrder.STATUS_CHOICES:
                status = status_choice[0]
                count = orders.filter(status=status).count()
                amount = orders.filter(status=status).aggregate(
                    total=Sum('total_amount'))['total'] or 0
                status_stats[status] = {
                    "count": count,
                    "amount": float(amount),
                    "display": status_choice[1]
                }

            # 分组统计
            grouped_data = []
            if group_by == "supplier":
                supplier_stats = orders.values('supplier__name').annotate(
                    order_count=Count('id'),
                    total_amount=Sum('total_amount')
                ).order_by('-total_amount')[:10]

                for stat in supplier_stats:
                    grouped_data.append({
                        "supplier_name": stat['supplier__name'],
                        "order_count": stat['order_count'],
                        "total_amount": float(stat['total_amount']),
                    })

            return ToolResult(
                success=True,
                data={
                    "period": {
                        "start_date": date_from,
                        "end_date": date_to,
                    },
                    "summary": {
                        "total_orders": total_orders,
                        "total_amount": float(total_amount),
                    },
                    "status_breakdown": status_stats,
                    "grouped_data": grouped_data,
                },
                message=f"采购报表生成成功，共 {total_orders} 个订单，总金额 {float(total_amount)} 元"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"生成采购报表失败: {str(e)}"
            )


class GenerateInventoryReportTool(BaseTool):
    """生成库存报表工具"""

    name = "generate_inventory_report"
    display_name = "生成库存报表"
    description = "生成当前库存报表，包含库存总量、金额等统计"
    category = "report"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "warehouse_id": {
                    "type": "integer",
                    "description": "仓库ID（可选，不指定则统计所有仓库）"
                },
                "low_stock_only": {
                    "type": "boolean",
                    "description": "是否只显示低库存产品（默认false）",
                    "default": False
                }
            }
        }

    def execute(self, warehouse_id: int = None,
                low_stock_only: bool = False, **kwargs) -> ToolResult:
        """执行生成报表"""
        try:
            from apps.products.models import Product

            # 查询库存
            inventories = InventoryStock.objects.filter(is_deleted=False)

            if warehouse_id:
                inventories = inventories.filter(warehouse_id=warehouse_id)

            # 按产品汇总
            product_stats = inventories.values('product__id', 'product__code',
                                              'product__name', 'product__min_stock').annotate(
                total_quantity=Sum('quantity')
            )

            # 格式化结果
            items = []
            total_items = 0
            low_stock_items = 0

            for stat in product_stats:
                quantity = float(stat['total_quantity'])
                min_stock = float(stat['product__min_stock'] or 0)
                is_low_stock = quantity < min_stock if min_stock > 0 else False

                # 如果只看低库存，过滤
                if low_stock_only and not is_low_stock:
                    continue

                items.append({
                    "product_id": stat['product__id'],
                    "product_code": stat['product__code'],
                    "product_name": stat['product__name'],
                    "quantity": quantity,
                    "min_stock": min_stock,
                    "is_low_stock": is_low_stock,
                })

                total_items += 1
                if is_low_stock:
                    low_stock_items += 1

            return ToolResult(
                success=True,
                data={
                    "summary": {
                        "total_items": total_items,
                        "low_stock_items": low_stock_items,
                    },
                    "items": items,
                },
                message=f"库存报表生成成功，共 {total_items} 个产品，其中 {low_stock_items} 个库存不足"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"生成库存报表失败: {str(e)}"
            )
