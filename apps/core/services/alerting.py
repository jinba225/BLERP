"""
告警服务 - 规则引擎和通知服务
支持钉钉、邮件通知，告警收敛，规则引擎
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

from celery import shared_task
from decouple import config
from django.core.cache import cache

from .config import ALERT_RULES, EMAIL_ALERT_CONFIG
from .monitor import get_monitor
from .smart_alert import get_smart_alert

logger = logging.getLogger(__name__)


class AlertingService:
    """
    告警服务

    功能：
    - 告警规则引擎
    - 钉钉/邮件通知
    - 告警收敛（防止告警风暴）
    - 告警历史记录

    告警收敛策略：
    - 冷却期：同一告警在冷却期内只触发一次
    - 聚合：相似告警聚合为一条
    """

    def __init__(self, redis_client=None):
        """
        初始化告警服务

        Args:
            redis_client: Redis客户端（可选）
        """
        self.redis_client = redis_client or cache
        self.monitor = get_monitor()
        self.smart_alert = get_smart_alert()
        self.rules = ALERT_RULES

        # 钉钉配置
        self.dingtalk_webhook = config("DINGTALK_WEBHOOK_URL", default=None)
        self.dingtalk_secret = config("DINGTALK_SECRET", default=None)

        # 邮件配置
        self.email_enabled = EMAIL_ALERT_CONFIG["enabled"]
        self.email_recipients = EMAIL_ALERT_CONFIG["recipients"]

        logger.debug("初始化告警服务")

    def check_and_alert(self):
        """
        检查告警规则并触发告警（同步版本）

        Example:
            >>> alerting = AlertingService()
            >>> alerting.check_and_alert()
        """
        try:
            # 获取当前告警状态
            alerts = self.monitor.get_alert_status()

            # 处理每个告警
            for alert in alerts:
                self._handle_alert(alert)

        except Exception as e:
            logger.error(f"检查告警失败: {e}")

    async def check_and_alert_async(self):
        """
        检查告警规则并触发告警（异步版本）

        Example:
            >>> alerting = AlertingService()
            >>> await alerting.check_and_alert_async()
        """
        import asyncio

        await asyncio.to_thread(self.check_and_alert)

    def _handle_alert(self, alert: Dict):
        """
        处理单个告警

        Args:
            alert: 告警信息
        """
        try:
            # 防止告警风暴
            if self.smart_alert.prevent_alert_storm(alert):
                return

            # 查找匹配的告警规则
            rule = self._find_rule(alert["alert_type"])

            if not rule or not rule.get("enabled"):
                return

            # 检查冷却期
            if self._is_in_cooldown(alert["alert_type"], alert["platform"]):
                logger.debug(f"告警在冷却期内: {alert['alert_type']} - {alert['platform']}")
                return

            # 智能告警路由
            channels = self.smart_alert.route_alert(alert)
            if channels:
                rule["channels"] = channels

            # 触发告警
            self._trigger_alert(alert, rule)

        except Exception as e:
            logger.error(f"处理告警失败: {e}")

    def _find_rule(self, alert_type: str) -> Optional[Dict]:
        """
        查找告警规则

        Args:
            alert_type: 告警类型

        Returns:
            dict: 告警规则
        """
        return self.rules.get(alert_type)

    def _is_in_cooldown(self, alert_type: str, platform: str) -> bool:
        """
        检查是否在冷却期内

        Args:
            alert_type: 告警类型
            platform: 平台标识

        Returns:
            bool: 是否在冷却期内
        """
        rule = self._find_rule(alert_type)
        if not rule:
            return False

        cooldown = rule.get("cooldown", 0)
        if cooldown == 0:
            return False

        key = f"alert_cooldown:{alert_type}:{platform}"

        # 检查上次告警时间
        last_alert_time = self.redis_client.get(key)

        if last_alert_time is not None:
            # 计算距离上次告警的时间
            elapsed = time.time() - float(last_alert_time)
            if elapsed < cooldown:
                return True

        # 更新告警时间
        self.redis_client.setex(key, cooldown, str(time.time()))

        return False

    def _trigger_alert(self, alert: Dict, rule: Dict):
        """
        触发告警

        Args:
            alert: 告警信息
            rule: 告警规则
        """
        try:
            # 记录告警历史
            self._record_alert_history(alert)

            # 根据配置的渠道发送通知
            channels = rule.get("channels", [])

            for channel in channels:
                if channel == "dingtalk":
                    self._send_dingtalk_alert(alert, rule)
                elif channel == "email":
                    self._send_email_alert(alert, rule)

            logger.warning(
                f"触发告警: {alert['alert_type']} - {alert['platform']}, " f"严重程度: {rule['severity']}"
            )

        except Exception as e:
            logger.error(f"触发告警失败: {e}")

    def _record_alert_history(self, alert: Dict):
        """
        记录告警历史

        Args:
            alert: 告警信息
        """
        try:
            key = f"alert_history:{alert['platform']}"
            alert_data = {
                **alert,
                "timestamp": datetime.now().isoformat(),
            }

            # 添加到列表（保留最近100条）
            self.redis_client.lpush(key, json.dumps(alert_data))
            self.redis_client.ltrim(key, 0, 99)
            self.redis_client.expire(key, 7 * 24 * 3600)  # 保留7天

        except Exception as e:
            logger.error(f"记录告警历史失败: {e}")

    def _send_dingtalk_alert(self, alert: Dict, rule: Dict):
        """
        发送钉钉告警

        Args:
            alert: 告警信息
            rule: 告警规则
        """
        if not self.dingtalk_webhook:
            logger.warning("钉钉Webhook未配置，跳过钉钉告警")
            return

        try:
            import base64
            import hashlib
            import hmac
            import urllib.parse

            import requests

            # 构造消息
            title = f"【{rule['severity'].upper()}】{rule['name']}"
            text = """
## {title}

**平台**: {alert['platform']}
**告警类型**: {alert['alert_type']}
**当前值**: {alert['value']}
**阈值**: {alert['threshold']}
**时间**: {alert['timestamp']}

**规则**: {rule.get('condition', '')}

请及时处理！
""".strip()

            # 构造钉钉消息
            webhook_url = self.dingtalk_webhook

            # 如果配置了加签密钥，计算签名
            if self.dingtalk_secret:
                timestamp = str(round(time.time() * 1000))
                secret_enc = self.dingtalk_secret.encode("utf-8")
                string_to_sign = f"{timestamp}\n{self.dingtalk_secret}"
                string_to_sign_enc = string_to_sign.encode("utf-8")

                hmac_code = hmac.new(
                    secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
                ).digest()

                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
                webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": text,
                },
            }

            # 发送请求
            response = requests.post(webhook_url, json=data, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    logger.info(f"钉钉告警发送成功: {alert['alert_type']}")
                else:
                    logger.error(f"钉钉告警发送失败: {result}")
            else:
                logger.error(f"钉钉告警发送失败: {response.status_code}")

        except Exception as e:
            logger.error(f"发送钉钉告警异常: {e}")

    def _send_email_alert(self, alert: Dict, rule: Dict):
        """
        发送邮件告警

        Args:
            alert: 告警信息
            rule: 告警规则
        """
        if not self.email_enabled or not self.email_recipients:
            logger.warning("邮件告警未配置或无接收人，跳过邮件告警")
            return

        try:
            from django.conf import settings
            from django.core.mail import send_mail

            # 构造邮件
            subject = f"{EMAIL_ALERT_CONFIG['subject_prefix']}{rule['name']} - {alert['platform']}"
            message = """
平台: {alert['platform']}
告警类型: {alert['alert_type']}
严重程度: {rule['severity']}

当前值: {alert['value']}
阈值: {alert['threshold']}

规则: {rule.get('condition', '')}

时间: {alert['timestamp']}

请及时处理！
""".strip()

            # 发送邮件
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=self.email_recipients,
                fail_silently=False,
            )

            logger.info(f"邮件告警发送成功: {alert['alert_type']}")

        except Exception as e:
            logger.error(f"发送邮件告警异常: {e}")

    def get_alert_history(self, platform: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        获取告警历史

        Args:
            platform: 平台标识（None表示所有平台）
            limit: 返回数量

        Returns:
            list: 告警历史列表

        Example:
            >>> alerting = AlertingService()
            >>> history = alerting.get_alert_history('taobao', limit=10)
        """
        try:
            if platform:
                key = f"alert_history:{platform}"
                keys = [key]
            else:
                pattern = "alert_history:*"
                keys = self._redis_keys(pattern)

            # 获取所有告警历史
            all_alerts = []
            for key in keys:
                alerts_data = self.redis_client.lrange(key, 0, limit - 1)
                for data in alerts_data:
                    try:
                        alert = json.loads(data)
                        all_alerts.append(alert)
                    except BaseException:
                        pass

            # 按时间排序
            all_alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return all_alerts[:limit]

        except Exception as e:
            logger.error(f"获取告警历史失败: {e}")
            return []

    def _redis_keys(self, pattern: str) -> List[str]:
        """
        查询匹配的Redis键

        Args:
            pattern: 键模式

        Returns:
            list: 键列表
        """
        try:
            keys = []
            for key in self.redis_client.keys(pattern):
                keys.append(key.decode() if isinstance(key, bytes) else key)
            return keys
        except Exception as e:
            logger.error(f"查询Redis键失败: {e}")
            return []


# 全局单例
_alerting_instance = None


def get_alerting() -> AlertingService:
    """
    获取告警服务实例（单例模式）

    Returns:
        AlertingService: 告警服务实例

    Example:
        >>> alerting = get_alerting()
        >>> alerting.check_and_alert()
    """
    global _alerting_instance
    if _alerting_instance is None:
        _alerting_instance = AlertingService()
    return _alerting_instance


# Celery定时任务


@shared_task
def check_alerts_task():
    """
    Celery定时任务：检查并触发告警

    配置示例：
    CELERY_BEAT_SCHEDULE = {
        'check-alerts': {
            'task': 'core.services.alerting.check_alerts_task',
            'schedule': crontab(minute='*/1'),  # 每1分钟检查一次
        },
    }
    """
    logger.info("开始执行告警检查任务")

    try:
        alerting = get_alerting()
        alerting.check_and_alert()

        logger.info("告警检查任务完成")

    except Exception as e:
        logger.error(f"告警检查任务失败: {e}")
