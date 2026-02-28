"""
测试对话流程的简化版本
"""

import os
from datetime import datetime

import django
from ai_assistant.providers import MockAIProvider
from django.contrib.auth import get_user_model
from django.test import TestCase

# 设置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "better_laser_erp.settings")
django.setup()

User = get_user_model()


class SimplifiedConversationFlowTest(TestCase):
    """简化的对话流程测试"""

    def setUp(self):
        """设置测试环境"""
        from ai_assistant.services import ConversationFlowManager, NLPService

        self.user = User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="testpass123",
            is_staff=True,
        )

        # 创建 Mock AI Provider
        self.mock_provider = MockAIProvider(api_key="test_key", model_name="mock-model", timeout=30)

        # 初始化服务
        self.nlp_service = NLPService(self.mock_provider)
        self.conversation_manager = ConversationFlowManager(self.nlp_service)
        self.channel_adapter = None

    def test_conversation_flow_simple(self):
        """测试简化的对话流程（2 轮对话）"""
        session_id = "test_simple_session"
        user_id = self.user.id

        # 第一轮：创建一个新订单
        reply1, completed1 = self.conversation_manager.process_message(
            session_id=session_id, user_id=user_id, user_message="创建一个新订单"
        )

        # 第一轮应该询问缺失信息
        self.assertIn("需要了解", reply1, "第一轮应该询问缺失信息")
        self.assertIn("客户", reply1, "第一轮应该询问'客户'")
        self.assertIn("产品", reply1, "第一轮应该询问'产品'")
        self.assertIn("数量", reply1, "第一轮应该询问'数量'")
        self.assertFalse(completed1, "第一轮不应该完成")

        # 第二轮：提供所有信息
        reply2, completed2 = self.conversation_manager.process_message(
            session_id=session_id,
            user_id=user_id,
            user_message="给北京科技有限公司创建一个销售订单，产品是笔记本电脑，数量是100，确认",
        )

        # 应该直接完成
        self.assertTrue(completed2, "第二轮应该完成")
        self.assertIn("成功", reply2, "第二轮应该包含成功信息")

    def test_intent_recognition(self):
        """测试意图识别"""
        from ai_assistant.services import Intent

        test_cases = [
            {
                "input": "给北京科技有限公司创建一个订单",
                "expected_intent": Intent.CREATE_ORDER,
                "expected_entities": {"customer_name": "北京科技有限公司"},
            },
            {
                "input": "查询订单 SO2025010001 的状态",
                "expected_intent": Intent.QUERY_ORDER,
                "expected_entities": {"order_number": "SO2025010001"},
            },
            {
                "input": "审核订单 SO2025010002",
                "expected_intent": Intent.APPROVE_ORDER,
                "expected_entities": {"order_number": "SO2025010002"},
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            result = self.nlp_service.parse_user_input(test_case["input"])

            self.assertEqual(
                result.intent,
                test_case["expected_intent"],
                f"测试用例 {i}: {test_case['input']}",
            )

            # 验证实体
            for key, expected_value in test_case.get("expected_entities", {}).items():
                if key in result.entities:
                    self.assertEqual(
                        result.entities[key],
                        expected_value,
                        f"测试用例 {i}: 实体 {key} 应该为 '{expected_value}'",
                    )

    def test_entity_extraction(self):
        """测试实体提取"""
        test_cases = [
            ("客户是北京科技有限公司", {"customer_name": "北京科技有限公司"}),
            ("产品是笔记本电脑", {"product_name": "笔记本电脑"}),
            ("数量是100", {"quantity": 100}),
        ]

        for msg, expected_entities in test_cases:
            entities = self.mock_provider._extract_intent_entities(msg)

            self.assertEqual(len(entities), len(expected_entities), f"输入: {msg}")
            for key, expected_value in expected_entities.items():
                self.assertIn(key, entities, f"应该包含 {key}")
                self.assertEqual(
                    entities[key],
                    expected_value,
                    f"实体 {key} 应该为 '{expected_value}'",
                )

    def test_multi_turn_conversation(self):
        """测试多轮对话（5 轮）"""
        session_id = f"test_multi_turn_session_{datetime.now().timestamp()}"
        user_id = self.user.id

        conversation = [
            "创建一个新订单",
            "客户是北京科技有限公司",
            "产品是笔记本电脑",
            "数量是 100",
            "确认",
        ]

        for i, msg in enumerate(conversation, 1):
            reply, completed = self.conversation_manager.process_message(
                session_id=session_id, user_id=user_id, user_message=msg
            )

            print(f"第 {i} 轮：{msg:30s}")
            print(f"回复：{reply:50s}")
            print(f"完成：{completed}")
            print("-" * 60)

            # 最终应该完成
        self.assertTrue(completed, f"对话应该在第 {len(conversation)} 轮后完成")
