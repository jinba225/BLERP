"""
Mistral Provider - 法国 Mistral AI 的开源大模型

支持模型：
- Mistral 7B Instruct
- Mistral 8x7B Instruct
- Mixtral 8x7B

官方文档：https://docs.mistral.ai/
"""

import requests

from .base import AIResponse, BaseAIProvider


class MistralProvider(BaseAIProvider):
    """Mistral 提供商"""

    DEFAULT_BASE_URL = "https://api.mistral.ai/v1"

    def __init__(self, api_key: str, model_id: str = "mistral-7b-instruct"):
        self.api_key = api_key
        self.model_id = model_id
        self.base_url = self.DEFAULT_BASE_URL

    def chat(self, messages: list, **kwargs) -> AIResponse:
        """调用 Mistral API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "top_p": kwargs.get("top_p", 0.95),
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()

        data = response.json()

        return AIResponse(
            content=data["choices"][0]["message"]["content"],
            model=self.model_id,
            usage=data.get("usage", {}),
            raw_response=data,
        )
