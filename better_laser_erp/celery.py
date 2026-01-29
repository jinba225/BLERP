"""
Celery 配置文件

用于异步任务处理
"""

import os
from celery import Celery
from celery.schedules import crontab

# 设置 Django settings 模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')

# 创建 Celery 应用
app = Celery('better_laser_erp')

# 从 Django settings 加载配置（使用 CELERY_ 前缀）
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现所有已安装应用中的 tasks.py
app.autodiscover_tasks()


# 定时任务配置
app.conf.beat_schedule = {
    # 每小时清理过期会话
    'cleanup-expired-conversations': {
        'task': 'apps.ai_assistant.tasks.cleanup_expired_conversations',
        'schedule': crontab(minute=0),  # 每小时执行
    },
    # 每天清理旧日志
    'cleanup-old-logs': {
        'task': 'apps.ai_assistant.tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点执行
    },
    
    # ========== 电商数据同步任务 ==========
    
    # 每日增量同步（凌晨2点）
    'sync-ecommerce-incremental': {
        'task': 'apps.ecomm_sync.tasks.sync_platform_products_task',
        'schedule': crontab(hour=2, minute=0),
        'options': {'expires': 3600}
    },
    
    # 每周全量同步（周日凌晨3点）
    'sync-ecommerce-full': {
        'task': 'apps.ecomm_sync.tasks.sync_platform_products_task',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),
        'options': {'expires': 7200}
    },
    
    # 每小时价格监控
    'monitor-price-changes': {
        'task': 'apps.ecomm_sync.tasks.sync_price_changes_task',
        'schedule': crontab(minute=0),
        'options': {'expires': 300}
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """调试任务"""
    print(f'Request: {self.request!r}')
