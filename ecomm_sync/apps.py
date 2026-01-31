from django.apps import AppConfig


class EcommSyncConfig(AppConfig):
    """电商同步应用配置"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ecomm_sync'
    verbose_name = '电商同步'
