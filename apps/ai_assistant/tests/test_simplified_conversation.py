"""
简化的对话流管理测试

测试对话流管理，关注修复实体提取逻辑
"""

import os

import django
from ai_assistant.providers import MockAIProvider
from ai_assistant.services import ConversationFlowManager, NLPService
from django.contrib.auth import get_user_model
from django.test import TestCase

# 设置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "better_laser_erp.settings")
django.setup()

User = get_user_model()


class SimplifiedConversationFlowTest(TestCase):
    """简化的对话流测试"""

    def setUp(self):
        """设置测试环境"""
        self.user = User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="testpass123",
            is_staff=True,
        )

    def test_intent_recognition(self):
        """测试意图识别"""

        provider = MockAIProvider(api_key="test_key", model_name="mock-model", timeout=30)
        nlp_service = NLPService(provider)

        # 测试订单创建意图识别
        result = nlp_service.parse_user_input("创建一个新订单")
        self.assertEqual(result.intent.value, "create_order", "创建订单意图应该被识别为create_order")

        # 测试查询意图识别
        result = nlp_service.parse_user_input("查询产品")
        self.assertEqual(result.intent.value, "query_product", "查询产品意图应该被识别为query_product")

    def test_entity_extraction(self):
        """测试实体提取"""
        provider = MockAIProvider(api_key="test_key", model_name="mock-model", timeout=30)

        # 测试客户名称提取
        entities = provider._extract_intent_entities("客户是北京科技有限公司")
        self.assertIn("customer_name", entities, "客户名称应该被提取")

        # 测试产品名称提取
        entities = provider._extract_intent_entities("产品是笔记本电脑")
        self.assertIn("product_name", entities, "产品名称应该被提取")

        # 测试数量提取
        entities = provider._extract_intent_entities("数量是 100")
        self.assertIn("quantity", entities, "数量应该被提取")

        # 测试多个实体提取
        entities = provider._extract_intent_entities("客户是北京科技有限公司，产品是笔记本电脑，数量是100")
        self.assertEqual(len(entities), 3, "应该提取3个实体")

    def test_simple_conversation_flow(self):
        """测试简单对话流程（2 轮对话）"""
        provider = MockAIProvider(api_key="test_key", model_name="mock-model", timeout=30)
        nlp_service = NLPService(provider)
        conversation_manager = ConversationFlowManager(nlp_service)

        session_id = "test_simple_session"
        user_id = 1

        # 第一轮：开始创建订单
        reply1, completed1 = conversation_manager.process_message(
            session_id=session_id, user_id=user_id, user_message="创建一个新订单"
        )

        # 测试第一轮
        self.assertIn("客户", reply1, "第一轮应该询问客户信息")
        self.assertFalse(completed1, "第一轮不应该完成")

        # 获取当前状态
        context = conversation_manager.get_context(session_id)
        self.assertEqual(context.intent.value, "create_order", "意图应该是create_order")
        self.assertEqual(context.state.value, "COLLECTING_INFO", "状态应该是COLLECTING_INFO")
        self.assertEqual(len(context.collected_data), 0, "第一轮不应该收集任何数据")

        # 第二轮：提供客户信息
        reply2, completed2 = conversation_manager.process_message(
            session_id=session_id, user_id=user_id, user_message="客户是北京科技有限公司"
        )

        # 测试第二轮
        self.assertIn("产品", reply2, "第二轮应该询问产品信息")
        self.assertIn("数量", reply2, "第二轮应该询问数量信息")
        self.assertFalse(completed2, "第二轮不应该完成")

        # 获取当前状态
        context = conversation_manager.get_context(session_id)
        self.assertEqual(context.intent.value, "create_order", "意图应该是create_order")
        self.assertEqual(context.state.value, "COLLECTING_INFO", "状态应该是COLLECTING_INFO")
        self.assertEqual(len(context.collected_data), 1, "第二轮应该收集1个实体")
        self.assertEqual(context.collected_data.get("customer_name"), "北京科技有限公司")

    def test_full_conversation_flow(self):
        """测试完整对话流程（4 轮对话）"""
        provider = MockAIProvider(api_key="test_key", model_name="mock-model", timeout=30)
        nlp_service = NLPService(provider)
        conversation_manager = ConversationFlowManager(nlp_service)

        session_id = "test_full_session"
        user_id = 1

        # 第一轮：开始创建订单
        reply1, completed1 = conversation_manager.process_message(
            session_id=session_id, user_id=user_id, user_message="创建一个新订单"
        )

        self.assertIn("客户", reply1, "第一轮应该询问客户信息")
        self.assertIn("产品", reply1, "第一轮应该询问产品信息")
        self.assertIn("数量", reply1, "第一轮应该询问数量信息")
        self.assertFalse(completed1, "第一轮不应该完成")

        # 第二轮：提供客户信息
        reply2, completed2 = conversation_manager.process_message(
            session_id=session_id, user_id=user_id, user_message="客户是北京科技有限公司"
        )

        self.assertIn("产品", reply2, "第二轮应该询问产品信息")
        self.assertIn("数量", reply2, "第二轮应该询问数量信息")
        self.assertFalse(completed2, "第二轮不应该完成")

        # 第三轮：提供产品信息
        reply3, completed3 = conversation_manager.process_message(
            session_id=session_id, user_id=user_id, user_message="产品是笔记本电脑"
        )

        # 第三轮应该询问数量
        self.assertIn("请提供数量", reply3, "第三轮应该询问数量信息")
        self.assertFalse(completed3, "第三轮不应该完成")

        # 第四轮：提供数量信息
        reply4, completed4 = conversation_manager.process_message(
            session_id=session_id, user_id=user_id, user_message="数量是 100"
        )

        # 第四轮应该进入确认阶段
        self.assertIn("请确认", reply4, "第四轮应该请求确认")
        self.assertFalse(completed4, "第四轮不应该完成")

        # 第五轮：确认执行
        reply5, completed5 = conversation_manager.process_message(
            session_id=session_id, user_id=user_id, user_message="确认"
        )

        # 最终应该完成
        self.assertTrue(completed5, "第五轮应该完成")
        self.assertIn("成功", reply5, "第五轮应该包含成功信息")

    def test_conversation_context_persistence(self):
        """测试对话上下文持续化"""
        provider = MockAIProvider(api_key="test_key", model_name="mock-model", timeout=30)
        nlp_service = NLPService(provider)
        conversation_manager = ConversationFlowManager(nlp_service)

        session_id = "test_persistence_session"
        user_id = 1

        # 执行完整对话流程
        messages = [
            "创建一个新订单",
            "客户是北京科技有限公司",
            "产品是笔记本电脑",
            "数量是 100",
            "确认",
        ]

        for i, msg in enumerate(messages, 1):
            reply, completed = conversation_manager.process_message(
                session_id=session_id, user_id=user_id, user_message=msg
            )
            print(f"第 {i} 轮：{msg}")
            print(f"  回复: {reply}")
            print(f"  完成: {completed}")
            print(f"  状态: {conversation_manager.get_context(session_id).state.value}")
            print("-" * 60)

        # 最终应该完成
        context = conversation_manager.get_context(session_id)
        self.assertEqual(context.state.value, "COMPLETED", "最终状态应该是COMPLETED")
        self.assertTrue(context.completed, "对话应该标记为已完成")
