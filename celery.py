"""
Celery 配置和初始化

用于异步任务处理
"""

from celery import Celery
import os
from django.conf import settings

# 设置默认的 Django settings 模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')

# 创建 Celery 应用
app = Celery('django_erp')

# 从 Django settings 中加载 Celery 配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现所有已安装应用中的任务
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """配置 Celery Beat 定时任务"""
    from celery.schedules import crontab
    
    # 清理过期会话 - 每天凌晨 2 点
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        'apps.ai_assistant.tasks.cleanup_expired_conversations.s()',
        name='cleanup-expired-conversations'
    )
    
    # 清理旧日志 - 每天凌晨 3 点
    sender.add_periodic_task(
        crontab(hour=3, minute=0),
        'apps.ai_assistant.tasks.cleanup_old_logs.s()',
        name='cleanup-old-logs'
    )


@app.task(bind=True)
def debug_task(self):
    """测试任务"""
    print(f'Request: {self.request!r}')
