"""
限流管理器 - 基于令牌桶算法
支持多平台配额管理、Redis持久化、动态限流调整
"""
import asyncio
import logging
import time
from typing import Dict, Optional

from django.core.cache import cache

from ..config import DEFAULT_RATE_LIMIT, PLATFORM_RATE_LIMITS

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    令牌桶限流器

    算法原理：
    - 桶的容量为 burst（突发流量上限）
    - 以 rate（平均速率）恒定生成令牌
    - 请求消耗令牌，令牌不足时阻塞或拒绝

    优势：
    - 平滑流量：限制平均速率，允许突发
    - 灵活配置：可动态调整 rate 和 burst
    - 分布式支持：基于Redis实现跨进程限流
    """

    def __init__(
        self,
        platform: str,
        rate: Optional[int] = None,
        burst: Optional[int] = None,
        redis_client=None,
    ):
        """
        初始化限流器

        Args:
            platform: 平台标识（如 'taobao', 'amazon'）
            rate: 每秒生成的令牌数（默认从配置读取）
            burst: 桶的容量（默认从配置读取）
            redis_client: Redis客户端（可选，默认使用Django cache）
        """
        self.platform = platform

        # 从配置读取限流参数
        config = PLATFORM_RATE_LIMITS.get(platform, DEFAULT_RATE_LIMIT)
        self.rate = rate or config["rate"]
        self.burst = burst or config["burst"]

        # Redis客户端（支持传入自定义client）
        self.redis_client = redis_client
        if self.redis_client is None:
            # 使用Django cache作为Redis client
            self.redis_client = cache

        # Redis键前缀
        self._key_prefix = f"rate_limiter:{platform}"

        logger.info(f"初始化限流器: platform={platform}, rate={self.rate}, burst={self.burst}")

    async def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        获取令牌（阻塞直到获取成功或超时）

        Args:
            tokens: 需要获取的令牌数量（默认1）
            timeout: 超时时间（秒），None表示不阻塞

        Returns:
            bool: 是否成功获取令牌

        Example:
            >>> limiter = RateLimiter('taobao')
            >>> # 非阻塞获取
            >>> success = await limiter.acquire(timeout=0)
            >>> # 阻塞获取（最多等待5秒）
            >>> success = await limiter.acquire(timeout=5)
        """
        start_time = time.time()

        while True:
            # 尝试获取令牌
            success, wait_time = self._try_acquire(tokens)

            if success:
                logger.debug(f"限流器获取成功: platform={self.platform}, tokens={tokens}")
                return True

            # 检查是否超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    logger.warning(
                        f"限流器获取超时: platform={self.platform}, " f"tokens={tokens}, timeout={timeout}"
                    )
                    return False

                # 计算剩余等待时间
                remaining_wait = min(wait_time, timeout - elapsed)
            else:
                # 非阻塞模式，直接返回
                return False

            # 等待后重试
            await asyncio.sleep(remaining_wait)

    def acquire_sync(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        同步版本的令牌获取（用于非异步环境）

        Args:
            tokens: 需要获取的令牌数量
            timeout: 超时时间（秒）

        Returns:
            bool: 是否成功获取令牌
        """
        start_time = time.time()

        while True:
            success, wait_time = self._try_acquire(tokens)

            if success:
                return True

            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
                remaining_wait = min(wait_time, timeout - elapsed)
            else:
                return False

            # 同步等待
            time.sleep(remaining_wait)

    def _try_acquire(self, tokens: int) -> tuple[bool, float]:
        """
        尝试获取令牌（核心逻辑）

        Returns:
            (success, wait_time): 是否成功，需要等待的时间
        """
        current_time = time.time()
        key = f"{self._key_prefix}:bucket"

        # 使用Redis Lua脚本保证原子性
        lua_script = """
        local key = KEYS[1]
        local tokens = tonumber(ARGV[1])
        local rate = tonumber(ARGV[2])
        local burst = tonumber(ARGV[3])
        local current_time = tonumber(ARGV[4])

        -- 获取当前桶状态
        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local current_tokens = tonumber(bucket[1]) or burst
        local last_refill = tonumber(bucket[2]) or current_time

        -- 计算需要补充的令牌数
        local elapsed = current_time - last_refill
        local refill_tokens = math.floor(elapsed * rate)

        -- 补充令牌（不超过桶容量）
        current_tokens = math.min(burst, current_tokens + refill_tokens)

        -- 检查是否有足够令牌
        if current_tokens >= tokens then
            -- 消耗令牌
            current_tokens = current_tokens - tokens

            -- 更新Redis
            redis.call('HMSET', key, 'tokens', current_tokens, 'last_refill', current_time)
            redis.call('EXPIRE', key, math.ceil(burst / rate) + 1)

            return {1, 0}  -- 成功，等待时间0
        else
            -- 令牌不足，计算等待时间
            local wait_time = (tokens - current_tokens) / rate
            return {0, wait_time}  -- 失败，返回需要等待的时间
        end
        """

        try:
            # 执行Lua脚本
            result = self.redis_client.eval(
                lua_script, 1, key, tokens, self.rate, self.burst, current_time
            )

            success = bool(result[0])
            wait_time = float(result[1])

            return success, wait_time

        except Exception as e:
            logger.error(f"限流器Redis操作失败: {e}")
            # Redis失败时降级：允许请求通过（避免阻塞业务）
            return True, 0

    def get_status(self) -> Dict:
        """
        获取当前限流器状态

        Returns:
            dict: 限流器状态信息
        """
        key = f"{self._key_prefix}:bucket"

        try:
            bucket = self.redis_client.hmget(key, "tokens", "last_refill")
            current_tokens = float(bucket[0]) if bucket[0] else self.burst
            last_refill = float(bucket[1]) if bucket[1] else time.time()

            # 计算令牌使用率
            usage_rate = (self.burst - current_tokens) / self.burst

            return {
                "platform": self.platform,
                "rate": self.rate,
                "burst": self.burst,
                "current_tokens": current_tokens,
                "available_tokens": int(current_tokens),
                "usage_rate": round(usage_rate * 100, 2),  # 百分比
                "last_refill": last_refill,
            }

        except Exception as e:
            logger.error(f"获取限流器状态失败: {e}")
            return {
                "platform": self.platform,
                "rate": self.rate,
                "burst": self.burst,
                "error": str(e),
            }

    def reset(self):
        """重置限流器（清空令牌桶）"""
        key = f"{self._key_prefix}:bucket"
        try:
            self.redis_client.delete(key)
            logger.info(f"限流器已重置: platform={self.platform}")
        except Exception as e:
            logger.error(f"重置限流器失败: {e}")

    def update_config(self, rate: Optional[int] = None, burst: Optional[int] = None):
        """
        动态更新限流配置

        Args:
            rate: 新的速率（None表示不更新）
            burst: 新的容量（None表示不更新）
        """
        if rate is not None:
            self.rate = rate
        if burst is not None:
            self.burst = burst

        # 重置限流器（使新配置生效）
        self.reset()

        logger.info(f"限流器配置已更新: platform={self.platform}, " f"rate={self.rate}, burst={self.burst}")


class RateLimiterFactory:
    """限流器工厂 - 管理多个平台的限流器实例"""

    _instances: Dict[str, RateLimiter] = {}

    @classmethod
    def get_limiter(cls, platform: str) -> RateLimiter:
        """
        获取平台限流器（单例模式）

        Args:
            platform: 平台标识

        Returns:
            RateLimiter: 限流器实例
        """
        if platform not in cls._instances:
            cls._instances[platform] = RateLimiter(platform)
        return cls._instances[platform]

    @classmethod
    def get_all_limiters(cls) -> Dict[str, RateLimiter]:
        """获取所有限流器实例"""
        return cls._instances.copy()

    @classmethod
    def reset_all(cls):
        """重置所有限流器"""
        for limiter in cls._instances.values():
            limiter.reset()
        logger.info("所有限流器已重置")


# 便捷函数
def get_rate_limiter(platform: str) -> RateLimiter:
    """
    获取平台限流器（便捷函数）

    Args:
        platform: 平台标识

    Returns:
        RateLimiter: 限流器实例

    Example:
        >>> limiter = get_rate_limiter('taobao')
        >>> await limiter.acquire()
    """
    return RateLimiterFactory.get_limiter(platform)
