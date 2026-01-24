"""
Core tasks for the ERP system.
"""
from celery import shared_task
from django.conf import settings
from pathlib import Path
import subprocess
import shlex
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_logs():
    """Clean up old audit logs."""
    try:
        from .models import AuditLog
        
        # Delete logs older than 90 days
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count = AuditLog.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old audit logs")
        return f"Cleaned up {deleted_count} old audit logs"
        
    except Exception as e:
        logger.error(f"Failed to cleanup old logs: {str(e)}")
        raise


@shared_task
def backup_database():
    """Backup database."""
    try:
        engine = settings.DATABASES['default']['ENGINE']
        if engine == 'django.db.backends.sqlite3':
            ts = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = Path(settings.BASE_DIR) / 'backups'
            backup_dir.mkdir(parents=True, exist_ok=True)
            src = Path(settings.DATABASES['default']['NAME'])
            dst = backup_dir / f'db_{ts}.sqlite3'
            result = subprocess.run(['bash', '-lc', f'cp {shlex.quote(str(src))} {shlex.quote(str(dst))}'], capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(result.stderr or result.stdout)
            logger.info(f"SQLite backup: {dst}")
            return f"SQLite backup: {dst}"
        result = subprocess.run(['bash', 'scripts/backup.sh'], cwd=settings.BASE_DIR, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)
        logger.info("Database backup completed")
        return "Database backup completed"
    except Exception as e:
        logger.error(f"Database backup failed: {str(e)}")
        raise


@shared_task
def send_system_notifications():
    """Send system notifications via email."""
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        from .models import Notification
        
        # Get notifications created in the last hour
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_notifications = Notification.objects.filter(
            is_read=False,
            created_at__gte=one_hour_ago
        ).select_related('recipient')
        
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
                
            subject = f'您有 {len(notes)} 条新通知 - Better Laser ERP'
            message = "您好，\n\n您有以下新通知：\n\n"
            
            for note in notes:
                message += f"- [{note.get_notification_type_display()}] {note.title}: {note.message}\n"
                
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
def update_system_status():
    """Update system status metrics."""
    try:
        from django.db import connection
        from django.core.cache import cache
        
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
        
        # Update cache with system status
        cache.set('system_status', {
            'database': db_status,
            'last_check': timezone.now().isoformat(),
        }, timeout=300)  # 5 minutes
        
        logger.info("System status updated")
        return "System status updated"
        
    except Exception as e:
        logger.error(f"Failed to update system status: {str(e)}")
        raise


@shared_task
def generate_daily_summary():
    """Generate daily summary report."""
    try:
        from django.contrib.auth import get_user_model
        from apps.sales.models import SalesOrder
        from apps.purchase.models import PurchaseOrder
        
        User = get_user_model()
        today = timezone.now().date()
        
        # Get daily statistics
        stats = {
            'date': today.isoformat(),
            'active_users': User.objects.filter(is_active=True).count(),
            'new_sales_orders': SalesOrder.objects.filter(
                order_date=today
            ).count(),
            'new_purchase_orders': PurchaseOrder.objects.filter(
                order_date=today
            ).count(),
        }
        
        # Store in cache for dashboard
        cache.set('daily_summary', stats, timeout=86400)  # 24 hours
        
        logger.info(f"Daily summary generated: {stats}")
        return f"Daily summary generated: {stats}"
        
    except Exception as e:
        logger.error(f"Failed to generate daily summary: {str(e)}")
        raise