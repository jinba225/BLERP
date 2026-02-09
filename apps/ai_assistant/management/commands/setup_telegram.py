"""
配置 Telegram Bot 的管理命令
"""
from django.core.management.base import BaseCommand

from apps.ai_assistant.models import TelegramConfig


class Command(BaseCommand):
    help = "配置 Telegram Bot 到系统"

    def handle(self, *args, **options):
        """执行配置"""

        # 检查是否已存在配置
        existing_config = TelegramConfig.objects.filter(is_active=True).first()
        if existing_config:
            self.stdout.write(self.style.WARNING(f"⚠️  发现已存在的激活配置 (ID: {existing_config.id})"))
            self.stdout.write("正在禁用旧配置...")
            existing_config.is_active = False
            existing_config.save()
            self.stdout.write(self.style.SUCCESS("✅ 旧配置已禁用"))

        # 创建新配置
        self.stdout.write("\n正在创建新的 Telegram Bot 配置...")

        config = TelegramConfig.objects.create(
            bot_token="8291865352:AAEKO7TxzThbgRMoqqgHTUqkRTnNnLJrrdE",
            bot_username="YOUR_BOT_USERNAME",  # 需要用户提供
            allow_groups=False,
            command_prefix="/",
            is_active=True,
        )

        self.stdout.write(self.style.SUCCESS(f"\n✅ Telegram Bot 配置创建成功！"))
        self.stdout.write(f"   配置 ID: {config.id}")
        self.stdout.write(f"   Bot 用户名: @{config.bot_username}")
        self.stdout.write(f"   Token (加密后): {config.bot_token[:20]}...")
        self.stdout.write(f'   状态: {"激活" if config.is_active else "未激活"}')
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📝 下一步: 运行 "python manage.py test_channel --channel telegram" 验证配置'
            )
        )
        self.stdout.write(self.style.WARNING(f"\n⚠️  请记得通过 Admin 后台或直接修改数据库更新 bot_username"))
