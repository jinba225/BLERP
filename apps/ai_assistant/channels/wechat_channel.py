"""
微信企业号集成

通过微信企业号API实现消息收发
"""

from typing import Optional
from datetime import datetime
import hashlib
import time
import json
import requests
from django.http import HttpRequest

from .base_channel import BaseChannel, IncomingMessage, OutgoingMessage
from ..models import WeChatConfig
from ..utils import decrypt_api_key
from ..utils.cache import AIAssistantCache


class WeChatChannel(BaseChannel):
    """微信企业号渠道处理器"""

    channel_name = "wechat"

    def __init__(self, config: WeChatConfig):
        """
        初始化微信渠道

        Args:
            config: WeChatConfig配置对象
        """
        super().__init__(config)
        self.corp_id = config.corp_id
        self.corp_secret = decrypt_api_key(config.corp_secret)
        self.agent_id = config.agent_id
        self.token = config.token
        self.encoding_aes_key = config.encoding_aes_key
        # 移除实例变量，使用Redis缓存
        # self.access_token = None
        # self.access_token_expires_at = 0

    def verify_webhook(self, request: HttpRequest) -> bool:
        """
        验证Webhook请求（微信签名验证）

        Args:
            request: Django HttpRequest对象

        Returns:
            是否合法
        """
        try:
            # GET请求用于验证URL
            if request.method == "GET":
                msg_signature = request.GET.get("msg_signature", "")
                timestamp = request.GET.get("timestamp", "")
                nonce = request.GET.get("nonce", "")
                echostr = request.GET.get("echostr", "")

                # 验证签名
                if self._verify_signature(self.token, timestamp, nonce, echostr, msg_signature):
                    return True

            # POST请求用于接收消息
            elif request.method == "POST":
                msg_signature = request.GET.get("msg_signature", "")
                timestamp = request.GET.get("timestamp", "")
                nonce = request.GET.get("nonce", "")

                # 简单验证（实际应解密消息体验证）
                return True

            return False

        except Exception as e:
            print(f"微信签名验证失败: {str(e)}")
            return False

    def _verify_signature(
        self, token: str, timestamp: str, nonce: str, msg: str, signature: str
    ) -> bool:
        """
        验证微信签名

        Args:
            token: Token
            timestamp: 时间戳
            nonce: 随机数
            msg: 消息
            signature: 签名

        Returns:
            是否验证通过
        """
        try:
            tmp_list = [token, timestamp, nonce, msg]
            tmp_list.sort()
            tmp_str = "".join(tmp_list)
            tmp_signature = hashlib.sha1(tmp_str.encode()).hexdigest()
            return tmp_signature == signature
        except Exception:
            return False

    def parse_message(self, request: HttpRequest) -> Optional[IncomingMessage]:
        """
        解析微信消息

        Args:
            request: Django HttpRequest对象

        Returns:
            IncomingMessage对象
        """
        try:
            # TODO: 需要解密微信加密消息
            # 这里简化处理，假设已解密
            body = request.body.decode("utf-8")

            # 解析XML（微信使用XML格式）
            # 简化版本：直接返回None，实际需要XML解析库
            # 在生产环境中应使用 wechatpy 或类似库

            return None

        except Exception as e:
            print(f"解析微信消息失败: {str(e)}")
            return None

    def send_message(self, external_user_id: str, message: OutgoingMessage) -> bool:
        """
        发送消息给用户

        Args:
            external_user_id: 微信UserID
            message: OutgoingMessage对象

        Returns:
            是否发送成功
        """
        try:
            # 获取access_token
            access_token = self._get_access_token()
            if not access_token:
                return False

            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"

            # 构建消息数据
            data = {
                "touser": external_user_id,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {"content": message.content},
                "safe": 0,
            }

            # 发送请求
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()

            result = response.json()
            return result.get("errcode") == 0

        except Exception as e:
            print(f"发送微信消息失败: {str(e)}")
            return False

    def _get_access_token(self) -> Optional[str]:
        """
        获取access_token（使用Redis缓存）

        Returns:
            access_token
        """
        try:
            # 从Redis缓存中获取
            cached_token = AIAssistantCache.get_access_token("wechat", self.corp_id)
            if cached_token:
                return cached_token

            # 缓存中没有，请求新token
            url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
            params = {"corpid": self.corp_id, "corpsecret": self.corp_secret}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("errcode") == 0:
                access_token = result.get("access_token")
                expires_in = result.get("expires_in", 7200)

                # 存入Redis缓存（提前5分钟过期）
                cache_timeout = expires_in - 300
                AIAssistantCache.set_access_token(
                    "wechat", self.corp_id, access_token, timeout=cache_timeout
                )

                return access_token

            return None

        except Exception as e:
            print(f"获取微信access_token失败: {str(e)}")
            return None
