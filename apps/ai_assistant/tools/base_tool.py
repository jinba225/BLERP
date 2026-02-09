"""
ERP工具基类

提供AI调用ERP系统的标准工具接口
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


@dataclass
class ToolResult:
    """工具执行结果"""

    success: bool
    data: Any = None
    message: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "success": self.success,
            "message": self.message,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        return result


class BaseTool(ABC):
    """
    ERP工具抽象基类

    所有ERP工具都应继承此类，实现execute方法
    """

    # 工具基本信息（子类必须定义）
    name: str = ""  # 工具名称（英文，用于AI调用）
    display_name: str = ""  # 显示名称（中文）
    description: str = ""  # 工具描述（AI会看到）
    category: str = ""  # 工具分类（sales/purchase/inventory/report）

    # 权限和风险控制
    require_permission: Optional[str] = None  # 需要的权限
    require_approval: bool = False  # 是否需要审核
    risk_level: str = "low"  # 风险级别：low/medium/high

    def __init__(self, user: User):
        """
        初始化工具

        Args:
            user: 执行操作的用户
        """
        self.user = user
        self._validate_tool_definition()

    def _validate_tool_definition(self):
        """验证工具定义是否完整"""
        if not self.name:
            raise ValueError(f"{self.__class__.__name__}: 必须定义工具名称(name)")
        if not self.display_name:
            raise ValueError(f"{self.__class__.__name__}: 必须定义显示名称(display_name)")
        if not self.description:
            raise ValueError(f"{self.__class__.__name__}: 必须定义工具描述(description)")
        if not self.category:
            raise ValueError(f"{self.__class__.__name__}: 必须定义工具分类(category)")

    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """
        获取参数Schema（JSON Schema格式）

        AI会根据这个Schema了解如何传参

        Returns:
            JSON Schema格式的参数定义
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            ToolResult对象
        """
        pass

    def check_permission(self) -> bool:
        """
        检查用户权限

        Returns:
            是否有权限
        """
        # 如果不需要特殊权限，默认允许
        if not self.require_permission:
            return True

        # 超级用户总是有权限
        if self.user.is_superuser:
            return True

        # 使用自定义权限检查
        try:
            from ai_assistant.utils.permissions import has_custom_permission

            return has_custom_permission(self.user, self.require_permission)
        except Exception as e:
            # 如果权限检查失败，返回 False（安全第一）
            return False

    def validate_parameters(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        验证参数

        Args:
            **kwargs: 工具参数

        Returns:
            (是否有效, 错误信息)
        """
        schema = self.get_parameters_schema()
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        # 检查必填参数
        for param in required:
            if param not in kwargs or kwargs[param] is None:
                return False, f"缺少必填参数: {param}"

        # 检查参数类型（简单验证）
        for param_name, param_value in kwargs.items():
            if param_name in properties:
                expected_type = properties[param_name].get("type")
                if expected_type == "string" and not isinstance(param_value, str):
                    return False, f"参数 {param_name} 应为字符串类型"
                elif expected_type == "integer" and not isinstance(param_value, int):
                    return False, f"参数 {param_name} 应为整数类型"
                elif expected_type == "number" and not isinstance(param_value, (int, float)):
                    return False, f"参数 {param_name} 应为数字类型"
                elif expected_type == "boolean" and not isinstance(param_value, bool):
                    return False, f"参数 {param_name} 应为布尔类型"

        return True, None

    def run(self, **kwargs) -> ToolResult:
        """
        运行工具（统一入口）

        包含权限检查、参数验证、执行日志等

        Args:
            **kwargs: 工具参数

        Returns:
            ToolResult对象
        """
        # 1. 检查权限
        if not self.check_permission():
            return ToolResult(success=False, error=f"权限不足：需要权限 {self.require_permission or '未知'}")

        # 2. 验证参数
        valid, error_msg = self.validate_parameters(**kwargs)
        if not valid:
            return ToolResult(success=False, error=f"参数验证失败: {error_msg}")

        # 3. 检查是否需要审核
        if self.require_approval:
            # TODO: 实现审核流程
            # 现在暂时允许超级用户直接执行
            if not self.user.is_superuser:
                return ToolResult(success=False, message="此操作需要审核", data={"pending_approval": True})

        # 4. 执行工具
        try:
            result = self.execute(**kwargs)

            # 5. 记录执行日志
            self._log_execution(kwargs, result)

            return result

        except Exception as e:
            error_result = ToolResult(success=False, error=f"工具执行失败: {str(e)}")

            # 记录错误日志
            self._log_execution(kwargs, error_result)

            return error_result

    def _log_execution(self, params: Dict[str, Any], result: ToolResult):
        """
        记录工具执行日志

        Args:
            params: 执行参数
            result: 执行结果
        """
        from ..models import AIToolExecutionLog

        try:
            AIToolExecutionLog.objects.create(
                tool_name=self.name,
                user=self.user,
                parameters=params,
                result=result.to_dict(),
                success=result.success,
                executed_at=timezone.now(),
                created_by=self.user,
            )
        except Exception as e:
            # 日志记录失败不应影响主流程
            print(f"工具执行日志记录失败: {str(e)}")

    def to_openai_function(self) -> Dict[str, Any]:
        """
        转换为OpenAI Function Calling格式

        Returns:
            OpenAI函数定义
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema(),
            },
        }

    def to_anthropic_tool(self) -> Dict[str, Any]:
        """
        转换为Anthropic Tool Use格式

        Returns:
            Anthropic工具定义
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.get_parameters_schema(),
        }

    def __str__(self):
        return f"{self.display_name} ({self.name})"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"
