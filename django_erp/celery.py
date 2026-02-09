"""
Celery 配置文件

用于异步任务处理
"""

import os
from celery import Celery
from celery.schedules import crontab

# 设置 Django settings 模块
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")

# 创建 Celery 应用
app = Celery("django_erp")

# 从 Django settings 加载配置（使用 CELERY_ 前缀）
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动发现所有已安装应用中的 tasks.py
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """调试任务"""
    print(f"Request: {self.request!r}")
