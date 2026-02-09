"""
监控服务 - API调用统计和性能指标采集
支持实时监控、历史查询、告警触发
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from django.conf import settings
from django.core.cache import cache

from ..config import MONITOR_CONFIG

logger = logging.getLogger(__name__)


class MonitorService:
    """
    监控服务

    功能：
    - API调用统计（次数、成功率、平均耗时）
    - 性能指标采集（P50、P95、P99延迟）
    - Redis时序数据存储
    - 告警触发

    存储结构：
    - metrics:{platform}:{endpoint}:{date} - 哈希表，存储一天的指标
      - count: 调用次数
      - success_count: 成功次数
      - error_count: 错误次数
      - total_duration: 总耗时（毫秒）
      - durations: 延迟列表（逗号分隔）

    - alerts:{platform} - 列表，存储告警记录
    """

    def __init__(self, redis_client=None):
        """
        初始化监控服务

        Args:
            redis_client: Redis客户端（可选）
        """
        self.redis_client = redis_client or cache
        self.config = MONITOR_CONFIG
        self.percentiles = self.config["percentiles"]

        logger.debug("初始化监控服务")

    def record_api_call(
        self,
        platform: str,
        endpoint: str,
        success: bool,
        duration: float,
        error_code: Optional[str] = None,
    ):
        """
        记录API调用（同步版本）

        Args:
            platform: 平台标识
            endpoint: API端点（如 '/products/get'）
            success: 是否成功
            duration: 耗时（秒）
            error_code: 错误代码（失败时）

        Example:
            >>> monitor = MonitorService()
            >>> monitor.record_api_call(
            ...     platform='taobao',
            ...     endpoint='/item/get',
            ...     success=True,
            ...     duration=1.23
            ... )
        """
        try:
            # 转换为毫秒
            duration_ms = int(duration * 1000)

            # 生成键名
            today = datetime.now().strftime("%Y-%m-%d")
            key = f"metrics:{platform}:{endpoint}:{today}"

            # 使用Lua脚本保证原子性
            lua_script = """
            local key = KEYS[1]
            local count = tonumber(ARGV[1])
            local success_count = tonumber(ARGV[2])
            local error_count = tonumber(ARGV[3])
            local total_duration = tonumber(ARGV[4])
            local duration = ARGV[5]

            -- 增加计数
            redis.call('HINCRBY', key, 'count', count)
            redis.call('HINCRBY', key, 'success_count', success_count)
            redis.call('HINCRBY', key, 'error_count', error_count)
            redis.call('HINCRBY', key, 'total_duration', total_duration)

            -- 记录延迟（保留最近1000条）
            redis.call('LPUSH', key .. ':durations', duration)
            redis.call('LTRIM', key .. ':durations', 0, 999)

            -- 设置过期时间（保留30天）
            local ttl = 30 * 24 * 3600
            redis.call('EXPIRE', key, ttl)
            redis.call('EXPIRE', key .. ':durations', ttl)

            return 1
            """

            self.redis_client.eval(
                lua_script,
                1,
                key,
                1,  # count
                1 if success else 0,  # success_count
                0 if success else 1,  # error_count
                duration_ms,  # total_duration
                str(duration_ms),  # duration
            )

            logger.debug(
                f"记录API调用: platform={platform}, endpoint={endpoint}, "
                f"success={success}, duration={duration}s"
            )

        except Exception as e:
            logger.error(f"记录API调用失败: {e}")

    async def record_api_call_async(
        self,
        platform: str,
        endpoint: str,
        success: bool,
        duration: float,
        error_code: Optional[str] = None,
    ):
        """
        记录API调用（异步版本）

        Args:
            platform: 平台标识
            endpoint: API端点
            success: 是否成功
            duration: 耗时（秒）
            error_code: 错误代码
        """
        # 异步版本使用相同的逻辑
        # 在实际使用中，可以使用asyncio.to_thread在线程池中执行
        import asyncio

        await asyncio.to_thread(
            self.record_api_call, platform, endpoint, success, duration, error_code
        )

    def get_metrics(
        self, platform: str, endpoint: Optional[str] = None, time_range: str = "1h"
    ) -> Dict:
        """
        获取监控指标

        Args:
            platform: 平台标识
            endpoint: API端点（None表示聚合所有端点）
            time_range: 时间范围（'1h', '1d', '7d', '30d'）

        Returns:
            dict: 监控指标

        Example:
            >>> monitor = MonitorService()
            >>> # 获取最近1小时的指标
            >>> metrics = monitor.get_metrics('taobao', time_range='1h')
            >>> print(metrics)
            {
                'platform': 'taobao',
                'time_range': '1h',
                'count': 1234,
                'success_rate': 0.95,
                'avg_duration': 1234,
                'p50_duration': 1000,
                'p95_duration': 2000,
                'p99_duration': 3000,
            }
        """
        try:
            # 计算时间范围
            days = self._parse_time_range(time_range)
            metrics = {
                "platform": platform,
                "time_range": time_range,
                "count": 0,
                "success_count": 0,
                "error_count": 0,
                "total_duration": 0,
                "durations": [],
            }

            # 聚合多天的数据
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")

                if endpoint:
                    # 特定端点
                    key = f"metrics:{platform}:{endpoint}:{date}"
                else:
                    # 聚合所有端点
                    pattern = f"metrics:{platform}:*:{date}"
                    keys = self._redis_keys(pattern)
                    if not keys:
                        continue

                # 获取数据
                if endpoint:
                    data = self._get_metrics_data(key)
                else:
                    # 聚合所有端点
                    data = {"count": 0, "success_count": 0, "error_count": 0, "total_duration": 0}
                    for k in keys:
                        d = self._get_metrics_data(k)
                        data["count"] += d["count"]
                        data["success_count"] += d["success_count"]
                        data["error_count"] += d["error_count"]
                        data["total_duration"] += d["total_duration"]

                metrics["count"] += data["count"]
                metrics["success_count"] += data["success_count"]
                metrics["error_count"] += data["error_count"]
                metrics["total_duration"] += data["total_duration"]

            # 计算衍生指标
            if metrics["count"] > 0:
                metrics["success_rate"] = metrics["success_count"] / metrics["count"]
                metrics["error_rate"] = metrics["error_count"] / metrics["count"]
                metrics["avg_duration"] = metrics["total_duration"] / metrics["count"]

                # 获取延迟列表并计算分位数
                if endpoint:
                    durations = self._get_durations(platform, endpoint, days)
                    if durations:
                        metrics["p50_duration"] = self._percentile(durations, 50)
                        metrics["p95_duration"] = self._percentile(durations, 95)
                        metrics["p99_duration"] = self._percentile(durations, 99)
            else:
                metrics["success_rate"] = 0
                metrics["error_rate"] = 0
                metrics["avg_duration"] = 0

            return metrics

        except Exception as e:
            logger.error(f"获取监控指标失败: {e}")
            return {
                "platform": platform,
                "error": str(e),
            }

    def get_alert_status(self) -> List[Dict]:
        """
        获取告警状态

        Returns:
            list: 告警列表

        Example:
            >>> monitor = MonitorService()
            >>> alerts = monitor.get_alert_status()
            >>> print(alerts)
            [
                {
                    'platform': 'taobao',
                    'alert_type': 'high_error_rate',
                    'severity': 'critical',
                    'value': 0.15,
                    'threshold': 0.1,
                    'timestamp': '2025-02-03 10:30:00',
                }
            ]
        """
        alerts = []

        try:
            # 获取所有平台
            platforms = self._get_all_platforms()

            for platform in platforms:
                # 获取最近1小时的指标
                metrics = self.get_metrics(platform, time_range="1h")

                if "error" in metrics:
                    continue

                # 检查告警规则
                thresholds = self.config["alert_thresholds"]

                # 错误率告警
                if metrics.get("error_rate", 0) > thresholds["error_rate"]:
                    alerts.append(
                        {
                            "platform": platform,
                            "alert_type": "high_error_rate",
                            "severity": "critical",
                            "value": metrics["error_rate"],
                            "threshold": thresholds["error_rate"],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

                # P95延迟告警
                if metrics.get("p95_duration", 0) > thresholds["p95_latency"]:
                    alerts.append(
                        {
                            "platform": platform,
                            "alert_type": "slow_response",
                            "severity": "warning",
                            "value": metrics["p95_duration"],
                            "threshold": thresholds["p95_latency"],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

                # 成功率告警
                if metrics.get("success_rate", 1) < thresholds["success_rate"]:
                    alerts.append(
                        {
                            "platform": platform,
                            "alert_type": "low_success_rate",
                            "severity": "critical",
                            "value": metrics["success_rate"],
                            "threshold": thresholds["success_rate"],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

            return alerts

        except Exception as e:
            logger.error(f"获取告警状态失败: {e}")
            return []

    def _parse_time_range(self, time_range: str) -> int:
        """
        解析时间范围

        Args:
            time_range: 时间范围字符串

        Returns:
            int: 天数
        """
        mapping = {
            "1h": 1,
            "1d": 1,
            "7d": 7,
            "30d": 30,
        }
        return mapping.get(time_range, 1)

    def _get_metrics_data(self, key: str) -> Dict:
        """
        获取指标数据

        Args:
            key: Redis键

        Returns:
            dict: 指标数据
        """
        try:
            data = self.redis_client.hmget(
                key, "count", "success_count", "error_count", "total_duration"
            )

            return {
                "count": int(data[0]) if data[0] else 0,
                "success_count": int(data[1]) if data[1] else 0,
                "error_count": int(data[2]) if data[2] else 0,
                "total_duration": int(data[3]) if data[3] else 0,
            }
        except Exception as e:
            logger.error(f"获取指标数据失败: {e}")
            return {
                "count": 0,
                "success_count": 0,
                "error_count": 0,
                "total_duration": 0,
            }

    def _get_durations(self, platform: str, endpoint: str, days: int) -> List[int]:
        """
        获取延迟列表

        Args:
            platform: 平台标识
            endpoint: API端点
            days: 天数

        Returns:
            list: 延迟列表（毫秒）
        """
        durations = []

        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            key = f"metrics:{platform}:{endpoint}:{date}:durations"

            try:
                # 从Redis列表获取所有延迟
                values = self.redis_client.lrange(key, 0, -1)
                durations.extend([int(v) for v in values if v])
            except Exception as e:
                logger.error(f"获取延迟列表失败: {e}")

        return durations

    def _percentile(self, data: List[int], p: int) -> int:
        """
        计算百分位数

        Args:
            data: 数据列表
            p: 百分位数（50, 95, 99）

        Returns:
            int: 百分位数值
        """
        if not data:
            return 0

        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (p / 100)
        f = int(k)
        c = k - f

        if f + 1 < len(sorted_data):
            return int(sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f]))
        else:
            return int(sorted_data[f])

    def _redis_keys(self, pattern: str) -> List[str]:
        """
        查询匹配的Redis键

        Args:
            pattern: 键模式

        Returns:
            list: 键列表
        """
        try:
            # 使用scan命令迭代查找
            keys = []
            for key in self.redis_client.keys(pattern):
                keys.append(key.decode() if isinstance(key, bytes) else key)
            return keys
        except Exception as e:
            logger.error(f"查询Redis键失败: {e}")
            return []

    def _get_all_platforms(self) -> List[str]:
        """
        获取所有平台列表

        Returns:
            list: 平台列表
        """
        # 从配置中获取平台列表
        from ..config import PLATFORM_RATE_LIMITS

        return list(PLATFORM_RATE_LIMITS.keys())


# 全局单例
_monitor_instance = None


def get_monitor() -> MonitorService:
    """
    获取监控服务实例（单例模式）

    Returns:
        MonitorService: 监控服务实例

    Example:
        >>> monitor = get_monitor()
        >>> monitor.record_api_call('taobao', '/item/get', True, 1.23)
    """
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = MonitorService()
    return _monitor_instance
