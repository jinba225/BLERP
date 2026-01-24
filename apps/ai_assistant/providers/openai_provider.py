"""
OpenAI Provider

支持 GPT-4, GPT-3.5-turbo 等模型
"""

from typing import List, Dict, Any, Optional, Iterator
import openai
from openai import OpenAI
from .base import (
    BaseAIProvider,
    AIResponse,
    ProviderAPIException,
    ProviderAuthException,
    ProviderTimeoutException,
    ProviderRateLimitException,
)


class OpenAIProvider(BaseAIProvider):
    """OpenAI Provider 实现"""

    def __init__(self, api_key: str, api_base: Optional[str] = None,
                 model_name: str = "gpt-3.5-turbo", **kwargs):
        super().__init__(api_key, api_base, model_name, **kwargs)

        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
            timeout=self.timeout,
        )

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
            # 构建请求参数
            params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }

            # 如果有工具定义，添加到参数中
            if tools:
                params["tools"] = self._build_tools(tools)

            # 调用OpenAI API
            response = self.client.chat.completions.create(**params)

            # 解析响应
            message = response.choices[0].message
            tool_calls = None

            # 检查是否有工具调用
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in message.tool_calls
                ]

            return AIResponse(
                content=message.content or "",
                tool_calls=tool_calls,
                finish_reason=response.choices[0].finish_reason,
                tokens_used=response.usage.total_tokens,
                model=response.model,
            )

        except openai.AuthenticationError as e:
            raise ProviderAuthException(f"OpenAI认证失败: {str(e)}")
        except openai.RateLimitError as e:
            raise ProviderRateLimitException(f"OpenAI频率限制: {str(e)}")
        except openai.APITimeoutError as e:
            raise ProviderTimeoutException(f"OpenAI请求超时: {str(e)}")
        except Exception as e:
            raise ProviderAPIException(f"OpenAI API调用失败: {str(e)}")

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
            # 构建请求参数
            params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": True,
            }

            # 如果有工具定义，添加到参数中
            if tools:
                params["tools"] = self._build_tools(tools)

            # 调用OpenAI API（流式）
            stream = self.client.chat.completions.create(**params)

            # 逐个返回生成的文本片段
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except openai.AuthenticationError as e:
            raise ProviderAuthException(f"OpenAI认证失败: {str(e)}")
        except openai.RateLimitError as e:
            raise ProviderRateLimitException(f"OpenAI频率限制: {str(e)}")
        except openai.APITimeoutError as e:
            raise ProviderTimeoutException(f"OpenAI请求超时: {str(e)}")
        except Exception as e:
            raise ProviderAPIException(f"OpenAI API调用失败: {str(e)}")

    def _build_tools(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """
        构建OpenAI工具格式

        Args:
            tools: 标准工具格式

        Returns:
            OpenAI工具格式
        """
        if not tools:
            return None

        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "parameters": tool.get("parameters", {}),
                }
            })

        return openai_tools
