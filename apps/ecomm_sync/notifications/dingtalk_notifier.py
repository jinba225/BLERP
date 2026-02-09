"""钉钉通知"""
import logging
import json
import hmac
import hashlib
import time
from typing import List


logger = logging.getLogger(__name__)


class DingTalkNotifier:
    """钉钉通知器"""

    def __init__(self):
        self.webhook_url = ""
        self.secret = ""
        self._init_config()

    def _init_config(self):
        """初始化配置"""
        from django.conf import settings

        self.webhook_url = getattr(settings, "ECOMM_DINGTALK_WEBHOOK", "")
        self.secret = getattr(settings, "ECOMM_DINGTALK_SECRET", "")

        if not self.webhook_url:
            logger.warning("未配置钉钉webhook")

        self._test_connection()

    def _generate_sign(self) -> str:
        """生成签名（钉钉加签）"""
        if not self.secret:
            return ""

        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}"

        sign = hmac.new(
            self.secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return sign

    def _send_webhook(self, content: dict) -> bool:
        """发送钉webhook"""
        if not self.webhook_url:
            logger.warning("未配置钉钉webhook")
            return False

        try:
            import requests

            sign = self._generate_sign()

            data = {
                "msgtype": "markdown",
                "markdown": content.get("text", ""),
                "at": content.get("at", ""),
            }

            response = requests.post(self.webhook_url, json=data, params={"sign": sign}, timeout=10)
            response.raise_for_status()

            if response.status_code == 200:
                logger.info("钉钉通知已发送")
                return True
            else:
                logger.warning(f"钉钉webhook失败: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"钉钉通知失败: {e}")
            return False

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            import requests

            response = self._send_webhook({"text": "这是一条测试消息"})

            return response.status_code == 200

        except Exception as e:
            logger.error(f"钉钉连接测试失败: {e}")
            return False

    def send_sync_success(self, count: int):
        """发送同步成功通知"""
        content = {
            "text": f"## 电商数据同步完成\n\n**同步结果：**\n\n"
            + f"- 商品总数：{count}\n"
            + f"- 状态：成功\n"
            + f'- 时间：{time.strftime("%Y-%m-%d %H:%M:%S")}',
            "at": int(time.time() * 1000),
        }

        return self._send_webhook(content)

    def send_sync_failure(self, error: str, platform: str = ""):
        """发送同步失败通知"""
        content = {
            "text": f"## 电商数据同步失败\n\n"
            + f"**平台：**{platform}\n\n"
            + f"**错误：**{error}\n\n"
            + f'- 时间：{time.strftime("%Y-%m-%d %H:%M:%S")}',
            "at": int(time.time() * 1000),
        }

        return self._send_webhook(content)

    def send_price_change_notification(self, changes: List[dict], summary: dict):
        """发送价格变更通知"""
        if not changes:
            return None

        count = len(changes)
        total_change = sum(c["change_percent"] for c in changes)
        avg_change = total_change / count if count > 0 else 0

        content = {
            "text": f"## 价格变更通知（{count}个商品）\n\n"
            + f"**平均涨幅：**{avg_change:.2f}%\n"
            + f'**最大涨幅：**{max(c["change_percent"] for c in changes):.2f}%\n\n'
            + f"**详情：**\n\n",
            "at": int(time.time() * 1000),
        }

        for change in changes[:5]:
            product = change["product"]
            content["text"] += f"### {product.name}\n\n"
            content["text"] += f"编码：{product.code}\n"
            content["text"] += f'原价：¥{change["old_price"]}\n'
            content["text"] += f'现价：¥{change["new_price"]}\n'
            content["text"] += f'涨幅：{change["change_percent"]}%\n\n'

        content["text"] += f'\n时间：{time.strftime("%Y-%m-%d %H:%M:%S")}\n'
        content["at"] = int(time.time() * 1000)

        return self._send_webhook(content)

    def send_error_notification(self, error: str, context: dict = None):
        """发送错误通知"""
        content = {
            "text": f"## 电商同步系统错误\n\n"
            + f'**错误类型：**{context.get("error_type", "未知")}\n\n'
            + f"**错误信息：**{error}\n\n"
            + f"**上下文：**{context}\n\n"
            + f'- 时间：{time.strftime("%Y-%m-%d %H:%M:%S")}',
            "at": int(time.time() * 1000),
        }

        return self._send_webhook(content)
