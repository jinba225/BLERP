"""
核心缓存管理器
管理系统级缓存，支持多级缓存和智能失效
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from core.config import CACHE_STRATEGIES, LOCAL_CACHE_CONFIG
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class CacheManager:
    """
    核心缓存管理器

    功能：
    - 多级缓存（L1内存 + L2Redis）
    - 缓存预热
    - 智能失效
    - 缓存统计

    缓存策略：
    - Write-Through：同时写本地和Redis
    - Write-Back：先写本地，异步刷Redis
    - Cache-Aside：旁路缓存
    """

    def __init__(self):
        """初始化缓存管理器"""
        self.redis_client = cache
        self.local_cache = {}  # L1内存缓存
        self.local_cache_ttl = LOCAL_CACHE_CONFIG["ttl"]
        self.local_cache_max_size = LOCAL_CACHE_CONFIG["max_size"]
        self.compression_enabled = LOCAL_CACHE_CONFIG.get("compression", False)
        self.stats_enabled = LOCAL_CACHE_CONFIG.get("stats_enabled", True)

        # 缓存统计
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "compression_ratio": 0,
            "local_cache_hits": 0,
            "redis_cache_hits": 0,
        }

        logger.info("初始化核心缓存管理器")

    async def get(self, key: str, cache_type: str = "default") -> Optional[Any]:
        """
        获取缓存（多级查询）

        Args:
            key: 缓存键
            cache_type: 缓存类型（system_config, company_info, etc.）

        Returns:
            缓存值，未命中返回None

        Example:
            >>> manager = get_cache_manager()
            >>> config = await manager.get('system_config:sales_auto_create_delivery_on_approve')
        """
        # 1. 查询L1本地缓存
        if key in self.local_cache:
            value, timestamp = self.local_cache[key]
            # 检查是否过期
            if datetime.now() - timestamp < timedelta(seconds=self.local_cache_ttl):
                self.stats["hits"] += 1
                self.stats["local_cache_hits"] += 1
                logger.debug(f"L1缓存命中: {key}")
                # 如果启用了压缩，需要解压缩
                if self.compression_enabled and isinstance(value, bytes):
                    import zlib

                    try:
                        value = zlib.decompress(value).decode("utf-8")
                        value = json.loads(value)
                    except Exception:
                        pass
                return value
            else:
                # 过期，删除
                del self.local_cache[key]

        # 2. 查询L2 Redis缓存
        try:
            value = self.redis_client.get(key)
            if value is not None:
                # 反序列化
                try:
                    if isinstance(value, bytes):
                        value = value.decode("utf-8")
                    value = json.loads(value)
                except Exception:
                    pass

                # 回写L1缓存
                if self.compression_enabled:
                    import zlib

                    try:
                        compressed_value = zlib.compress(json.dumps(value).encode("utf-8"))
                        self.local_cache[key] = (compressed_value, datetime.now())
                        # 计算压缩率
                        original_size = len(json.dumps(value).encode("utf-8"))
                        compressed_size = len(compressed_value)
                        if original_size > 0:
                            compression_ratio = (original_size - compressed_size) / original_size
                            self.stats["compression_ratio"] = compression_ratio
                    except Exception:
                        self.local_cache[key] = (value, datetime.now())
                else:
                    self.local_cache[key] = (value, datetime.now())

                # 检查本地缓存大小
                self._check_local_cache_size()

                self.stats["hits"] += 1
                self.stats["redis_cache_hits"] += 1
                logger.debug(f"L2缓存命中: {key}")
                return value

        except Exception as e:
            logger.error(f"Redis缓存查询失败: {e}")

        # 缓存未命中
        self.stats["misses"] += 1
        logger.debug(f"缓存未命中: {key}")
        return None

    async def set(self, key: str, value: Any, cache_type: str = "default"):
        """
        设置缓存（根据策略选择写入方式）

        Args:
            key: 缓存键
            value: 缓存值
            cache_type: 缓存类型

        Example:
            >>> await manager.set('system_config:sales_auto_create_delivery_on_approve', 'true')
        """
        # 获取缓存策略
        strategy_config = CACHE_STRATEGIES.get(cache_type, {})
        strategy = strategy_config.get("strategy", "cache_aside")
        ttl = strategy_config.get("ttl", 300)
        enable_local_cache = strategy_config.get("enable_local_cache", True)

        # 序列化值
        try:
            serialized_value = json.dumps(value)
        except Exception:
            serialized_value = str(value)

        # 根据策略写入
        if strategy == "write_through":
            # 写透：同时写本地和Redis
            if enable_local_cache:
                if self.compression_enabled:
                    import zlib

                    try:
                        compressed_value = zlib.compress(json.dumps(value).encode("utf-8"))
                        self.local_cache[key] = (compressed_value, datetime.now())
                    except Exception:
                        self.local_cache[key] = (value, datetime.now())
                else:
                    self.local_cache[key] = (value, datetime.now())
            self.redis_client.setex(key, ttl, serialized_value)

        elif strategy == "write_back":
            # 写回：先写本地，异步刷Redis
            if enable_local_cache:
                if self.compression_enabled:
                    import zlib

                    try:
                        compressed_value = zlib.compress(json.dumps(value).encode("utf-8"))
                        self.local_cache[key] = (compressed_value, datetime.now())
                    except Exception:
                        self.local_cache[key] = (value, datetime.now())
                else:
                    self.local_cache[key] = (value, datetime.now())
            asyncio.create_task(self._write_back_to_redis(key, serialized_value, ttl))

        elif strategy == "cache_aside":
            # 旁路：只写Redis
            self.redis_client.setex(key, ttl, serialized_value)

        # 检查本地缓存大小
        self._check_local_cache_size()

        self.stats["sets"] += 1
        logger.debug(f"缓存已设置: {key}, strategy={strategy}, local_cache={enable_local_cache}")

    async def delete(self, key: str):
        """
        删除缓存

        Args:
            key: 缓存键

        Example:
            >>> await manager.delete('system_config:sales_auto_create_delivery_on_approve')
        """
        # 删除L1缓存
        if key in self.local_cache:
            del self.local_cache[key]

        # 删除L2缓存
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Redis缓存删除失败: {e}")

        self.stats["deletes"] += 1
        logger.debug(f"缓存已删除: {key}")

    async def invalidate_pattern(self, pattern: str, event_type: str = None):
        """
        批量失效缓存（通配符）

        Args:
            pattern: 键模式（如 'system_config:*'）
            event_type: 事件类型，用于基于事件的失效策略

        Example:
            >>> await manager.invalidate_pattern('system_config:*')
            >>> await manager.invalidate_pattern('product:*', event_type='product_updated')
        """
        # 1. 清空L1缓存（清空所有）
        self.local_cache.clear()

        # 2. 批量删除L2缓存
        try:
            # 查询匹配的键
            keys = self._redis_keys(pattern)

            if keys:
                self.redis_client.delete_many(*keys)
                logger.info(
                    f"批量失效缓存: pattern={pattern}, count={len(keys)}, event_type={event_type}"
                )
            else:
                logger.debug(f"无匹配缓存: pattern={pattern}")

        except Exception as e:
            logger.error(f"批量失效缓存失败: {e}")

    async def invalidate_by_event(self, event_type: str, event_data: Dict = None):
        """
        基于事件的缓存失效

        Args:
            event_type: 事件类型
            event_data: 事件数据

        Example:
            >>> await manager.invalidate_by_event('product_updated', {'product_id': 123})
        """
        logger.info(f"处理缓存失效事件: {event_type}")

        # 事件到缓存模式的映射
        event_patterns = {
            # 产品相关事件
            "product_created": ["product:*"],
            "product_updated": ["product:*", "inventory:*"],
            "product_deleted": ["product:*", "inventory:*"],
            # 库存相关事件
            "inventory_updated": ["inventory:*", "product:*"],
            "stock_adjusted": ["inventory:*"],
            # 订单相关事件
            "order_created": ["order:*", "customer:*"],
            "order_updated": ["order:*"],
            "order_deleted": ["order:*"],
            # 客户相关事件
            "customer_created": ["customer:*"],
            "customer_updated": ["customer:*"],
            "customer_deleted": ["customer:*"],
            # 供应商相关事件
            "supplier_created": ["supplier:*"],
            "supplier_updated": ["supplier:*"],
            "supplier_deleted": ["supplier:*"],
            # 系统配置事件
            "config_updated": ["system_config:*"],
            # 分类相关事件
            "category_updated": ["category:*", "product:*"],
        }

        # 获取对应的缓存模式
        patterns = event_patterns.get(event_type, [])

        # 处理特定事件的数据
        if event_data:
            if event_type in ["product_updated", "product_deleted"]:
                product_id = event_data.get("product_id")
                if product_id:
                    patterns.append(f"product:{product_id}:*")
                    patterns.append(f"inventory:*:{product_id}:*")
            elif event_type in ["customer_updated", "customer_deleted"]:
                customer_id = event_data.get("customer_id")
                if customer_id:
                    patterns.append(f"customer:{customer_id}:*")
                    patterns.append(f"order:*:{customer_id}:*")

        # 执行缓存失效
        for pattern in patterns:
            await self.invalidate_pattern(pattern, event_type)

        logger.info(f"事件处理完成: {event_type}, 失效模式数: {len(patterns)}")

    async def warm_up(
        self,
        data_loader: callable,
        keys: List[str],
        cache_type: str = "default",
        batch_size: int = 10,
    ):
        """
        缓存预热

        Args:
            data_loader: 数据加载函数（异步）
            keys: 键列表
            cache_type: 缓存类型
            batch_size: 批处理大小，默认为10

        Example:
            >>> async def load_config(key):
            ...     return await SystemConfig.objects.get(key=key).value
            >>> await manager.warm_up(load_config, ['system_config:key1', 'system_config:key2'])
        """
        logger.info(f"开始缓存预热: count={len(keys)}, batch_size={batch_size}")

        # 过滤掉已缓存的键
        uncached_keys = []
        for key in keys:
            cached = await self.get(key, cache_type)
            if cached is None:
                uncached_keys.append(key)

        if not uncached_keys:
            logger.info("所有键已缓存，无需预热")
            return

        logger.info(f"需要预热的键数量: {len(uncached_keys)}")

        # 分批处理
        success_count = 0
        total_batches = (len(uncached_keys) + batch_size - 1) // batch_size

        for batch_idx in range(total_batches):
            start = batch_idx * batch_size
            end = min(start + batch_size, len(uncached_keys))
            batch_keys = uncached_keys[start:end]

            logger.debug(f"处理批次 {batch_idx + 1}/{total_batches}, 键数量: {len(batch_keys)}")

            # 并行处理批次中的键
            async def process_key(key):
                try:
                    # 加载数据
                    value = await data_loader(key)
                    # 设置缓存
                    await self.set(key, value, cache_type)
                    return True
                except Exception as e:
                    logger.error(f"预热失败: key={key}, error={e}")
                    return False

            # 并行执行
            results = await asyncio.gather(*[process_key(key) for key in batch_keys])
            success_count += sum(results)

        logger.info(f"缓存预热完成: 成功={success_count}/{len(uncached_keys)}")

    def get_stats(self) -> Dict:
        """
        获取缓存统计

        Returns:
            dict: 缓存统计信息

        Example:
            >>> stats = manager.get_stats()
            >>> print(stats)
            {
                'hits': 1234,
                'misses': 123,
                'hit_rate': 0.91,
                'sets': 456,
                'deletes': 78,
                'local_cache_hits': 1000,
                'redis_cache_hits': 234,
                'local_cache_hit_rate': 0.81,
                'redis_cache_hit_rate': 0.19,
                'compression_ratio': 0.6,
                'local_cache_size': 500,
            }
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0
        local_cache_hit_rate = (
            self.stats["local_cache_hits"] / self.stats["hits"] if self.stats["hits"] > 0 else 0
        )
        redis_cache_hit_rate = (
            self.stats["redis_cache_hits"] / self.stats["hits"] if self.stats["hits"] > 0 else 0
        )

        return {
            **self.stats,
            "hit_rate": round(hit_rate, 4),
            "total_requests": total,
            "local_cache_size": len(self.local_cache),
            "local_cache_hit_rate": round(local_cache_hit_rate, 4),
            "redis_cache_hit_rate": round(redis_cache_hit_rate, 4),
            "compression_ratio": round(self.stats.get("compression_ratio", 0), 4),
        }

    def reset_stats(self):
        """重置缓存统计"""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "compression_ratio": 0,
            "local_cache_hits": 0,
            "redis_cache_hits": 0,
        }
        logger.info("缓存统计已重置")

    async def _write_back_to_redis(self, key: str, value: str, ttl: int):
        """
        异步写回Redis（内部方法）

        Args:
            key: 缓存键
            value: 序列化的值
            ttl: 过期时间
        """
        try:
            await asyncio.sleep(0.1)  # 异步延迟
            self.redis_client.setex(key, ttl, value)
            logger.debug(f"写回Redis: {key}")
        except Exception as e:
            logger.error(f"写回Redis失败: {e}")

    def get_cache_strategy(self, business_scenario: str) -> Dict:
        """
        根据业务场景获取缓存策略

        Args:
            business_scenario: 业务场景

        Returns:
            dict: 缓存策略配置

        Example:
            >>> strategy = manager.get_cache_strategy('product_detail')
        """
        # 业务场景到缓存策略的映射
        scenario_strategies = {
            # 产品相关
            "product_detail": "product_info",
            "product_list": "product_info",
            # 库存相关
            "inventory_status": "inventory",
            "stock_levels": "inventory",
            # 订单相关
            "order_detail": "order_list",
            "order_list": "order_list",
            # 客户相关
            "customer_detail": "customer_info",
            "customer_list": "customer_info",
            # 供应商相关
            "supplier_detail": "supplier_info",
            "supplier_list": "supplier_info",
            # 系统配置
            "system_config": "system_config",
            # 分类相关
            "category_list": "category_list",
            # API响应
            "api_response": "api_response",
            # 销售报价
            "quote_detail": "sales_quote",
            "quote_list": "sales_quote",
            # 财务报表
            "finance_report": "finance_report",
            "financial_summary": "finance_report",
            # 仪表盘
            "dashboard_overview": "dashboard",
            "dashboard_sales": "dashboard",
            "dashboard_inventory": "dashboard",
        }

        # 获取对应的缓存类型
        cache_type = scenario_strategies.get(business_scenario, "default")
        # 返回缓存策略配置
        return CACHE_STRATEGIES.get(cache_type, {})

    def _redis_keys(self, pattern: str) -> List[str]:
        """
        查询匹配的Redis键（内部方法）

        Args:
            pattern: 键模式

        Returns:
            list: 键列表
        """
        try:
            keys = []
            for key in self.redis_client.keys(pattern):
                if isinstance(key, bytes):
                    key = key.decode("utf-8")
                keys.append(key)
            return keys
        except Exception as e:
            logger.error(f"查询Redis键失败: {e}")
            return []

    def _check_local_cache_size(self):
        """
        检查本地缓存大小，超过上限时清理
        """
        if len(self.local_cache) > self.local_cache_max_size:
            # 清理最旧的缓存项
            items = sorted(self.local_cache.items(), key=lambda x: x[1][1])
            to_remove = len(self.local_cache) - self.local_cache_max_size
            for key, _ in items[:to_remove]:
                del self.local_cache[key]
            logger.debug(f"本地缓存清理: 移除{to_remove}个项")


# 全局单例
_cache_manager_instance = None


def get_cache_manager() -> CacheManager:
    """
    获取缓存管理器实例（单例模式）

    Returns:
        CacheManager: 缓存管理器实例

    Example:
        >>> from core.services.cache_manager import get_cache_manager
        >>> manager = get_cache_manager()
        >>> config = await manager.get('system_config:sales_auto_create_delivery_on_approve')
    """
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager()
    return _cache_manager_instance
