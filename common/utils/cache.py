"""
AI助手缓存工具

提供统一的缓存接口，支持Redis和本地内存缓存
"""

import json
from datetime import timedelta
from typing import Any, Optional

from django.core.cache import cache


class AIAssistantCache:
    """AI助手缓存管理器"""

    # 缓存键前缀
    PREFIX_ACCESS_TOKEN = "ai_assistant:access_token"
    PREFIX_CONVERSATION = "ai_assistant:conversation"
    PREFIX_AI_CONFIG = "ai_assistant:ai_config"

    # 默认过期时间
    DEFAULT_TIMEOUT = 300  # 5分钟
    ACCESS_TOKEN_TIMEOUT = 7200  # 2小时（微信/钉钉 Access Token 有效期）
    CONVERSATION_TIMEOUT = 3600  # 1小时（会话缓存）

    @classmethod
    def _make_key(cls, prefix: str, identifier: str) -> str:
        """
        生成缓存键

        Args:
            prefix: 键前缀
            identifier: 标识符

        Returns:
            完整的缓存键
        """
        return f"{prefix}:{identifier}"

    # ==================== Access Token 缓存 ====================

    @classmethod
    def get_access_token(cls, channel: str, app_id: str) -> Optional[str]:
        """
        获取Access Token

        Args:
            channel: 渠道类型 (wechat/dingtalk)
            app_id: 应用ID

        Returns:
            Access Token 或 None
        """
        key = cls._make_key(cls.PREFIX_ACCESS_TOKEN, f"{channel}:{app_id}")
        return cache.get(key)

    @classmethod
    def set_access_token(cls, channel: str, app_id: str, token: str, timeout: Optional[int] = None):
        """
        缓存Access Token

        Args:
            channel: 渠道类型
            app_id: 应用ID
            token: Access Token
            timeout: 过期时间（秒），默认2小时
        """
        key = cls._make_key(cls.PREFIX_ACCESS_TOKEN, f"{channel}:{app_id}")
        timeout = timeout or cls.ACCESS_TOKEN_TIMEOUT
        cache.set(key, token, timeout)

    @classmethod
    def delete_access_token(cls, channel: str, app_id: str):
        """
        删除Access Token缓存

        Args:
            channel: 渠道类型
            app_id: 应用ID
        """
        key = cls._make_key(cls.PREFIX_ACCESS_TOKEN, f"{channel}:{app_id}")
        cache.delete(key)

    # ==================== 会话缓存 ====================

    @classmethod
    def get_conversation(cls, conversation_id: str) -> Optional[dict]:
        """
        获取会话缓存

        Args:
            conversation_id: 会话ID

        Returns:
            会话数据字典或None
        """
        key = cls._make_key(cls.PREFIX_CONVERSATION, conversation_id)
        data = cache.get(key)

        if data:
            try:
                return json.loads(data) if isinstance(data, str) else data
            except json.JSONDecodeError:
                return None
        return None

    @classmethod
    def set_conversation(cls, conversation_id: str, data: dict, timeout: Optional[int] = None):
        """
        缓存会话数据

        Args:
            conversation_id: 会话ID
            data: 会话数据
            timeout: 过期时间（秒），默认1小时
        """
        key = cls._make_key(cls.PREFIX_CONVERSATION, conversation_id)
        timeout = timeout or cls.CONVERSATION_TIMEOUT

        # 序列化为JSON
        cache.set(key, json.dumps(data, ensure_ascii=False), timeout)

    @classmethod
    def delete_conversation(cls, conversation_id: str):
        """
        删除会话缓存

        Args:
            conversation_id: 会话ID
        """
        key = cls._make_key(cls.PREFIX_CONVERSATION, conversation_id)
        cache.delete(key)

    # ==================== AI配置缓存 ====================

    @classmethod
    def get_ai_config(cls, user_id: int) -> Optional[dict]:
        """
        获取用户的AI配置缓存

        Args:
            user_id: 用户ID

        Returns:
            AI配置字典或None
        """
        key = cls._make_key(cls.PREFIX_AI_CONFIG, str(user_id))
        data = cache.get(key)

        if data:
            try:
                return json.loads(data) if isinstance(data, str) else data
            except json.JSONDecodeError:
                return None
        return None

    @classmethod
    def set_ai_config(cls, user_id: int, config_data: dict, timeout: Optional[int] = None):
        """
        缓存AI配置

        Args:
            user_id: 用户ID
            config_data: 配置数据
            timeout: 过期时间（秒），默认5分钟
        """
        key = cls._make_key(cls.PREFIX_AI_CONFIG, str(user_id))
        timeout = timeout or cls.DEFAULT_TIMEOUT

        cache.set(key, json.dumps(config_data, ensure_ascii=False), timeout)

    @classmethod
    def delete_ai_config(cls, user_id: int):
        """
        删除AI配置缓存

        Args:
            user_id: 用户ID
        """
        key = cls._make_key(cls.PREFIX_AI_CONFIG, str(user_id))
        cache.delete(key)

    # ==================== 通用缓存操作 ====================

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        return cache.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any, timeout: Optional[int] = None):
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            timeout: 过期时间（秒）
        """
        timeout = timeout or cls.DEFAULT_TIMEOUT
        cache.set(key, value, timeout)

    @classmethod
    def delete(cls, key: str):
        """
        删除缓存

        Args:
            key: 缓存键
        """
        cache.delete(key)

    @classmethod
    def clear_all(cls, prefix: Optional[str] = None):
        """
        清除所有缓存（谨慎使用）

        Args:
            prefix: 仅清除指定前缀的缓存
        """
        if prefix:
            # 注意：这个方法需要Redis支持，LocMemCache不支持
            # 生产环境可以使用，开发环境会静默失败
            try:
                cache.delete_pattern(f"{prefix}:*")
            except AttributeError:
                # LocMemCache 不支持 delete_pattern
                pass
        else:
            cache.clear()

    @classmethod
    def get_stats(cls) -> dict:
        """
        获取缓存统计信息（仅Redis支持）

        Returns:
            统计信息字典
        """
        try:
            # 尝试获取Redis统计信息
            from django.core.cache.backends.redis import RedisCache

            if isinstance(cache, RedisCache):
                client = cache._cache
                info = client.info()
                return {
                    "used_memory": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "total_commands_processed": info.get("total_commands_processed"),
                }
        except Exception:
            pass

        return {"backend": "locmem", "stats": "not available"}
