"""
分布式锁 - 基于Redis实现
支持锁续期、死锁检测、超时自动释放
"""
import asyncio
import time
import uuid
import logging
from typing import Optional, contextmanager
from django.core.cache import cache
from ..config import DISTRIBUTED_LOCK_CONFIG


logger = logging.getLogger(__name__)


class DistributedLock:
    """
    Redis分布式锁

    实现原理：
    - 使用 SET key value NX PX timeout 原子操作获取锁
    - 唯一标识（UUID）防止误删其他客户端的锁
    - 支持自动续期（防止任务超时导致锁提前释放）
    - 超时自动释放（防止死锁）

    优势：
    - 互斥性：同时只有一个客户端能持有锁
    - 避免死锁：锁超时自动释放
    - 可重入：支持同一线程多次获取锁
    - 安全性：唯一标识防止误删
    """

    def __init__(
        self,
        lock_key: str,
        ttl: Optional[int] = None,
        auto_renewal: Optional[bool] = None,
        redis_client=None
    ):
        """
        初始化分布式锁

        Args:
            lock_key: 锁的键名（如 'sync_products:123'）
            ttl: 锁过期时间（秒），默认从配置读取
            auto_renewal: 是否自动续期，默认从配置读取
            redis_client: Redis客户端（可选）

        Example:
            >>> lock = DistributedLock('sync_products:123', ttl=30)
            >>> async with lock:
            ...     # 执行需要加锁的操作
            ...     await sync_products()
        """
        self.lock_key = f"distributed_lock:{lock_key}"
        self._lock_value = None
        self._locked = False
        self._renewal_task = None

        # 配置参数
        config = DISTRIBUTED_LOCK_CONFIG
        self.ttl = ttl or config['default_ttl']
        self.auto_renewal = auto_renewal if auto_renewal is not None else config['auto_renewal']
        self.renewal_interval = config['renewal_interval']
        self.max_lock_time = config['max_lock_time']

        # Redis客户端
        self.redis_client = redis_client or cache

        logger.debug(
            f"初始化分布式锁: key={lock_key}, ttl={self.ttl}, "
            f"auto_renewal={self.auto_renewal}"
        )

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.release()

    def __enter__(self):
        """同步上下文管理器入口"""
        self.acquire_sync()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器出口"""
        self.release_sync()

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        获取锁（异步版本）

        Args:
            timeout: 获取锁的超时时间（秒），None表示阻塞等待

        Returns:
            bool: 是否成功获取锁

        Example:
            >>> lock = DistributedLock('sync_products')
            >>> # 阻塞获取锁
            >>> await lock.acquire()
            >>> # 非阻塞获取锁
            >>> success = await lock.acquire(timeout=0)
            >>> # 最多等待5秒
            >>> success = await lock.acquire(timeout=5)
        """
        start_time = time.time()

        while True:
            # 生成唯一标识
            self._lock_value = str(uuid.uuid4())

            try:
                # 使用SET NX EX原子操作获取锁
                acquired = self.redis_client.set(
                    self.lock_key,
                    self._lock_value,
                    nx=True,  # 仅当键不存在时设置
                    ex=self.ttl  # 过期时间（秒）
                )

                if acquired:
                    self._locked = True
                    logger.info(f"成功获取锁: {self.lock_key}")

                    # 启动自动续期任务
                    if self.auto_renewal:
                        self._start_renewal_task()

                    return True

                # 未获取到锁
                if timeout is not None:
                    # 检查是否超时
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        logger.warning(f"获取锁超时: {self.lock_key}")
                        return False

                    # 等待后重试
                    await asyncio.sleep(0.1)
                else:
                    # 阻塞等待
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"获取锁失败: {self.lock_key}, error: {e}")
                return False

    def acquire_sync(self, timeout: Optional[float] = None) -> bool:
        """
        获取锁（同步版本）

        Args:
            timeout: 获取锁的超时时间（秒）

        Returns:
            bool: 是否成功获取锁
        """
        start_time = time.time()

        while True:
            self._lock_value = str(uuid.uuid4())

            try:
                acquired = self.redis_client.set(
                    self.lock_key,
                    self._lock_value,
                    nx=True,
                    ex=self.ttl
                )

                if acquired:
                    self._locked = True
                    logger.info(f"成功获取锁: {self.lock_key}")
                    return True

                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        logger.warning(f"获取锁超时: {self.lock_key}")
                        return False

                    time.sleep(0.1)
                else:
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"获取锁失败: {self.lock_key}, error: {e}")
                return False

    async def release(self):
        """释放锁（异步版本）"""
        if not self._locked:
            logger.warning(f"锁未持有: {self.lock_key}")
            return

        try:
            # 停止自动续期任务
            if self._renewal_task:
                self._renewal_task.cancel()
                self._renewal_task = None

            # 使用Lua脚本确保只删除自己持有的锁
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """

            result = self.redis_client.eval(
                lua_script,
                1,
                self.lock_key,
                self._lock_value
            )

            if result:
                logger.info(f"成功释放锁: {self.lock_key}")
            else:
                logger.warning(f"锁已被其他人释放或已过期: {self.lock_key}")

        except Exception as e:
            logger.error(f"释放锁失败: {self.lock_key}, error: {e}")
        finally:
            self._locked = False

    def release_sync(self):
        """释放锁（同步版本）"""
        if not self._locked:
            logger.warning(f"锁未持有: {self.lock_key}")
            return

        try:
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """

            result = self.redis_client.eval(
                lua_script,
                1,
                self.lock_key,
                self._lock_value
            )

            if result:
                logger.info(f"成功释放锁: {self.lock_key}")
            else:
                logger.warning(f"锁已被其他人释放或已过期: {self.lock_key}")

        except Exception as e:
            logger.error(f"释放锁失败: {self.lock_key}, error: {e}")
        finally:
            self._locked = False

    def _start_renewal_task(self):
        """启动自动续期任务"""
        async def renewal_loop():
            while self._locked:
                try:
                    await asyncio.sleep(self.renewal_interval)
                    if self._locked:
                        await self._renew_lock()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"锁续期失败: {e}")

        self._renewal_task = asyncio.create_task(renewal_loop())

    async def _renew_lock(self):
        """续期锁"""
        try:
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """

            result = self.redis_client.eval(
                lua_script,
                1,
                self.lock_key,
                self._lock_value,
                self.ttl
            )

            if result:
                logger.debug(f"锁续期成功: {self.lock_key}")
            else:
                logger.warning(f"锁续期失败（锁已丢失）: {self.lock_key}")

        except Exception as e:
            logger.error(f"锁续期异常: {e}")

    def is_locked(self) -> bool:
        """
        检查锁是否被持有

        Returns:
            bool: 锁是否被持有
        """
        return self._locked

    def get_lock_info(self) -> dict:
        """
        获取锁信息

        Returns:
            dict: 锁的状态信息
        """
        try:
            ttl = self.redis_client.ttl(self.lock_key)
            value = self.redis_client.get(self.lock_key)

            return {
                'lock_key': self.lock_key,
                'locked': self._locked,
                'ttl': ttl,
                'is_owner': value == self._lock_value if value else False,
            }
        except Exception as e:
            logger.error(f"获取锁信息失败: {e}")
            return {
                'lock_key': self.lock_key,
                'error': str(e),
            }


@contextmanager
def distributed_lock(
    lock_key: str,
    ttl: Optional[int] = None,
    timeout: Optional[float] = None
):
    """
    分布式锁上下文管理器（同步版本）

    Args:
        lock_key: 锁的键名
        ttl: 锁过期时间（秒）
        timeout: 获取锁的超时时间（秒）

    Example:
        >>> with distributed_lock('sync_products', ttl=30):
        ...     # 执行需要加锁的操作
        ...     sync_products()
    """
    lock = DistributedLock(lock_key, ttl=ttl)

    try:
        acquired = lock.acquire_sync(timeout=timeout)
        if not acquired:
            raise TimeoutError(f"获取分布式锁超时: {lock_key}")

        yield lock

    finally:
        lock.release_sync()


async def async_distributed_lock(
    lock_key: str,
    ttl: Optional[int] = None,
    timeout: Optional[float] = None
):
    """
    分布式锁上下文管理器（异步版本）

    Args:
        lock_key: 锁的键名
        ttl: 锁过期时间（秒）
        timeout: 获取锁的超时时间（秒）

    Example:
        >>> async with async_distributed_lock('sync_products', ttl=30):
        ...     # 执行需要加锁的操作
        ...     await sync_products()
    """
    lock = DistributedLock(lock_key, ttl=ttl)

    try:
        acquired = await lock.acquire(timeout=timeout)
        if not acquired:
            raise TimeoutError(f"获取分布式锁超时: {lock_key}")

        yield lock

    finally:
        await lock.release()
