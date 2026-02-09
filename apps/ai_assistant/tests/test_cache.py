"""
测试Redis缓存功能
"""

import json

from ai_assistant.utils.cache import AIAssistantCache
from django.core.cache import cache
from django.test import TestCase


class AIAssistantCacheTestCase(TestCase):
    """AI助手缓存测试"""

    def setUp(self):
        """测试前清除缓存"""
        cache.clear()

    def tearDown(self):
        """测试后清除缓存"""
        cache.clear()

    # ==================== Access Token 缓存测试 ====================

    def test_access_token_set_and_get(self):
        """测试设置和获取Access Token"""
        # 设置微信Access Token
        AIAssistantCache.set_access_token("wechat", "test_corp_id", "test_token_123")

        # 获取微信Access Token
        token = AIAssistantCache.get_access_token("wechat", "test_corp_id")

        self.assertEqual(token, "test_token_123")

    def test_access_token_expiration(self):
        """测试Access Token过期时间"""
        # 设置一个1秒过期的token
        AIAssistantCache.set_access_token(
            "dingtalk", "test_app_key", "short_lived_token", timeout=1
        )

        # 立即获取应该存在
        token = AIAssistantCache.get_access_token("dingtalk", "test_app_key")
        self.assertEqual(token, "short_lived_token")

        # 等待2秒后应该过期
        import time

        time.sleep(2)

        token_expired = AIAssistantCache.get_access_token("dingtalk", "test_app_key")
        self.assertIsNone(token_expired)

    def test_access_token_delete(self):
        """测试删除Access Token"""
        # 设置token
        AIAssistantCache.set_access_token("wechat", "corp_001", "token_abc")

        # 确认存在
        self.assertIsNotNone(AIAssistantCache.get_access_token("wechat", "corp_001"))

        # 删除token
        AIAssistantCache.delete_access_token("wechat", "corp_001")

        # 确认已删除
        self.assertIsNone(AIAssistantCache.get_access_token("wechat", "corp_001"))

    def test_access_token_different_channels(self):
        """测试不同渠道的token隔离"""
        # 设置不同渠道的token
        AIAssistantCache.set_access_token("wechat", "app_001", "wechat_token")
        AIAssistantCache.set_access_token("dingtalk", "app_001", "dingtalk_token")

        # 验证token隔离
        wechat_token = AIAssistantCache.get_access_token("wechat", "app_001")
        dingtalk_token = AIAssistantCache.get_access_token("dingtalk", "app_001")

        self.assertEqual(wechat_token, "wechat_token")
        self.assertEqual(dingtalk_token, "dingtalk_token")

    # ==================== 会话缓存测试 ====================

    def test_conversation_set_and_get(self):
        """测试设置和获取会话缓存"""
        conversation_data = {
            "conversation_id": "conv_001",
            "user_id": 123,
            "channel": "telegram",
            "last_message": "Hello",
            "context": ["message1", "message2"],
        }

        # 设置会话缓存
        AIAssistantCache.set_conversation("conv_001", conversation_data)

        # 获取会话缓存
        cached_data = AIAssistantCache.get_conversation("conv_001")

        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data["conversation_id"], "conv_001")
        self.assertEqual(cached_data["user_id"], 123)
        self.assertEqual(cached_data["channel"], "telegram")
        self.assertEqual(len(cached_data["context"]), 2)

    def test_conversation_with_complex_data(self):
        """测试复杂数据结构的会话缓存"""
        complex_data = {
            "messages": [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "您好！有什么可以帮您的？"},
            ],
            "metadata": {"created_at": "2026-01-07T10:00:00Z", "status": "active"},
        }

        # 设置缓存
        AIAssistantCache.set_conversation("conv_complex", complex_data)

        # 获取缓存
        cached = AIAssistantCache.get_conversation("conv_complex")

        self.assertEqual(len(cached["messages"]), 2)
        self.assertEqual(cached["messages"][0]["role"], "user")
        self.assertEqual(cached["metadata"]["status"], "active")

    def test_conversation_delete(self):
        """测试删除会话缓存"""
        # 设置会话
        AIAssistantCache.set_conversation("conv_to_delete", {"data": "test"})

        # 确认存在
        self.assertIsNotNone(AIAssistantCache.get_conversation("conv_to_delete"))

        # 删除会话
        AIAssistantCache.delete_conversation("conv_to_delete")

        # 确认已删除
        self.assertIsNone(AIAssistantCache.get_conversation("conv_to_delete"))

    # ==================== AI配置缓存测试 ====================

    def test_ai_config_set_and_get(self):
        """测试设置和获取AI配置缓存"""
        config_data = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000,
            "provider": "openai",
        }

        # 设置配置缓存
        AIAssistantCache.set_ai_config(user_id=1, config_data=config_data)

        # 获取配置缓存
        cached_config = AIAssistantCache.get_ai_config(user_id=1)

        self.assertIsNotNone(cached_config)
        self.assertEqual(cached_config["model"], "gpt-4")
        self.assertEqual(cached_config["temperature"], 0.7)

    def test_ai_config_different_users(self):
        """测试不同用户的配置隔离"""
        # 设置不同用户的配置
        AIAssistantCache.set_ai_config(1, {"model": "gpt-4"})
        AIAssistantCache.set_ai_config(2, {"model": "claude-3"})

        # 验证配置隔离
        config_user1 = AIAssistantCache.get_ai_config(1)
        config_user2 = AIAssistantCache.get_ai_config(2)

        self.assertEqual(config_user1["model"], "gpt-4")
        self.assertEqual(config_user2["model"], "claude-3")

    # ==================== 通用缓存测试 ====================

    def test_generic_cache_operations(self):
        """测试通用缓存操作"""
        # 设置缓存
        AIAssistantCache.set("test_key", "test_value", timeout=60)

        # 获取缓存
        value = AIAssistantCache.get("test_key")
        self.assertEqual(value, "test_value")

        # 获取不存在的键（带默认值）
        default_value = AIAssistantCache.get("nonexistent_key", default="default")
        self.assertEqual(default_value, "default")

        # 删除缓存
        AIAssistantCache.delete("test_key")
        self.assertIsNone(AIAssistantCache.get("test_key"))

    def test_cache_key_format(self):
        """测试缓存键格式"""
        # Access Token 键格式
        AIAssistantCache.set_access_token("wechat", "corp_id", "token")

        # 直接使用完整键访问（验证键格式）
        full_key = "ai_assistant:access_token:wechat:corp_id"
        raw_value = cache.get(full_key)
        self.assertEqual(raw_value, "token")

    def test_cache_stats(self):
        """测试缓存统计信息"""
        # 获取缓存统计（开发环境使用LocMemCache，不支持详细统计）
        stats = AIAssistantCache.get_stats()

        self.assertIsNotNone(stats)
        self.assertIn("backend", stats)
