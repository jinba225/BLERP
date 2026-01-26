"""
AI Providers 模块
"""

from apps.ai_assistant.providers.base import BaseAIProvider, AIResponse, ProviderException

__all__ = ['BaseAIProvider', 'AIResponse', 'ProviderException']

# 原有的 8 个 Provider
from apps.ai_assistant.providers.openai_provider import OpenAIProvider
from apps.ai_assistant.providers.anthropic_provider import AnthropicProvider
from apps.ai_assistant.providers.baidu_provider import BaiduProvider
from apps.ai_assistant.providers.aliyun_provider import AliyunProvider
from apps.ai_assistant.providers.tencent_provider import TencentProvider
from apps.ai_assistant.providers.zhipu_provider import ZhipuProvider
from apps.ai_assistant.providers.moonshot_provider import MoonshotProvider
from apps.ai_assistant.providers.deepseek_provider import DeepSeekProvider
from apps.ai_assistant.providers.mock_provider import MockAIProvider

# 新增 10 个 Provider
from apps.ai_assistant.providers.google_provider import GeminiProvider
from apps.ai_assistant.providers.azure_provider import AzureProvider
from apps.ai_assistant.providers.aws_bedrock_provider import BedrockProvider
from apps.ai_assistant.providers.groq_provider import GroqProvider
from apps.ai_assistant.providers.huggingface_provider import HuggingFaceProvider
from apps.ai_assistant.providers.cohere_provider import CohereProvider
from apps.ai_assistant.providers.mistral_provider import MistralProvider
from apps.ai_assistant.providers.perplexity_provider import PerplexityProvider
from apps.ai_assistant.providers.together_provider import TogetherProvider
from apps.ai_assistant.providers.openrouter_provider import OpenRouterProvider

__all__ = [
           # 基础类
           'BaseAIProvider',
           'AIResponse',
           'ProviderException',
           # 原有的 8 个 Provider
           'OpenAIProvider',
           'AnthropicProvider',
           'BaiduProvider',
           'AliyunProvider',
           'TencentProvider',
           'ZhipuProvider',
           'MoonshotProvider',
           'DeepSeekProvider',
           'MockAIProvider',
           # 新增 10 个 Provider
           'GeminiProvider',
           'AzureProvider',
           'BedrockProvider',
           'GroqProvider',
           'HuggingFaceProvider',
           'CohereProvider',
           'MistralProvider',
           'PerplexityProvider',
           'TogetherProvider',
           'OpenRouterProvider',
          ]
