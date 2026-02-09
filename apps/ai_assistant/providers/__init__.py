"""
AI Providers 模块
"""

from ai_assistant.providers.anthropic_provider import AnthropicProvider
from ai_assistant.providers.azure_provider import AzureProvider
from ai_assistant.providers.baidu_provider import BaiduProvider
from ai_assistant.providers.base import AIResponse, BaseAIProvider, ProviderException
from ai_assistant.providers.deepseek_provider import DeepSeekProvider

# 新增 10 个 Provider
from ai_assistant.providers.google_provider import GeminiProvider as GoogleProvider
from ai_assistant.providers.mock_provider import MockAIProvider

# 原有的 Provider
from ai_assistant.providers.openai_provider import OpenAIProvider

# AWS Bedrock Provider（如需要请取消注释并安装 boto3）
# try:
#     from ai_assistant.providers.aws_bedrock_provider import BedrockProvider as AWSBedrockProvider
# except ImportError:
#     AWSBedrockProvider = None
#     print("警告: AWS Bedrock Provider 需要安装 boto3: pip install boto3")
AWSBedrockProvider = None

try:
    from ai_assistant.providers.groq_provider import GroqProvider
except ImportError:
    GroqProvider = None
    print("警告: Groq Provider 需要安装 groq: pip install groq")

try:
    from ai_assistant.providers.huggingface_provider import HuggingFaceProvider
except ImportError:
    HuggingFaceProvider = None
    print("警告: HuggingFace Provider 需要安装 huggingface_hub: pip install huggingface_hub")

# Cohere Provider（如需要请取消注释并安装 cohere）
# try:
#     from ai_assistant.providers.cohere_provider import CohereProvider
# except ImportError:
#     CohereProvider = None
#     print("警告: Cohere Provider 需要安装 cohere: pip install cohere")
CohereProvider = None

try:
    from ai_assistant.providers.mistral_provider import MistralProvider
except ImportError:
    MistralProvider = None
    print("警告: Mistral Provider 需要安装 mistralai: pip install mistralai")

try:
    from ai_assistant.providers.perplexity_provider import PerplexityProvider
except ImportError:
    PerplexityProvider = None
    print("警告: Perplexity Provider 需要安装 openai (或 perplexity SDK): pip install openai")

try:
    from ai_assistant.providers.together_provider import TogetherProvider
except ImportError:
    TogetherProvider = None
    print("警告: Together Provider 需要安装 openai: pip install openai")

try:
    from ai_assistant.providers.openrouter_provider import OpenRouterProvider
except ImportError:
    OpenRouterProvider = None
    print("警告: OpenRouter Provider 需要安装 openai: pip install openai")

__all__ = [
    # 基础类
    "BaseAIProvider",
    "AIResponse",
    "ProviderException",
    # 原有的 Provider
    "OpenAIProvider",
    "AnthropicProvider",
    "BaiduProvider",
    "MockAIProvider",
    "DeepSeekProvider",
    # 新增 Provider
    "GoogleProvider",
    "AzureProvider",
    # 'AWSBedrockProvider',  # 已禁用
    "GroqProvider",
    "HuggingFaceProvider",
    # 'CohereProvider',  # 已禁用
    "MistralProvider",
    "PerplexityProvider",
    "TogetherProvider",
    "OpenRouterProvider",
]
