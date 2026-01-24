from django.apps import AppConfig


class AiAssistantConfig(AppConfig):
    """AI助手应用配置"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_assistant'
    verbose_name = 'AI助手'

    def ready(self):
        """应用启动时执行"""
        # 可以在这里导入信号处理器等
        pass
