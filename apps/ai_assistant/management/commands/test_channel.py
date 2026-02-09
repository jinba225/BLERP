"""
测试渠道连接的 Django 管理命令

测试 Telegram、企业微信、钉钉的连接和配置
"""

import json

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "测试渠道连接和配置"

    def add_arguments(self, parser):
        parser.add_argument(
            "--channel",
            type=str,
            required=True,
            choices=["telegram", "wechat", "dingtalk"],
            help="渠道类型",
        )
        parser.add_argument(
            "--action",
            type=str,
            default="all",
            choices=["all", "connection", "webhook", "token"],
            help="测试操作：all/连接/webhook/token",
        )

    def handle(self, *args, **options):
        channel = options["channel"]
        action = options["action"]

        if channel == "telegram":
            self._test_telegram(action)
        elif channel == "wechat":
            self._test_wechat(action)
        elif channel == "dingtalk":
            self._test_dingtalk(action)

    def _test_telegram(self, action):
        """测试 Telegram"""
        from ai_assistant.models import TelegramConfig

        from common.utils import decrypt_api_key

        config = TelegramConfig.objects.filter(is_active=True, is_deleted=False).first()

        if not config:
            raise CommandError("未找到激活的 Telegram 配置")

        self.stdout.write("=" * 60)
        self.stdout.write(f"Telegram 配置测试")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Bot 用户名: {config.bot_username}")
        self.stdout.write(f"允许群组: {config.allow_groups}")
        self.stdout.write(f"命令前缀: {config.command_prefix}")
        self.stdout.write(f'是否激活: {"✅" if config.is_active else "❌"}')

        # 获取 Bot Token
        try:
            bot_token = decrypt_api_key(config.bot_token)
            token_start = bot_token[:10] + "..."
            self.stdout.write(f"Bot Token: {token_start}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Bot Token 解密失败: {str(e)}"))
            return

        # 测试获取 Bot 信息
        if action in ["all", "connection"]:
            self.stdout.write("\n正在测试 Bot 连接...")
            try:
                from ai_assistant.channels import TelegramChannel

                channel_adapter = TelegramChannel(config)
                bot_info = channel_adapter.get_bot_info()

                if bot_info:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Bot 连接成功！\n   Bot ID: {bot_info.get("id")}\n   Bot 用户名: {bot_info.get("username")}'
                        )
                    )
                else:
                    self.stdout.write(self.style.ERROR("❌ Bot 连接失败：无法获取 Bot 信息"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Bot 连接测试失败: {str(e)}"))

        # 测试 Webhook
        if action in ["all", "webhook"]:
            if config.webhook_url:
                self.stdout.write(f"\n当前 Webhook URL: {config.webhook_url}")

                try:
                    url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()

                    result = response.json()
                    if result.get("ok"):
                        webhook_url = result.get("result", {}).get("url")
                        if webhook_url:
                            self.stdout.write(f"✅ Webhook 已设置: {webhook_url}")
                        else:
                            self.stdout.write("⚠️  Webhook 未设置")
                    else:
                        self.stdout.write(f'❌ 获取 Webhook 信息失败: {result.get("description", "未知错误")}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Webhook 测试失败: {str(e)}"))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "\n⚠️  Webhook URL 未配置，请使用以下命令设置：\n   python manage.py set_webhook --channel telegram --url <your-webhook-url>"
                    )
                )

        self.stdout.write("=" * 60)

    def _test_wechat(self, action):
        """测试企业微信"""
        from ai_assistant.models import WeChatConfig

        from common.utils import decrypt_api_key

        config = WeChatConfig.objects.filter(is_active=True, is_deleted=False).first()

        if not config:
            raise CommandError("未找到激活的企业微信配置")

        self.stdout.write("=" * 60)
        self.stdout.write("企业微信配置测试")
        self.stdout.write("=" * 60)
        self.stdout.write(f"企业 ID: {config.corp_id}")
        self.stdout.write(f"Agent ID: {config.agent_id}")
        self.stdout.write(f'是否激活: {"✅" if config.is_active else "❌"}')

        # 测试获取 Access Token
        if action in ["all", "token"]:
            self.stdout.write("\n正在测试 Access Token 获取...")
            try:
                from ai_assistant.channels import WeChatChannel

                channel_adapter = WeChatChannel(config)
                access_token = channel_adapter._get_access_token()

                if access_token:
                    token_start = access_token[:10] + "..."
                    self.stdout.write(self.style.SUCCESS(f"✅ Access Token 获取成功: {token_start}"))
                else:
                    self.stdout.write(self.style.ERROR("❌ Access Token 获取失败"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Access Token 测试失败: {str(e)}"))

        # Webhook 说明
        if action in ["all", "webhook"]:
            self.stdout.write(self.style.WARNING("\n⚠️  企业微信 Webhook 需要在企业微信管理后台手动配置"))
            self.stdout.write("   配置方法：登录企业微信管理后台 -> 应用管理 -> 应用 -> 接收消息 -> 设置回调 URL")

        self.stdout.write("=" * 60)

    def _test_dingtalk(self, action):
        """测试钉钉"""
        from ai_assistant.models import DingTalkConfig

        from common.utils import decrypt_api_key

        config = DingTalkConfig.objects.filter(is_active=True, is_deleted=False).first()

        if not config:
            raise CommandError("未找到激活的钉钉配置")

        self.stdout.write("=" * 60)
        self.stdout.write("钉钉配置测试")
        self.stdout.write("=" * 60)
        self.stdout.write(f"App Key: {config.app_key}")
        self.stdout.write(f"Agent ID: {config.agent_id}")
        self.stdout.write(f'是否激活: {"✅" if config.is_active else "❌"}')

        # 测试获取 Access Token
        if action in ["all", "token"]:
            self.stdout.write("\n正在测试 Access Token 获取...")
            try:
                from ai_assistant.channels import DingTalkChannel

                channel_adapter = DingTalkChannel(config)
                access_token = channel_adapter._get_access_token()

                if access_token:
                    token_start = access_token[:10] + "..."
                    self.stdout.write(self.style.SUCCESS(f"✅ Access Token 获取成功: {token_start}"))
                else:
                    self.stdout.write(self.style.ERROR("❌ Access Token 获取失败"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Access Token 测试失败: {str(e)}"))

        # Webhook 说明
        if action in ["all", "webhook"]:
            self.stdout.write(self.style.WARNING("\n⚠️  钉钉 Webhook 需要在钉钉开放平台手动配置"))
            self.stdout.write("   配置方法：登录钉钉开放平台 -> 应用开发 -> 企业内部应用 -> 机器人 -> 事件订阅 -> 设置回调 URL")

        self.stdout.write("=" * 60)
