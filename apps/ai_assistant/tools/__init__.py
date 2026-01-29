"""
AI Assistant Tools
 
提供AI调用ERP系统的各类工具
"""

from .base_tool import BaseTool, ToolResult
from .registry import ToolRegistry

# 销售工具
from .sales_tools import (
    SearchCustomerTool,
    CreateSalesQuoteTool,
    CreateSalesOrderTool,
    QuerySalesOrdersTool,
    GetOrderDetailTool,
    ApproveSalesOrderTool,
)

# 采购工具
from .purchase_tools import (
    SearchSupplierTool,
    CreatePurchaseRequestTool,
    QueryPurchaseOrdersTool,
    ApprovePurchaseOrderTool,
)

# 库存工具
from .inventory_tools import (
    CheckInventoryTool,
    SearchProductTool,
    GetLowStockAlertTool,
)

# 报表工具
from .report_tools import (
    GenerateSalesReportTool,
    GeneratePurchaseReportTool,
    GenerateInventoryReportTool,
)

__all__ = [
    # 基础类
    'BaseTool',
    'ToolResult',
    'ToolRegistry',
    # 销售工具
    'SearchCustomerTool',
    'CreateSalesQuoteTool',
    'CreateSalesOrderTool',
    'QuerySalesOrdersTool',
    'GetOrderDetailTool',
    'ApproveSalesOrderTool',
    # 采购工具
    'SearchSupplierTool',
    'CreatePurchaseRequestTool',
    'QueryPurchaseOrdersTool',
    'ApprovePurchaseOrderTool',
    # 库存工具
    'CheckInventoryTool',
    'SearchProductTool',
    'GetLowStockAlertTool',
    # 报表工具
    'GenerateSalesReportTool',
    'GeneratePurchaseReportTool',
    'GenerateInventoryReportTool',
]
