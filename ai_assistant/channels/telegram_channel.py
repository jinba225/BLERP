"""
Telegram Bot集成

通过Telegram Bot API实现消息收发
"""

from typing import Optional
from datetime import datetime
import json
import requests
from django.http import HttpRequest

from .base_channel import BaseChannel, IncomingMessage, OutgoingMessage
from ..models import TelegramConfig
from ..utils import decrypt_api_key


class TelegramChannel(BaseChannel):
    """Telegram Bot渠道处理器"""

    channel_name = "telegram"

    def __init__(self, config: TelegramConfig):
        """
        初始化Telegram渠道

        Args:
            config: TelegramConfig配置对象
        """
        super().__init__(config)
        self.bot_token = decrypt_api_key(config.bot_token)
        self.bot_username = config.bot_username
        self.allow_groups = config.allow_groups

    def verify_webhook(self, request: HttpRequest) -> bool:
        """
        验证Webhook请求

        Telegram不需要额外验证，只需检查是否是POST请求

        Args:
            request: Django HttpRequest对象

        Returns:
            是否合法
        """
        return request.method == 'POST'

    def parse_message(self, request: HttpRequest) -> Optional[IncomingMessage]:
        """
        解析Telegram Update

        Args:
            request: Django HttpRequest对象

        Returns:
            IncomingMessage对象
        """
        try:
            # 解析请求体
            body = json.loads(request.body.decode('utf-8'))

            # 获取消息对象
            message = body.get('message')
            if not message:
                # 可能是其他类型的update（edited_message, callback_query等）
                return None

            # 检查是否是文本消息
            text = message.get('text')
            if not text:
                return None

            # 获取发送者信息
            from_user = message.get('from', {})
            chat = message.get('chat', {})

            # 检查是否是群组消息
            if chat.get('type') in ['group', 'supergroup'] and not self.allow_groups:
                return None

            # 获取用户ID
            external_user_id = str(from_user.get('id'))
            username = from_user.get('username') or from_user.get('first_name', 'Unknown')

            # 构建会话ID（私聊用user_id，群聊用chat_id）
            if chat.get('type') == 'private':
                conversation_id = f"telegram_{external_user_id}"
            else:
                conversation_id = f"telegram_group_{chat.get('id')}"

            return IncomingMessage(
                message_id=str(message.get('message_id')),
                channel=self.channel_name,
                external_user_id=external_user_id,
                content=text,
                timestamp=datetime.fromtimestamp(message.get('date', 0)),
                message_type="text",
                conversation_id=conversation_id,
                raw_data={
                    'username': username,
                    'chat_id': chat.get('id'),
                    'chat_type': chat.get('type'),
                }
            )

        except Exception as e:
            print(f"解析Telegram消息失败: {str(e)}")
            return None

    def send_message(self, external_user_id: str, message: OutgoingMessage) -> bool:
        """
        发送消息给用户

        Args:
            external_user_id: Telegram User ID或Chat ID
            message: OutgoingMessage对象

        Returns:
            是否发送成功
        """
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

            # 构建请求数据
            data = {
                "chat_id": external_user_id,
                "text": message.content,
                "parse_mode": "Markdown",  # 支持Markdown格式
            }

            # 添加额外参数（如按钮）
            if message.extra:
                if 'reply_markup' in message.extra:
                    data['reply_markup'] = message.extra['reply_markup']

            # 发送请求
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()

            result = response.json()
            return result.get('ok', False)

        except Exception as e:
            print(f"发送Telegram消息失败: {str(e)}")
            return False

    def set_webhook(self, webhook_url: str) -> bool:
        """
        设置Webhook URL

        Args:
            webhook_url: Webhook完整URL

        Returns:
            是否设置成功
        """
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/setWebhook"

            data = {
                "url": webhook_url,
                "allowed_updates": ["message"],  # 只接收消息更新
            }

            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()

            result = response.json()
            return result.get('ok', False)

        except Exception as e:
            print(f"设置Telegram Webhook失败: {str(e)}")
            return False

    def delete_webhook(self) -> bool:
        """
        删除Webhook

        Returns:
            是否删除成功
        """
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/deleteWebhook"

            response = requests.post(url, timeout=10)
            response.raise_for_status()

            result = response.json()
            return result.get('ok', False)

        except Exception as e:
            print(f"删除Telegram Webhook失败: {str(e)}")
            return False

    def get_bot_info(self) -> Optional[dict]:
        """
        获取Bot信息

        Returns:
            Bot信息字典
        """
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get('ok'):
                return result.get('result')

            return None

        except Exception as e:
            print(f"获取Telegram Bot信息失败: {str(e)}")
            return None
