# Better Laser ERP System

# Celery configuration
# 根据环境变量自动启用（设置 CELERY_BROKER_URL 即可启用）
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except Exception:
    # Celery 未配置或导入失败，开发环境可正常运行
    __all__ = ()
