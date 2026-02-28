"""
库存模块扩展工具

提供库存业务的高级查询和操作工具，包括仓库、调拨、盘点、出入库、调整等功能
"""

from typing import Any, Dict

from django.db.models import Q
from inventory.models import (
    InboundOrder,
    InventoryStock,
    OutboundOrder,
    StockAdjustment,
    StockCount,
    StockTransfer,
    Warehouse,
)

from .base_tool import BaseTool, ToolResult


class QueryWarehousesTool(BaseTool):
    """查询仓库工具"""

    name = "query_warehouses"
    display_name = "查询仓库"
    description = "查询仓库列表，支持按名称、代码、状态筛选"
    category = "inventory"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "is_active": {"type": "boolean", "description": "是否仅显示启用的仓库"},
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词（仓库名称或代码）",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认50）",
                    "default": 50,
                },
            },
        }

    def execute(
        self, is_active: bool = None, keyword: str = None, limit: int = 50, **kwargs
    ) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            warehouses = Warehouse.objects.filter(is_deleted=False)

            if is_active is not None:
                warehouses = warehouses.filter(is_active=is_active)

            if keyword:
                warehouses = warehouses.filter(
                    Q(name__icontains=keyword) | Q(code__icontains=keyword)
                )

            warehouses = warehouses.order_by("code")[:limit]

            # 格式化结果
            results = []
            for wh in warehouses:
                # 统计仓库的库存产品数量
                stock_count = InventoryStock.objects.filter(warehouse=wh).count()

                results.append(
                    {
                        "id": wh.id,
                        "name": wh.name,
                        "code": wh.code,
                        "address": wh.address or "",
                        "manager": wh.manager.username if wh.manager else "",
                        "is_active": wh.is_active,
                        "stock_count": stock_count,
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个仓库")

        except Exception as e:
            return ToolResult(success=False, error=f"查询仓库失败: {str(e)}")


class QueryStockTransfersTool(BaseTool):
    """查询库存调拨工具"""

    name = "query_stock_transfers"
    display_name = "查询库存调拨"
    description = "查询库存调拨单列表，支持按状态、仓库、日期范围筛选"
    category = "inventory"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "调拨状态（draft/pending/shipped/received/cancelled）",
                    "enum": ["draft", "pending", "shipped", "received", "cancelled"],
                },
                "source_warehouse_id": {"type": "integer", "description": "源仓库ID"},
                "target_warehouse_id": {"type": "integer", "description": "目标仓库ID"},
                "date_from": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）",
                },
                "date_to": {"type": "string", "description": "结束日期（YYYY-MM-DD）"},
                "keyword": {"type": "string", "description": "搜索关键词（调拨单号）"},
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认20）",
                    "default": 20,
                },
            },
        }

    def execute(
        self,
        status: str = None,
        source_warehouse_id: int = None,
        target_warehouse_id: int = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            transfers = StockTransfer.objects.filter(is_deleted=False)

            if status:
                transfers = transfers.filter(status=status)

            if source_warehouse_id:
                transfers = transfers.filter(source_warehouse_id=source_warehouse_id)

            if target_warehouse_id:
                transfers = transfers.filter(target_warehouse_id=target_warehouse_id)

            if date_from:
                transfers = transfers.filter(transfer_date__gte=date_from)

            if date_to:
                transfers = transfers.filter(transfer_date__lte=date_to)

            if keyword:
                transfers = transfers.filter(transfer_number__icontains=keyword)

            transfers = transfers.select_related("source_warehouse", "target_warehouse").order_by(
                "-transfer_date"
            )[:limit]

            # 格式化结果
            results = []
            for transfer in transfers:
                results.append(
                    {
                        "id": transfer.id,
                        "transfer_number": transfer.transfer_number,
                        "source_warehouse": (
                            transfer.source_warehouse.name if transfer.source_warehouse else ""
                        ),
                        "target_warehouse": (
                            transfer.target_warehouse.name if transfer.target_warehouse else ""
                        ),
                        "transfer_date": (
                            transfer.transfer_date.strftime("%Y-%m-%d")
                            if transfer.transfer_date
                            else None
                        ),
                        "status": transfer.status,
                        "status_display": transfer.get_status_display(),
                        "items_count": (
                            transfer.items.count() if hasattr(transfer, "items") else 0
                        ),
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个调拨单")

        except Exception as e:
            return ToolResult(success=False, error=f"查询库存调拨失败: {str(e)}")


class QueryStockCountsTool(BaseTool):
    """查询库存盘点工具"""

    name = "query_stock_counts"
    display_name = "查询库存盘点"
    description = "查询库存盘点单列表，支持按状态、仓库、日期范围筛选"
    category = "inventory"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "盘点状态（draft/in_progress/completed/cancelled）",
                    "enum": ["draft", "in_progress", "completed", "cancelled"],
                },
                "warehouse_id": {"type": "integer", "description": "仓库ID"},
                "date_from": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）",
                },
                "date_to": {"type": "string", "description": "结束日期（YYYY-MM-DD）"},
                "keyword": {"type": "string", "description": "搜索关键词（盘点单号）"},
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认20）",
                    "default": 20,
                },
            },
        }

    def execute(
        self,
        status: str = None,
        warehouse_id: int = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            counts = StockCount.objects.filter(is_deleted=False)

            if status:
                counts = counts.filter(status=status)

            if warehouse_id:
                counts = counts.filter(warehouse_id=warehouse_id)

            if date_from:
                counts = counts.filter(count_date__gte=date_from)

            if date_to:
                counts = counts.filter(count_date__lte=date_to)

            if keyword:
                counts = counts.filter(count_number__icontains=keyword)

            counts = counts.select_related("warehouse").order_by("-count_date")[:limit]

            # 格式化结果
            results = []
            for count in counts:
                results.append(
                    {
                        "id": count.id,
                        "count_number": count.count_number,
                        "warehouse": count.warehouse.name if count.warehouse else "",
                        "count_date": (
                            count.count_date.strftime("%Y-%m-%d") if count.count_date else None
                        ),
                        "status": count.status,
                        "status_display": count.get_status_display(),
                        "items_count": (count.items.count() if hasattr(count, "items") else 0),
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个盘点单")

        except Exception as e:
            return ToolResult(success=False, error=f"查询库存盘点失败: {str(e)}")


class QueryInboundOrdersTool(BaseTool):
    """查询入库单工具"""

    name = "query_inbound_orders"
    display_name = "查询入库单"
    description = "查询入库单列表，支持按状态、仓库、日期范围筛选"
    category = "inventory"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "入库状态（draft/pending/approved/cancelled）",
                    "enum": ["draft", "pending", "approved", "cancelled"],
                },
                "warehouse_id": {"type": "integer", "description": "仓库ID"},
                "date_from": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）",
                },
                "date_to": {"type": "string", "description": "结束日期（YYYY-MM-DD）"},
                "keyword": {"type": "string", "description": "搜索关键词（入库单号）"},
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认20）",
                    "default": 20,
                },
            },
        }

    def execute(
        self,
        status: str = None,
        warehouse_id: int = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            inbounds = InboundOrder.objects.filter(is_deleted=False)

            if status:
                inbounds = inbounds.filter(status=status)

            if warehouse_id:
                inbounds = inbounds.filter(warehouse_id=warehouse_id)

            if date_from:
                inbounds = inbounds.filter(inbound_date__gte=date_from)

            if date_to:
                inbounds = inbounds.filter(inbound_date__lte=date_to)

            if keyword:
                inbounds = inbounds.filter(inbound_number__icontains=keyword)

            inbounds = inbounds.select_related("warehouse").order_by("-inbound_date")[:limit]

            # 格式化结果
            results = []
            for inbound in inbounds:
                results.append(
                    {
                        "id": inbound.id,
                        "inbound_number": inbound.inbound_number,
                        "warehouse": (inbound.warehouse.name if inbound.warehouse else ""),
                        "inbound_date": (
                            inbound.inbound_date.strftime("%Y-%m-%d")
                            if inbound.inbound_date
                            else None
                        ),
                        "status": inbound.status,
                        "status_display": inbound.get_status_display(),
                        "items_count": (inbound.items.count() if hasattr(inbound, "items") else 0),
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个入库单")

        except Exception as e:
            return ToolResult(success=False, error=f"查询入库单失败: {str(e)}")


class QueryOutboundOrdersTool(BaseTool):
    """查询出库单工具"""

    name = "query_outbound_orders"
    display_name = "查询出库单"
    description = "查询出库单列表，支持按状态、仓库、日期范围筛选"
    category = "inventory"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "出库状态（draft/pending/approved/cancelled）",
                    "enum": ["draft", "pending", "approved", "cancelled"],
                },
                "warehouse_id": {"type": "integer", "description": "仓库ID"},
                "date_from": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）",
                },
                "date_to": {"type": "string", "description": "结束日期（YYYY-MM-DD）"},
                "keyword": {"type": "string", "description": "搜索关键词（出库单号）"},
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认20）",
                    "default": 20,
                },
            },
        }

    def execute(
        self,
        status: str = None,
        warehouse_id: int = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            outbounds = OutboundOrder.objects.filter(is_deleted=False)

            if status:
                outbounds = outbounds.filter(status=status)

            if warehouse_id:
                outbounds = outbounds.filter(warehouse_id=warehouse_id)

            if date_from:
                outbounds = outbounds.filter(outbound_date__gte=date_from)

            if date_to:
                outbounds = outbounds.filter(outbound_date__lte=date_to)

            if keyword:
                outbounds = outbounds.filter(outbound_number__icontains=keyword)

            outbounds = outbounds.select_related("warehouse").order_by("-outbound_date")[:limit]

            # 格式化结果
            results = []
            for outbound in outbounds:
                results.append(
                    {
                        "id": outbound.id,
                        "outbound_number": outbound.outbound_number,
                        "warehouse": (outbound.warehouse.name if outbound.warehouse else ""),
                        "outbound_date": (
                            outbound.outbound_date.strftime("%Y-%m-%d")
                            if outbound.outbound_date
                            else None
                        ),
                        "status": outbound.status,
                        "status_display": outbound.get_status_display(),
                        "items_count": (
                            outbound.items.count() if hasattr(outbound, "items") else 0
                        ),
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个出库单")

        except Exception as e:
            return ToolResult(success=False, error=f"查询出库单失败: {str(e)}")


class QueryStockAdjustmentsTool(BaseTool):
    """查询库存调整工具"""

    name = "query_stock_adjustments"
    display_name = "查询库存调整"
    description = "查询库存调整单列表，支持按状态、仓库、日期范围筛选"
    category = "inventory"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "调整状态（draft/pending/approved/cancelled）",
                    "enum": ["draft", "pending", "approved", "cancelled"],
                },
                "warehouse_id": {"type": "integer", "description": "仓库ID"},
                "date_from": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）",
                },
                "date_to": {"type": "string", "description": "结束日期（YYYY-MM-DD）"},
                "keyword": {"type": "string", "description": "搜索关键词（调整单号）"},
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认20）",
                    "default": 20,
                },
            },
        }

    def execute(
        self,
        status: str = None,
        warehouse_id: int = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            adjustments = StockAdjustment.objects.filter(is_deleted=False)

            if status:
                adjustments = adjustments.filter(status=status)

            if warehouse_id:
                adjustments = adjustments.filter(warehouse_id=warehouse_id)

            if date_from:
                adjustments = adjustments.filter(adjustment_date__gte=date_from)

            if date_to:
                adjustments = adjustments.filter(adjustment_date__lte=date_to)

            if keyword:
                adjustments = adjustments.filter(adjustment_number__icontains=keyword)

            adjustments = adjustments.select_related("warehouse").order_by("-adjustment_date")[
                :limit
            ]

            # 格式化结果
            results = []
            for adj in adjustments:
                results.append(
                    {
                        "id": adj.id,
                        "adjustment_number": adj.adjustment_number,
                        "warehouse": adj.warehouse.name if adj.warehouse else "",
                        "adjustment_date": (
                            adj.adjustment_date.strftime("%Y-%m-%d")
                            if adj.adjustment_date
                            else None
                        ),
                        "adjustment_reason": adj.adjustment_reason,
                        "adjustment_reason_display": adj.get_adjustment_reason_display(),
                        "status": adj.status,
                        "status_display": adj.get_status_display(),
                        "items_count": (adj.items.count() if hasattr(adj, "items") else 0),
                    }
                )

            return ToolResult(success=True, data=results, message=f"找到 {len(results)} 个调整单")

        except Exception as e:
            return ToolResult(success=False, error=f"查询库存调整失败: {str(e)}")
