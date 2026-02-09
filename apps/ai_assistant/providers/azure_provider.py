"""
Microsoft Azure OpenAI Provider

支持模型：
- GPT-4o
- GPT-4 Turbo
- GPT-35 Turbo
- GPT-35
- GPT-3.5 Turbo

官方文档：https://learn.microsoft.com/zh-cn/azure/ai-services/openai/
"""

from typing import Any, Dict

import openai

from .base import AIResponse, BaseAIProvider, ProviderException


class AzureProvider(BaseAIProvider):
    """Microsoft Azure OpenAI 提供商"""

    def __init__(self, api_key: str, deployment_id: str, resource_name: str = "openai"):
        self.api_key = api_key
        self.deployment_id = deployment_id
        self.resource_name = resource_name
        self.api_version = "2024-02-01-preview"  # 最新的 API 版本
        self.timeout = 60

    def chat(self, messages: list, **kwargs) -> AIResponse:
        """调用 Azure OpenAI API"""
        headers = {"Content-Type": "application/json", "api-key": self.api_key}

        # 构建 OpenAI 格式的请求
        payload = {
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }

        # 构建 URL
        url = f"https://{self.resource_name}.openai.azure.com/openai/deployments/{self.deployment_id}/chat/completions"

        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()

        return AIResponse(
            content=data["choices"][0]["message"]["content"],
            model=self.deployment_id,
            usage=data.get("usage", {}),
            raw_response=data,
        )
