"""
OpenRouter Provider - 多模型路由平台

支持 100+ 个模型，包括：
- OpenAI GPT-4/3.5
- Anthropic Claude 3/2
- Meta Llama 系列
- Mistral 系列
- Cohere 系列
- 其他开源模型

官方文档：https://openrouter.com/docs
"""

import openai

from .base import AIResponse, BaseAIProvider


class OpenRouterProvider(BaseAIProvider):
    """OpenRouter 提供商（兼容 OpenAI API 格式）"""

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str, model_id: str = "openai/gpt-4"):
        self.client = openai.OpenAI(api_key=api_key, base_url=self.DEFAULT_BASE_URL)
        self.model_id = model_id

    def chat(self, messages: list, **kwargs) -> AIResponse:
        """调用 OpenRouter API"""
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
