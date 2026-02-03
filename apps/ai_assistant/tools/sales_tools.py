"""
销售模块工具

提供AI操作销售业务的工具集
"""

from typing import Dict, Any
from django.db.models import Q
from customers.models import Customer
from sales.models import Quote, SalesOrder
from products.models import Product
from .base_tool import BaseTool, ToolResult


class SearchCustomerTool(BaseTool):
    """搜索客户工具"""

    name = "search_customer"
    display_name = "搜索客户"
    description = "根据客户名称、编号或联系人搜索客户信息"
    category = "sales"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词（客户名称、编号或联系人）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认10）",
                    "default": 10
                }
            },
            "required": ["keyword"]
        }

    def execute(self, keyword: str, limit: int = 10, **kwargs) -> ToolResult:
        """执行搜索"""
        try:
            # 构建搜索查询
            customers = Customer.objects.filter(
                Q(name__icontains=keyword) |
                Q(code__icontains=keyword),
                is_deleted=False
            )[:limit]

            # 格式化结果
            results = []
            for customer in customers:
                results.append({
                    "id": customer.id,
                    "code": customer.code,
                    "name": customer.name,
                    "customer_level": customer.customer_level,
                    "status": customer.status,
                    "website": customer.website or "",
                    "tax_number": customer.tax_number or "",
                })

            return ToolResult(
                success=True,
                data=results,
                message=f"找到 {len(results)} 个客户"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"搜索客户失败: {str(e)}"
            )


class CreateSalesQuoteTool(BaseTool):
    """创建销售报价单工具"""

    name = "create_sales_quote"
    display_name = "创建销售报价单"
    description = "为客户创建销售报价单"
    category = "sales"
    risk_level = "medium"
    require_permission = "sales.add_quote"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "客户ID"
                },
                "items": {
                    "type": "array",
                    "description": "报价明细列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"},
                            "quantity": {"type": "number", "description": "数量"},
                            "unit_price": {"type": "number", "description": "含税单价"},
                        },
                        "required": ["product_id", "quantity", "unit_price"]
                    }
                },
                "valid_days": {
                    "type": "integer",
                    "description": "报价有效天数（默认30天）",
                    "default": 30
                },
                "notes": {
                    "type": "string",
                    "description": "备注说明"
                }
            },
            "required": ["customer_id", "items"]
        }

    def execute(self, customer_id: int, items: list,
                valid_days: int = 30, notes: str = "", **kwargs) -> ToolResult:
        """执行创建报价单"""
        try:
            from django.db import transaction
            from datetime import datetime, timedelta
            from core.utils import DocumentNumberGenerator

            # 验证客户
            try:
                customer = Customer.objects.get(id=customer_id, is_deleted=False)
            except Customer.DoesNotExist:
                return ToolResult(
                    success=False,
                    error=f"客户ID {customer_id} 不存在"
                )

            # 验证产品和计算金额
            total_amount = 0
            validated_items = []

            for item in items:
                try:
                    product = Product.objects.get(id=item['product_id'], is_deleted=False)
                except Product.DoesNotExist:
                    return ToolResult(
                        success=False,
                        error=f"产品ID {item['product_id']} 不存在"
                    )

                quantity = float(item['quantity'])
                unit_price = float(item['unit_price'])
                line_total = quantity * unit_price
                total_amount += line_total

                validated_items.append({
                    'product': product,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'line_total': line_total,
                })

            # 创建报价单
            with transaction.atomic():
                quote_number = DocumentNumberGenerator.generate('quotation')
                quote_date = datetime.now().date()
                valid_until = quote_date + timedelta(days=valid_days)

                quote = Quote.objects.create(
                    quote_number=quote_number,
                    customer=customer,
                    quote_date=quote_date,
                    valid_until=valid_until,
                    total_amount=total_amount,
                    notes=notes,
                    status='draft',
                    created_by=self.user
                )

                # 创建明细
                for item_data in validated_items:
                    from sales.models import QuoteItem
                    QuoteItem.objects.create(
                        quote=quote,
                        product=item_data['product'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        line_total=item_data['line_total'],
                        created_by=self.user
                    )

            return ToolResult(
                success=True,
                data={
                    "quote_id": quote.id,
                    "quote_number": quote.quote_number,
                    "customer_name": customer.name,
                    "total_amount": float(total_amount),
                    "items_count": len(validated_items),
                    "valid_until": valid_until.strftime("%Y-%m-%d"),
                },
                message=f"报价单 {quote.quote_number} 创建成功"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"创建报价单失败: {str(e)}"
            )


class QuerySalesOrdersTool(BaseTool):
    """查询销售订单工具"""

    name = "query_sales_orders"
    display_name = "查询销售订单"
    description = "查询销售订单列表，支持按状态、客户、日期范围筛选"
    category = "sales"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "订单状态（draft/pending/confirmed/completed/cancelled）",
                    "enum": ["draft", "pending", "confirmed", "in_production",
                            "ready_to_ship", "shipped", "delivered", "completed", "cancelled"]
                },
                "customer_id": {
                    "type": "integer",
                    "description": "客户ID"
                },
                "date_from": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）"
                },
                "date_to": {
                    "type": "string",
                    "description": "结束日期（YYYY-MM-DD）"
                },
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词（订单号）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认20）",
                    "default": 20
                }
            }
        }

    def execute(self, status: str = None, customer_id: int = None,
                date_from: str = None, date_to: str = None,
                keyword: str = None, limit: int = 20, **kwargs) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            orders = SalesOrder.objects.filter(is_deleted=False)

            if status:
                orders = orders.filter(status=status)

            if customer_id:
                orders = orders.filter(customer_id=customer_id)

            if date_from:
                orders = orders.filter(order_date__gte=date_from)

            if date_to:
                orders = orders.filter(order_date__lte=date_to)

            if keyword:
                orders = orders.filter(order_number__icontains=keyword)

            orders = orders.order_by('-order_date')[:limit]

            # 格式化结果
            results = []
            for order in orders:
                results.append({
                    "id": order.id,
                    "order_number": order.order_number,
                    "customer_name": order.customer.name,
                    "order_date": order.order_date.strftime("%Y-%m-%d"),
                    "total_amount": float(order.total_amount),
                    "status": order.status,
                    "status_display": order.get_status_display(),
                    "items_count": order.items.count(),
                })

            return ToolResult(
                success=True,
                data=results,
                message=f"找到 {len(results)} 个订单"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"查询订单失败: {str(e)}"
            )


class GetOrderDetailTool(BaseTool):
    """获取订单详情工具"""

    name = "get_order_detail"
    display_name = "获取订单详情"
    description = "获取指定销售订单的完整详情，包括明细、发货记录等"
    category = "sales"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "订单ID"
                }
            },
            "required": ["order_id"]
        }

    def execute(self, order_id: int, **kwargs) -> ToolResult:
        """执行获取详情"""
        try:
            # 获取订单
            try:
                order = SalesOrder.objects.get(id=order_id, is_deleted=False)
            except SalesOrder.DoesNotExist:
                return ToolResult(
                    success=False,
                    error=f"订单ID {order_id} 不存在"
                )

            # 获取订单明细
            items = []
            for item in order.items.filter(is_deleted=False):
                items.append({
                    "product_name": item.product.name,
                    "product_code": item.product.code,
                    "quantity": float(item.quantity),
                    "unit_price": float(item.unit_price),
                    "line_total": float(item.line_total),
                    "delivered_quantity": float(item.delivered_quantity),
                    "remaining_quantity": float(item.remaining_quantity),
                })

            # 获取发货记录
            deliveries = []
            for delivery in order.deliveries.filter(is_deleted=False):
                deliveries.append({
                    "delivery_number": delivery.delivery_number,
                    "delivery_date": delivery.delivery_date.strftime("%Y-%m-%d") if delivery.delivery_date else None,
                    "status": delivery.status,
                    "status_display": delivery.get_status_display(),
                })

            # 构建完整信息
            result = {
                "order_number": order.order_number,
                "customer": {
                    "id": order.customer.id,
                    "name": order.customer.name,
                    "contact_person": order.customer.contact_person or "",
                    "phone": order.customer.phone or "",
                },
                "order_date": order.order_date.strftime("%Y-%m-%d"),
                "delivery_date": order.delivery_date.strftime("%Y-%m-%d") if order.delivery_date else None,
                "total_amount": float(order.total_amount),
                "status": order.status,
                "status_display": order.get_status_display(),
                "notes": order.notes or "",
                "items": items,
                "deliveries": deliveries,
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": order.created_by.username if order.created_by else "",
            }

            return ToolResult(
                success=True,
                data=result,
                message=f"订单 {order.order_number} 详情获取成功"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"获取订单详情失败: {str(e)}"
            )


class ApproveSalesOrderTool(BaseTool):
    """审核销售订单工具"""

    name = "approve_sales_order"
    display_name = "审核销售订单"
    description = "审核销售订单，审核通过后会自动创建发货单和应收账款"
    category = "sales"
    risk_level = "high"  # 高风险操作
    require_permission = "sales.change_salesorder"
    require_approval = True  # 需要用户确认

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "订单ID"
                },
                "notes": {
                    "type": "string",
                    "description": "审核备注"
                }
            },
            "required": ["order_id"]
        }

    def execute(self, order_id: int, notes: str = "", **kwargs) -> ToolResult:
        """执行审核"""
        try:
            # 获取订单
            try:
                order = SalesOrder.objects.get(id=order_id, is_deleted=False)
            except SalesOrder.DoesNotExist:
                return ToolResult(
                    success=False,
                    error=f"订单ID {order_id} 不存在"
                )

            # 检查订单状态
            if order.status != 'pending':
                return ToolResult(
                    success=False,
                    error=f"订单状态为 {order.get_status_display()}，不是待审核状态"
                )

            # 执行审核
            order.approve_order(approved_by_user=self.user)

            return ToolResult(
                success=True,
                data={
                    "order_number": order.order_number,
                    "status": order.status,
                    "status_display": order.get_status_display(),
                },
                message=f"订单 {order.order_number} 审核成功，已自动创建发货单和应收账款"
            )

        except Exception as e:
             return ToolResult(
                success=False,
                error=f"审核订单失败: {str(e)}"
            )


class CreateSalesOrderTool(BaseTool):
    """创建销售订单工具"""

    name = "create_sales_order"
    display_name = "创建销售订单"
    description = "为客户创建销售订单"
    category = "sales"
    risk_level = "medium"
    require_permission = "sales.add_order"
    require_approval = True  # 需要用户确认
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "客户ID"
                },
                "items": {
                    "type": "array",
                    "description": "订单明细列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "integer",
                                "description": "产品ID"
                            },
                            "quantity": {
                                "type": "number",
                                "description": "数量"
                            },
                            "unit_price": {
                                "type": "number",
                                "description": "含税单价"
                            }
                        },
                        "required": ["product_id", "quantity", "unit_price"]
                    }
                },
                "delivery_address": {
                    "type": "string",
                    "description": "交付地址（可选）"
                },
                "notes": {
                    "type": "string",
                    "description": "订单备注（可选）"
                }
            },
            "required": ["customer_id", "items"]
        }
    
    def execute(self, customer_id: int, items: list,
                 delivery_address: str = "", notes: str = "", **kwargs) -> ToolResult:
        """执行创建订单"""
        try:
            from django.db import transaction
            from datetime import datetime, timedelta
            from core.utils import DocumentNumberGenerator
            
            # 验证客户
            try:
                from customers.models import Customer
                customer = Customer.objects.get(id=customer_id, is_deleted=False)
            except Customer.DoesNotExist:
                return ToolResult(
                    success=False,
                    error=f"客户ID {customer_id} 不存在"
                )
            
            # 验证产品和计算金额
            total_amount = 0
            validated_items = []
            
            for item in items:
                try:
                    from products.models import Product
                    product = Product.objects.get(id=item['product_id'], is_deleted=False)
                except Product.DoesNotExist:
                    return ToolResult(
                        success=False,
                        error=f"产品ID {item['product_id']} 不存在"
                    )
                
                quantity = float(item['quantity'])
                unit_price = float(item['unit_price'])
                line_total = quantity * unit_price
                total_amount += line_total
                
                validated_items.append({
                    'product': product,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'line_total': line_total
                })
            
            # 创建订单
            with transaction.atomic():
                order_number = DocumentNumberGenerator.generate('sales_order')
                order_date = datetime.now().date()
                delivery_date = order_date + timedelta(days=30)  # 默认 30 天后交货
                
                from sales.models import SalesOrder
                order = SalesOrder.objects.create(
                    order_number=order_number,
                    customer=customer,
                    order_date=order_date,
                    total_amount=total_amount,
                    delivery_address=delivery_address or customer.address or "",
                    notes=notes,
                    status='pending',  # 默认待审核
                    created_by=self.user
                )
                
                # 创建明细
                from sales.models import SalesOrderItem
                for i, item_data in enumerate(validated_items, 1):
                    product = item_data['product']
                    SalesOrderItem.objects.create(
                        order=order,
                        product=product,
                        product_code=product.code,
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        line_total=item_data['line_total'],
                        sequence=i,
                        created_by=self.user
                    )
                
                return ToolResult(
                    success=True,
                    data={
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "customer_name": customer.name,
                        "total_amount": float(total_amount),
                        "items_count": len(validated_items),
                        "delivery_date": delivery_date.strftime("%Y-%m-%d"),
                    },
                    message=f"订单 {order.order_number} 创建成功，包含 {len(validated_items)} 个明细"
                )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"创建销售订单失败: {str(e)}"
            )
