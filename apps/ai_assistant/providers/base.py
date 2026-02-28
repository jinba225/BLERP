"""
AI Provider 抽象基类

定义所有AI Provider必须实现的接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class AIResponse:
    """AI响应数据类"""

    content: str  # AI回复内容
    tool_calls: Optional[List[Dict[str, Any]]] = None  # 工具调用列表
    finish_reason: Optional[str] = None  # 结束原因
    tokens_used: int = 0  # 消耗的Token数
    model: Optional[str] = None  # 使用的模型名称


class BaseAIProvider(ABC):
    """AI Provider 抽象基类"""

    def __init__(
        self,
        api_key: str,
        api_base: Optional[str] = None,
        model_name: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 60,
    ):
        """
        初始化Provider

        Args:
            api_key: API密钥
            api_base: API基础URL（可选）
            model_name: 模型名称
            temperature: 温度参数（0-1）
            max_tokens: 最大Token数
            timeout: 超时时间（秒）
        """
        self.api_key = api_key
        self.api_base = api_base
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AIResponse:
        """
        发送对话请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            tools: 工具列表（可选，用于Function Calling）

        Returns:
            AIResponse对象
        """

    @abstractmethod
    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Iterator[str]:
        """
        流式对话请求

        Args:
            messages: 消息列表
            tools: 工具列表（可选）

        Yields:
            生成的文本片段
        """

    def _build_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        构建消息格式（可被子类覆盖以适配不同格式）

        Args:
            messages: 标准消息格式

        Returns:
            适配后的消息格式
        """
        return messages

    def _build_tools(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[Any]:
        """
        构建工具格式（可被子类覆盖以适配不同格式）

        Args:
            tools: 标准工具格式

        Returns:
            适配后的工具格式
        """
        return tools

    def test_connection(self) -> bool:
        """
        测试连接

        Returns:
            连接是否成功
        """
        try:
            response = self.chat([{"role": "user", "content": "Hello"}])
            return response.content is not None
        except Exception as e:
            print(f"连接测试失败: {str(e)}")
            return False


class ProviderException(Exception):
    """Provider异常基类"""


class ProviderAPIException(ProviderException):
    """API调用异常"""


class ProviderAuthException(ProviderException):
    """认证失败异常"""


class ProviderTimeoutException(ProviderException):
    """超时异常"""


class ProviderRateLimitException(ProviderException):
    """频率限制异常"""
