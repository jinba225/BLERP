"""
Together AI Provider - 开源模型聚合平台

支持模型：
- Meta Llama 系列
- Mixtral 系列
- Mistral 系列

官方文档：https://docs.together.ai/
"""


import openai

from .base import AIResponse, BaseAIProvider


class TogetherProvider(BaseAIProvider):
    """Together AI 提供商（兼容 OpenAI API 格式）"""

    DEFAULT_BASE_URL = "https://api.together.xyz/v1"

    def __init__(self, api_key: str, model_id: str = "meta-llama/Meta-Llama-3-70B-Instruct"):
        self.client = openai.OpenAI(api_key=api_key, base_url=self.DEFAULT_BASE_URL)
        self.model_id = model_id

    def chat(self, messages: list, **kwargs) -> AIResponse:
        """调用 Together AI API"""
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
