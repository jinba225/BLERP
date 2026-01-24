"""
工具注册表

管理所有ERP工具的注册和发现
"""

from typing import Dict, List, Type, Optional
from django.contrib.auth import get_user_model
from .base_tool import BaseTool
from .sales_tools import (
    SearchCustomerTool,
    CreateSalesQuoteTool,
    QuerySalesOrdersTool,
    GetOrderDetailTool,
    ApproveSalesOrderTool,
)
from .purchase_tools import (
    SearchSupplierTool,
    CreatePurchaseRequestTool,
    QueryPurchaseOrdersTool,
    ApprovePurchaseOrderTool,
)
from .inventory_tools import (
    CheckInventoryTool,
    SearchProductTool,
    GetLowStockAlertTool,
)
from .report_tools import (
    GenerateSalesReportTool,
    GeneratePurchaseReportTool,
    GenerateInventoryReportTool,
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
    # 销售工具
    ToolRegistry.register(SearchCustomerTool)
    ToolRegistry.register(CreateSalesQuoteTool)
    ToolRegistry.register(QuerySalesOrdersTool)
    ToolRegistry.register(GetOrderDetailTool)
    ToolRegistry.register(ApproveSalesOrderTool)

    # 采购工具
    ToolRegistry.register(SearchSupplierTool)
    ToolRegistry.register(CreatePurchaseRequestTool)
    ToolRegistry.register(QueryPurchaseOrdersTool)
    ToolRegistry.register(ApprovePurchaseOrderTool)

    # 库存工具
    ToolRegistry.register(CheckInventoryTool)
    ToolRegistry.register(SearchProductTool)
    ToolRegistry.register(GetLowStockAlertTool)

    # 报表工具
    ToolRegistry.register(GenerateSalesReportTool)
    ToolRegistry.register(GeneratePurchaseReportTool)
    ToolRegistry.register(GenerateInventoryReportTool)


# 执行自动注册
auto_register_tools()
