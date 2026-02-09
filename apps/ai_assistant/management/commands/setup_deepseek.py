"""
配置 DeepSeek AI Provider

设置 DeepSeek API Key 并启用它作为默认 AI Provider
"""

from ai_assistant.models import AIModelConfig
from django.conf import settings
from django.core.management.base import BaseCommand

from common.utils import encrypt_api_key


class Command(BaseCommand):
    help = "配置 DeepSeek AI Provider"

    def handle(self, *args, **options):
        # 获取 DeepSeek API Key
        deepseek_api_key = getattr(settings, "DEEPSEEK_API_KEY", None)

        if not deepseek_api_key:
            self.stdout.write(self.style.ERROR("DEEPSEEK_API_KEY 未在 settings.py 或环境变量中设置"))
            self.stdout.write("请在 settings.py 中添加:\n" 'DEEPSEEK_API_KEY = "your-deepseek-api-key"')
            return

        # 加密 API Key
        encrypted_api_key = encrypt_api_key(deepseek_api_key)

        # 检查是否已存在 DeepSeek 配置
        existing_config = AIModelConfig.objects.filter(
            provider="deepseek", is_deleted=False
        ).first()

        if existing_config:
            # 更新现有配置
            existing_config.api_key = encrypted_api_key
            existing_config.is_active = True
            existing_config.is_default = True
            existing_config.save()
            self.stdout.write(self.style.SUCCESS(f"✓ 已更新 DeepSeek 配置 (ID: {existing_config.id})"))
        else:
            # 创建新配置
            config = AIModelConfig.objects.create(
                name="DeepSeek",
                provider="deepseek",
                model_name="deepseek-chat",
                api_key=encrypted_api_key,
                api_base="https://api.deepseek.com/v1",
                is_active=True,
                is_default=True,
                timeout=30,
                created_by_id=1,  # 假设第一个用户是管理员
            )
            self.stdout.write(self.style.SUCCESS(f"✓ 已创建 DeepSeek 配置 (ID: {config.id})"))

        # 禁用其他默认配置
        AIModelConfig.objects.filter(
            is_default=True,
            is_deleted=False,
        ).exclude(
            provider="deepseek",
        ).update(is_default=False)

        self.stdout.write(self.style.SUCCESS("DeepSeek 已设置为默认 AI Provider"))
