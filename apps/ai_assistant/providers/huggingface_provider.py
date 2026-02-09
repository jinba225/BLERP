"""
Hugging Face Provider - 开源模型平台

支持模型：
- Meta Llama 系列
- Mistral 系列
- Qwen 系列
- 其他开源模型

官方文档：https://huggingface.co/docs/api-inference
"""


import requests

from .base import AIResponse, BaseAIProvider


class HuggingFaceProvider(BaseAIProvider):
    """Hugging Face 提供商"""

    DEFAULT_BASE_URL = "https://api-inference.huggingface.co/models"

    def __init__(self, api_token: str, model_id: str):
        self.api_token = api_token
        self.model_id = model_id
        self.base_url = f"{self.DEFAULT_BASE_URL}/{model_id}"

    def chat(self, messages: list, **kwargs) -> AIResponse:
        """调用 Hugging Face API"""
        headers = {"Authorization": f"Bearer {self.api_token}"}

        # 构建提示词
        prompt = self._build_prompt(messages)

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.95),
                "return_full_text": False,
            },
        }

        response = requests.post(self.base_url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        data = response.json()

        # Hugging Face 可能返回多个候选结果
        content = data.get("0", {}).get("generated_text", "")

        return AIResponse(
            content=content, model=self.model_id, usage=data.get("usage", {}), raw_response=data
        )

    def _build_prompt(self, messages: list) -> str:
        """构建提示词（Hugging Face 使用文本格式）"""
        prompt = ""
        for msg in messages:
            if msg.get("role") == "system":
                prompt += f"System: {msg.get('content')}\n"
            elif msg.get("role") == "user":
                prompt += f"User: {msg.get('content')}\n"
            elif msg.get("role") == "assistant":
                prompt += f"Assistant: {msg.get('content')}\n"
        return prompt
