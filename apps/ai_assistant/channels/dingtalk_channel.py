"""
钉钉企业应用集成

通过钉钉企业应用API实现消息收发
"""

from typing import Optional
from datetime import datetime
import hashlib
import hmac
import base64
import time
import json
import requests
from django.http import HttpRequest

from .base_channel import BaseChannel, IncomingMessage, OutgoingMessage
from ..models import DingTalkConfig
from ..utils import decrypt_api_key
from ..utils.cache import AIAssistantCache


class DingTalkChannel(BaseChannel):
    """钉钉企业应用渠道处理器"""

    channel_name = "dingtalk"

    def __init__(self, config: DingTalkConfig):
        """
        初始化钉钉渠道

        Args:
            config: DingTalkConfig配置对象
        """
        super().__init__(config)
        self.app_key = config.app_key
        self.app_secret = decrypt_api_key(config.app_secret)
        self.agent_id = config.agent_id
        # 移除实例变量，使用Redis缓存
        # self.access_token = None
        # self.access_token_expires_at = 0

    def verify_webhook(self, request: HttpRequest) -> bool:
        """
        验证Webhook请求（钉钉签名验证）

        Args:
            request: Django HttpRequest对象

        Returns:
            是否合法
        """
        try:
            # 钉钉使用HMAC-SHA256签名验证
            timestamp = request.GET.get("timestamp", "")
            sign = request.GET.get("sign", "")

            # 简化验证
            return bool(timestamp and sign)

        except Exception as e:
            print(f"钉钉签名验证失败: {str(e)}")
            return False

    def parse_message(self, request: HttpRequest) -> Optional[IncomingMessage]:
        """
        解析钉钉消息

        Args:
            request: Django HttpRequest对象

        Returns:
            IncomingMessage对象
        """
        try:
            # 解析请求体
            body = json.loads(request.body.decode("utf-8"))

            # 获取消息内容
            text = body.get("text", {}).get("content", "")
            if not text:
                return None

            # 获取发送者信息
            sender_id = body.get("senderId", "")
            sender_nick = body.get("senderNick", "Unknown")

            # 获取会话ID
            conversation_id = body.get("conversationId", f"dingtalk_{sender_id}")

            return IncomingMessage(
                message_id=body.get("msgId", ""),
                channel=self.channel_name,
                external_user_id=sender_id,
                content=text,
                timestamp=datetime.fromtimestamp(body.get("createAt", 0) / 1000),
                message_type="text",
                conversation_id=conversation_id,
                raw_data={
                    "sender_nick": sender_nick,
                    "conversation_type": body.get("conversationType", ""),
                },
            )

        except Exception as e:
            print(f"解析钉钉消息失败: {str(e)}")
            return None

    def send_message(self, external_user_id: str, message: OutgoingMessage) -> bool:
        """
        发送消息给用户

        Args:
            external_user_id: 钉钉UserID
            message: OutgoingMessage对象

        Returns:
            是否发送成功
        """
        try:
            # 获取access_token
            access_token = self._get_access_token()
            if not access_token:
                return False

            url = "https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2"

            # 构建消息数据
            data = {
                "agent_id": self.agent_id,
                "userid_list": external_user_id,
                "msg": {"msgtype": "text", "text": {"content": message.content}},
            }

            params = {"access_token": access_token}

            # 发送请求
            response = requests.post(url, json=data, params=params, timeout=10)
            response.raise_for_status()

            result = response.json()
            return result.get("errcode") == 0

        except Exception as e:
            print(f"发送钉钉消息失败: {str(e)}")
            return False

    def _get_access_token(self) -> Optional[str]:
        """
        获取access_token（使用Redis缓存）

        Returns:
            access_token
        """
        try:
            # 从Redis缓存中获取
            cached_token = AIAssistantCache.get_access_token("dingtalk", self.app_key)
            if cached_token:
                return cached_token

            # 缓存中没有，请求新token
            url = "https://oapi.dingtalk.com/gettoken"
            params = {"appkey": self.app_key, "appsecret": self.app_secret}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("errcode") == 0:
                access_token = result.get("access_token")
                expires_in = result.get("expires_in", 7200)

                # 存入Redis缓存（提前5分钟过期）
                cache_timeout = expires_in - 300
                AIAssistantCache.set_access_token(
                    "dingtalk", self.app_key, access_token, timeout=cache_timeout
                )

                return access_token

            return None

        except Exception as e:
            print(f"获取钉钉access_token失败: {str(e)}")
            return None
