"""
设置渠道 Webhook 的 Django 管理命令

支持设置 Telegram、企业微信、钉钉的 Webhook URL
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import requests


class Command(BaseCommand):
    help = '设置渠道 Webhook'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--channel',
            type=str,
            required=True,
            choices=['telegram', 'wechat', 'dingtalk'],
            help='渠道类型'
        )
        parser.add_argument(
            '--url',
            type=str,
            required=True,
            help='Webhook URL（完整的 URL，如：https://your-domain.com/ai_assistant/webhook/telegram）'
        )
    
    def handle(self, *args, **options):
        channel = options['channel']
        webhook_url = options['url']
        
        if channel == 'telegram':
            self._set_telegram_webhook(webhook_url)
        elif channel == 'wechat':
            self._set_wechat_webhook(webhook_url)
        elif channel == 'dingtalk':
            self._set_dingtalk_webhook(webhook_url)
    
    def _set_telegram_webhook(self, webhook_url):
        """设置 Telegram Webhook"""
        from apps.ai_assistant.models import TelegramConfig
        from apps.ai_assistant.utils import decrypt_api_key
        
        config = TelegramConfig.objects.filter(
            is_active=True,
            is_deleted=False
        ).first()
        
        if not config:
            raise CommandError('未找到激活的 Telegram 配置，请先在 Admin 后台添加配置')
        
        try:
            from apps.ai_assistant.channels import TelegramChannel
            channel_adapter = TelegramChannel(config)
            
            success = channel_adapter.set_webhook(webhook_url)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Telegram Webhook 设置成功！\n   URL: {webhook_url}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Telegram Webhook 设置失败')
                )
        except Exception as e:
            raise CommandError(f'Telegram Webhook 设置失败: {str(e)}')
    
    def _set_wechat_webhook(self, webhook_url):
        """设置企业微信 Webhook"""
        self.stdout.write(
            self.style.WARNING('⚠️  企业微信 Webhook 需要在企业微信管理后台手动配置')
        )
        self.stdout.write(f'   Webhook URL: {webhook_url}')
        self.stdout.write(
            self.style.WARNING('   配置方法：登录企业微信管理后台 -> 应用管理 -> 应用 -> 接收消息 -> 设置回调 URL')
        )
    
    def _set_dingtalk_webhook(self, webhook_url):
        """设置钉钉 Webhook"""
        self.stdout.write(
            self.style.WARNING('⚠️  钉钉 Webhook 需要在钉钉开放平台手动配置')
        )
        self.stdout.write(f'   Webhook URL: {webhook_url}')
        self.stdout.write(
            self.style.WARNING('   配置方法：登录钉钉开放平台 -> 应用开发 -> 企业内部应用 -> 机器人 -> 事件订阅 -> 设置回调 URL')
        )
