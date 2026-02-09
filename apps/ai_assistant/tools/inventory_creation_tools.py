"""
库存模块创建工具

提供库存业务的创建功能，包括仓库、调拨、盘点、出入库、调整等
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from django.db import transaction
from django.utils import timezone
from inventory.models import (
    InboundOrder,
    InboundOrderItem,
    InventoryStock,
    OutboundOrder,
    OutboundOrderItem,
    StockAdjustment,
    StockCount,
    StockCountItem,
    StockTransfer,
    StockTransferItem,
    Warehouse,
)
from products.models import Product

from common.utils import DocumentNumberGenerator

from .base_tool import BaseTool, ToolResult


class CreateWarehouseTool(BaseTool):
    """创建仓库工具"""

    name = "create_warehouse"
    display_name = "创建仓库"
    description = "创建新的仓库"
    category = "inventory"
    risk_level = "medium"
    require_permission = "inventory.add_warehouse"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "仓库名称"},
                "code": {"type": "string", "description": "仓库代码"},
                "address": {"type": "string", "description": "仓库地址"},
                "manager_id": {"type": "integer", "description": "仓库管理员用户ID"},
                "is_active": {"type": "boolean", "description": "是否启用", "default": True},
            },
            "required": ["name", "code"],
        }

    def execute(
        self,
        name: str,
        code: str,
        address: str = "",
        manager_id: int = None,
        is_active: bool = True,
        **kwargs,
    ) -> ToolResult:
        """执行创建仓库"""
        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()

            # 检查代码是否已存在
            if Warehouse.objects.filter(code=code, is_deleted=False).exists():
                return ToolResult(success=False, error=f"仓库代码 {code} 已存在")

            # 获取管理员
            manager = None
            if manager_id:
                try:
                    manager = User.objects.get(id=manager_id)
                except User.DoesNotExist:
                    return ToolResult(success=False, error=f"用户ID {manager_id} 不存在")

            # 创建仓库
            warehouse = Warehouse.objects.create(
                name=name,
                code=code,
                address=address,
                manager=manager,
                is_active=is_active,
                created_by=self.user,
            )

            return ToolResult(
                success=True,
                data={
                    "warehouse_id": warehouse.id,
                    "name": warehouse.name,
                    "code": warehouse.code,
                    "address": warehouse.address,
                    "is_active": warehouse.is_active,
                },
                message=f"仓库 {warehouse.name} 创建成功",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"创建仓库失败: {str(e)}")


class CreateStockTransferTool(BaseTool):
    """创建库存调拨工具"""

    name = "create_stock_transfer"
    display_name = "创建库存调拨"
    description = "创建仓库间库存调拨单"
    category = "inventory"
    risk_level = "medium"
    require_permission = "inventory.add_stocktransfer"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "source_warehouse_id": {"type": "integer", "description": "源仓库ID"},
                "target_warehouse_id": {"type": "integer", "description": "目标仓库ID"},
                "items": {
                    "type": "array",
                    "description": "调拨明细列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"},
                            "quantity": {"type": "number", "description": "数量"},
                        },
                        "required": ["product_id", "quantity"],
                    },
                },
                "transfer_date": {"type": "string", "description": "调拨日期（YYYY-MM-DD，默认今天）"},
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["source_warehouse_id", "target_warehouse_id", "items"],
        }

    def execute(
        self,
        source_warehouse_id: int,
        target_warehouse_id: int,
        items: list,
        transfer_date: str = None,
        notes: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行创建调拨单"""
        try:
            # 获取仓库
            try:
                source_warehouse = Warehouse.objects.get(id=source_warehouse_id, is_deleted=False)
                target_warehouse = Warehouse.objects.get(id=target_warehouse_id, is_deleted=False)
            except Warehouse.DoesNotExist:
                return ToolResult(success=False, error=f"仓库ID不存在")

            if source_warehouse_id == target_warehouse_id:
                return ToolResult(success=False, error=f"源仓库和目标仓库不能相同")

            # 验证明细
            validated_items = []

            for item in items:
                try:
                    product = Product.objects.get(id=item["product_id"], is_deleted=False)
                except Product.DoesNotExist:
                    return ToolResult(success=False, error=f"产品ID {item['product_id']} 不存在")

                quantity = float(item["quantity"])

                # 检查源仓库库存
                stock = InventoryStock.objects.filter(
                    warehouse=source_warehouse, product=product
                ).first()

                if not stock or stock.quantity_available < quantity:
                    available = stock.quantity_available if stock else 0
                    return ToolResult(
                        success=False,
                        error=f"产品 {product.name} 在源仓库的可用库存不足：需要 {quantity}，可用 {available}",
                    )

                validated_items.append(
                    {
                        "product": product,
                        "quantity": quantity,
                    }
                )

            # 创建调拨单
            with transaction.atomic():
                transfer_number = DocumentNumberGenerator.generate("stock_transfer")
                transfer_date_obj = (
                    datetime.strptime(transfer_date, "%Y-%m-%d").date()
                    if transfer_date
                    else timezone.now().date()
                )

                transfer = StockTransfer.objects.create(
                    transfer_number=transfer_number,
                    source_warehouse=source_warehouse,
                    target_warehouse=target_warehouse,
                    transfer_date=transfer_date_obj,
                    status="pending",
                    notes=notes,
                    created_by=self.user,
                )

                # 创建明细
                for item_data in validated_items:
                    StockTransferItem.objects.create(
                        stock_transfer=transfer,
                        product=item_data["product"],
                        quantity=item_data["quantity"],
                        created_by=self.user,
                    )

            return ToolResult(
                success=True,
                data={
                    "transfer_id": transfer.id,
                    "transfer_number": transfer.transfer_number,
                    "source_warehouse": source_warehouse.name,
                    "target_warehouse": target_warehouse.name,
                    "transfer_date": transfer.transfer_date.strftime("%Y-%m-%d"),
                    "items_count": len(validated_items),
                },
                message=f"调拨单 {transfer.transfer_number} 创建成功",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"创建调拨单失败: {str(e)}")


class CreateStockCountTool(BaseTool):
    """创建库存盘点工具"""

    name = "create_stock_count"
    display_name = "创建库存盘点"
    description = "创建库存盘点单"
    category = "inventory"
    risk_level = "medium"
    require_permission = "inventory.add_stockcount"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "warehouse_id": {"type": "integer", "description": "仓库ID"},
                "count_date": {"type": "string", "description": "盘点日期（YYYY-MM-DD，默认今天）"},
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["warehouse_id"],
        }

    def execute(
        self, warehouse_id: int, count_date: str = None, notes: str = "", **kwargs
    ) -> ToolResult:
        """执行创建盘点单"""
        try:
            # 获取仓库
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id, is_deleted=False)
            except Warehouse.DoesNotExist:
                return ToolResult(success=False, error=f"仓库ID {warehouse_id} 不存在")

            # 创建盘点单（不包含明细，后续添加）
            with transaction.atomic():
                count_number = DocumentNumberGenerator.generate("stock_count")
                count_date_obj = (
                    datetime.strptime(count_date, "%Y-%m-%d").date()
                    if count_date
                    else timezone.now().date()
                )

                count = StockCount.objects.create(
                    count_number=count_number,
                    warehouse=warehouse,
                    count_date=count_date_obj,
                    status="draft",
                    notes=notes,
                    created_by=self.user,
                )

            return ToolResult(
                success=True,
                data={
                    "count_id": count.id,
                    "count_number": count.count_number,
                    "warehouse": warehouse.name,
                    "count_date": count.count_date.strftime("%Y-%m-%d"),
                },
                message=f"盘点单 {count.count_number} 创建成功，请添加盘点明细",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"创建盘点单失败: {str(e)}")


class CreateInboundOrderTool(BaseTool):
    """创建入库单工具"""

    name = "create_inbound_order"
    display_name = "创建入库单"
    description = "创建入库单"
    category = "inventory"
    risk_level = "medium"
    require_permission = "inventory.add_inboundorder"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "warehouse_id": {"type": "integer", "description": "仓库ID"},
                "items": {
                    "type": "array",
                    "description": "入库明细列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"},
                            "quantity": {"type": "number", "description": "数量"},
                            "unit_price": {"type": "number", "description": "单价"},
                        },
                        "required": ["product_id", "quantity"],
                    },
                },
                "inbound_date": {"type": "string", "description": "入库日期（YYYY-MM-DD，默认今天）"},
                "reference_number": {"type": "string", "description": "参考单号"},
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["warehouse_id", "items"],
        }

    def execute(
        self,
        warehouse_id: int,
        items: list,
        inbound_date: str = None,
        reference_number: str = "",
        notes: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行创建入库单"""
        try:
            # 获取仓库
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id, is_deleted=False)
            except Warehouse.DoesNotExist:
                return ToolResult(success=False, error=f"仓库ID {warehouse_id} 不存在")

            # 验证明细
            validated_items = []

            for item in items:
                try:
                    product = Product.objects.get(id=item["product_id"], is_deleted=False)
                except Product.DoesNotExist:
                    return ToolResult(success=False, error=f"产品ID {item['product_id']} 不存在")

                quantity = float(item["quantity"])
                unit_price = float(item.get("unit_price", 0))

                validated_items.append(
                    {
                        "product": product,
                        "quantity": quantity,
                        "unit_price": unit_price,
                    }
                )

            # 创建入库单
            with transaction.atomic():
                inbound_number = DocumentNumberGenerator.generate("inbound_order")
                inbound_date_obj = (
                    datetime.strptime(inbound_date, "%Y-%m-%d").date()
                    if inbound_date
                    else timezone.now().date()
                )

                inbound = InboundOrder.objects.create(
                    inbound_number=inbound_number,
                    warehouse=warehouse,
                    inbound_date=inbound_date_obj,
                    reference_number=reference_number,
                    status="pending",
                    notes=notes,
                    created_by=self.user,
                )

                # 创建明细
                for item_data in validated_items:
                    InboundOrderItem.objects.create(
                        inbound_order=inbound,
                        product=item_data["product"],
                        quantity=item_data["quantity"],
                        unit_price=item_data["unit_price"],
                        created_by=self.user,
                    )

            return ToolResult(
                success=True,
                data={
                    "inbound_id": inbound.id,
                    "inbound_number": inbound.inbound_number,
                    "warehouse": warehouse.name,
                    "inbound_date": inbound.inbound_date.strftime("%Y-%m-%d"),
                    "items_count": len(validated_items),
                },
                message=f"入库单 {inbound.inbound_number} 创建成功",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"创建入库单失败: {str(e)}")


class CreateStockAdjustmentTool(BaseTool):
    """创建库存调整工具"""

    name = "create_stock_adjustment"
    display_name = "创建库存调整"
    description = "创建库存调整单"
    category = "inventory"
    risk_level = "high"
    require_permission = "inventory.add_stockadjustment"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "warehouse_id": {"type": "integer", "description": "仓库ID"},
                "items": {
                    "type": "array",
                    "description": "调整明细列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "产品ID"},
                            "quantity": {"type": "number", "description": "调整数量（正数为增加，负数为减少）"},
                        },
                        "required": ["product_id", "quantity"],
                    },
                },
                "adjustment_date": {"type": "string", "description": "调整日期（YYYY-MM-DD，默认今天）"},
                "adjustment_reason": {
                    "type": "string",
                    "description": "调整原因（damage/loss/gain/other）",
                    "enum": ["damage", "loss", "gain", "other"],
                },
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["warehouse_id", "items", "adjustment_reason"],
        }

    def execute(
        self,
        warehouse_id: int,
        items: list,
        adjustment_reason: str,
        adjustment_date: str = None,
        notes: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行创建调整单"""
        try:
            # 获取仓库
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id, is_deleted=False)
            except Warehouse.DoesNotExist:
                return ToolResult(success=False, error=f"仓库ID {warehouse_id} 不存在")

            # StockAdjustment每个记录就是一个调整项，所以items列表中每一项对应一个StockAdjustment
            adjustment_number = DocumentNumberGenerator.generate("stock_adjustment")
            adjustment_date_obj = (
                datetime.strptime(adjustment_date, "%Y-%m-%d").date()
                if adjustment_date
                else timezone.now().date()
            )

            # 批量创建调整记录
            adjustments_created = []

            with transaction.atomic():
                for item in items:
                    try:
                        product = Product.objects.get(id=item["product_id"], is_deleted=False)
                    except Product.DoesNotExist:
                        return ToolResult(success=False, error=f"产品ID {item['product_id']} 不存在")

                    quantity = float(item["quantity"])

                    if quantity == 0:
                        return ToolResult(success=False, error=f"产品 {product.name} 的调整数量不能为0")

                    # 获取当前库存
                    stock = InventoryStock.objects.filter(
                        warehouse=warehouse, product=product
                    ).first()

                    original_quantity = stock.quantity_available if stock else 0

                    # 确定调整类型和调整后数量
                    if quantity > 0:
                        adjustment_type = "increase"
                        adjusted_quantity = original_quantity + quantity
                    else:
                        adjustment_type = "decrease"
                        adjusted_quantity = original_quantity + quantity  # quantity是负数

                    # 创建调整记录
                    adjustment = StockAdjustment.objects.create(
                        adjustment_number=f"{adjustment_number}-{len(adjustments_created) + 1}",
                        adjustment_type=adjustment_type,
                        reason=adjustment_reason,
                        product=product,
                        warehouse=warehouse,
                        original_quantity=original_quantity,
                        adjusted_quantity=int(adjusted_quantity),
                        is_approved=False,  # 待审核
                        notes=notes,
                        created_by=self.user,
                    )

                    adjustments_created.append(adjustment)

            return ToolResult(
                success=True,
                data={
                    "adjustment_base_number": adjustment_number,
                    "warehouse": warehouse.name,
                    "adjustment_date": adjustment_date_obj.strftime("%Y-%m-%d"),
                    "adjustment_reason": adjustment_reason,
                    "items_count": len(adjustments_created),
                },
                message=f"创建 {len(adjustments_created)} 条调整记录成功，单号前缀 {adjustment_number}",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"创建调整单失败: {str(e)}")
