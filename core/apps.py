from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = '系统设置 - 核心配置'

    def ready(self):
        """
        应用启动时注册信号
        """
        import core.signals  # noqa: F401
