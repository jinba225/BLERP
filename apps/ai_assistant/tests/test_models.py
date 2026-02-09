"""
AI Assistant module tests
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

User = get_user_model()

from apps.customers.models import Customer

from ..models import (
    AIConversation,
    AIMessage,
    AIModelConfig,
    AITool,
    AIToolExecutionLog,
    ChannelUserMapping,
    CustomerAIConfig,
    DingTalkConfig,
    TelegramConfig,
    WeChatConfig,
)


class CustomerAIConfigModelTest(TestCase):
    """CustomerAIConfig模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.customer = Customer.objects.create(
            name="测试客户",
            code="CUST001",
            created_by=self.user,
        )
        self.config = CustomerAIConfig.objects.create(
            customer=self.customer,
            permission_level="read_write",
            max_conversation_turns=20,
            created_by=self.user,
        )

    def test_customer_config_creation(self):
        """测试客户AI配置创建"""
        self.assertEqual(self.config.customer, self.customer)
        self.assertEqual(self.config.permission_level, "read_write")
        self.assertEqual(self.config.max_conversation_turns, 20)
        self.assertTrue(self.config.enable_tool_calling)
        self.assertTrue(self.config.enable_data_query)

    def test_custom_system_prompt(self):
        """测试自定义系统提示词"""
        self.config.system_prompt = "你是一个专业的销售助手"
        self.config.save()

        updated = CustomerAIConfig.objects.get(id=self.config.id)
        self.assertEqual(updated.system_prompt, "你是一个专业的销售助手")

    def test_allowed_tools(self):
        """测试允许的工具列表"""
        tools = ["query_customer", "query_product", "create_order"]
        self.config.allowed_tools = tools
        self.config.save()

        updated = CustomerAIConfig.objects.get(id=self.config.id)
        self.assertEqual(updated.allowed_tools, tools)

    def test_blocked_tools(self):
        """测试阻止的工具列表"""
        tools = ["delete_customer"]
        self.config.blocked_tools = tools
        self.config.save()

        updated = CustomerAIConfig.objects.get(id=self.config.id)
        self.assertEqual(updated.blocked_tools, tools)

    def test_permission_levels(self):
        """测试权限级别"""
        levels = ["read_only", "read_write", "full_access"]
        for level in levels:
            config = CustomerAIConfig.objects.create(
                customer=self.customer,
                permission_level=level,
                created_by=self.user,
            )
            self.assertEqual(config.permission_level, level)


class AIModelConfigModelTest(TestCase):
    """AIModelConfig模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.config = AIModelConfig.objects.create(
            model_name="GPT-4",
            model_version="gpt-4",
            provider="openai",
            api_key="sk-test-key",
            max_tokens=4000,
            temperature=0.7,
            created_by=self.user,
        )

    def test_model_config_creation(self):
        """测试AI模型配置创建"""
        self.assertEqual(self.config.model_name, "GPT-4")
        self.assertEqual(self.config.model_version, "gpt-4")
        self.assertEqual(self.config.provider, "openai")
        self.assertEqual(self.config.max_tokens, 4000)
        self.assertEqual(self.config.temperature, Decimal("0.7"))
        self.assertTrue(self.config.is_active)

    def test_model_providers(self):
        """测试不同的模型提供商"""
        providers = ["openai", "azure", "anthropic", "google"]
        for provider in providers:
            config = AIModelConfig.objects.create(
                model_name="Test-Model",
                provider=provider,
                created_by=self.user,
            )
            self.assertEqual(config.provider, provider)

    def test_max_tokens_validation(self):
        """测试最大token数验证"""
        invalid_tokens = [-100, 0, 100001]  # 超出范围
        for tokens in invalid_tokens:
            config = AIModelConfig(
                model_name="Test-Model",
                provider="openai",
                max_tokens=tokens,
                created_by=self.user,
            )
            self.assertTrue(not config.max_tokens or config.max_tokens < 100000)

    def test_temperature_range(self):
        """测试温度参数范围"""
        invalid_temps = [-1, 0, 0.5, 1, 2]  # 超出范围
        for temp in invalid_temps:
            config = AIModelConfig(
                model_name="Test-Model",
                provider="openai",
                temperature=temp,
                created_by=self.user,
            )
            self.assertTrue(0 <= config.temperature <= 1)


class AIConversationModelTest(TestCase):
    """AI对话模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.conversation = AIConversation.objects.create(
            customer_user=self.user,
            channel="web",
            status="active",
            created_by=self.user,
        )

    def test_conversation_creation(self):
        """测试对话创建"""
        self.assertEqual(self.conversation.customer_user, self.user)
        self.assertEqual(self.conversation.channel, "web")
        self.assertEqual(self.conversation.status, "active")
        self.assertTrue(self.conversation.is_active)

    def test_conversation_status_transitions(self):
        """测试对话状态转换"""
        self.conversation.status = "completed"
        self.conversation.completed_at = timezone.now()
        self.conversation.save()

        self.assertEqual(self.conversation.status, "completed")
        self.assertIsNotNone(self.conversation.completed_at)

    def test_channel_types(self):
        """测试不同的渠道类型"""
        channels = ["web", "wechat", "dingtalk", "telegram", "api"]
        for channel in channels:
            conv = AIConversation.objects.create(
                customer_user=self.user,
                channel=channel,
                created_by=self.user,
            )
            self.assertEqual(conv.channel, channel)

    def test_conversation_statistics(self):
        """测试对话统计"""
        self.conversation.message_count = 10
        self.conversation.token_count = 500
        self.conversation.save()

        self.assertEqual(self.conversation.message_count, 10)
        self.assertEqual(self.conversation.token_count, 500)


class AIMessageModelTest(TestCase):
    """AI消息模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.conversation = AIConversation.objects.create(
            customer_user=self.user,
            channel="web",
            created_by=self.user,
        )
        self.message = AIMessage.objects.create(
            conversation=self.conversation,
            role="user",
            content="你好，帮我查一下订单",
            created_by=self.user,
        )

    def test_message_creation(self):
        """测试消息创建"""
        self.assertEqual(self.message.conversation, self.conversation)
        self.assertEqual(self.message.role, "user")
        self.assertEqual(self.message.content, "你好，帮我查一下订单")
        self.assertTrue(self.message.is_active)

    def test_message_roles(self):
        """测试不同的消息角色"""
        roles = ["user", "assistant", "system"]
        for role in roles:
            msg = AIMessage.objects.create(
                conversation=self.conversation,
                role=role,
                content=f"测试消息-{role}",
                created_by=self.user,
            )
            self.assertEqual(msg.role, role)

    def test_message_statistics(self):
        """测试消息统计"""
        self.message.token_count = 100
        self.message.save()

        self.assertEqual(self.message.token_count, 100)

    def test_message_attachment(self):
        """测试消息附件"""
        self.message.has_attachment = True
        self.message.attachment_type = "image"
        self.message.attachment_url = "https://example.com/image.jpg"
        self.message.save()

        self.assertTrue(self.message.has_attachment)
        self.assertEqual(self.message.attachment_type, "image")


class AIToolModelTest(TestCase):
    """AI工具模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.tool = AITool.objects.create(
            tool_name="query_customer",
            display_name="查询客户",
            tool_type="data_query",
            description="根据客户名称或编码查询客户信息",
            function_name="query_customer_func",
            is_active=True,
            created_by=self.user,
        )

    def test_tool_creation(self):
        """测试工具创建"""
        self.assertEqual(self.tool.tool_name, "query_customer")
        self.assertEqual(self.tool.display_name, "查询客户")
        self.assertEqual(self.tool.tool_type, "data_query")
        self.assertEqual(self.tool.function_name, "query_customer_func")
        self.assertTrue(self.tool.is_active)

    def test_tool_types(self):
        """测试不同的工具类型"""
        tool_types = ["data_query", "data_modification", "system", "custom"]
        for tool_type in tool_types:
            tool = AITool.objects.create(
                tool_name=f"test_tool_{tool_type}",
                tool_type=tool_type,
                function_name=f"test_func",
                created_by=self.user,
            )
            self.assertEqual(tool.tool_type, tool_type)

    def test_tool_permissions(self):
        """测试工具权限"""
        required_permissions = ["customers.view_customer", "sales.view_order"]
        self.tool.required_permissions = required_permissions
        self.tool.save()

        self.assertEqual(self.tool.required_permissions, required_permissions)

    def test_tool_execution_count(self):
        """测试工具执行次数统计"""
        self.tool.total_executions = 10
        self.tool.successful_executions = 9
        self.tool.save()

        self.assertEqual(self.tool.total_executions, 10)
        self.assertEqual(self.tool.successful_executions, 9)


class AIToolExecutionLogModelTest(TestCase):
    """AI工具执行日志模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.conversation = AIConversation.objects.create(
            customer_user=self.user,
            channel="web",
            created_by=self.user,
        )
        self.tool = AITool.objects.create(
            tool_name="query_customer",
            tool_type="data_query",
            function_name="query_customer_func",
            is_active=True,
            created_by=self.user,
        )
        self.log = AIToolExecutionLog.objects.create(
            conversation=self.conversation,
            tool=self.tool,
            status="success",
            execution_time_ms=500,
            created_by=self.user,
        )

    def test_execution_log_creation(self):
        """测试执行日志创建"""
        self.assertEqual(self.log.conversation, self.conversation)
        self.assertEqual(self.log.tool, self.tool)
        self.assertEqual(self.log.status, "success")
        self.assertEqual(self.log.execution_time_ms, 500)

    def test_execution_status(self):
        """测试不同的执行状态"""
        statuses = ["success", "failed", "timeout", "cancelled"]
        for status in statuses:
            log = AIToolExecutionLog.objects.create(
                conversation=self.conversation,
                tool=self.tool,
                status=status,
                execution_time_ms=500,
                created_by=self.user,
            )
            self.assertEqual(log.status, status)

    def test_execution_time_recording(self):
        """测试执行时间记录"""
        times = [100, 500, 1000, 5000]
        for time_ms in times:
            log = AIToolExecutionLog.objects.create(
                conversation=self.conversation,
                tool=self.tool,
                status="success",
                execution_time_ms=time_ms,
                created_by=self.user,
            )
            self.assertEqual(log.execution_time_ms, time_ms)

    def test_error_handling(self):
        """测试错误处理"""
        self.log.status = "failed"
        self.log.error_message = "工具执行失败：连接超时"
        self.log.save()

        self.assertEqual(self.log.status, "failed")
        self.assertEqual(self.log.error_message, "工具执行失败：连接超时")


class ChannelUserMappingModelTest(TestCase):
    """渠道用户映射模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.config = TelegramConfig.objects.create(
            config_name="测试Telegram配置",
            bot_token="test-token",
            chat_id="test-chat-id",
            is_active=True,
            created_by=self.user,
        )
        self.mapping = ChannelUserMapping.objects.create(
            config=self.config,
            channel="telegram",
            channel_user_id="telegram_user_123",
            system_user=self.user,
            is_active=True,
            created_by=self.user,
        )

    def test_mapping_creation(self):
        """测试映射创建"""
        self.assertEqual(self.mapping.config, self.config)
        self.assertEqual(self.mapping.channel, "telegram")
        self.assertEqual(self.mapping.channel_user_id, "telegram_user_123")
        self.assertEqual(self.mapping.system_user, self.user)
        self.assertTrue(self.mapping.is_active)

    def test_channel_types(self):
        """测试不同的渠道类型"""
        channels = ["wechat", "dingtalk", "telegram", "email"]
        for channel in channels:
            config = TelegramConfig.objects.create(
                config_name=f"测试{channel}配置",
                bot_token="test-token",
                chat_id="test-chat-id",
                created_by=self.user,
            )
            mapping = ChannelUserMapping.objects.create(
                config=config,
                channel=channel,
                channel_user_id=f"{channel}_user_123",
                system_user=self.user,
                created_by=self.user,
            )
            self.assertEqual(mapping.channel, channel)

    def test_unique_channel_mapping(self):
        """测试渠道用户映射的唯一性"""
        # 同一个渠道用户ID应该对应唯一的系统用户
        with self.assertRaises(Exception):
            ChannelUserMapping.objects.create(
                config=self.config,
                channel="telegram",
                channel_user_id="telegram_user_123",
                system_user=self.user,
                created_by=self.user,
            )
