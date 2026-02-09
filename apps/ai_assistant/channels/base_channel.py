"""
渠道集成基类

提供统一的消息处理接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model

User = get_user_model()


@dataclass
class IncomingMessage:
    """统一的入站消息格式"""

    # 消息基本信息
    message_id: str  # 消息ID
    channel: str  # 渠道（wechat/dingtalk/telegram）
    external_user_id: str  # 外部用户ID
    content: str  # 消息内容

    # 消息元数据
    timestamp: datetime  # 消息时间
    message_type: str = "text"  # 消息类型（text/image/voice等）
    raw_data: Optional[Dict[str, Any]] = None  # 原始数据

    # 会话信息
    conversation_id: Optional[str] = None  # 会话ID

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "channel": self.channel,
            "external_user_id": self.external_user_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_type": self.message_type,
            "conversation_id": self.conversation_id,
        }


@dataclass
class OutgoingMessage:
    """统一的出站消息格式"""

    content: str  # 消息内容
    message_type: str = "text"  # 消息类型
    extra: Optional[Dict[str, Any]] = None  # 额外数据（如按钮、卡片等）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "content": self.content,
            "message_type": self.message_type,
        }
        if self.extra:
            result["extra"] = self.extra
        return result


class BaseChannel(ABC):
    """
    渠道集成抽象基类

    所有渠道集成都应继承此类
    """

    # 渠道标识（子类必须定义）
    channel_name: str = ""

    def __init__(self, config: Any = None):
        """
        初始化渠道

        Args:
            config: 渠道配置对象（WeChatConfig/DingTalkConfig等）
        """
        self.config = config
        if not self.channel_name:
            raise ValueError(f"{self.__class__.__name__}: 必须定义渠道名称(channel_name)")

    @abstractmethod
    def verify_webhook(self, request) -> bool:
        """
        验证Webhook请求的合法性

        Args:
            request: Django HttpRequest对象

        Returns:
            是否合法
        """
        pass

    @abstractmethod
    def parse_message(self, request) -> Optional[IncomingMessage]:
        """
        解析入站消息

        Args:
            request: Django HttpRequest对象

        Returns:
            IncomingMessage对象，如果无法解析则返回None
        """
        pass

    @abstractmethod
    def send_message(self, external_user_id: str, message: OutgoingMessage) -> bool:
        """
        发送消息给用户

        Args:
            external_user_id: 外部用户ID
            message: OutgoingMessage对象

        Returns:
            是否发送成功
        """
        pass

    def get_or_create_user_mapping(self, external_user_id: str) -> Optional[User]:
        """
        获取或创建用户映射

        Args:
            external_user_id: 外部用户ID

        Returns:
            系统User对象，如果无法映射则返回None
        """
        from ..models import ChannelUserMapping

        try:
            # 查找现有映射
            mapping = ChannelUserMapping.objects.filter(
                channel=self.channel_name,
                external_user_id=external_user_id,
                is_active=True,
                is_deleted=False,
            ).first()

            if mapping:
                return mapping.user

            # 如果没有映射，返回None（需要管理员手动绑定）
            return None

        except Exception as e:
            print(f"获取用户映射失败: {str(e)}")
            return None

    def __str__(self):
        return f"{self.channel_name.upper()} Channel"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.channel_name}>"
