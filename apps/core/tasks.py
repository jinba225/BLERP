"""
Core tasks for the ERP system.
"""

import logging
import shlex
import subprocess
import time
from datetime import timedelta
from functools import wraps
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


def task_monitor(func):
    """
    任务执行监控装饰器
    记录任务的执行时间、状态等信息
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        task_name = func.__name__
        start_time = time.time()
        status = "success"
        error_message = ""

        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            status = "failed"
            error_message = str(e)
            raise
        finally:
            end_time = time.time()
            execution_time = end_time - start_time

            # 记录任务执行信息
            logger.info(
                f"Task {task_name} completed with status {status} in {execution_time:.2f}s"
                f"{f', error: {error_message}' if error_message else ''}"
            )

            # 保存任务执行记录到数据库（如果需要）
            try:
                from apps.bi.models import TaskPerformance

                TaskPerformance.objects.create(
                    task_name=task_name,
                    execution_time=execution_time * 1000,  # 转换为毫秒
                    status=status,
                    error_message=error_message[:500] if error_message else "",
                    args=str(args)[:255],
                    kwargs=str(kwargs)[:255],
                )
            except Exception as e:
                logger.error(f"Failed to save task performance: {e}")

    return wrapper


@shared_task
@task_monitor
def cleanup_old_logs():
    """Clean up old audit logs."""
    try:
        from .models import AuditLog

        # Delete logs older than 90 days
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count = AuditLog.objects.filter(timestamp__lt=cutoff_date).delete()[0]

        logger.info(f"Cleaned up {deleted_count} old audit logs")
        return f"Cleaned up {deleted_count} old audit logs"

    except Exception as e:
        logger.error(f"Failed to cleanup old logs: {str(e)}")
        raise


@shared_task
@task_monitor
def backup_database():
    """Backup database."""
    try:
        engine = settings.DATABASES["default"]["ENGINE"]
        if engine == "django.db.backends.sqlite3":
            ts = timezone.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(settings.BASE_DIR) / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            src = Path(settings.DATABASES["default"]["NAME"])
            dst = backup_dir / f"db_{ts}.sqlite3"
            result = subprocess.run(
                ["bash", "-lc", f"cp {shlex.quote(str(src))} {shlex.quote(str(dst))}"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr or result.stdout)
            logger.info(f"SQLite backup: {dst}")
            return f"SQLite backup: {dst}"
        result = subprocess.run(
            ["bash", "scripts/backup.sh"],
            cwd=settings.BASE_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)
        logger.info("Database backup completed")
        return "Database backup completed"
    except Exception as e:
        logger.error(f"Database backup failed: {str(e)}")
        raise


@shared_task
@task_monitor
def send_system_notifications():
    """Send system notifications via email."""
    try:
        from django.conf import settings
        from django.core.mail import send_mail

        from .models import Notification

        # Get notifications created in the last hour
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_notifications = Notification.objects.filter(
            is_read=False, created_at__gte=one_hour_ago
        ).select_related("recipient")

        if not recent_notifications.exists():
            return "No new notifications to send"

        # Group by user
        user_notifications = {}
        for note in recent_notifications:
            if note.recipient not in user_notifications:
                user_notifications[note.recipient] = []
            user_notifications[note.recipient].append(note)

        # Send emails
        sent_count = 0
        for user, notes in user_notifications.items():
            if not user.email:
                continue

            subject = f"您有 {len(notes)} 条新通知 - Better Laser ERP"
            message = "您好，\n\n您有以下新通知：\n\n"

            for note in notes:
                message += (
                    f"- [{note.get_notification_type_display()}] {note.title}: {note.message}\n"
                )

            message += "\n请登录系统查看详情。"

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send notification email to {user.email}: {e}")

        logger.info(f"Sent notification emails to {sent_count} users")
        return f"Sent notification emails to {sent_count} users"

    except Exception as e:
        logger.error(f"Failed to send notifications: {str(e)}")
        raise


@shared_task
@task_monitor
def update_system_status():
    """Update system status metrics."""
    try:
        from django.core.cache import cache
        from django.db import connection

        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"

        # Update cache with system status
        cache.set(
            "system_status",
            {
                "database": db_status,
                "last_check": timezone.now().isoformat(),
            },
            timeout=300,
        )  # 5 minutes

        logger.info("System status updated")
        return "System status updated"

    except Exception as e:
        logger.error(f"Failed to update system status: {str(e)}")
        raise


@shared_task
@task_monitor
def generate_daily_summary():
    """Generate daily summary report."""
    try:
        from django.contrib.auth import get_user_model
        from purchase.models import PurchaseOrder
        from sales.models import SalesOrder

        User = get_user_model()
        today = timezone.now().date()

        # Get daily statistics
        stats = {
            "date": today.isoformat(),
            "active_users": User.objects.filter(is_active=True).count(),
            "new_sales_orders": SalesOrder.objects.filter(order_date=today).count(),
            "new_purchase_orders": PurchaseOrder.objects.filter(order_date=today).count(),
        }

        # Store in cache for dashboard
        cache.set("daily_summary", stats, timeout=86400)  # 24 hours

        logger.info(f"Daily summary generated: {stats}")
        return f"Daily summary generated: {stats}"

    except Exception as e:
        logger.error(f"Failed to generate daily summary: {str(e)}")
        raise


@shared_task
@task_monitor
def collect_system_health():
    """Collect system health metrics and save to database."""
    try:
        import psutil
        from django.contrib.auth import get_user_model
        from django.core.cache import cache
        from django.db import connection, models
        from django.utils import timezone

        from apps.bi.models import ApiPerformance, SystemHealth

        # 获取系统资源使用情况
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent

        # 获取活跃用户数（最近30分钟内活跃）
        User = get_user_model()
        thirty_minutes_ago = timezone.now() - timezone.timedelta(minutes=30)
        active_users = User.objects.filter(last_login__gte=thirty_minutes_ago).count()

        # 获取API性能统计（最近5分钟）
        five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
        api_performance = ApiPerformance.objects.filter(request_time__gte=five_minutes_ago)
        avg_response_time = api_performance.aggregate(avg=models.Avg("response_time"))["avg"] or 0
        error_count = api_performance.filter(status_code__gte=400).count()
        warning_count = api_performance.filter(response_time__gt=1000).count()  # 响应时间超过1秒的警告

        # 计算缓存命中率（模拟值，实际应根据缓存系统统计）
        cache_hit_rate = 75.5  # 示例值，实际应从缓存系统获取

        # 计算Celery任务统计（模拟值，实际应从Celery获取）
        celery_task_count = 120  # 示例值
        celery_task_success_rate = 98.5  # 示例值

        # 确定系统状态
        status = "normal"
        if cpu_usage > 80 or memory_usage > 80:
            status = "warning"
        if cpu_usage > 90 or memory_usage > 90:
            status = "critical"
        if error_count > 10:
            status = "warning"
        if error_count > 20:
            status = "critical"

        # 创建系统健康记录
        SystemHealth.objects.create(
            api_response_time=avg_response_time,
            db_query_count=0,  # 实际应从数据库监控获取
            db_query_time=0,  # 实际应从数据库监控获取
            cache_hit_rate=cache_hit_rate,
            celery_task_count=celery_task_count,
            celery_task_success_rate=celery_task_success_rate,
            active_users=active_users,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            status=status,
            error_count=error_count,
            warning_count=warning_count,
        )

        logger.info(
            f"System health collected: status={status}, cpu={cpu_usage}%, memory={memory_usage}%, active_users={active_users}"
        )
        return f"System health collected: status={status}"

    except ImportError:
        logger.warning("psutil library not installed, skipping system resource monitoring")
        # 不依赖psutil的基本统计
        from django.contrib.auth import get_user_model
        from django.utils import timezone

        from apps.bi.models import ApiPerformance, SystemHealth

        # 获取活跃用户数
        User = get_user_model()
        thirty_minutes_ago = timezone.now() - timezone.timedelta(minutes=30)
        active_users = User.objects.filter(last_login__gte=thirty_minutes_ago).count()

        # 获取API性能统计
        five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
        api_performance = ApiPerformance.objects.filter(request_time__gte=five_minutes_ago)
        avg_response_time = api_performance.aggregate(avg=models.Avg("response_time"))["avg"] or 0
        error_count = api_performance.filter(status_code__gte=400).count()
        warning_count = api_performance.filter(response_time__gt=1000).count()

        # 创建系统健康记录（不包含系统资源使用情况）
        SystemHealth.objects.create(
            api_response_time=avg_response_time,
            db_query_count=0,
            db_query_time=0,
            cache_hit_rate=70.0,
            celery_task_count=100,
            celery_task_success_rate=95.0,
            active_users=active_users,
            memory_usage=0,
            cpu_usage=0,
            status="normal" if error_count < 10 else "warning",
            error_count=error_count,
            warning_count=warning_count,
        )

        logger.info(
            f"System health collected (basic): active_users={active_users}, error_count={error_count}"
        )
        return f"System health collected (basic)"
    except Exception as e:
        logger.error(f"Failed to collect system health: {str(e)}")
        raise
