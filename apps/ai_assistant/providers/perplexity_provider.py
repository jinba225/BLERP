"""
Perplexity Provider - 强大的 AI 搜索

支持模型：
- pplx-7b-online
- pplx-70b-online
- pplx-12b-online
- mixtral-8x7b-instruct

官方文档：https://docs.perplexity.ai/
"""

from typing import Any, Dict

import openai

from .base import AIResponse, BaseAIProvider, ProviderException


class PerplexityProvider(BaseAIProvider):
    """Perplexity 提供商（兼容 OpenAI API 格式）"""

    DEFAULT_BASE_URL = "https://api.perplexity.ai/v1"

    def __init__(self, api_key: str, model_id: str = "pplx-7b-online"):
        self.client = openai.OpenAI(api_key=api_key, base_url=self.DEFAULT_BASE_URL)
        self.model_id = model_id

    def chat(self, messages: list, **kwargs) -> AIResponse:
        """调用 Perplexity API"""
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2048),
        )

        return AIResponse(
            content=response.choices[0].message.content,
            model=self.model_id,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
            raw_response=response,
        )
