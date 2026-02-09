"""
渠道 AI 服务

集成 NLP 和对话流管理器，为不同渠道提供统一的 AI 对话接口
"""

from typing import Optional

from ai_assistant.channels import ChannelAdapter
from ai_assistant.channels.base_channel import IncomingMessage, OutgoingMessage
from ai_assistant.providers import BaseAIProvider
from ai_assistant.services import ConversationContext, ConversationFlowManager, NLPService
from ai_assistant.services.customer_ai_service import CustomerAIService
from django.contrib.auth import get_user_model

from common.utils import decrypt_api_key

User = get_user_model()


class ChannelAIService:
    """
    渠道 AI 服务

    为不同渠道提供统一的 AI 对话接口
    """

    def __init__(self, user: User, channel: str):
        """
        初始化服务

        Args:
            user: 系统用户
            channel: 渠道类型（telegram/wechat/dingtalk/web）
        """
        self.user = user
        self.channel = channel

        # 获取用户 AI 配置（如果存在）- 必须在初始化 AI Provider 之前
        self.user_ai_config = self._get_user_ai_config()

        # 初始化 AI Provider
        self.ai_provider = self._get_effective_provider()

        # 初始化 NLP 服务
        if self.ai_provider:
            self.nlp_service = NLPService(self.ai_provider)

            # 初始化对话流管理器
            self.conversation_manager = ConversationFlowManager(self.nlp_service)

        # 初始化渠道适配器
        self.channel_adapter = ChannelAdapter(channel)

    def _get_effective_provider(self) -> Optional[BaseAIProvider]:
        """
        获取有效的 AI Provider

        Returns:
            BaseAIProvider 实例，如果没有配置则返回 None
        """
        from ai_assistant.models import AIModelConfig

        # 1. 优先使用客户级别的配置
        if self.user_ai_config and self.user_ai_config.model_config:
            config = self.user_ai_config.model_config
            return self._create_provider(config)

        # 2. 使用全局默认配置
        config = AIModelConfig.objects.filter(
            is_active=True, is_deleted=False, is_default=True
        ).first()

        if config:
            return self._create_provider(config)

        return None

    def _create_provider(self, config) -> BaseAIProvider:
        """创建 Provider 实例"""
        from ai_assistant.providers import (
            AnthropicProvider,
            DeepSeekProvider,
            MockAIProvider,
            OpenAIProvider,
        )

        provider_map = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "mock": MockAIProvider,
            "deepseek": DeepSeekProvider,
        }

        provider_class = provider_map.get(config.provider.lower())
        if not provider_class:
            return None

        # 创建 Provider 实例
        # Mock Provider 不需要解密
        if config.provider.lower() == "mock":
            api_key = config.api_key
        else:
            api_key = decrypt_api_key(config.api_key)

        provider_config = {
            "api_key": api_key,
            "model_name": config.model_name,
            "timeout": config.timeout,
        }

        # 添加可选配置
        if config.api_base:
            provider_config["api_base"] = config.api_base

        return provider_class(**provider_config)

    def _get_user_ai_config(self):
        """获取用户 AI 配置"""
        from ai_assistant.models import CustomerAIConfig
        from customers.models import Customer

        # 获取用户关联的客户
        try:
            customer = Customer.objects.filter(
                contact_person=self.user.email, is_deleted=False
            ).first()

            if customer:
                config = CustomerAIConfig.objects.filter(
                    customer=customer, is_active=True, is_deleted=False
                ).first()
                return config
        except Exception:
            pass

        return None

    def get_effective_system_prompt(self) -> str:
        """
        获取有效的系统提示词（客户配置 > 默认配置）

        Returns:
            系统提示词
        """
        # 优先使用客户配置
        if self.user_ai_config and self.user_ai_config.system_prompt:
            return self.user_ai_config.system_prompt

        # 返回默认提示词
        return """你是一个专业的 ERP 系统智能助手，帮助企业用户高效管理业务数据。

你的主要功能:
1. 协助用户创建和查询销售订单、报价单等业务单据
2. 回答关于客户、产品、库存等业务数据的问题
3. 提供数据分析和建议

注意事项:
- 严格按照用户的权限级别操作数据
- 对于重要操作，需要用户明确确认
- 保护用户隐私和商业机密
- 不确定的回答，请说明并建议用户咨询相关部门"""

    def process_message(self, message: IncomingMessage) -> OutgoingMessage:
        """
        处理入站消息

        Args:
            message: 入站消息

        Returns:
            出站消息
        """
        if not self.ai_provider:
            return self.channel_adapter.format_error_message("AI 模型未配置，请联系管理员配置", self.channel)

        # 1. 解析意图
        intent_result = self.nlp_service.parse_user_input(message.content)

        # 2. 处理对话
        session_id = self._get_session_id(message)

        try:
            reply, completed = self.conversation_manager.process_message(
                session_id=session_id, user_id=self.user.id, user_message=message.content
            )

            # 3. 更新用户 AI 配置统计
            if completed:
                self._update_conversation_stats(session_id)

            # 4. 转换为渠道格式
            return self.channel_adapter.format_response(reply, message)

        except Exception as e:
            return self.channel_adapter.format_error_message(f"处理消息时出错: {str(e)}", self.channel)

    def _get_session_id(self, message: IncomingMessage) -> str:
        """
        获取会话 ID

        Args:
            message: 入站消息

        Returns:
            会话 ID
        """
        if message.conversation_id:
            return message.conversation_id

        return f"{self.channel}_{message.external_user_id}"

    def _update_conversation_stats(self, session_id: str):
        """更新会话统计"""
        from ai_assistant.services import CustomerAIService

        try:
            # 从 session_id 中提取用户 ID
            parts = session_id.split("_", 1)
            if len(parts) == 3:
                # 格式: channel_external_user_id
                external_user_id = parts[1]

                # 查找用户映射
                from ai_assistant.models import ChannelUserMapping

                mapping = ChannelUserMapping.objects.filter(
                    channel=self.channel,
                    external_user_id=external_user_id,
                    is_active=True,
                    is_deleted=False,
                ).first()

                if mapping:
                    # 获取关联的客户
                    from customers.models import Customer

                    customer = Customer.objects.filter(
                        contact_person=mapping.user.email, is_deleted=False
                    ).first()

                    if customer:
                        CustomerAIService.increment_conversation_stats(customer.id, message_count=1)
        except Exception as e:
            print(f"更新会话统计失败: {str(e)}")

    def can_use_tool(self, tool_name: str) -> bool:
        """
        检查用户是否可以使用指定工具

        Args:
            tool_name: 工具名称

        Returns:
            是否可以使用
        """
        if not self.user_ai_config:
            # 没有配置，使用默认权限
            return tool_name in [
                "search_customer",
                "query_customer",
                "search_product",
                "query_product",
                "check_inventory",
                "query_inventory",
            ]

        return self.user_ai_config.can_use_tool(tool_name)

    def get_available_tools(self) -> list:
        """
        获取用户可用的工具列表

        Returns:
            工具名称列表
        """
        from ai_assistant.tools import ToolRegistry

        if self.user_ai_config:
            # 使用客户配置的工具列表
            allowed_tools = self.user_ai_config.get_allowed_tools_list()
            blocked_tools = self.user_ai_config.blocked_tools or []

            all_tools = ToolRegistry.get_available_tools(self.user)
            available = [
                tool.name
                for tool in all_tools
                if tool.name in allowed_tools and tool.name not in blocked_tools
            ]

            return available
        else:
            # 使用默认工具列表
            return [
                "search_customer",
                "query_customer",
                "search_product",
                "query_product",
                "check_inventory",
                "query_inventory",
            ]

    def can_query_data(self) -> bool:
        """检查用户是否可以查询数据"""
        if not self.user_ai_config:
            return True  # 默认允许查询

        return self.user_ai_config.can_query_data()

    def can_modify_data(self) -> bool:
        """检查用户是否可以修改数据"""
        if not self.user_ai_config:
            return False  # 默认不允许修改

        return self.user_ai_config.can_modify_data()

    def get_permission_summary(self) -> dict:
        """获取权限摘要"""
        if not self.user_ai_config:
            return {
                "has_config": False,
                "permission_level": "default",
                "can_query": True,
                "can_modify": False,
                "allowed_tools": [
                    "search_customer",
                    "query_customer",
                    "search_product",
                    "query_product",
                    "check_inventory",
                    "query_inventory",
                ],
                "blocked_tools": [],
            }

        return (
            CustomerAIService.get_customer_permission_summary(self.user_ai_config.customer.id)
            if self.user_ai_config
            else {}
        )

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return self.get_effective_system_prompt()

    def get_session_context(self, session_id: str) -> Optional[ConversationContext]:
        """获取会话上下文"""
        return self.conversation_manager.get_context(session_id)

    def reset_session(self, session_id: str) -> None:
        """重置会话"""
        return self.conversation_manager.reset_context(session_id)
