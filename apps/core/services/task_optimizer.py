"""
Celery任务优化服务

功能：
- 任务执行监控
- 任务重试机制优化
- 任务队列优先级管理
- 任务执行统计
"""
import logging
import time
from functools import wraps
from typing import Dict, Optional, Any

from celery import current_app
from celery.result import AsyncResult
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class TaskOptimizer:
    """
    任务优化器
    """

    def __init__(self):
        """
        初始化任务优化器
        """
        self.app = current_app
        self.task_stats = {}
        logger.debug("初始化任务优化器")

    def task_with_retry(self, max_retries=3, retry_backoff=2, retry_jitter=True, **options):
        """
        带重试机制的任务装饰器

        Args:
            max_retries: 最大重试次数
            retry_backoff: 重试间隔基数（秒）
            retry_jitter: 是否添加随机抖动
            **options: 其他Celery任务选项

        Returns:
            装饰器函数
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                task_name = func.__name__
                start_time = time.time()
                status = "success"
                error_message = ""

                try:
                    # 记录任务开始
                    self._record_task_start(task_name, args, kwargs)

                    # 执行任务
                    result = func(*args, **kwargs)

                    # 记录任务成功
                    execution_time = time.time() - start_time
                    self._record_task_success(task_name, execution_time, result)

                    return result
                except Exception as e:
                    # 记录任务失败
                    status = "failed"
                    error_message = str(e)
                    execution_time = time.time() - start_time
                    self._record_task_failure(task_name, execution_time, error_message)

                    # 处理重试
                    task = current_app.current_task
                    if task and task.request.retries < max_retries:
                        # 计算重试延迟
                        delay = retry_backoff ** task.request.retries
                        if retry_jitter:
                            import random
                            delay = delay * (0.8 + 0.4 * random.random())

                        logger.warning(
                            f"任务 {task_name} 失败，将在 {delay:.2f} 秒后重试 "
                            f"({task.request.retries + 1}/{max_retries})"
                        )
                        raise task.retry(exc=e, countdown=delay, max_retries=max_retries)
                    else:
                        logger.error(f"任务 {task_name} 最终失败: {error_message}")
                        raise

            # 应用Celery任务装饰器
            wrapper = self.app.task(
                **options,
                max_retries=max_retries,
                retry_backoff=retry_backoff,
                retry_jitter=retry_jitter
            )(wrapper)

            return wrapper

        return decorator

    def task_with_priority(self, priority=5, **options):
        """
        带优先级的任务装饰器

        Args:
            priority: 任务优先级，1-10，1最高
            **options: 其他Celery任务选项

        Returns:
            装饰器函数
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            # 应用Celery任务装饰器
            wrapper = self.app.task(
                **options,
                priority=priority
            )(wrapper)

            return wrapper

        return decorator

    def _record_task_start(self, task_name: str, args: tuple, kwargs: dict):
        """
        记录任务开始

        Args:
            task_name: 任务名称
            args: 任务参数
            kwargs: 任务关键字参数
        """
        try:
            from apps.bi.models import TaskPerformance

            TaskPerformance.objects.create(
                task_name=task_name,
                status="success",  # 使用success作为默认状态
                args=str(args)[:255],
                kwargs=str(kwargs)[:255]
            )
        except Exception as e:
            logger.error(f"记录任务开始失败: {e}")

    def _record_task_success(self, task_name: str, execution_time: float, result: Any):
        """
        记录任务成功

        Args:
            task_name: 任务名称
            execution_time: 执行时间（秒）
            result: 任务结果
        """
        try:
            from apps.bi.models import TaskPerformance

            # 创建新的任务记录
            TaskPerformance.objects.create(
                task_name=task_name,
                execution_time=execution_time * 1000,  # 转换为毫秒
                status="success",
                args="",
                kwargs=""
            )

            # 更新任务统计
            self._update_task_stats(task_name, "success", execution_time)
        except Exception as e:
            logger.error(f"记录任务成功失败: {e}")

    def _record_task_failure(self, task_name: str, execution_time: float, error_message: str):
        """
        记录任务失败

        Args:
            task_name: 任务名称
            execution_time: 执行时间（秒）
            error_message: 错误信息
        """
        try:
            from apps.bi.models import TaskPerformance

            # 创建新的任务记录
            TaskPerformance.objects.create(
                task_name=task_name,
                execution_time=execution_time * 1000,  # 转换为毫秒
                status="failed",
                error_message=error_message[:500],
                args="",
                kwargs=""
            )

            # 更新任务统计
            self._update_task_stats(task_name, "failed", execution_time)
        except Exception as e:
            logger.error(f"记录任务失败: {e}")

    def _update_task_stats(self, task_name: str, status: str, execution_time: float):
        """
        更新任务统计信息

        Args:
            task_name: 任务名称
            status: 任务状态
            execution_time: 执行时间（秒）
        """
        if task_name not in self.task_stats:
            self.task_stats[task_name] = {
                "total": 0,
                "success": 0,
                "failed": 0,
                "total_time": 0,
                "avg_time": 0
            }

        stats = self.task_stats[task_name]
        stats["total"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["total"]

        if status == "success":
            stats["success"] += 1
        elif status == "failed":
            stats["failed"] += 1

    def get_task_stats(self, task_name: Optional[str] = None) -> Dict:
        """
        获取任务统计信息

        Args:
            task_name: 任务名称，None表示所有任务

        Returns:
            任务统计信息
        """
        if task_name:
            return self.task_stats.get(task_name, {})
        return self.task_stats

    def get_task_status(self, task_id: str) -> Dict:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        try:
            result = AsyncResult(task_id)
            return {
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
                "traceback": result.traceback if result.failed() else None,
                "started_at": result.started_at,
                "completed_at": result.completed_at
            }
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            return {
                "task_id": task_id,
                "error": str(e)
            }

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否取消成功
        """
        try:
            result = AsyncResult(task_id)
            return result.revoke(terminate=True)
        except Exception as e:
            logger.error(f"取消任务失败: {e}")
            return False

    def get_queue_stats(self) -> Dict:
        """
        获取队列统计信息

        Returns:
            队列统计信息
        """
        try:
            inspect = self.app.control.inspect()
            stats = inspect.stats()
            active = inspect.active()
            reserved = inspect.reserved()
            scheduled = inspect.scheduled()

            return {
                "stats": stats,
                "active": active,
                "reserved": reserved,
                "scheduled": scheduled
            }
        except Exception as e:
            logger.error(f"获取队列统计失败: {e}")
            return {"error": str(e)}


# 全局单例
_task_optimizer_instance = None


def get_task_optimizer() -> TaskOptimizer:
    """
    获取任务优化器实例（单例模式）

    Returns:
        TaskOptimizer: 任务优化器实例
    """
    global _task_optimizer_instance
    if _task_optimizer_instance is None:
        _task_optimizer_instance = TaskOptimizer()
    return _task_optimizer_instance


# 导出便捷装饰器
task_with_retry = get_task_optimizer().task_with_retry
task_with_priority = get_task_optimizer().task_with_priority
