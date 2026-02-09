"""
Groq Provider - 高性能、低延迟

支持模型：
- Llama 3 70B
- Mixtral 8x7B

官方文档：https://console.groq.com/docs
"""


import openai

from .base import AIResponse, BaseAIProvider


class GroqProvider(BaseAIProvider):
    """Groq 提供商（兼容 OpenAI API 格式）"""

    DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self, api_key: str, model_id: str = "llama3-70b-8192"):
        self.client = openai.OpenAI(api_key=api_key, base_url=self.DEFAULT_BASE_URL)
        self.model_id = model_id

    def chat(self, messages: list, **kwargs) -> AIResponse:
        """调用 Groq API"""
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
