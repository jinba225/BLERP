"""
重试管理器 - 基于指数退避算法
支持智能错误判断、随机抖动、可配置重试策略
"""
import asyncio
import random
import time
import logging
from typing import Optional, Callable, Any, Type, Tuple
from functools import wraps
from ..config import RETRY_CONFIG


logger = logging.getLogger(__name__)


class RetryManager:
    """
    智能重试管理器

    算法原理：
    - 指数退避：每次重试等待时间指数增长（base_delay * 2^attempt）
    - 随机抖动：避免多个请求同时重试导致惊群效应
    - 错误分类：自动判断错误是否可重试

    优势：
    - 减轻服务器压力：避免频繁重试
    - 提高成功率：智能判断可重试错误
    - 避免惊群：随机抖动分散重试时间
    """

    def __init__(
        self,
        max_retries: Optional[int] = None,
        base_delay: Optional[float] = None,
        max_delay: Optional[float] = None,
        jitter: Optional[bool] = None
    ):
        """
        初始化重试管理器

        Args:
            max_retries: 最大重试次数（默认从配置读取）
            base_delay: 基础退避时间（秒）
            max_delay: 最大退避时间（秒）
            jitter: 是否添加随机抖动
        """
        config = RETRY_CONFIG

        self.max_retries = max_retries or config['max_retries']
        self.base_delay = base_delay or config['base_delay']
        self.max_delay = max_delay or config['max_delay']
        self.jitter = jitter if jitter is not None else config['jitter']

        self.retryable_errors = set(config['retryable_errors'])
        self.non_retryable_errors = set(config['non_retryable_errors'])

        logger.debug(
            f"初始化重试管理器: max_retries={self.max_retries}, "
            f"base_delay={self.base_delay}, jitter={self.jitter}"
        )

    def calculate_backoff(self, retry_count: int) -> float:
        """
        计算退避时间（指数退避 + 随机抖动）

        Args:
            retry_count: 当前重试次数（从0开始）

        Returns:
            float: 退避时间（秒）

        Example:
            >>> manager = RetryManager()
            >>> manager.calculate_backoff(0)  # 第1次重试，约1秒
            >>> manager.calculate_backoff(1)  # 第2次重试，约2秒
            >>> manager.calculate_backoff(2)  # 第3次重试，约4秒
        """
        # 指数退避：base_delay * 2^retry_count
        exponential_delay = self.base_delay * (2 ** retry_count)

        # 限制最大延迟
        delay = min(exponential_delay, self.max_delay)

        # 添加随机抖动（避免惊群效应）
        if self.jitter:
            # 抖动范围：±50%
            jitter_range = delay * 0.5
            delay = delay - jitter_range + random.uniform(0, jitter_range * 2)

        return max(0, delay)  # 确保非负

    def should_retry(self, error: Exception, retry_count: int) -> bool:
        """
        判断是否应该重试

        Args:
            error: 捕获的异常
            retry_count: 当前重试次数

        Returns:
            bool: 是否应该重试
        """
        # 检查重试次数
        if retry_count >= self.max_retries:
            logger.debug(f"达到最大重试次数: {self.max_retries}")
            return False

        # 检查错误类型
        error_type = self._classify_error(error)

        if error_type in self.non_retryable_errors:
            logger.debug(f"不可重试错误: {error_type}")
            return False

        if error_type in self.retryable_errors:
            logger.debug(f"可重试错误: {error_type}")
            return True

        # 未知错误，默认不重试（保守策略）
        logger.debug(f"未知错误类型: {type(error).__name__}")
        return False

    def _classify_error(self, error: Exception) -> str:
        """
        分类错误类型

        Args:
            error: 异常对象

        Returns:
            str: 错误类型标识
        """
        error_name = type(error).__name__.lower()
        error_msg = str(error).lower()

        # 超时错误
        if 'timeout' in error_name or 'timeout' in error_msg:
            return 'timeout'

        # 连接错误
        if 'connection' in error_name or 'connection' in error_msg:
            return 'connection_error'

        # 限流错误
        if 'rate limit' in error_msg or '429' in error_msg:
            return 'rate_limit'

        # 服务器错误
        if hasattr(error, 'status_code'):
            status_code = getattr(error, 'status_code')
            if 500 <= status_code < 600:
                return 'server_error_5xx'

        # 认证错误（不可重试）
        if 'authentication' in error_msg or 'unauthorized' in error_msg:
            return 'authentication_failed'

        # 权限错误（不可重试）
        if 'permission' in error_msg or 'forbidden' in error_msg:
            return 'permission_denied'

        # 请求错误（不可重试）
        if 'invalid' in error_msg or 'bad request' in error_msg:
            return 'invalid_request'

        # 未找到（不可重试）
        if 'not found' in error_msg or '404' in error_msg:
            return 'not_found'

        # 默认：未知错误
        return 'unknown'

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        执行函数并自动重试（异步版本）

        Args:
            func: 要执行的异步函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            Any: 函数返回值

        Raises:
            Exception: 重试失败后抛出最后一次异常

        Example:
            >>> manager = RetryManager()
            >>> result = await manager.execute_with_retry(
            ...     api_client.get_product,
            ...     product_id='123'
            ... )
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except Exception as e:
                last_error = e

                # 判断是否重试
                if not self.should_retry(e, attempt):
                    logger.error(f"不可重试错误，放弃重试: {e}")
                    raise

                # 计算退避时间
                backoff = self.calculate_backoff(attempt)

                logger.warning(
                    f"第{attempt + 1}次尝试失败: {e}, "
                    f"等待{backoff:.2f}秒后重试..."
                )

                # 等待后重试
                await asyncio.sleep(backoff)

        # 所有重试都失败
        logger.error(
            f"达到最大重试次数({self.max_retries})，放弃重试: {last_error}"
        )
        raise last_error

    def execute_with_retry_sync(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        执行函数并自动重试（同步版本）

        Args:
            func: 要执行的同步函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            Any: 函数返回值

        Raises:
            Exception: 重试失败后抛出最后一次异常
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                last_error = e

                if not self.should_retry(e, attempt):
                    logger.error(f"不可重试错误，放弃重试: {e}")
                    raise

                backoff = self.calculate_backoff(attempt)

                logger.warning(
                    f"第{attempt + 1}次尝试失败: {e}, "
                    f"等待{backoff:.2f}秒后重试..."
                )

                time.sleep(backoff)

        logger.error(
            f"达到最大重试次数({self.max_retries})，放弃重试: {last_error}"
        )
        raise last_error


def retry(
    max_retries: int = 3,
    base_delay: float = 1,
    max_delay: float = 60,
    jitter: bool = True
):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        base_delay: 基础退避时间
        max_delay: 最大退避时间
        jitter: 是否添加随机抖动

    Example:
        >>> @retry(max_retries=3, base_delay=2)
        >>> async def fetch_product(product_id: str):
        ...     # 可能失败的操作
        ...     return await api.get(product_id)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = RetryManager(max_retries, base_delay, max_delay, jitter)
            return await manager.execute_with_retry(func, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            manager = RetryManager(max_retries, base_delay, max_delay, jitter)
            return manager.execute_with_retry_sync(func, *args, **kwargs)

        # 根据函数类型返回对应的wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 便捷函数
def get_retry_manager(
    max_retries: Optional[int] = None,
    base_delay: Optional[float] = None
) -> RetryManager:
    """
    获取重试管理器实例（便捷函数）

    Args:
        max_retries: 最大重试次数
        base_delay: 基础退避时间

    Returns:
        RetryManager: 重试管理器实例
    """
    return RetryManager(max_retries=max_retries, base_delay=base_delay)
