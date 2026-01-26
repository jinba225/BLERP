"""
Google Gemini Provider

支持模型：
- Gemini 1.5 Pro
- Gemini 1.5 Flash
- Gemini 1.0 Pro

官方文档：https://ai.google.dev/gemini-api/docs
"""

from typing import Dict, Any
from ..base import BaseAIProvider, AIResponse, ProviderException
import requests


class GeminiProvider(BaseAIProvider):
    """Google Gemini 提供商"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://generativelanguage.googleapis.com/v1"
    
    def chat(self, messages: list, **kwargs) -> AIResponse:
        """调用 Gemini API"""
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        # 构建 Gemini 请求格式
        payload = self._build_payload(messages, **kwargs)
        
        # 调用 Gemini API
        url = f"{self.base_url}/models/{self.model_name}:generateContent"
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        # 解析响应
        content = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        
        return AIResponse(
            content=content,
            model=self.model_name,
            usage=data.get('usageMetadata', {}),
            raw_response=data
        )
    
    def _build_payload(self, messages: list, **kwargs) -> Dict:
        """构建 Gemini 请求载荷"""
        # Gemini 使用特殊的 prompt 格式
        contents = []
        for msg in messages:
            role = msg.get('role', 'user')
            if role == 'system':
                parts = [{"text": msg.get('content')}]
            else:
                parts = [{"text": msg.get('content')}]
            contents.append({"role": role, "parts": parts})
        
        return {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get('temperature', 0.7),
                "topK": kwargs.get('top_k', 40),
                "topP": kwargs.get('top_p', 0.95),
                "maxOutputTokens": kwargs.get('max_tokens', 2048),
            }
        }
