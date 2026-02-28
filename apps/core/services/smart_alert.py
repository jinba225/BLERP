"""
智能告警服务

功能：
- 异常检测（基于统计方法）
- 告警关联分析
- 告警风暴预防
- 智能告警路由
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
from django.core.cache import cache

from .config import MONITOR_CONFIG

logger = logging.getLogger(__name__)


class SmartAlertService:
    """
    智能告警服务
    """

    def __init__(self, redis_client=None):
        """
        初始化智能告警服务

        Args:
            redis_client: Redis客户端（可选）
        """
        self.redis_client = redis_client or cache
        self.config = MONITOR_CONFIG.get("smart_alert", {})
        self.enabled = self.config.get("enabled", True)
        self.anomaly_config = self.config.get("anomaly_detection", {})
        self.correlation_config = self.config.get("alert_correlation", {})
        self.auto_resolution_config = self.config.get("auto_resolution", {})

        logger.debug("初始化智能告警服务")

    def detect_anomalies(self, metric_name: str, values: List[float]) -> Tuple[bool, float]:
        """
        检测异常值

        Args:
            metric_name: 指标名称
            values: 指标值列表

        Returns:
            tuple: (是否异常, 异常分数)
        """
        if not self.enabled or not self.anomaly_config.get("enabled", False):
            return False, 0.0

        try:
            if len(values) < 10:  # 数据不足，无法检测
                return False, 0.0

            # 计算均值和标准差
            mean = np.mean(values)
            std = np.std(values)

            if std == 0:  # 无波动，无法检测
                return False, 0.0

            # 计算最近值的Z-score
            recent_value = values[-1]
            z_score = abs((recent_value - mean) / std)

            # 判断是否异常
            threshold = self.anomaly_config.get("threshold_factor", 3.0)
            is_anomaly = z_score > threshold

            logger.debug(f"异常检测: {metric_name} - Z-score: {z_score:.2f}, 阈值: {threshold}")

            return is_anomaly, z_score

        except Exception as e:
            logger.error(f"异常检测失败: {e}")
            return False, 0.0

    def correlate_alerts(self, alerts: List[Dict]) -> List[List[Dict]]:
        """
        关联相关告警

        Args:
            alerts: 告警列表

        Returns:
            list: 关联后的告警组
        """
        if not self.enabled or not self.correlation_config.get("enabled", False):
            return [alerts]

        try:
            time_window = self.correlation_config.get("time_window", 60)  # 时间窗口（分钟）
            correlated_groups = []
            processed = set()

            for i, alert1 in enumerate(alerts):
                if i in processed:
                    continue

                group = [alert1]
                processed.add(i)

                # 解析告警时间
                alert1_time = datetime.fromisoformat(
                    alert1.get("timestamp", datetime.now().isoformat())
                )

                for j, alert2 in enumerate(alerts):
                    if j in processed or i == j:
                        continue

                    alert2_time = datetime.fromisoformat(
                        alert2.get("timestamp", datetime.now().isoformat())
                    )
                    time_diff = abs((alert2_time - alert1_time).total_seconds() / 60)

                    # 检查时间窗口
                    if time_diff <= time_window:
                        # 检查告警类型是否相关
                        if self._are_alerts_correlated(alert1, alert2):
                            group.append(alert2)
                            processed.add(j)

            correlated_groups.append(group)
            return correlated_groups

        except Exception as e:
            logger.error(f"告警关联失败: {e}")
            return [alerts]

    def _are_alerts_correlated(self, alert1: Dict, alert2: Dict) -> bool:
        """
        判断两个告警是否相关

        Args:
            alert1: 第一个告警
            alert2: 第二个告警

        Returns:
            bool: 是否相关
        """
        # 基于告警类型的相关性规则
        correlation_rules = {
            "high_cpu_usage": ["slow_response", "high_memory_usage"],
            "high_memory_usage": ["high_cpu_usage", "slow_response"],
            "slow_response": ["high_cpu_usage", "high_memory_usage"],
            "high_error_rate": ["low_success_rate"],
            "low_success_rate": ["high_error_rate"],
        }

        alert1_type = alert1.get("alert_type")
        alert2_type = alert2.get("alert_type")

        if alert1_type in correlation_rules:
            return alert2_type in correlation_rules[alert1_type]

        return False

    def prevent_alert_storm(self, alert: Dict) -> bool:
        """
        防止告警风暴

        Args:
            alert: 告警信息

        Returns:
            bool: 是否应该抑制该告警
        """
        try:
            alert_type = alert.get("alert_type")
            platform = alert.get("platform", "system")

            # 检查最近相同类型的告警数量
            key = f"alert_storm:{alert_type}:{platform}"
            window = 300  # 5分钟窗口

            # 获取最近的告警时间
            recent_alerts = self.redis_client.lrange(key, 0, 99)  # 最近100条

            # 清理过期的告警记录
            current_time = time.time()
            valid_alerts = []
            for alert_time_str in recent_alerts:
                try:
                    alert_time = float(alert_time_str)
                    if current_time - alert_time < window:
                        valid_alerts.append(alert_time_str)
                except Exception:
                    pass

            # 保存有效的告警记录
            if valid_alerts:
                self.redis_client.delete(key)
                for alert_time_str in valid_alerts:
                    self.redis_client.lpush(key, alert_time_str)

            # 添加当前告警
            self.redis_client.lpush(key, str(current_time))
            self.redis_client.expire(key, window)

            # 检查告警频率
            if len(valid_alerts) > 5:  # 5分钟内超过5条相同告警
                logger.warning(f"抑制告警风暴: {alert_type} - {platform}")
                return True

            return False

        except Exception as e:
            logger.error(f"防止告警风暴失败: {e}")
            return False

    def route_alert(self, alert: Dict) -> List[str]:
        """
        智能告警路由

        Args:
            alert: 告警信息

        Returns:
            list: 通知渠道列表
        """
        try:
            alert_type = alert.get("alert_type")
            severity = alert.get("severity", "warning")

            # 基于告警类型和严重程度的路由规则
            routing_rules = {
                "critical": ["dingtalk", "email"],
                "warning": ["dingtalk"],
                "info": [],
            }

            # 特殊规则
            special_rules = {
                "high_disk_usage": ["dingtalk", "email"],  # 磁盘告警总是发送邮件
                "high_memory_usage": ["dingtalk", "email"],  # 内存告警总是发送邮件
            }

            if alert_type in special_rules:
                return special_rules[alert_type]

            return routing_rules.get(severity, ["dingtalk"])

        except Exception as e:
            logger.error(f"告警路由失败: {e}")
            return ["dingtalk"]

    def get_metric_history(self, metric_name: str, platform: str, minutes: int = 60) -> List[float]:
        """
        获取指标历史数据

        Args:
            metric_name: 指标名称
            platform: 平台标识
            minutes: 时间范围（分钟）

        Returns:
            list: 指标值列表
        """
        try:
            key = f"metric_history:{metric_name}:{platform}"
            history = self.redis_client.get(key)

            if history:
                data = json.loads(history)
                # 过滤时间范围内的数据
                current_time = time.time()
                cutoff_time = current_time - (minutes * 60)
                return [v for t, v in data if t >= cutoff_time]

            return []

        except Exception as e:
            logger.error(f"获取指标历史失败: {e}")
            return []

    def update_metric_history(self, metric_name: str, platform: str, value: float):
        """
        更新指标历史数据

        Args:
            metric_name: 指标名称
            platform: 平台标识
            value: 指标值
        """
        try:
            key = f"metric_history:{metric_name}:{platform}"
            history = self.redis_client.get(key)

            data = []
            if history:
                data = json.loads(history)

            # 添加新数据
            current_time = time.time()
            data.append([current_time, value])

            # 保留最近24小时的数据
            cutoff_time = current_time - (24 * 3600)
            data = [[t, v] for t, v in data if t >= cutoff_time]

            # 保存数据
            self.redis_client.setex(key, 24 * 3600, json.dumps(data))

        except Exception as e:
            logger.error(f"更新指标历史失败: {e}")

    def analyze_alert_trend(self, alert_type: str, platform: str, days: int = 7) -> Dict:
        """
        分析告警趋势

        Args:
            alert_type: 告警类型
            platform: 平台标识
            days: 分析天数

        Returns:
            dict: 趋势分析结果
        """
        try:
            key = f"alert_history:{platform}"
            history = self.redis_client.lrange(key, 0, 999)  # 最近1000条

            alerts = []
            for alert_data in history:
                try:
                    alert = json.loads(alert_data)
                    if alert.get("alert_type") == alert_type:
                        alerts.append(alert)
                except Exception:
                    pass

            # 按天统计
            daily_counts = {}
            for alert in alerts:
                timestamp = alert.get("timestamp")
                if timestamp:
                    date = timestamp.split("T")[0]
                    daily_counts[date] = daily_counts.get(date, 0) + 1

            # 计算趋势
            dates = sorted(daily_counts.keys())
            counts = [daily_counts[date] for date in dates]

            if len(counts) < 2:
                return {
                    "trend": "insufficient_data",
                    "daily_counts": daily_counts,
                    "message": "数据不足，无法分析趋势",
                }

            # 计算斜率
            x = range(len(counts))
            slope = np.polyfit(x, counts, 1)[0]

            if slope > 0.1:
                trend = "increasing"
                message = "告警数量呈上升趋势，需要关注"
            elif slope < -0.1:
                trend = "decreasing"
                message = "告警数量呈下降趋势，情况正在改善"
            else:
                trend = "stable"
                message = "告警数量稳定，保持监控"

            return {
                "trend": trend,
                "slope": slope,
                "daily_counts": daily_counts,
                "message": message,
            }

        except Exception as e:
            logger.error(f"分析告警趋势失败: {e}")
            return {"trend": "error", "message": f"分析失败: {e}"}


# 全局单例
_smart_alert_instance = None


def get_smart_alert() -> SmartAlertService:
    """
    获取智能告警服务实例（单例模式）

    Returns:
        SmartAlertService: 智能告警服务实例
    """
    global _smart_alert_instance
    if _smart_alert_instance is None:
        _smart_alert_instance = SmartAlertService()
    return _smart_alert_instance
