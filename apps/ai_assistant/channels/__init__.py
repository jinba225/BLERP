"""
渠道集成模块

提供微信、钉钉、Telegram等渠道的统一集成接口
"""

from .base_channel import BaseChannel, IncomingMessage, OutgoingMessage
from .channel_adapter import ChannelAdapter
from .dingtalk_channel import DingTalkChannel
from .telegram_channel import TelegramChannel
from .wechat_channel import WeChatChannel

__all__ = [
    "BaseChannel",
    "IncomingMessage",
    "OutgoingMessage",
    "ChannelAdapter",
    "WeChatChannel",
    "DingTalkChannel",
    "TelegramChannel",
]
