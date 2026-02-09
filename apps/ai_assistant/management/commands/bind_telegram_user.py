"""
绑定 Telegram 用户到系统用户

自动或手动将 Telegram 用户 ID 映射到系统用户账号
"""

import requests
from ai_assistant.models import ChannelUserMapping, TelegramConfig
from django.core.management.base import BaseCommand
from users.models import User

from common.utils import decrypt_api_key


class Command(BaseCommand):
    help = "绑定 Telegram 用户到系统用户"

    def add_arguments(self, parser):
        parser.add_argument("--auto", action="store_true", help="自动绑定最近的 Telegram 用户到 admin")
        parser.add_argument("--user-id", type=str, help="Telegram 用户 ID")
        parser.add_argument("--username", type=str, help="Telegram 用户名")
        parser.add_argument("--system-user", type=str, default="admin", help="系统用户名（默认: admin）")

    def handle(self, *args, **options):
        if options["auto"]:
            self._auto_bind(options["system_user"])
        elif options["user_id"]:
            self._manual_bind(
                options["user_id"], options.get("username", ""), options["system_user"]
            )
        else:
            self.stdout.write(self.style.ERROR("请提供 --user-id 或使用 --auto"))

    def _auto_bind(self, system_username):
        """自动绑定最近的 Telegram 用户"""
        try:
            # 获取 Telegram 配置
            config = TelegramConfig.objects.filter(is_active=True).first()
            if not config:
                self.stdout.write(self.style.ERROR("未找到激活的 Telegram 配置"))
                return

            token = decrypt_api_key(config.bot_token)

            # 获取最近的更新
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            response = requests.get(url)
            data = response.json()

            if not data.get("ok") or not data.get("result"):
                self.stdout.write(self.style.ERROR("没有收到任何消息，请先给 Bot 发送消息"))
                return

            # 获取最新消息的用户信息
            update = data["result"][-1]
            user = update["message"]["from"]

            telegram_user_id = str(user["id"])
            telegram_username = user.get("username", "")

            # 创建映射
            self._create_mapping(telegram_user_id, telegram_username, system_username)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"自动绑定失败: {str(e)}"))

    def _manual_bind(self, user_id, username, system_username):
        """手动绑定"""
        self._create_mapping(user_id, username, system_username)

    def _create_mapping(self, telegram_user_id, telegram_username, system_username):
        """创建用户映射"""
        try:
            # 获取系统用户
            user = User.objects.get(username=system_username)

            # 创建或获取映射
            mapping, created = ChannelUserMapping.objects.get_or_create(
                channel="telegram",
                external_user_id=telegram_user_id,
                defaults={"external_username": telegram_username, "user": user, "is_active": True},
            )

            if created:
                self.stdout.write(self.style.SUCCESS("✅ 用户绑定成功！"))
                self.stdout.write(f"   Telegram ID: {telegram_user_id}")
                self.stdout.write(f'   Telegram 用户名: {telegram_username or "无"}')
                self.stdout.write(f"   系统用户: {user.username}")
            else:
                self.stdout.write(self.style.WARNING("ℹ️  用户已绑定"))
                self.stdout.write(f"   当前绑定的系统用户: {mapping.user.username}")

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'系统用户 "{system_username}" 不存在'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"绑定失败: {str(e)}"))
