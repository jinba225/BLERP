"""
缓存服务

提供工具执行结果的缓存机制，提高查询性能
"""

import hashlib
import json
from typing import Any, Dict, Optional

from django.core.cache import cache
from django.utils import timezone


class CacheService:
    """
    缓存服务

    负责管理工具执行结果的缓存
    """

    # 缓存键前缀
    CACHE_KEY_PREFIX = "erp_tool_result"

    # 默认缓存时间（秒）
    DEFAULT_TTL = 300  # 5分钟

    @staticmethod
    def generate_cache_key(tool_name: str, params: Dict[str, Any]) -> str:
        """
        生成缓存键

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            缓存键
        """
        # 将参数转换为字符串并哈希
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]

        return f"{CacheService.CACHE_KEY_PREFIX}:{tool_name}:{params_hash}"

    @staticmethod
    def get(tool_name: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        从缓存获取工具执行结果

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            缓存的结果，如果不存在则返回None
        """
        cache_key = CacheService.generate_cache_key(tool_name, params)
        return cache.get(cache_key)

    @staticmethod
    def set(
        tool_name: str, params: Dict[str, Any], result: Dict[str, Any], ttl: int = None
    ) -> bool:
        """
        将工具执行结果存入缓存

        Args:
            tool_name: 工具名称
            params: 工具参数
            result: 执行结果
            ttl: 缓存时间（秒），默认使用DEFAULT_TTL

        Returns:
            是否成功设置缓存
        """
        if ttl is None:
            ttl = CacheService.DEFAULT_TTL

        cache_key = CacheService.generate_cache_key(tool_name, params)
        return cache.set(cache_key, result, ttl)

    @staticmethod
    def delete(tool_name: str, params: Dict[str, Any]) -> bool:
        """
        删除工具执行结果缓存

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            是否成功删除
        """
        cache_key = CacheService.generate_cache_key(tool_name, params)
        return cache.delete(cache_key)

    @staticmethod
    def clear_all():
        """清空所有工具结果缓存"""
        # 注意：这会清空所有缓存，需要谨慎使用
        keys = cache.keys("erp_tool_result:*")
        for key in keys:
            cache.delete(key)

    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息
        """
        try:
            # 获取所有工具缓存键
            keys = cache.keys("erp_tool_result:*")

            # 统计信息
            total_keys = len(keys)
            tool_stats = {}

            for key in keys:
                # 解析工具名称
                parts = key.split(":")
                if len(parts) >= 3:
                    tool_name = parts[2]
                    tool_stats[tool_name] = tool_stats.get(tool_name, 0) + 1

            return {
                "total_cached_results": total_keys,
                "tools_with_cache": len(tool_stats),
                "cache_hit_ratio": "N/A",  # 需要额外统计
                "tool_distribution": tool_stats,
            }
        except Exception as e:
            return {"error": str(e)}


class CachedToolWrapper:
    """
    缓存工具包装器

    为查询工具提供透明的缓存支持
    """

    def __init__(self, tool, ttl: int = None):
        """
        初始化包装器

        Args:
            tool: 被包装的工具实例
            ttl: 缓存时间（秒），默认使用工具特定的TTL
        """
        self.tool = tool
        self.ttl = ttl or CacheService.DEFAULT_TTL

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行工具（带缓存）

        Args:
            **kwargs: 工具参数

        Returns:
            执行结果
        """
        tool_name = self.tool.name

        # 检查是否是查询工具（查询工具可以缓存）
        if self.tool.risk_level != "low":
            # 非查询工具不缓存
            result = self.tool.run(**kwargs)
            return result.to_dict()

        # 尝试从缓存获取
        cached_result = CacheService.get(tool_name, kwargs)
        if cached_result is not None:
            # 添加缓存标记
            cached_result["_cached"] = True
            return cached_result

        # 缓存未命中，执行工具
        result = self.tool.run(**kwargs)
        result_dict = result.to_dict()

        # 将成功的结果存入缓存
        if result.success and result.data is not None:
            CacheService.set(tool_name, kwargs, result_dict, self.ttl)

        return result_dict


class QueryOptimizer:
    """
    查询优化器

    提供数据库查询优化功能
    """

    @staticmethod
    def optimize_queryset(queryset, tool_name: str):
        """
        优化查询集

        Args:
            queryset: Django查询集
            tool_name: 工具名称

        Returns:
            优化后的查询集
        """
        # 根据工具类型应用不同的优化策略
        if tool_name.startswith("query_"):
            # 查询工具优化
            # 使用select_related减少查询次数
            if tool_name == "query_sales_orders":
                queryset = queryset.select_related("customer")
            elif tool_name == "query_deliveries":
                queryset = queryset.select_related("sales_order__customer")
            elif tool_name == "query_purchase_orders":
                queryset = queryset.select_related("supplier")
            elif tool_name == "query_purchase_receipts":
                queryset = queryset.select_related("purchase_order__supplier")
            elif tool_name == "query_invoices":
                queryset = queryset.select_related()
            # 可以添加更多优化...

        elif tool_name.startswith("get_"):
            # 详情查询工具优化
            # 使用prefetch_related预加载关联数据
            if tool_name == "get_order_detail":
                queryset = queryset.select_related("customer", "items__product").prefetch_related(
                    "deliveries__items", "returns__items"
                )
            # 可以添加更多优化...

        return queryset


class AIModelConfigCache:
    """
    AI模型配置缓存服务

    提供模型配置的缓存功能，减少数据库查询
    """

    # 缓存键前缀
    CACHE_KEY_PREFIX = "ai_model_config"

    # 缓存过期时间（秒）
    DEFAULT_TIMEOUT = 900  # 15分钟

    @classmethod
    def get_cache_key(cls, key_type: str, identifier: str = "") -> str:
        """
        生成缓存键

        Args:
            key_type: 缓存类型 (default, customer, etc.)
            identifier: 标识符

        Returns:
            str: 缓存键
        """
        if identifier:
            return f"{cls.CACHE_KEY_PREFIX}:{key_type}:{identifier}"
        return f"{cls.CACHE_KEY_PREFIX}:{key_type}"

    @classmethod
    def get_default_config(cls):
        """
        获取缓存的默认模型配置

        Returns:
            AIModelConfig实例或None
        """
        cache_key = cls.get_cache_key("default")
        from django.core.cache import cache

        return cache.get(cache_key)

    @classmethod
    def set_default_config(cls, config, timeout: int = None):
        """
        缓存默认模型配置

        Args:
            config: AIModelConfig实例
            timeout: 缓存时间（秒），默认使用DEFAULT_TIMEOUT
        """
        cache_key = cls.get_cache_key("default")
        from django.core.cache import cache

        cache.set(cache_key, config, timeout or cls.DEFAULT_TIMEOUT)

    @classmethod
    def get_customer_config(cls, customer_id: int):
        """
        获取缓存的客户模型配置

        Args:
            customer_id: 客户ID

        Returns:
            CustomerAIConfig实例或None
        """
        cache_key = cls.get_cache_key("customer", str(customer_id))
        from django.core.cache import cache

        return cache.get(cache_key)

    @classmethod
    def set_customer_config(cls, customer_id: int, config, timeout: int = None):
        """
        缓存客户模型配置

        Args:
            customer_id: 客户ID
            config: CustomerAIConfig实例
            timeout: 缓存时间（秒），默认使用DEFAULT_TIMEOUT
        """
        cache_key = cls.get_cache_key("customer", str(customer_id))
        from django.core.cache import cache

        cache.set(cache_key, config, timeout or cls.DEFAULT_TIMEOUT)

    @classmethod
    def invalidate_default_config(cls):
        """使默认配置缓存失效"""
        cache_key = cls.get_cache_key("default")
        from django.core.cache import cache

        cache.delete(cache_key)

    @classmethod
    def invalidate_customer_config(cls, customer_id: int):
        """
        使客户配置缓存失效

        Args:
            customer_id: 客户ID
        """
        cache_key = cls.get_cache_key("customer", str(customer_id))
        from django.core.cache import cache

        cache.delete(cache_key)

    @classmethod
    def invalidate_all_configs(cls):
        """使所有配置缓存失效"""
        from django.core.cache import cache

        # 删除默认配置缓存
        cls.invalidate_default_config()
        # 注意：无法批量删除所有客户配置，需要在客户配置更新时主动失效
