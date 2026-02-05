"""
工具注册表

管理所有ERP工具的注册和发现
"""

from typing import Dict, List, Type, Optional
from django.contrib.auth import get_user_model
from .base_tool import BaseTool

# ========== 基础销售工具 ==========
from .sales_tools import (
    SearchCustomerTool,
    CreateSalesQuoteTool,
    CreateSalesOrderTool,
    QuerySalesOrdersTool,
    GetOrderDetailTool,
    ApproveSalesOrderTool,
)

# ========== 销售扩展工具 ==========
from .sales_tools_extended import (
    QueryDeliveriesTool,
    QuerySalesReturnsTool,
    QuerySalesLoansTool,
    GetDeliveryDetailTool,
)

# ========== 销售创建工具 ==========
from .sales_creation_tools import (
    CreateDeliveryTool,
    CreateSalesReturnTool,
    CreateSalesLoanTool,
    ConvertQuoteToOrderTool,
)

# ========== 基础采购工具 ==========
from .purchase_tools import (
    SearchSupplierTool,
    CreatePurchaseRequestTool,
    QueryPurchaseOrdersTool,
    ApprovePurchaseOrderTool,
)

# ========== 采购扩展工具 ==========
from .purchase_tools_extended import (
    QueryPurchaseInquiriesTool,
    QuerySupplierQuotationsTool,
    QueryPurchaseReceiptsTool,
    QueryPurchaseReturnsTool,
    QueryPurchaseBorrowsTool,
)

# ========== 采购创建工具 ==========
from .purchase_creation_tools import (
    CreatePurchaseInquiryTool,
    AddSupplierQuotationTool,
    CreatePurchaseReceiptTool,
)

# ========== 基础库存工具 ==========
from .inventory_tools import (
    CheckInventoryTool,
    SearchProductTool,
    GetLowStockAlertTool,
)

# ========== 库存扩展工具 ==========
from .inventory_tools_extended import (
    QueryWarehousesTool,
    QueryStockTransfersTool,
    QueryStockCountsTool,
    QueryInboundOrdersTool,
    QueryOutboundOrdersTool,
    QueryStockAdjustmentsTool,
)

# ========== 库存创建工具 ==========
from .inventory_creation_tools import (
    CreateWarehouseTool,
    CreateStockTransferTool,
    CreateStockCountTool,
    CreateInboundOrderTool,
    CreateStockAdjustmentTool,
)

# ========== 财务工具 ==========
from .finance_tools import (
    QueryAccountsTool,
    QueryJournalsTool,
    QueryCustomerAccountsTool,
    QuerySupplierAccountsTool,
    QueryPaymentsTool,
    QueryPrepaymentsTool,
    QueryExpensesTool,
    QueryInvoicesTool,
)

# ========== 财务创建工具 ==========
from .finance_creation_tools import (
    CreateJournalTool,
    CreatePaymentTool,
    CreatePrepaymentTool,
    CreateExpenseTool,
)

# ========== 审核和状态变更工具 ==========
from .approval_tools import (
    ApproveDeliveryTool,
    ApproveSalesReturnTool,
    ConfirmShipmentTool,
    ApprovePurchaseReceiptTool,
    ConfirmReceiptTool,
    ApproveExpenseTool,
    ApproveJournalTool,
    ShipTransferTool,
    ReceiveTransferTool,
)

# ========== 高级操作工具 ==========
from .advanced_tools import (
    ConsolidatePrepaymentTool,
    ProcessPaymentTool,
    ApproveBudgetTool,
)

# ========== 报表工具 ==========
from .report_tools import (
    GenerateSalesReportTool,
    GeneratePurchaseReportTool,
    GenerateInventoryReportTool,
)

# ========== 批量操作工具 ==========
from .batch_tools import (
    BatchQueryTool,
    BatchApproveTool,
    BatchExportTool,
    BatchCreateTool,
)

User = get_user_model()


class ToolRegistry:
    """工具注册表"""

    # 所有已注册的工具类
    _registered_tools: Dict[str, Type[BaseTool]] = {}

    @classmethod
    def register(cls, tool_class: Type[BaseTool]):
        """
        注册工具

        Args:
            tool_class: 工具类
        """
        # 实例化一个临时对象来获取工具名称
        # 使用None作为user，因为我们只是要获取名称
        try:
            temp_instance = tool_class(user=None)
            tool_name = temp_instance.name
            cls._registered_tools[tool_name] = tool_class
        except Exception:
            # 如果实例化失败，跳过
            pass

    @classmethod
    def get_tool(cls, tool_name: str, user: User) -> Optional[BaseTool]:
        """
        获取工具实例

        Args:
            tool_name: 工具名称
            user: 用户对象

        Returns:
            工具实例，如果不存在则返回None
        """
        tool_class = cls._registered_tools.get(tool_name)
        if tool_class:
            return tool_class(user=user)
        return None

    @classmethod
    def get_all_tools(cls, user: User) -> List[BaseTool]:
        """
        获取所有工具实例

        Args:
            user: 用户对象

        Returns:
            工具实例列表
        """
        tools = []
        for tool_class in cls._registered_tools.values():
            try:
                tool = tool_class(user=user)
                tools.append(tool)
            except Exception:
                continue
        return tools

    @classmethod
    def get_tools_by_category(cls, category: str, user: User) -> List[BaseTool]:
        """
        获取指定分类的工具

        Args:
            category: 工具分类
            user: 用户对象

        Returns:
            工具实例列表
        """
        tools = []
        for tool_class in cls._registered_tools.values():
            try:
                tool = tool_class(user=user)
                if tool.category == category:
                    tools.append(tool)
            except Exception:
                continue
        return tools

    @classmethod
    def get_available_tools(cls, user: User) -> List[BaseTool]:
        """
        获取用户有权限使用的工具

        Args:
            user: 用户对象

        Returns:
            用户有权限的工具列表
        """
        available_tools = []
        for tool_class in cls._registered_tools.values():
            try:
                tool = tool_class(user=user)
                if tool.check_permission():
                    available_tools.append(tool)
            except Exception:
                continue
        return available_tools

    @classmethod
    def to_openai_functions(cls, user: User) -> List[Dict]:
        """
        转换为OpenAI Function Calling格式

        Args:
            user: 用户对象

        Returns:
            OpenAI函数定义列表
        """
        tools = cls.get_available_tools(user)
        return [tool.to_openai_function() for tool in tools]

    @classmethod
    def to_anthropic_tools(cls, user: User) -> List[Dict]:
        """
        转换为Anthropic Tool Use格式

        Args:
            user: 用户对象

        Returns:
            Anthropic工具定义列表
        """
        tools = cls.get_available_tools(user)
        return [tool.to_anthropic_tool() for tool in tools]


# 自动注册所有工具
def auto_register_tools():
    """自动注册所有工具"""

    # ========== 销售工具 ==========
    # 基础销售工具
    ToolRegistry.register(SearchCustomerTool)
    ToolRegistry.register(CreateSalesQuoteTool)
    ToolRegistry.register(CreateSalesOrderTool)
    ToolRegistry.register(QuerySalesOrdersTool)
    ToolRegistry.register(GetOrderDetailTool)
    ToolRegistry.register(ApproveSalesOrderTool)

    # 销售扩展工具
    ToolRegistry.register(QueryDeliveriesTool)
    ToolRegistry.register(QuerySalesReturnsTool)
    ToolRegistry.register(QuerySalesLoansTool)
    ToolRegistry.register(GetDeliveryDetailTool)

    # 销售创建工具
    ToolRegistry.register(CreateDeliveryTool)
    ToolRegistry.register(CreateSalesReturnTool)
    ToolRegistry.register(CreateSalesLoanTool)
    ToolRegistry.register(ConvertQuoteToOrderTool)

    # ========== 采购工具 ==========
    # 基础采购工具
    ToolRegistry.register(SearchSupplierTool)
    ToolRegistry.register(CreatePurchaseRequestTool)
    ToolRegistry.register(QueryPurchaseOrdersTool)
    ToolRegistry.register(ApprovePurchaseOrderTool)

    # 采购扩展工具
    ToolRegistry.register(QueryPurchaseInquiriesTool)
    ToolRegistry.register(QuerySupplierQuotationsTool)
    ToolRegistry.register(QueryPurchaseReceiptsTool)
    ToolRegistry.register(QueryPurchaseReturnsTool)
    ToolRegistry.register(QueryPurchaseBorrowsTool)

    # 采购创建工具
    ToolRegistry.register(CreatePurchaseInquiryTool)
    ToolRegistry.register(AddSupplierQuotationTool)
    ToolRegistry.register(CreatePurchaseReceiptTool)

    # ========== 库存工具 ==========
    # 基础库存工具
    ToolRegistry.register(CheckInventoryTool)
    ToolRegistry.register(SearchProductTool)
    ToolRegistry.register(GetLowStockAlertTool)

    # 库存扩展工具
    ToolRegistry.register(QueryWarehousesTool)
    ToolRegistry.register(QueryStockTransfersTool)
    ToolRegistry.register(QueryStockCountsTool)
    ToolRegistry.register(QueryInboundOrdersTool)
    ToolRegistry.register(QueryOutboundOrdersTool)
    ToolRegistry.register(QueryStockAdjustmentsTool)

    # 库存创建工具
    ToolRegistry.register(CreateWarehouseTool)
    ToolRegistry.register(CreateStockTransferTool)
    ToolRegistry.register(CreateStockCountTool)
    ToolRegistry.register(CreateInboundOrderTool)
    ToolRegistry.register(CreateStockAdjustmentTool)

    # ========== 财务工具 ==========
    ToolRegistry.register(QueryAccountsTool)
    ToolRegistry.register(QueryJournalsTool)
    ToolRegistry.register(QueryCustomerAccountsTool)
    ToolRegistry.register(QuerySupplierAccountsTool)
    ToolRegistry.register(QueryPaymentsTool)
    ToolRegistry.register(QueryPrepaymentsTool)
    ToolRegistry.register(QueryExpensesTool)
    ToolRegistry.register(QueryInvoicesTool)

    # 财务创建工具
    ToolRegistry.register(CreateJournalTool)
    ToolRegistry.register(CreatePaymentTool)
    ToolRegistry.register(CreatePrepaymentTool)
    ToolRegistry.register(CreateExpenseTool)

    # 审核和状态变更工具
    ToolRegistry.register(ApproveDeliveryTool)
    ToolRegistry.register(ApproveSalesReturnTool)
    ToolRegistry.register(ConfirmShipmentTool)
    ToolRegistry.register(ApprovePurchaseReceiptTool)
    ToolRegistry.register(ConfirmReceiptTool)
    ToolRegistry.register(ApproveExpenseTool)
    ToolRegistry.register(ApproveJournalTool)
    ToolRegistry.register(ShipTransferTool)
    ToolRegistry.register(ReceiveTransferTool)

    # 高级操作工具
    ToolRegistry.register(ConsolidatePrepaymentTool)
    ToolRegistry.register(ProcessPaymentTool)
    ToolRegistry.register(ApproveBudgetTool)

    # ========== 报表工具 ==========
    ToolRegistry.register(GenerateSalesReportTool)
    ToolRegistry.register(GeneratePurchaseReportTool)
    ToolRegistry.register(GenerateInventoryReportTool)

    # ========== 批量操作工具 ==========
    ToolRegistry.register(BatchQueryTool)
    ToolRegistry.register(BatchApproveTool)
    ToolRegistry.register(BatchExportTool)
    ToolRegistry.register(BatchCreateTool)


# 执行自动注册
auto_register_tools()
