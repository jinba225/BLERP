"""
DeepSeek AI Provider

DeepSeek API 提供商实现
"""

import asyncio
import json
from typing import Any, Dict, Iterator, List, Optional

import httpx

from .base import AIResponse, BaseAIProvider


class DeepSeekProvider(BaseAIProvider):
    """DeepSeek AI Provider

    使用 DeepSeek API 调用 AI 模型
    DeepSeek API 兼容 OpenAI API 格式
    """

    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
    DEFAULT_MODEL = "deepseek-chat"

    def __init__(
        self,
        api_key: str,
        model_name: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: int = 30,
        **kwargs,
    ):
        """初始化 DeepSeek Provider

        Args:
            api_key: DeepSeek API Key
            model_name: 模型名称（默认为 deepseek-chat）
            api_base: API Base URL（默认为 https://api.deepseek.com/v1）
            timeout: 超时时间（秒）
            **kwargs: 其他参数
        """
        super().__init__(
            api_key=api_key,
            api_base=api_base,
            model_name=model_name or self.DEFAULT_MODEL,
            timeout=timeout,
        )

        self.api_base = api_base or self.DEFAULT_BASE_URL

        # 创建 HTTP 客户端
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    async def generate_text(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> str:
        """生成文本（兼容旧接口）

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            **kwargs: 其他参数（temperature, max_tokens 等）

        Returns:
            生成的文本
        """
        # 将 prompt 转换为 messages 格式
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 调用新的 chat 方法
        response = await self._chat_async(messages, **kwargs)
        return response.content

    async def _chat_async(self, messages: List[Dict[str, str]], **kwargs) -> AIResponse:
        """异步chat方法（内部使用）

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            AIResponse对象
        """
        # 构建请求参数
        request_params = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
        }

        # 添加可选参数
        if "temperature" in kwargs:
            request_params["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            request_params["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            request_params["top_p"] = kwargs["top_p"]

        # 发送请求
        try:
            # 调试日志
            import logging

            logger = logging.getLogger(__name__)
            logger.info(f"DeepSeek API 请求: model={self.model_name}, messages={len(messages)}")

            response = await self.client.post("/chat/completions", json=request_params)
            response.raise_for_status()

            # 解析响应
            result = response.json()

            # 提取生成的文本
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                # 提取token使用情况
                tokens_used = result.get("usage", {}).get("total_tokens", 0)

                return AIResponse(
                    content=content,
                    tokens_used=tokens_used,
                    model=self.model_name,
                    finish_reason=result["choices"][0].get("finish_reason"),
                )
            else:
                raise ValueError(f"DeepSeek API 返回的格式不正确: {result}")

        except httpx.HTTPError as e:
            raise Exception(f"DeepSeek API 请求失败: {str(e)}")

    def chat(
        self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None
    ) -> AIResponse:
        """同步chat方法（实现BaseAIProvider接口）

        Args:
            messages: 消息列表
            tools: 工具列表（暂不支持）

        Returns:
            AIResponse对象
        """
        # 在新的事件循环中运行异步方法
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self._chat_async(messages))

    def stream_chat(
        self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None
    ) -> Iterator[str]:
        """流式chat方法（实现BaseAIProvider接口）

        Args:
            messages: 消息列表
            tools: 工具列表（暂不支持）

        Yields:
            生成的文本片段
        """
        # 在新的事件循环中运行异步方法
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        async def _stream():
            async for chunk in self._stream_chat_async(messages):
                yield chunk

        # 创建生成器
        gen = _stream()
        try:
            while True:
                yield loop.run_until_complete(gen.__anext__())
        except StopAsyncIteration:
            pass

    async def _stream_chat_async(
        self,
        messages: List[Dict[str, str]],
    ):
        """异步流式chat方法（内部使用）

        Args:
            messages: 消息列表

        Yields:
            生成的文本片段
        """
        # 构建请求参数
        request_params = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
        }

        # 发送请求
        try:
            async with self.client.stream(
                "POST", "/chat/completions", json=request_params
            ) as response:
                response.raise_for_status()

                # 解析流式响应
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # 去掉 "data: " 前缀

                        # 跳过 [DONE] 标记
                        if data == "[DONE]":
                            break

                        # 解析 JSON
                        try:
                            import json

                            chunk = json.loads(data)

                            # 提取生成的文本
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPError as e:
            raise Exception(f"DeepSeek API 请求失败: {str(e)}")

    async def generate_text_stream(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ):
        """流式生成文本

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            **kwargs: 其他参数（temperature, max_tokens 等）

        Yields:
            生成的文本片段
        """
        messages = []

        # 添加系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # 添加用户提示词
        messages.append({"role": "user", "content": prompt})

        # 构建请求参数
        request_params = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
        }

        # 添加可选参数
        if "temperature" in kwargs:
            request_params["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            request_params["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            request_params["top_p"] = kwargs["top_p"]

        # 发送请求
        try:
            async with self.client.stream(
                "POST", "/chat/completions", json=request_params
            ) as response:
                response.raise_for_status()

                # 解析流式响应
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # 去掉 "data: " 前缀

                        # 跳过 [DONE] 标记
                        if data == "[DONE]":
                            break

                        # 解析 JSON
                        try:
                            chunk = json.loads(data)

                            # 提取生成的文本
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPError as e:
            raise Exception(f"DeepSeek API 请求失败: {str(e)}")

    async def test_connection(self) -> bool:
        """测试连接

        Returns:
            是否连接成功
        """
        try:
            # 发送一个简单的请求
            response = await self.generate_text(prompt="你好", max_tokens=10)
            return bool(response)
        except Exception:
            return False

    def close(self):
        """关闭客户端"""
        import asyncio

        # 异步关闭客户端
        if hasattr(self, "client") and not self.client.is_closed:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.client.aclose())
                else:
                    loop.run_until_complete(self.client.aclose())
            except Exception:
                pass

    def __del__(self):
        """析构函数，确保客户端被关闭"""
        self.close()

    @classmethod
    def get_provider_info(cls) -> Dict[str, Any]:
        """获取 Provider 信息"""
        return {
            "name": "DeepSeek",
            "type": "deepseek",
            "models": [
                {
                    "id": "deepseek-chat",
                    "name": "DeepSeek Chat",
                    "description": "DeepSeek 对话模型",
                    "context_length": 128000,
                },
                {
                    "id": "deepseek-coder",
                    "name": "DeepSeek Coder",
                    "description": "DeepSeek 代码模型",
                    "context_length": 128000,
                },
            ],
            "api_base": cls.DEFAULT_BASE_URL,
            "features": [
                "text_generation",
                "streaming",
                "system_prompt",
            ],
        }
