"""
AI Service 统一服务接口

负责：
1. Provider选择和初始化
2. 会话管理
3. 消息记录
4. Token统计
"""

from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import time

from ..models import AIModelConfig, AIConversation, AIMessage
from ..utils import decrypt_api_key
from ..providers.base import BaseAIProvider, AIResponse
from ..providers.openai_provider import OpenAIProvider
from ..providers.anthropic_provider import AnthropicProvider
from ..providers.baidu_provider import BaiduProvider
from ..providers.mock_provider import MockAIProvider

User = get_user_model()


class AIService:
    """AI服务统一接口"""

    # Provider映射表
    PROVIDER_MAP = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "baidu": BaiduProvider,
        "mock": MockAIProvider,  # 测试用Mock Provider
        # 其他Provider可以后续添加
    }

    def __init__(self, user: User, model_config: Optional[AIModelConfig] = None):
        """
        初始化AI服务

        Args:
            user: 用户对象
            model_config: 指定的模型配置（可选，不指定则使用默认配置）
        """
        self.user = user

        # 获取模型配置
        if model_config:
            self.model_config = model_config
        else:
            self.model_config = self._get_default_model_config()

        # 初始化Provider
        self.provider = self._init_provider()

    def _get_default_model_config(self) -> AIModelConfig:
        """获取默认的模型配置"""
        config = (
            AIModelConfig.objects.filter(is_active=True, is_deleted=False)
            .order_by("-is_default", "-priority")
            .first()
        )

        if not config:
            raise ValueError("没有可用的AI模型配置，请先在系统中添加配置")

        return config

    def _init_provider(self) -> BaseAIProvider:
        """初始化Provider"""
        provider_class = self.PROVIDER_MAP.get(self.model_config.provider)

        if not provider_class:
            raise ValueError(f"不支持的Provider类型: {self.model_config.provider}")

        # Mock Provider 不需要解密API Key
        if self.model_config.provider == "mock":
            api_key = "mock-api-key"
        else:
            # 解密API Key
            try:
                api_key = decrypt_api_key(self.model_config.api_key)
            except Exception as e:
                raise ValueError(f"API Key解密失败: {str(e)}")

        # 初始化Provider
        return provider_class(
            api_key=api_key,
            api_base=self.model_config.api_base or None,
            model_name=self.model_config.model_name,
            temperature=float(self.model_config.temperature),
            max_tokens=self.model_config.max_tokens,
            timeout=self.model_config.timeout,
        )

    def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        channel: str = "web",
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AIResponse:
        """
        发送对话消息

        Args:
            message: 用户消息
            conversation_id: 会话ID（可选，用于多轮对话）
            channel: 渠道（web/wechat/dingtalk）
            tools: 可用工具列表（可选）

        Returns:
            AIResponse对象
        """
        # 获取或创建会话
        conversation = self._get_or_create_conversation(conversation_id, channel)

        # 记录用户消息
        self._save_message(conversation=conversation, role="user", content=message)

        # 获取上下文消息
        context_messages = self._get_context_messages(conversation)

        # 添加当前用户消息
        context_messages.append({"role": "user", "content": message})

        # 调用Provider
        start_time = time.time()
        response = self.provider.chat(context_messages, tools)
        response_time = time.time() - start_time

        # 记录AI响应
        self._save_message(
            conversation=conversation,
            role="assistant",
            content=response.content,
            tool_calls=response.tool_calls,
            tokens_used=response.tokens_used,
            response_time=response_time,
        )

        # 更新会话信息
        conversation.message_count = conversation.messages.count()
        conversation.last_message_at = timezone.now()
        conversation.save()

        # 更新模型配置统计
        self.model_config.total_requests += 1
        self.model_config.total_tokens += response.tokens_used
        self.model_config.last_used_at = timezone.now()
        self.model_config.save()

        return response

    def stream_chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        channel: str = "web",
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Iterator[str]:
        """
        流式对话

        Args:
            message: 用户消息
            conversation_id: 会话ID
            channel: 渠道
            tools: 可用工具列表

        Yields:
            生成的文本片段
        """
        # 获取或创建会话
        conversation = self._get_or_create_conversation(conversation_id, channel)

        # 记录用户消息
        self._save_message(conversation=conversation, role="user", content=message)

        # 获取上下文消息
        context_messages = self._get_context_messages(conversation)
        context_messages.append({"role": "user", "content": message})

        # 流式调用Provider
        start_time = time.time()
        full_response = ""

        for chunk in self.provider.stream_chat(context_messages, tools):
            full_response += chunk
            yield chunk

        response_time = time.time() - start_time

        # 记录完整的AI响应
        self._save_message(
            conversation=conversation,
            role="assistant",
            content=full_response,
            response_time=response_time,
        )

        # 更新会话信息
        conversation.message_count = conversation.messages.count()
        conversation.last_message_at = timezone.now()
        conversation.save()

        # 更新模型配置统计
        self.model_config.total_requests += 1
        self.model_config.last_used_at = timezone.now()
        self.model_config.save()

    def _get_or_create_conversation(
        self, conversation_id: Optional[str], channel: str
    ) -> AIConversation:
        """获取或创建会话"""
        if conversation_id:
            # 尝试获取现有会话
            conversation = AIConversation.objects.filter(
                conversation_id=conversation_id, user=self.user, is_deleted=False
            ).first()

            if conversation:
                return conversation

        # 创建新会话
        conversation_id = conversation_id or self._generate_conversation_id()
        conversation = AIConversation.objects.create(
            conversation_id=conversation_id,
            user=self.user,
            channel=channel,
            status="active",
            created_by=self.user,
        )

        return conversation

    def _generate_conversation_id(self) -> str:
        """生成会话ID"""
        return f"conv_{uuid.uuid4().hex[:16]}"

    def _get_context_messages(
        self, conversation: AIConversation, limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        获取上下文消息

        Args:
            conversation: 会话对象
            limit: 最多获取多少条消息（默认10条）

        Returns:
            消息列表
        """
        messages = conversation.messages.filter(is_deleted=False).order_by("-created_at")[:limit]

        # 反转顺序（最早的在前）
        messages = list(reversed(messages))

        context = []
        for msg in messages:
            # 跳过最后一条用户消息（因为会在外部添加）
            if msg == messages[-1] and msg.role == "user":
                continue

            context.append({"role": msg.role, "content": msg.content})

        return context

    def _save_message(
        self,
        conversation: AIConversation,
        role: str,
        content: str,
        tool_calls: Optional[List] = None,
        tokens_used: int = 0,
        response_time: float = None,
    ):
        """保存消息到数据库"""
        AIMessage.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            tool_calls=tool_calls,
            model_config=self.model_config if role == "assistant" else None,
            tokens_used=tokens_used,
            response_time=response_time,
            created_by=self.user,
        )

    @classmethod
    def test_config(cls, config: AIModelConfig) -> tuple[bool, str]:
        """
        测试配置是否可用

        Args:
            config: 模型配置

        Returns:
            (是否成功, 消息)
        """
        try:
            # 创建临时Provider
            provider_class = cls.PROVIDER_MAP.get(config.provider)
            if not provider_class:
                return False, f"不支持的Provider类型: {config.provider}"

            # 解密API Key
            api_key = decrypt_api_key(config.api_key)

            # 初始化Provider
            provider = provider_class(
                api_key=api_key,
                api_base=config.api_base or None,
                model_name=config.model_name,
                temperature=float(config.temperature),
                max_tokens=config.max_tokens,
                timeout=config.timeout,
            )

            # 测试连接
            if provider.test_connection():
                return True, "连接测试成功！"
            else:
                return False, "连接测试失败，请检查配置"

        except Exception as e:
            return False, f"测试失败: {str(e)}"
