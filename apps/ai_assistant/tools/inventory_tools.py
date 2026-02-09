"""
库存模块工具

提供AI操作库存业务的工具集
"""

from typing import Any, Dict

from django.db.models import Q, Sum
from inventory.models import InventoryStock
from products.models import Product

from .base_tool import BaseTool, ToolResult


class CheckInventoryTool(BaseTool):
    """检查库存工具"""

    name = "check_inventory"
    display_name = "检查库存"
    description = "检查指定产品的库存情况"
    category = "inventory"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer", "description": "产品ID"},
                "warehouse_id": {"type": "integer", "description": "仓库ID（可选，不指定则查询所有仓库）"},
            },
            "required": ["product_id"],
        }

    def execute(self, product_id: int, warehouse_id: int = None, **kwargs) -> ToolResult:
        """执行检查"""
        try:
            # 验证产品
            try:
                product = Product.objects.get(id=product_id, is_deleted=False)
            except Product.DoesNotExist:
                return ToolResult(success=False, error=f"产品ID {product_id} 不存在")

            # 查询库存
            inventories = InventoryStock.objects.filter(product=product, is_deleted=False)

            if warehouse_id:
                inventories = inventories.filter(warehouse_id=warehouse_id)

            # 格式化结果
            results = []
            total_quantity = 0

            for inv in inventories:
                results.append(
                    {
                        "warehouse_id": inv.warehouse.id,
                        "warehouse_name": inv.warehouse.name,
                        "quantity": float(inv.quantity),
                        "unit": product.unit,
                    }
                )
                total_quantity += float(inv.quantity)

            return ToolResult(
                success=True,
                data={
                    "product": {
                        "id": product.id,
                        "code": product.code,
                        "name": product.name,
                        "unit": product.unit,
                    },
                    "total_quantity": total_quantity,
                    "inventories": results,
                },
                message=f"产品 {product.name} 总库存: {total_quantity} {product.unit}",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"检查库存失败: {str(e)}")


class SearchProductTool(BaseTool):
    """搜索产品工具"""

    name = "search_product"
    display_name = "搜索产品"
    description = "根据产品名称、编号或规格搜索产品信息"
    category = "inventory"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "搜索关键词（产品名称、编号或规格）"},
                "limit": {"type": "integer", "description": "返回结果数量限制（默认10）", "default": 10},
            },
            "required": ["keyword"],
        }

    def execute(self, keyword: str, limit: int = 10, **kwargs) -> ToolResult:
        """执行搜索"""
        try:
            # 构建搜索查询
            products = Product.objects.filter(
                Q(name__icontains=keyword) | Q(code__icontains=keyword), is_deleted=False
            )[:limit]

            # 格式化结果
            results = []
            for product in products:
                results.append(
                    {
                        "id": product.id,
                        "code": product.code,
                        "name": product.name,
                        "specifications": product.specifications or "",
                        "unit": product.unit.symbol if product.unit else "",
                        "category": product.category.name if product.category else "",
                        "status": product.status,
                        "product_type": product.product_type,
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个产品")

        except Exception as e:
            return ToolResult(success=False, error=f"搜索产品失败: {str(e)}")


class GetLowStockAlertTool(BaseTool):
    """获取低库存预警工具"""

    name = "get_low_stock_alert"
    display_name = "获取低库存预警"
    description = "获取库存不足的产品列表"
    category = "inventory"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "返回结果数量限制（默认20）", "default": 20}
            },
        }

    def execute(self, limit: int = 20, **kwargs) -> ToolResult:
        """执行获取预警"""
        try:
            # 获取所有有最小库存要求的产品
            products = Product.objects.filter(min_stock__gt=0, is_deleted=False)[
                : limit * 2
            ]  # 多获取一些，因为需要过滤

            # 检查库存
            alerts = []
            for product in products:
                total_inventory = (
                    InventoryStock.objects.filter(product=product, is_deleted=False).aggregate(
                        total=Sum("quantity")
                    )["total"]
                    or 0
                )

                if total_inventory < product.min_stock:
                    alerts.append(
                        {
                            "product_id": product.id,
                            "product_code": product.code,
                            "product_name": product.name,
                            "current_stock": float(total_inventory),
                            "min_stock": float(product.min_stock),
                            "shortage": float(product.min_stock - total_inventory),
                            "unit": product.unit,
                        }
                    )

                if len(alerts) >= limit:
                    break

            return ToolResult(success=True, data=alerts, message=f"发现 {len(alerts)} 个产品库存不足")

        except Exception as e:
            return ToolResult(success=False, error=f"获取低库存预警失败: {str(e)}")
