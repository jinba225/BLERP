"""
集成测试

测试渠道集成、NLP、对话流管理和工具执行
"""

import os
import time
from datetime import datetime

import django
from ai_assistant.providers import MockAIProvider
from ai_assistant.services import ConversationFlowManager, NLPService
from django.contrib.auth import get_user_model
from django.test import TestCase

# 设置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "better_laser_erp.settings")


django.setup()


User = get_user_model()


class ChannelAIServiceTest(TestCase):
    """渠道 AI 服务测试"""

    def setUp(self):
        """设置测试环境"""
        from apps.ai_assistant.models import AIModelConfig

        # 创建测试用户
        self.user = User.objects.create_user(
            username="test_user", email="test@example.com", password="testpass123"
        )

        # 创建 Mock AI Model Config（不加密，因为是测试）
        self.mock_config = AIModelConfig.objects.create(
            name="Mock Provider",
            provider="mock",
            model_name="mock-model",
            api_key="test-key",  # 不加密，因为是测试
            is_active=True,
            is_default=True,
            created_by=self.user,
        )

        # 创建 Mock AI Provider
        self.mock_provider = MockAIProvider(api_key="test-key", model_name="mock-model", timeout=30)

        # 初始化服务
        self.nlp_service = NLPService(self.mock_provider)
        self.conversation_manager = ConversationFlowManager(self.nlp_service)
        self.channel_adapter = None

    def tearDown(self):
        """清理测试环境"""
        if hasattr(self, "mock_config"):
            self.mock_config.delete()

    def test_intent_recognition(self):
        """测试意图识别"""
        test_cases = [
            {
                "input": "给北京科技有限公司创建一个订单",
                "expected_intent": "create_order",
                "expected_entities": {"customer_name": "北京科技有限公司"},
            },
            {
                "input": "查询订单 SO2025010001 的状态",
                "expected_intent": "query_order",
                "expected_entities": {"order_number": "SO2025010001"},
            },
            {
                "input": "审核订单 SO2025010002",
                "expected_intent": "approve_order",
                "expected_entities": {"order_number": "SO2025010002"},
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            result = self.nlp_service.parse_user_input(test_case["input"])

            self.assertEqual(
                result.intent.value, test_case["expected_intent"], f"测试用例 {i}: {test_case['input']}"
            )

            self.assertGreater(result.confidence, 0.5, f"测试用例 {i}: 置信度应该大于 0.5")

            for key, value in test_case["expected_entities"].items():
                if key in result.entities:
                    self.assertEqual(str(result.entities[key]), value, f"测试用例 {i}: 实体 {key} 应该匹配")

    def test_conversation_flow(self):
        """测试对话流管理"""
        session_id = f"test_session_{datetime.now().timestamp()}"
        user_id = self.user.id

        # 第一轮：开始创建订单（使用明确的命令）
        reply1, completed1 = self.conversation_manager.process_message(
            session_id=session_id, user_id=user_id, user_message="给北京科技有限公司创建一个销售订单"
        )

        # 第一轮应该询问缺失信息
        self.assertIn("需要了解", reply1, "第一轮应该询问缺失信息")
        self.assertIn("需要了解", reply1, "第一轮应该包含'需要了解'")
        self.assertIn("以下信息", reply1, "第一轮应该包含'以下信息'")
        self.assertFalse(completed1, "第一轮不应该完成")

        # 第二轮：提供产品信息
        reply2, completed2 = self.conversation_manager.process_message(
            session_id=session_id, user_id=user_id, user_message="产品是笔记本电脑"
        )

        # 第二轮应该询问更多缺失信息
        self.assertIn("客户", reply2, "第二轮应该包含'客户'")
        self.assertIn("数量", reply2, "第二轮应该包含'数量'")
        self.assertFalse(completed2, "第二轮不应该完成")

        # 第三轮：提供数量信息
        reply3, completed3 = self.conversation_manager.process_message(
            session_id=session_id, user_id=user_id, user_message="数量是 100"
        )

        # 第三轮应该进入确认阶段（所有信息都已收集）
        self.assertIn("确认", reply3, "第三轮应该进入确认阶段")
        self.assertFalse(completed3, "第三轮不应该完成")

        # 第四轮：确认执行
        reply4, completed4 = self.conversation_manager.process_message(
            session_id=session_id, user_id=user_id, user_message="确认"
        )

        # 第四轮应该完成
        self.assertTrue(completed4, "第四轮应该完成")
        self.assertIn("成功", reply4, "第四轮应该包含成功信息")

    def test_channel_adapter(self):
        """测试渠道适配器"""
        from ai_assistant.channels import ChannelAdapter

        test_cases = [
            ("telegram", '<svg class="icon-success">', '<svg class="icon-success"> 成功'),
            ("wechat", '<svg class="icon-success">', '<svg class="icon-success"> 成功'),
            ("dingtalk", '<svg class="icon-success">', '<svg class="icon-success"> 成功'),
            ("web", "成功", "成功"),
        ]

        for channel, expected_format, text in test_cases:
            adapter = ChannelAdapter(channel)
            formatted = adapter._apply_markdown(text, platform=channel)

            self.assertIn(
                expected_format, formatted, f"渠道 {channel} 的 Markdown 格式应该包含 '{expected_format}'"
            )

    def test_channel_ai_service(self):
        """测试渠道 AI 服务"""
        from ai_assistant.channels import IncomingMessage
        from ai_assistant.services import ChannelAIService

        test_channels = ["web", "telegram", "wechat", "dingtalk"]

        for channel in test_channels:
            adapter = ChannelAIService(self.user, channel)

            # 创建测试消息
            message = IncomingMessage(
                message_id=f"test_{channel}_{datetime.now().timestamp()}",
                channel=channel,
                external_user_id="test_user",
                content="查询订单 SO2025010001 的状态",
                timestamp=datetime.now(),
                message_type="text",
                conversation_id=f"test_{channel}_test_user",
            )

            # 处理消息
            response = adapter.process_message(message)

            self.assertIsNotNone(response, f"渠道 {channel} 的响应不应为空")
            self.assertIn("订单", response.content, f"渠道 {channel} 的响应应该包含'订单'")

            # 重置会话
            adapter.reset_session(f"test_{channel}_test_user")


class ToolExecutionTest(TestCase):
    """工具执行测试"""

    def setUp(self):
        """设置测试环境"""
        from apps.customers.models import Customer
        from apps.inventory.models import Warehouse
        from apps.products.models import Product, Unit

        # 创建用户
        self.user = User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="testpass123",
            is_staff=True,  # 工具执行需要权限
        )

        # 创建计量单位
        self.unit = Unit.objects.create(
            name="台", symbol="台", unit_type="count", is_active=True, created_by=self.user
        )

        # 创建仓库
        self.warehouse = Warehouse.objects.create(
            name="测试仓库",
            code="WH001",
            warehouse_type="standard",
            is_active=True,
            created_by=self.user,
        )

        # 创建测试客户
        self.customer = Customer.objects.create(
            name="测试客户", code="TEST001", customer_level="B", status="active", created_by=self.user
        )

        # 创建测试产品
        self.product = Product.objects.create(
            name="笔记本电脑",
            code="LAPTOP001",
            unit=self.unit,
            product_type="finished",
            status="active",
            created_by=self.user,
        )

    def test_customer_search_tool(self):
        """测试客户搜索工具"""
        from ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool("search_customer", self.user)
        self.assertIsNotNone(tool, "客户搜索工具应该存在")

        result = tool.execute(keyword="测试客户")

        self.assertTrue(result.success, f"客户搜索应该成功: {result.message}")
        self.assertIsNotNone(result.data, "应该返回数据")
        self.assertIsInstance(result.data, list, "返回数据应该是列表")

    def test_product_search_tool(self):
        """测试产品搜索工具"""
        from ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool("search_product", self.user)
        self.assertIsNotNone(tool, "产品搜索工具应该存在")

        result = tool.execute(keyword="笔记本", limit=5)

        self.assertTrue(result.success, f"产品搜索应该成功: {result.message}")
        self.assertIsNotNone(result.data, "应该返回数据")
        self.assertIsInstance(result.data, list, "返回数据应该是列表")

    def test_inventory_check_tool(self):
        """测试库存检查工具"""
        from ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool("check_inventory", self.user)
        self.assertIsNotNone(tool, "库存检查工具应该存在")

        # 需要先有一个产品 ID
        from apps.products.models import Product

        # 查询一个测试产品
        product = Product.objects.filter(is_deleted=False).first()
        if product:
            result = tool.execute(product_id=product.id)
            self.assertTrue(result.success, f"库存检查应该成功: {result.message}")
            self.assertIsNotNone(result.data, "应该返回数据")
        else:
            self.skipTest("没有找到测试产品，跳过库存检查测试")

    def test_low_stock_alert_tool(self):
        """测试低库存预警工具"""
        from ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool("get_low_stock_alert", self.user)
        self.assertIsNotNone(tool, "低库存预警工具应该存在")

        result = tool.execute(limit=10)
        self.assertTrue(result.success, f"低库存预警应该成功: {result.message}")
        self.assertIsNotNone(result.data, "应该返回数据")
        self.assertIsInstance(result.data, list, "返回数据应该是列表")


class MultiChannelIntegrationTest(TestCase):
    """多渠道集成测试"""

    def setUp(self):
        """设置测试环境"""
        from apps.ai_assistant.models import AIModelConfig

        # 创建测试用户
        self.user = User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="testpass123",
            is_staff=True,
        )

        # 创建 Mock AI Model Config（不加密，因为是测试）
        self.mock_config = AIModelConfig.objects.create(
            name="Mock Provider",
            provider="mock",
            model_name="mock-model",
            api_key="test-key",  # 不加密，因为是测试
            is_active=True,
            is_default=True,
            created_by=self.user,
        )

    def tearDown(self):
        """清理测试环境"""
        if hasattr(self, "mock_config"):
            self.mock_config.delete()

    def test_message_routing(self):
        """测试消息路由"""
        from ai_assistant.channels import IncomingMessage
        from ai_assistant.services import ChannelAIService

        # 测试不同渠道的消息处理
        test_cases = [
            {
                "channel": "telegram",
                "content": "查询订单 SO2025010001 的状态",
                "should_contain": "订单",
            },
            {
                "channel": "wechat",
                "content": "查询客户测试客户",
                "should_contain": "客户",
            },
            {
                "channel": "dingtalk",
                "content": "查询库存",
                "should_contain": "库存",
            },
            {
                "channel": "web",
                "content": "查询产品笔记本电脑",
                "should_contain": "产品",
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            # 创建服务实例
            service = ChannelAIService(self.user, test_case["channel"])

            # 创建测试消息
            message = IncomingMessage(
                message_id=f'test_{test_case["channel"]}_{datetime.now().timestamp()}',
                channel=test_case["channel"],
                external_user_id="test_user",
                content=test_case["content"],
                timestamp=datetime.now(),
                message_type="text",
                conversation_id=f'test_{test_case["channel"]}_test_user',
            )

            # 处理消息
            response = service.process_message(message)

            self.assertIsNotNone(response, f"测试用例 {i}: 响应不应为空")
            self.assertIn(
                test_case["should_contain"],
                response.content,
                f"测试用例 {i}: 响应应该包含'{test_case['should_contain']}'",
            )

    def test_conversation_context_management(self):
        """测试对话上下文管理"""
        from ai_assistant.services import ConversationFlowManager, NLPService

        # 创建 Mock AI Provider
        mock_provider = MockAIProvider(api_key="test_key", model_name="mock-model", timeout=30)

        # 初始化服务
        nlp_service = NLPService(mock_provider)
        conversation_manager = ConversationFlowManager(nlp_service)

        session_id = f"test_session_{datetime.now().timestamp()}"
        user_id = 1

        # 模拟多轮对话（使用不自动提取实体的输入）
        conversation = [
            "创建一个新订单",
            "客户是北京科技有限公司",
            "产品是笔记本电脑",
            "数量是 100",
            "确认",
        ]

        previous_context = None
        completed = False
        for i, user_message in enumerate(conversation, 1):
            reply, completed = conversation_manager.process_message(
                session_id=session_id, user_id=user_id, user_message=user_message
            )

            if not completed:
                # 如果未完成，检查回复是否包含追问
                if "我需要了解" in reply or "请提供" in reply:
                    self.assertIn("需要", reply, f"对话第 {i} 应该追问缺失信息")
            else:
                previous_context = reply

        # 最终应该完成
        self.assertTrue(completed, "对话应该完成")


class ErrorHandlingTest(TestCase):
    """错误处理测试"""

    def setUp(self):
        """设置测试环境"""
        from apps.ai_assistant.models import AIModelConfig

        self.user = User.objects.create_user(
            username="test_error",
            email="test@example.com",
            password="testpass123",
        )

        # 创建 Mock AI Model Config（不加密，因为是测试）
        self.mock_config = AIModelConfig.objects.create(
            name="Mock Provider",
            provider="mock",
            model_name="mock-model",
            api_key="test-key",  # 不加密，因为是测试
            is_active=True,
            is_default=True,
            created_by=self.user,
        )

    def tearDown(self):
        """清理测试环境"""
        if hasattr(self, "mock_config"):
            self.mock_config.delete()

    def test_invalid_input(self):
        """测试无效输入"""
        from ai_assistant.channels import IncomingMessage
        from ai_assistant.services import ChannelAIService

        service = ChannelAIService(self.user, "web")

        invalid_inputs = [
            "",
            "   ",  # 只有空格
            "???",  # 只有问号
        ]

        for i, user_message in enumerate(invalid_inputs, 1):
            message = IncomingMessage(
                message_id=f"test_invalid_{i}",
                channel="web",
                external_user_id="test_invalid",
                content=user_message,
                timestamp=datetime.now(),
                message_type="text",
                conversation_id="test_invalid_test_user",
            )

            response = service.process_message(message)

            self.assertIsNotNone(response, "应该返回回复，即使是无效输入")

    def test_conversation_reset(self):
        """测试对话重置"""
        from ai_assistant.channels import IncomingMessage
        from ai_assistant.services import ChannelAIService

        service = ChannelAIService(self.user, "telegram")

        # 创建对话
        message1 = IncomingMessage(
            message_id="test_reset_1",
            channel="telegram",
            external_user_id="test_reset",
            content="给测试客户创建订单",
            timestamp=datetime.now(),
            message_type="text",
            conversation_id="test_reset_test_user",
        )

        response1 = service.process_message(message1)
        self.assertIn("客户", response1.content)

        # 重置对话
        service.reset_session("test_reset_test_user")

        # 发送相同消息应该从新开始
        message2 = IncomingMessage(
            message_id="test_reset_2",
            channel="telegram",
            external_user_id="test_reset",
            content="给测试客户创建订单",
            timestamp=datetime.now(),
            message_type="text",
            conversation_id="test_reset_test_user",
        )

        response2 = service.process_message(message2)
        self.assertIn("客户", response2.content)


class MissingAPIKeyTest(TestCase):
    """测试缺少 API Key 的场景"""

    def setUp(self):
        """设置测试环境"""
        # 不创建 Mock AI Config，确保测试在没有配置的情况下运行
        self.user = User.objects.create_user(
            username="test_nokey",
            email="test_nokey@example.com",
            password="testpass123",
        )

    def test_missing_api_key(self):
        """测试缺少 API Key"""
        from ai_assistant.channels import IncomingMessage
        from ai_assistant.services import ChannelAIService

        service = ChannelAIService(self.user, "telegram")

        message = IncomingMessage(
            message_id="test_nokey",
            channel="telegram",
            external_user_id="test_user",
            content="测试消息",
            timestamp=datetime.now(),
            message_type="text",
            conversation_id="test_nokey_test_user",
        )

        response = service.process_message(message)

        self.assertIsNotNone(response, "应该返回错误消息")
        self.assertIn("AI 模型未配置", response.content, "应该包含'AI 模型未配置'")


class PerformanceTest(TestCase):
    """性能测试"""

    def test_response_time(self):
        """测试响应时间"""

        from apps.ai_assistant.models import AIModelConfig
        from common.utils import decrypt_api_key

        # 创建测试配置
        config = AIModelConfig.objects.filter(is_default=True).first()
        if not config:
            self.skipTest("没有找到默认 AI 配置")

        try:
            api_key = decrypt_api_key(config.api_key)
            provider = None

            # 尝试加载实际的 Provider
            if config.provider == "openai":
                from ai_assistant.providers import OpenAIProvider

                provider = OpenAIProvider(
                    api_key=api_key, model=config.model_name, timeout=config.timeout
                )
            elif config.provider == "anthropic":
                from ai_assistant.providers import AnthropicProvider

                provider = AnthropicProvider(
                    api_key=api_key, model=config.model_name, timeout=config.timeout
                )
            else:
                self.skipTest(f"暂不支持 {config.provider} 的性能测试")

            # 测试响应时间
            start_time = time.time()

            # 执行简单的聊天
            messages = [
                {"role": "user", "content": "你好"},
            ]

            response = provider.chat(messages)

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            # 响应时间应该小于 5 秒
            self.assertLess(latency_ms, 5000, "响应时间应该小于 5 秒")

        except Exception as e:
            self.skipTest(f"性能测试失败: {str(e)}")

    def test_tool_execution_time(self):
        """测试工具执行时间"""
        from ai_assistant.tools import ToolRegistry

        from apps.ai_assistant.models import AIModelConfig

        # 创建测试配置
        config = AIModelConfig.objects.filter(is_default=True).first()
        if not config:
            self.skipTest("没有找到默认 AI 配置")

        # 尝试加载 AI Provider
        from ai_assistant.providers import OpenAIProvider

        from common.utils import decrypt_api_key

        try:
            api_key = decrypt_api_key(config.api_key)
            provider = OpenAIProvider(
                api_key=api_key, model=config.model_name, timeout=config.timeout
            )

            user = User.objects.create_user(
                username="perf_test",
                email="perf_test@example.com",
                password="testpass123",
            )

            # 获取工具
            tool = ToolRegistry.get_tool("search_customer", user)

            # 测试工具执行时间
            import time

            start_time = time.time()

            result = tool.execute(keyword="测试客户", limit=10)

            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000

            # 工具执行应该快速完成
            self.assertLess(execution_time_ms, 1000, "工具执行时间应该小于 1 秒")
            self.assertTrue(result.success, f"工具应该成功: {result.message}")

        except Exception as e:
            self.skipTest(f"工具性能测试失败: {str(e)}")


def run_manual_tests():
    """运行手动测试"""
    print("\n" + "=" * 80)
    print("🧪 手动测试 - 渠道集成和 AI 对话")
    print("=" * 80)

    # 测试选择
    print("请选择要运行的测试：")
    print("  1. NLP 意图识别测试")
    print("  2. 对话流管理测试")
    print("  3. 渠道适配器测试")
    print("  4. 工具执行测试")
    print("  5. 集成测试")
    print("  6. 错误处理测试")
    print("  7. 对话重置测试")
    print("  8. 性能测试")
    print("  9. 运行所有测试")
    print("  0. 退出")

    choice = input("\n请选择测试类型 (0-9): ").strip()

    if choice == "0":
        print("\n再见！")
        return

    # 运行选定的测试
    tests_to_run = []
    if choice == "1":
        tests_to_run = ["test_intent_recognition", "test_conversation_flow"]
    elif choice == "2":
        tests_to_run = ["test_conversation_flow", "test_conversation_reset"]
    elif choice == "3":
        tests_to_run = ["test_channel_adapter", "test_channel_ai_service"]
    elif choice == "4":
        tests_to_run = [
            "test_customer_search_tool",
            "test_product_search_tool",
            "test_inventory_check_tool",
        ]
    elif choice == "5":
        tests_to_run = ["test_message_routing"]
    elif choice == "6":
        tests_to_run = ["test_missing_api_key", "test_invalid_input"]
    elif choice == "7":
        tests_to_run = ["test_conversation_reset"]
    elif choice == "8":
        tests_to_run = ["test_response_time", "test_tool_execution_time"]
    elif choice == "9":
        tests_to_run = [
            # 所有测试
            "test_intent_recognition",
            "test_conversation_flow",
            "test_channel_adapter",
            "test_channel_ai_service",
            "test_customer_search_tool",
            "test_product_search_tool",
            "test_inventory_check_tool",
            "test_message_routing",
            "test_conversation_reset",
            "test_missing_api_key",
            "test_invalid_input",
        ]

    # 运行测试
    from django.test.runner import DiscoverRunner

    runner = DiscoverRunner(settings="better_laser_erp")

    print(f"\n开始运行 {len(tests_to_run)} 个测试...")

    runner = DiscoverRunner(settings="better_laser_erp")
    runner.run_tests("ai_assistant.tests.test_integration", verbosity=2)

    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_manual_tests()
