"""
采购模块工具

提供AI操作采购业务的工具集
"""

from typing import Dict, Any
from django.db.models import Q
from suppliers.models import Supplier
from purchase.models import PurchaseRequest, PurchaseOrder
from products.models import Product
from .base_tool import BaseTool, ToolResult


class SearchSupplierTool(BaseTool):
    """搜索供应商工具"""

    name = "search_supplier"
    display_name = "搜索供应商"
    description = "根据供应商名称、编号或联系人搜索供应商信息"
    category = "purchase"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词（供应商名称、编号或联系人）"
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
            suppliers = Supplier.objects.filter(
                Q(name__icontains=keyword) |
                Q(code__icontains=keyword) |
                Q(contact_person__icontains=keyword),
                is_deleted=False
            )[:limit]

            # 格式化结果
            results = []
            for supplier in suppliers:
                results.append({
                    "id": supplier.id,
                    "code": supplier.code,
                    "name": supplier.name,
                    "contact_person": supplier.contact_person or "",
                    "phone": supplier.phone or "",
                    "email": supplier.email or "",
                    "address": supplier.address or "",
                    "supplier_type": supplier.get_supplier_type_display(),
                    "is_active": supplier.is_active,
                })

            return ToolResult(
                success=True,
                data=results,
                message=f"找到 {len(results)} 个供应商"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"搜索供应商失败: {str(e)}"
            )


class CreatePurchaseRequestTool(BaseTool):
    """创建采购申请单工具"""

    name = "create_purchase_request"
    display_name = "创建采购申请单"
    description = "创建采购申请单，用于申请采购物料"
    category = "purchase"
    risk_level = "medium"
    require_permission = "purchase.add_purchaserequest"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "description": "采购申请明细列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"},
                            "quantity": {"type": "number", "description": "申请数量"},
                            "required_date": {"type": "string", "description": "需求日期（YYYY-MM-DD）"},
                            "purpose": {"type": "string", "description": "用途说明"},
                        },
                        "required": ["product_id", "quantity"]
                    }
                },
                "urgency": {
                    "type": "string",
                    "description": "紧急程度（normal/urgent/very_urgent）",
                    "enum": ["normal", "urgent", "very_urgent"],
                    "default": "normal"
                },
                "notes": {
                    "type": "string",
                    "description": "备注说明"
                }
            },
            "required": ["items"]
        }

    def execute(self, items: list, urgency: str = "normal",
                notes: str = "", **kwargs) -> ToolResult:
        """执行创建采购申请"""
        try:
            from django.db import transaction
            from datetime import datetime
            from core.utils import DocumentNumberGenerator

            # 验证产品
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
                required_date = item.get('required_date')
                if required_date:
                    try:
                        required_date = datetime.strptime(required_date, '%Y-%m-%d').date()
                    except ValueError:
                        return ToolResult(
                            success=False,
                            error=f"需求日期格式错误，应为 YYYY-MM-DD"
                        )

                validated_items.append({
                    'product': product,
                    'quantity': quantity,
                    'required_date': required_date,
                    'purpose': item.get('purpose', ''),
                })

            # 创建采购申请
            with transaction.atomic():
                request_number = DocumentNumberGenerator.generate('purchase_request')

                purchase_request = PurchaseRequest.objects.create(
                    request_number=request_number,
                    request_date=datetime.now().date(),
                    urgency=urgency,
                    notes=notes,
                    status='draft',
                    created_by=self.user
                )

                # 创建明细
                for item_data in validated_items:
                    from purchase.models import PurchaseRequestItem
                    PurchaseRequestItem.objects.create(
                        purchase_request=purchase_request,
                        product=item_data['product'],
                        quantity=item_data['quantity'],
                        required_date=item_data['required_date'],
                        purpose=item_data['purpose'],
                        created_by=self.user
                    )

            return ToolResult(
                success=True,
                data={
                    "request_id": purchase_request.id,
                    "request_number": purchase_request.request_number,
                    "items_count": len(validated_items),
                    "urgency": urgency,
                    "urgency_display": purchase_request.get_urgency_display(),
                },
                message=f"采购申请单 {purchase_request.request_number} 创建成功"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"创建采购申请失败: {str(e)}"
            )


class QueryPurchaseOrdersTool(BaseTool):
    """查询采购订单工具"""

    name = "query_purchase_orders"
    display_name = "查询采购订单"
    description = "查询采购订单列表，支持按状态、供应商、日期范围筛选"
    category = "purchase"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "订单状态（draft/pending/confirmed/in_progress/completed/cancelled）",
                    "enum": ["draft", "pending", "confirmed", "in_progress",
                            "partially_received", "received", "completed", "cancelled"]
                },
                "supplier_id": {
                    "type": "integer",
                    "description": "供应商ID"
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

    def execute(self, status: str = None, supplier_id: int = None,
                date_from: str = None, date_to: str = None,
                keyword: str = None, limit: int = 20, **kwargs) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            orders = PurchaseOrder.objects.filter(is_deleted=False)

            if status:
                orders = orders.filter(status=status)

            if supplier_id:
                orders = orders.filter(supplier_id=supplier_id)

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
                    "supplier_name": order.supplier.name,
                    "order_date": order.order_date.strftime("%Y-%m-%d"),
                    "total_amount": float(order.total_amount),
                    "status": order.status,
                    "status_display": order.get_status_display(),
                    "items_count": order.items.count(),
                })

            return ToolResult(
                success=True,
                data=results,
                message=f"找到 {len(results)} 个采购订单"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"查询采购订单失败: {str(e)}"
            )


class ApprovePurchaseOrderTool(BaseTool):
    """审核采购订单工具"""

    name = "approve_purchase_order"
    display_name = "审核采购订单"
    description = "审核采购订单，审核通过后可以进行收货"
    category = "purchase"
    risk_level = "high"  # 高风险操作
    require_permission = "purchase.change_purchaseorder"
    require_approval = True  # 需要用户确认

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "采购订单ID"
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
                order = PurchaseOrder.objects.get(id=order_id, is_deleted=False)
            except PurchaseOrder.DoesNotExist:
                return ToolResult(
                    success=False,
                    error=f"采购订单ID {order_id} 不存在"
                )

            # 检查订单状态
            if order.status != 'pending':
                return ToolResult(
                    success=False,
                    error=f"订单状态为 {order.get_status_display()}，不是待审核状态"
                )

            # 执行审核
            order.status = 'confirmed'
            if notes:
                order.notes = (order.notes or '') + f"\n审核备注: {notes}"
            order.save()

            return ToolResult(
                success=True,
                data={
                    "order_number": order.order_number,
                    "status": order.status,
                    "status_display": order.get_status_display(),
                },
                message=f"采购订单 {order.order_number} 审核成功"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"审核采购订单失败: {str(e)}"
            )
