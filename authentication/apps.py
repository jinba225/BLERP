from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    verbose_name = '系统设置 - 认证'

    def ready(self):
        """
        Run when Django app is ready.
        Register drf-spectacular authentication extensions.
        """
        from .spectacular import register_authentication_extensions
        register_authentication_extensions()
