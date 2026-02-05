"""
智能助手服务

提供上下文感知的建议、自动补全和历史记录分析
"""

from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta


class IntelligentAssistant:
    """
    智能助手

    基于上下文和历史记录提供智能建议和自动补全
    """

    def __init__(self, user):
        """
        初始化智能助手

        Args:
            user: 当前用户
        """
        self.user = user

    def get_suggestions(self, current_context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        根据当前上下文提供操作建议

        Args:
            current_context: 当前对话上下文

        Returns:
            建议列表
        """
        suggestions = []

        # 根据最近的对话内容提供建议
        last_intents = current_context.get("recent_intents", [])
        last_entities = current_context.get("recent_entities", {})

        # 如果用户最近在查询客户信息
        if "query_customer" in last_intents:
            customer_name = last_entities.get("customer_name")
            suggestions.append({
                "action": "create_order",
                "suggestion": f"为 {customer_name} 创建销售订单",
                "reason": "刚查询了客户信息，可能需要创建订单"
            })
            suggestions.append({
                "action": "create_quote",
                "suggestion": f"为 {customer_name} 创建报价单",
                "reason": "可以先创建报价单"
            })

        # 如果用户最近在查询订单
        elif "query_order" in last_intents:
            suggestions.append({
                "action": "get_order_detail",
                "suggestion": "查看订单详情",
                "reason": "可以查看订单的详细信息"
            })
            suggestions.append({
                "action": "create_delivery",
                "suggestion": "为订单创建发货单",
                "reason": "订单可能需要发货"
            })

        # 如果用户最近在查询库存
        elif "query_inventory" in last_intents or "query_product" in last_intents:
            product_name = last_entities.get("product_name")
            suggestions.append({
                "action": "create_inbound",
                "suggestion": f"创建 {product_name} 的入库单",
                "reason": "产品库存可能需要补充"
            })

        # 如果用户最近在创建单据
        elif "create_" in last_intents:
            suggestions.append({
                "action": "query_recent",
                "suggestion": "查看最近创建的单据",
                "reason": "确认创建是否成功"
            })

        return suggestions

    def autocomplete_parameter(self, param_name: str, partial_value: str,
                           context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        自动补全参数

        Args:
            param_name: 参数名称
            partial_value: 部分值
            context: 当前上下文

        Returns:
            补全建议列表
        """
        suggestions = []

        if param_name == "customer_name":
            # 客户名称自动补全
            suggestions = self._autocomplete_customer(partial_value, context)

        elif param_name == "supplier_name":
            # 供应商名称自动补全
            suggestions = self._autocomplete_supplier(partial_value, context)

        elif param_name == "product_name":
            # 产品名称自动补全
            suggestions = self._autocomplete_product(partial_value, context)

        elif param_name == "warehouse_name":
            # 仓库名称自动补全
            suggestions = self._autocomplete_warehouse(partial_value, context)

        elif param_name == "order_number":
            # 订单号自动补全
            suggestions = self._autocomplete_order(partial_value, context)

        return suggestions

    def _autocomplete_customer(self, partial: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """自动补全客户名称"""
        from customers.models import Customer

        customers = Customer.objects.filter(
            Q(name__icontains=partial) | Q(code__icontains=partial),
            is_deleted=False
        )[:5]

        return [
            {
                "value": customer.name,
                "display": f"{customer.name} ({customer.code})",
                "type": "customer",
                "id": customer.id
            }
            for customer in customers
        ]

    def _autocomplete_supplier(self, partial: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """自动补全供应商名称"""
        from suppliers.models import Supplier

        suppliers = Supplier.objects.filter(
            Q(name__icontains=partial) | Q(code__icontains=partial),
            is_deleted=False
        )[:5]

        return [
            {
                "value": supplier.name,
                "display": f"{supplier.name} ({supplier.code})",
                "type": "supplier",
                "id": supplier.id
            }
            for supplier in suppliers
        ]

    def _autocomplete_product(self, partial: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """自动补全产品名称"""
        from products.models import Product

        products = Product.objects.filter(
            Q(name__icontains=partial) | Q(code__icontains=partial),
            is_deleted=False
        )[:5]

        return [
            {
                "value": product.name,
                "display": f"{product.name} ({product.code})",
                "type": "product",
                "id": product.id,
                "stock_info": self._get_product_stock_info(product)
            }
            for product in products
        ]

    def _autocomplete_warehouse(self, partial: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """自动补全仓库名称"""
        from inventory.models import Warehouse

        warehouses = Warehouse.objects.filter(
            Q(name__icontains=partial) | Q(code__icontains=partial),
            is_deleted=False,
            is_active=True
        )[:5]

        return [
            {
                "value": warehouse.name,
                "display": f"{warehouse.name} ({warehouse.code})",
                "type": "warehouse",
                "id": warehouse.id
            }
            for warehouse in warehouses
        ]

    def _autocomplete_order(self, partial: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """自动补全订单号"""
        from sales.models import SalesOrder
        from purchase.models import PurchaseOrder

        results = []

        # 搜索销售订单
        sales_orders = SalesOrder.objects.filter(
            order_number__icontains=partial,
            is_deleted=False
        )[:3]

        for order in sales_orders:
            results.append({
                "value": order.order_number,
                "display": f"销售订单 {order.order_number} ({order.get_status_display()})",
                "type": "sales_order",
                "id": order.id
            })

        # 搜索采购订单
        purchase_orders = PurchaseOrder.objects.filter(
            order_number__icontains=partial,
            is_deleted=False
        )[:3]

        for order in purchase_orders:
            results.append({
                "value": order.order_number,
                "display": f"采购订单 {order.order_number} ({order.get_status_display()})",
                "type": "purchase_order",
                "id": order.id
            })

        return results

    def _get_product_stock_info(self, product) -> str:
        """获取产品库存信息"""
        try:
            from inventory.models import InventoryStock

            stocks = InventoryStock.objects.filter(
                product=product,
                is_deleted=False
            )

            if not stocks:
                return "无库存"

            total_available = sum(stock.quantity_available for stock in stocks)
            total_on_order = sum(stock.quantity_on_order for stock in stocks)

            return f"可用:{total_available}, 在途:{total_on_order}"
        except:
            return "库存未知"

    def get_recent_entities(self, entity_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取最近使用的实体（客户、供应商、产品等）

        Args:
            entity_type: 实体类型（customer, supplier, product等）
            limit: 返回数量限制

        Returns:
            最近使用的实体列表
        """
        # TODO: 从历史记录中获取
        # 这里提供一个简单的实现

        if entity_type == "customer":
            from customers.models import Customer
            entities = Customer.objects.filter(
                is_deleted=False
            ).order_by('-updated_at')[:limit]

            return [
                {
                    "id": entity.id,
                    "name": entity.name,
                    "code": entity.code,
                    "last_used": entity.updated_at.strftime("%Y-%m-%d")
                }
                for entity in entities
            ]

        elif entity_type == "supplier":
            from suppliers.models import Supplier
            entities = Supplier.objects.filter(
                is_deleted=False
            ).order_by('-updated_at')[:limit]

            return [
                {
                    "id": entity.id,
                    "name": entity.name,
                    "code": entity.code,
                    "last_used": entity.updated_at.strftime("%Y-%m-%d")
                }
                for entity in entities
            ]

        return []

    def get_usage_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        获取使用统计

        Args:
            days: 统计天数

        Returns:
            使用统计信息
        """
        # TODO: 从工具执行日志中统计
        # 这里返回一个示例结构

        from datetime import date, timedelta
        start_date = date.today() - timedelta(days=days)

        return {
            "period": f"最近{days}天",
            "total_executions": 0,
            "tool_usage": {},
            "success_rate": 0.0,
            "most_used_tools": [],
            "average_response_time": 0.0
        }

    def detect_repeated_operation(self, context: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        检测重复操作

        Args:
            context: 当前上下文

        Returns:
            重复操作警告，如果没有重复则返回None
        """
        recent_actions = context.get("recent_actions", [])

        if len(recent_actions) < 2:
            return None

        # 检查最近的操作是否相同
        last_action = recent_actions[0]
        second_last_action = recent_actions[1]

        if (last_action.get("tool") == second_last_action.get("tool") and
            last_action.get("params") == second_last_action.get("params")):

            return {
                "warning": "重复操作",
                "message": f"您刚刚执行了相同的操作（{last_action.get('tool')}），是否确认再次执行？",
                "tool": last_action.get("tool"),
                "params": last_action.get("params")
            }

        return None

    def suggest_next_step(self, last_result: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """
        根据上一个操作结果建议下一步操作

        Args:
            last_result: 上一个工具执行结果
            context: 当前上下文

        Returns:
            建议的下一步操作列表
        """
        suggestions = []

        success = last_result.get("success", False)
        tool_name = last_result.get("tool", "")
        data = last_result.get("data", {})

        if not success:
            return suggestions

        # 根据不同的工具类型提供建议
        if tool_name == "query_sales_orders":
            suggestions.append("查看某个订单的详细信息")
            suggestions.append("为订单创建发货单")

        elif tool_name == "create_sales_order":
            order_number = data.get("order_number")
            suggestions.append(f"审核订单 {order_number}")
            suggestions.append("创建发货单")

        elif tool_name == "get_order_detail":
            status = data.get("status")
            order_number = data.get("order_number")
            if status == "pending":
                suggestions.append(f"审核订单 {order_number}")
            elif status in ["confirmed", "in_production", "ready_to_ship"]:
                suggestions.append(f"创建发货单")

        elif tool_name == "create_delivery":
            delivery_number = data.get("delivery_number")
            suggestions.append(f"确认发货 {delivery_number}")
            suggestions.append("填写快递单号")

        elif tool_name == "query_expenses":
            suggestions.append("创建费用报销")
            suggestions.append("查看费用统计")

        # 根据数据状态提供建议
        if "items_count" in data:
            items_count = data["items_count"]
            if items_count > 0:
                suggestions.append(f"查看{items_count}个明细的详细信息")

        return suggestions


class ContextManager:
    """
    上下文管理器

    管理对话上下文和历史记录
    """

    def __init__(self, user, session_id: str = None):
        """
        初始化上下文管理器

        Args:
            user: 当前用户
            session_id: 会话ID
        """
        self.user = user
        self.session_id = session_id or str(user.id)
        self.context = self._load_context()

    def _load_context(self) -> Dict[str, Any]:
        """从缓存或数据库加载上下文"""
        from django.core.cache import cache

        cache_key = f"erp_context:{self.session_id}"
        context = cache.get(cache_key)

        if context:
            return context

        # 创建新上下文
        return {
            "session_id": self.session_id,
            "created_at": timezone.now().isoformat(),
            "recent_intents": [],
            "recent_entities": {},
            "recent_actions": [],
            "conversation_history": []
        }

    def _save_context(self):
        """保存上下文到缓存"""
        from django.core.cache import cache

        cache_key = f"erp_context:{self.session_id}"
        # 缓存1小时
        cache.set(cache_key, self.context, 3600)

    def add_intent(self, intent: str, entities: Dict[str, Any]):
        """添加意图到上下文"""
        self.context["recent_intents"].append(intent)
        # 只保留最近10个意图
        self.context["recent_intents"] = self.context["recent_intents"][-10:]
        self._save_context()

    def add_entities(self, entities: Dict[str, Any]):
        """添加实体到上下文"""
        self.context["recent_entities"].update(entities)
        self._save_context()

    def add_action(self, tool_name: str, params: Dict[str, Any], result: Dict[str, Any]):
        """添加操作到上下文"""
        action = {
            "tool": tool_name,
            "params": params,
            "timestamp": timezone.now().isoformat(),
            "success": result.get("success", False)
        }
        self.context["recent_actions"].append(action)
        # 只保留最近10个操作
        self.context["recent_actions"] = self.context["recent_actions"][-10:]
        self._save_context()

    def get_context(self) -> Dict[str, Any]:
        """获取当前上下文"""
        return self.context.copy()

    def clear_context(self):
        """清空上下文"""
        self.context = {
            "session_id": self.session_id,
            "created_at": timezone.now().isoformat(),
            "recent_intents": [],
            "recent_entities": {},
            "recent_actions": [],
            "conversation_history": []
        }
        self._save_context()
