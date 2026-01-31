"""
Anthropic Claude Provider

支持 Claude-3-5-Sonnet, Claude-3-Opus 等模型
"""

from typing import List, Dict, Any, Optional, Iterator
import anthropic
from anthropic import Anthropic
from .base import (
    BaseAIProvider,
    AIResponse,
    ProviderAPIException,
    ProviderAuthException,
    ProviderTimeoutException,
    ProviderRateLimitException,
)


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude Provider 实现"""

    def __init__(self, api_key: str, api_base: Optional[str] = None,
                 model_name: str = "claude-3-5-sonnet-20241022", **kwargs):
        super().__init__(api_key, api_base, model_name, **kwargs)

        # 初始化Anthropic客户端
        client_params = {
            "api_key": self.api_key,
            "timeout": self.timeout,
        }
        if self.api_base:
            client_params["base_url"] = self.api_base

        self.client = Anthropic(**client_params)

    def chat(self, messages: List[Dict[str, str]],
             tools: Optional[List[Dict[str, Any]]] = None) -> AIResponse:
        """
        发送对话请求

        Args:
            messages: 消息列表
            tools: 工具列表（可选）

        Returns:
            AIResponse对象
        """
        try:
            # 分离system消息和其他消息
            system_message = None
            chat_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    chat_messages.append(msg)

            # 构建请求参数
            params = {
                "model": self.model_name,
                "messages": chat_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }

            # 添加system消息（如果有）
            if system_message:
                params["system"] = system_message

            # 如果有工具定义，添加到参数中
            if tools:
                params["tools"] = self._build_tools(tools)

            # 调用Anthropic API
            response = self.client.messages.create(**params)

            # 解析响应
            content = ""
            tool_calls = None

            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    if tool_calls is None:
                        tool_calls = []
                    tool_calls.append({
                        "id": block.id,
                        "type": "function",
                        "function": {
                            "name": block.name,
                            "arguments": str(block.input),
                        }
                    })

            return AIResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=response.stop_reason,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                model=response.model,
            )

        except anthropic.AuthenticationError as e:
            raise ProviderAuthException(f"Claude认证失败: {str(e)}")
        except anthropic.RateLimitError as e:
            raise ProviderRateLimitException(f"Claude频率限制: {str(e)}")
        except anthropic.APITimeoutError as e:
            raise ProviderTimeoutException(f"Claude请求超时: {str(e)}")
        except Exception as e:
            raise ProviderAPIException(f"Claude API调用失败: {str(e)}")

    def stream_chat(self, messages: List[Dict[str, str]],
                   tools: Optional[List[Dict[str, Any]]] = None) -> Iterator[str]:
        """
        流式对话请求

        Args:
            messages: 消息列表
            tools: 工具列表（可选）

        Yields:
            生成的文本片段
        """
        try:
            # 分离system消息和其他消息
            system_message = None
            chat_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    chat_messages.append(msg)

            # 构建请求参数
            params = {
                "model": self.model_name,
                "messages": chat_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }

            # 添加system消息（如果有）
            if system_message:
                params["system"] = system_message

            # 如果有工具定义，添加到参数中
            if tools:
                params["tools"] = self._build_tools(tools)

            # 调用Anthropic API（流式）
            with self.client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield text

        except anthropic.AuthenticationError as e:
            raise ProviderAuthException(f"Claude认证失败: {str(e)}")
        except anthropic.RateLimitError as e:
            raise ProviderRateLimitException(f"Claude频率限制: {str(e)}")
        except anthropic.APITimeoutError as e:
            raise ProviderTimeoutException(f"Claude请求超时: {str(e)}")
        except Exception as e:
            raise ProviderAPIException(f"Claude API调用失败: {str(e)}")

    def _build_tools(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """
        构建Claude工具格式

        Args:
            tools: 标准工具格式

        Returns:
            Claude工具格式
        """
        if not tools:
            return None

        claude_tools = []
        for tool in tools:
            claude_tools.append({
                "name": tool.get("name"),
                "description": tool.get("description"),
                "input_schema": tool.get("parameters", {}),
            })

        return claude_tools
