"""
工具监控服务

提供工具使用统计、性能指标收集和执行日志记录
"""

from collections import defaultdict
from datetime import timedelta
from typing import Any, Dict, List

from django.core.cache import cache
from django.utils import timezone


class ToolMonitor:
    """
    工具监控器

    负责收集工具使用统计和性能指标
    """

    # 缓存键前缀
    CACHE_PREFIX = "erp_tool_monitor"

    def __init__(self):
        """初始化监控器"""
        self.stats = self._load_stats()

    def _load_stats(self) -> Dict[str, Any]:
        """从缓存加载统计数据"""
        cache_key = f"{self.CACHE_PREFIX}:stats"
        stats = cache.get(cache_key)

        if not stats:
            stats = {
                "executions": defaultdict(int),
                "successes": defaultdict(int),
                "failures": defaultdict(int),
                "total_time": defaultdict(float),
                "avg_time": defaultdict(float),
                "last_used": {},
                "daily_executions": defaultdict(lambda: defaultdict(int)),
                "user_stats": defaultdict(lambda: defaultdict(int)),
            }

        return stats

    def _save_stats(self):
        """保存统计数据到缓存"""
        cache_key = f"{self.CACHE_PREFIX}:stats"
        # 缓存1天
        cache.set(cache_key, self.stats, 86400)

    def record_execution(
        self,
        tool_name: str,
        user_id: int,
        success: bool,
        execution_time: float,
        metadata: Dict[str, Any] = None,
    ):
        """
        记录工具执行

        Args:
            tool_name: 工具名称
            user_id: 用户ID
            success: 是否成功
            execution_time: 执行时间（秒）
            metadata: 额外元数据
        """
        today = timezone.now().strftime("%Y-%m-%d")

        # 更新执行统计
        self.stats["executions"][tool_name] += 1

        if success:
            self.stats["successes"][tool_name] += 1
        else:
            self.stats["failures"][tool_name] += 1

        # 更新执行时间
        self.stats["total_time"][tool_name] += execution_time
        exec_count = self.stats["executions"][tool_name]
        self.stats["avg_time"][tool_name] = self.stats["total_time"][tool_name] / exec_count

        # 更新最后使用时间
        self.stats["last_used"][tool_name] = timezone.now().isoformat()

        # 更新每日执行统计
        self.stats["daily_executions"][today][tool_name] += 1

        # 更新用户统计
        self.stats["user_stats"][user_id][tool_name] += 1

        # 保存到缓存
        self._save_stats()

        # 同时记录到日志（如果配置了日志模型）
        self._log_execution(tool_name, user_id, success, execution_time, metadata)

    def _log_execution(
        self,
        tool_name: str,
        user_id: int,
        success: bool,
        execution_time: float,
        metadata: Dict[str, Any] = None,
    ):
        """记录执行到日志（预留数据库日志接口）"""
        # TODO: 如果需要持久化日志，可以在这里写入数据库
        # 例如创建ToolExecutionLog模型

    def get_tool_stats(self, tool_name: str) -> Dict[str, Any]:
        """
        获取指定工具的统计信息

        Args:
            tool_name: 工具名称

        Returns:
            统计信息字典
        """
        executions = self.stats["executions"].get(tool_name, 0)
        successes = self.stats["successes"].get(tool_name, 0)
        failures = self.stats["failures"].get(tool_name, 0)
        avg_time = self.stats["avg_time"].get(tool_name, 0.0)
        last_used = self.stats["last_used"].get(tool_name, "")

        # 计算成功率
        success_rate = 0.0
        if executions > 0:
            success_rate = (successes / executions) * 100

        return {
            "tool_name": tool_name,
            "total_executions": executions,
            "success_count": successes,
            "failure_count": failures,
            "success_rate": round(success_rate, 2),
            "avg_execution_time": round(avg_time, 3),
            "last_used": last_used,
        }

    def get_all_tools_stats(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的统计信息

        Returns:
            工具统计信息列表
        """
        all_tools = set(self.stats["executions"].keys())

        stats_list = []
        for tool_name in all_tools:
            stats_list.append(self.get_tool_stats(tool_name))

        # 按执行次数排序
        stats_list.sort(key=lambda x: x["total_executions"], reverse=True)

        return stats_list

    def get_top_tools(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取使用最频繁的工具

        Args:
            limit: 返回数量限制

        Returns:
            工具统计列表
        """
        all_stats = self.get_all_tools_stats()
        return all_stats[:limit]

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户使用统计

        Args:
            user_id: 用户ID

        Returns:
            用户统计信息
        """
        user_tools = self.stats["user_stats"].get(user_id, {})

        total_executions = sum(user_tools.values())

        # 找出用户最常用的工具
        top_tools = sorted(user_tools.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "user_id": user_id,
            "total_executions": total_executions,
            "tools_used": len(user_tools),
            "top_tools": [{"tool_name": tool, "count": count} for tool, count in top_tools],
        }

    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取每日统计

        Args:
            days: 天数

        Returns:
            每日统计列表
        """
        daily_stats = []
        today = timezone.now()

        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")

            day_executions = self.stats["daily_executions"].get(date_str, {})
            total_executions = sum(day_executions.values())

            daily_stats.append(
                {
                    "date": date_str,
                    "total_executions": total_executions,
                    "tools_used": len(day_executions),
                    "top_tools": [
                        {"tool_name": tool, "count": count}
                        for tool, count in sorted(
                            day_executions.items(), key=lambda x: x[1], reverse=True
                        )[:3]
                    ],
                }
            )

        return daily_stats

    def get_performance_report(self) -> Dict[str, Any]:
        """
        获取性能报告

        Returns:
            性能报告数据
        """
        all_stats = self.get_all_tools_stats()

        if not all_stats:
            return {
                "total_tools": 0,
                "total_executions": 0,
                "avg_success_rate": 0.0,
                "avg_execution_time": 0.0,
                "slowest_tools": [],
                "fastest_tools": [],
            }

        total_executions = sum(s["total_executions"] for s in all_stats)

        # 计算平均成功率
        weighted_success_rate = sum(s["success_rate"] * s["total_executions"] for s in all_stats)
        avg_success_rate = weighted_success_rate / total_executions if total_executions > 0 else 0.0

        # 计算平均执行时间
        avg_execution_time = sum(s["avg_execution_time"] for s in all_stats) / len(all_stats)

        # 最慢的工具
        slowest_tools = sorted(all_stats, key=lambda x: x["avg_execution_time"], reverse=True)[:5]

        # 最快的工具
        fastest_tools = sorted(all_stats, key=lambda x: x["avg_execution_time"])[:5]

        return {
            "total_tools": len(all_stats),
            "total_executions": total_executions,
            "avg_success_rate": round(avg_success_rate, 2),
            "avg_execution_time": round(avg_execution_time, 3),
            "slowest_tools": slowest_tools,
            "fastest_tools": fastest_tools,
            "most_used_tools": self.get_top_tools(5),
        }

    def get_category_stats(self) -> Dict[str, Any]:
        """
        获取按分类的统计

        Returns:
            分类统计信息
        """
        # TODO: 从工具注册表获取分类信息
        # 这里提供一个简化版本
        return {}

    def clear_stats(self, tool_name: str = None):
        """
        清除统计数据

        Args:
            tool_name: 工具名称，如果为None则清除所有
        """
        if tool_name:
            # 清除指定工具的统计
            self.stats["executions"].pop(tool_name, None)
            self.stats["successes"].pop(tool_name, None)
            self.stats["failures"].pop(tool_name, None)
            self.stats["total_time"].pop(tool_name, None)
            self.stats["avg_time"].pop(tool_name, None)
            self.stats["last_used"].pop(tool_name, None)
        else:
            # 清除所有统计
            self.stats = {
                "executions": defaultdict(int),
                "successes": defaultdict(int),
                "failures": defaultdict(int),
                "total_time": defaultdict(float),
                "avg_time": defaultdict(float),
                "last_used": {},
                "daily_executions": defaultdict(lambda: defaultdict(int)),
                "user_stats": defaultdict(lambda: defaultdict(int)),
            }

        self._save_stats()

    def export_stats(self, format: str = "dict") -> Any:
        """
        导出统计数据

        Args:
            format: 导出格式（dict, json）

        Returns:
            导出的数据
        """
        if format == "dict":
            return {
                "tools": self.get_all_tools_stats(),
                "performance": self.get_performance_report(),
                "daily": self.get_daily_stats(30),
            }
        elif format == "json":
            import json

            return json.dumps(self.export_stats("dict"), ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的导出格式: {format}")


class ToolExecutionTimer:
    """
    工具执行计时器

    上下文管理器，用于自动记录工具执行时间
    """

    def __init__(self, tool_name: str, user_id: int, monitor: ToolMonitor = None):
        """
        初始化计时器

        Args:
            tool_name: 工具名称
            user_id: 用户ID
            monitor: 监控器实例，如果为None则创建新实例
        """
        self.tool_name = tool_name
        self.user_id = user_id
        self.monitor = monitor or ToolMonitor()
        self.start_time = None
        self.success = False

    def __enter__(self):
        """进入上下文"""
        self.start_time = timezone.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.start_time:
            end_time = timezone.now()
            execution_time = (end_time - self.start_time).total_seconds()

            # 如果没有异常，认为执行成功
            self.success = exc_type is None

            # 记录执行
            self.monitor.record_execution(
                self.tool_name, self.user_id, self.success, execution_time
            )

        return False  # 不抑制异常

    def mark_success(self):
        """标记执行成功"""
        self.success = True

    def mark_failure(self):
        """标记执行失败"""
        self.success = False


class PerformanceAlert:
    """
    性能告警

    检测工具性能问题并发送告警
    """

    # 性能阈值（秒）
    SLOW_EXECUTION_THRESHOLD = 5.0
    VERY_SLOW_EXECUTION_THRESHOLD = 10.0

    # 成功率阈值（%）
    LOW_SUCCESS_RATE_THRESHOLD = 80.0

    @staticmethod
    def check_performance(monitor: ToolMonitor) -> List[Dict[str, Any]]:
        """
        检查性能问题

        Args:
            monitor: 监控器实例

        Returns:
            告警列表
        """
        alerts = []
        all_stats = monitor.get_all_tools_stats()

        for stats in all_stats:
            tool_name = stats["tool_name"]

            # 检查执行时间
            if stats["avg_execution_time"] > PerformanceAlert.VERY_SLOW_EXECUTION_THRESHOLD:
                alerts.append(
                    {
                        "type": "critical",
                        "tool": tool_name,
                        "message": f"工具 {tool_name} 平均执行时间过长",
                        "value": stats["avg_execution_time"],
                        "threshold": PerformanceAlert.VERY_SLOW_EXECUTION_THRESHOLD,
                    }
                )
            elif stats["avg_execution_time"] > PerformanceAlert.SLOW_EXECUTION_THRESHOLD:
                alerts.append(
                    {
                        "type": "warning",
                        "tool": tool_name,
                        "message": f"工具 {tool_name} 执行时间偏长",
                        "value": stats["avg_execution_time"],
                        "threshold": PerformanceAlert.SLOW_EXECUTION_THRESHOLD,
                    }
                )

            # 检查成功率
            if stats["success_rate"] < PerformanceAlert.LOW_SUCCESS_RATE_THRESHOLD:
                alerts.append(
                    {
                        "type": "warning",
                        "tool": tool_name,
                        "message": f"工具 {tool_name} 成功率偏低",
                        "value": stats["success_rate"],
                        "threshold": PerformanceAlert.LOW_SUCCESS_RATE_THRESHOLD,
                    }
                )

        return alerts
