"""
Cohere Provider - 专注于 RAG（检索增强生成）

支持模型：
- Command R
- Command R+
- Command Light
- Command Light

官方文档：https://docs.cohere.com/
"""


import cohere

from .base import AIResponse, BaseAIProvider


class CohereProvider(BaseAIProvider):
    """Cohere 提供商"""

    def __init__(self, api_key: str, model_id: str = "command-r"):
        self.client = cohere.Client(api_key=api_key)
        self.model_id = model_id

    def chat(self, messages: list, **kwargs) -> AIResponse:
        """调用 Cohere API"""
        # 构建 Chat 消息
        chat_history = []
        for msg in messages:
            chat_history.append(
                cohere.ChatMessage(role=msg.get("role", "user"), message=msg.get("content"))
            )

        # 如果有系统消息，单独处理
        if messages and messages[0].get("role") == "system":
            system_message = messages[0].get("content")
            response = self.client.chat(
                message=chat_history[1:],
                model=self.model_id,
                preamble=system_message,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
            )
        else:
            response = self.client.chat(
                message=chat_history,
                model=self.model_id,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
            )

        return AIResponse(
            content=response.text,
            model=self.model_id,
            usage={
                "tokens": response.meta.tokens.input_tokens + response.meta.tokens.output_tokens,
            },
            raw_response=response,
        )
