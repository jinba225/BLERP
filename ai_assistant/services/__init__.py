"""
AI Assistant Services 模块

提供 AI 助手相关服务，包括自然语言处理、对话流管理和渠道集成。
"""

from .ai_service import AIService

from .nlp_service import (
    NLPService,
    Intent,
    IntentResult
)

from .conversation_flow_manager import (
    ConversationFlowManager,
    ConversationContext,
    ConversationState
)

from .customer_ai_service import (
    CustomerAIService
)

from .channel_ai_service import ChannelAIService

__all__ = [
    # AI Service
    'AIService',
    
    # NLP Service
    'NLPService',
    'Intent',
    'IntentResult',
    
    # Conversation Flow Manager
    'ConversationFlowManager',
    'ConversationContext',
    'ConversationState',
    
    # Customer AI Service
    'CustomerAIService',
    
    # Channel AI Service
    'ChannelAIService',
]
