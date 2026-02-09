"""
自然语言生成服务

提供智能响应生成、摘要生成和报表格式化功能
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional


class NLGGenerator:
    """
    自然语言生成器

    负责将工具执行结果转换为自然语言响应
    """

    def __init__(self, user=None):
        """
        初始化NLG生成器

        Args:
            user: 当前用户（用于个性化响应）
        """
        self.user = user

    def generate_response(
        self, tool_result: Dict[str, Any], tool_name: str = "", verbose: bool = True
    ) -> str:
        """
        生成自然语言响应

        Args:
            tool_result: 工具执行结果
            tool_name: 工具名称
            verbose: 是否详细输出

        Returns:
            自然语言响应字符串
        """
        success = tool_result.get("success", False)
        message = tool_result.get("message", "")
        data = tool_result.get("data", {})
        error = tool_result.get("error", "")

        if not success:
            # 生成错误响应
            return self._format_error_response(error, tool_name)

        # 生成成功响应
        if verbose and data:
            return self._format_detailed_response(message, data, tool_name)
        else:
            return message

    def _format_error_response(self, error: str, tool_name: str) -> str:
        """格式化错误响应"""
        if tool_name:
            return f"❌ 执行 {tool_name} 失败：{error}"
        return f"❌ 操作失败：{error}"

    def _format_detailed_response(self, message: str, data: Dict[str, Any], tool_name: str) -> str:
        """格式化详细响应"""
        response_parts = [message]

        # 根据数据类型添加详细信息
        if "items" in data or "results" in data:
            items = data.get("items") or data.get("results", [])
            if items and isinstance(items, list):
                response_parts.append(self._format_list_items(items))

        if "total_count" in data:
            response_parts.append(f"📊 总计：{data['total_count']} 项")

        if "summary" in data:
            response_parts.append(f"📝 摘要：{data['summary']}")

        # 添加数据摘要
        if data and isinstance(data, dict):
            summary = self._generate_data_summary(data)
            if summary:
                response_parts.append(summary)

        return "\n".join(response_parts)

    def _format_list_items(self, items: List[Dict[str, Any]]) -> str:
        """格式化列表项"""
        if not items:
            return "📋 暂无数据"

        # 限制显示数量
        display_items = items[:5]
        formatted_lines = []

        for i, item in enumerate(display_items, 1):
            line = f"{i}. {self._format_item(item)}"
            formatted_lines.append(line)

        if len(items) > 5:
            formatted_lines.append(f"... 还有 {len(items) - 5} 项")

        return "\n".join(formatted_lines)

    def _format_item(self, item: Dict[str, Any]) -> str:
        """格式化单个项"""
        # 优先显示关键字段
        priority_fields = [
            "order_number",
            "delivery_number",
            "receipt_number",
            "expense_number",
            "journal_number",
            "name",
            "code",
        ]

        for field in priority_fields:
            if field in item:
                value = item[field]
                # 添加状态信息
                if "status" in item:
                    return f"{value} ({item['status']})"
                return str(value)

        # 如果没有优先字段，返回第一个值
        if item:
            first_value = next(iter(item.values()))
            return str(first_value)

        return "项目"

    def _generate_data_summary(self, data: Dict[str, Any]) -> Optional[str]:
        """生成数据摘要"""
        summary_parts = []

        # 提取关键指标
        if "total_amount" in data:
            amount = data["total_amount"]
            if isinstance(amount, (int, float, Decimal)):
                summary_parts.append(f"💰 总金额：¥{amount:,.2f}")

        if "items_count" in data:
            summary_parts.append(f"📦 项目数：{data['items_count']}")

        if "pending_count" in data:
            summary_parts.append(f"⏳ 待处理：{data['pending_count']}")

        if "approved_count" in data:
            summary_parts.append(f"✅ 已批准：{data['approved_count']}")

        if "rejected_count" in data:
            summary_parts.append(f"❌ 已拒绝：{data['rejected_count']}")

        return " | ".join(summary_parts) if summary_parts else None

    def generate_summary(self, data: List[Dict[str, Any]], summary_type: str = "default") -> str:
        """
        生成数据摘要

        Args:
            data: 数据列表
            summary_type: 摘要类型（default, financial, statistical）

        Returns:
            摘要文本
        """
        if not data:
            return "暂无数据"

        if summary_type == "financial":
            return self._generate_financial_summary(data)
        elif summary_type == "statistical":
            return self._generate_statistical_summary(data)
        else:
            return self._generate_default_summary(data)

    def _generate_default_summary(self, data: List[Dict[str, Any]]) -> str:
        """生成默认摘要"""
        count = len(data)
        return f"共 {count} 条记录"

    def _generate_financial_summary(self, data: List[Dict[str, Any]]) -> str:
        """生成财务摘要"""
        total_amount = Decimal(0)

        for item in data:
            amount = item.get("amount") or item.get("total_amount") or 0
            if isinstance(amount, str):
                amount = Decimal(amount.replace(",", "").replace("¥", ""))
            total_amount += Decimal(amount)

        return f"共 {len(data)} 条记录，总金额 ¥{total_amount:,.2f}"

    def _generate_statistical_summary(self, data: List[Dict[str, Any]]) -> str:
        """生成统计摘要"""
        count = len(data)

        # 按状态统计
        status_count = {}
        for item in data:
            status = item.get("status", "unknown")
            status_count[status] = status_count.get(status, 0) + 1

        summary_parts = [f"共 {count} 条记录"]

        if status_count:
            status_parts = [f"{status}: {count}" for status, count in status_count.items()]
            summary_parts.append(" | ".join(status_parts))

        return "，".join(summary_parts)

    def format_report(self, report_data: Dict[str, Any], report_type: str = "table") -> str:
        """
        格式化报表

        Args:
            report_data: 报表数据
            report_type: 报表类型（table, card, list）

        Returns:
            格式化的报表文本
        """
        if report_type == "table":
            return self._format_table_report(report_data)
        elif report_type == "card":
            return self._format_card_report(report_data)
        elif report_type == "list":
            return self._format_list_report(report_data)
        else:
            return str(report_data)

    def _format_table_report(self, report_data: Dict[str, Any]) -> str:
        """格式化表格报表"""
        headers = report_data.get("headers", [])
        rows = report_data.get("rows", [])

        if not headers or not rows:
            return "暂无报表数据"

        # 计算列宽
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        # 生成表格
        lines = []

        # 表头
        header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
        lines.append(header_line)

        # 分隔线
        separator = "-+-".join("-" * w for w in col_widths)
        lines.append(separator)

        # 数据行
        for row in rows[:10]:  # 限制显示行数
            row_line = " | ".join(
                str(cell)[:w].ljust(w) if i < len(col_widths) else str(cell)
                for i, (cell, w) in enumerate(zip(row, col_widths))
            )
            lines.append(row_line)

        if len(rows) > 10:
            lines.append(f"... 还有 {len(rows) - 10} 行")

        return "\n".join(lines)

    def _format_card_report(self, report_data: Dict[str, Any]) -> str:
        """格式化卡片报表"""
        cards = report_data.get("cards", [])

        if not cards:
            return "暂无数据"

        lines = []
        for card in cards:
            title = card.get("title", "")
            value = card.get("value", "")
            subtitle = card.get("subtitle", "")

            lines.append(f"📊 {title}")
            lines.append(f"   {value}")
            if subtitle:
                lines.append(f"   {subtitle}")
            lines.append("")

        return "\n".join(lines)

    def _format_list_report(self, report_data: Dict[str, Any]) -> str:
        """格式化列表报表"""
        items = report_data.get("items", [])

        if not items:
            return "暂无数据"

        lines = []
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {self._format_item(item)}")

        return "\n".join(lines)

    def format_suggestions(self, suggestions: List[Dict[str, str]]) -> str:
        """
        格式化建议列表

        Args:
            suggestions: 建议列表

        Returns:
            格式化的建议文本
        """
        if not suggestions:
            return ""

        lines = ["💡 建议操作："]

        for i, suggestion in enumerate(suggestions, 1):
            action = suggestion.get("suggestion", "")
            reason = suggestion.get("reason", "")

            if reason:
                lines.append(f"{i}. {action} ({reason})")
            else:
                lines.append(f"{i}. {action}")

        return "\n".join(lines)

    def format_confirmation(self, action: str, entity: str, details: Dict[str, Any]) -> str:
        """
        格式化确认提示

        Args:
            action: 操作描述
            entity: 实体描述
            details: 详细信息

        Returns:
            确认提示文本
        """
        lines = ["⚠️ 请确认操作", "", f"操作：{action}", f"对象：{entity}", "", "详细信息："]

        for key, value in details.items():
            lines.append(f"  • {key}: {value}")

        lines.append("")
        lines.append("回复「确认」继续，或「取消」放弃")

        return "\n".join(lines)

    def format_progress(self, current: int, total: int, description: str = "") -> str:
        """
        格式化进度信息

        Args:
            current: 当前进度
            total: 总数
            description: 描述

        Returns:
            进度信息文本
        """
        percentage = (current / total * 100) if total > 0 else 0
        bar_length = 20
        filled = int(bar_length * current / total) if total > 0 else 0

        bar = "█" * filled + "░" * (bar_length - filled)

        lines = [f"进度：{bar} {percentage:.1f}%", f"{current}/{total} {description}"]

        return "\n".join(lines)

    def translate_status(self, status: str, entity_type: str = "") -> str:
        """
        翻译状态为中文

        Args:
            status: 状态值
            entity_type: 实体类型

        Returns:
            中文状态
        """
        status_map = {
            # 通用状态
            "pending": "待处理",
            "in_progress": "处理中",
            "approved": "已批准",
            "rejected": "已拒绝",
            "cancelled": "已取消",
            "completed": "已完成",
            # 订单状态
            "draft": "草稿",
            "confirmed": "已确认",
            "in_production": "生产中",
            "ready_to_ship": "待发货",
            "shipped": "已发货",
            "delivered": "已交付",
            "returned": "已退货",
            # 发货状态
            "packed": "已打包",
            "partial_shipped": "部分发货",
            # 收货状态
            "inspecting": "检验中",
            "received": "已收货",
            "partial_received": "部分收货",
        }

        return status_map.get(status.lower(), status)

    def format_datetime(self, dt: datetime, format_type: str = "default") -> str:
        """
        格式化日期时间

        Args:
            dt: 日期时间对象
            format_type: 格式类型（default, date, time, relative）

        Returns:
            格式化的日期时间字符串
        """
        if not dt:
            return ""

        if format_type == "date":
            return dt.strftime("%Y年%m月%d日")
        elif format_type == "time":
            return dt.strftime("%H:%M")
        elif format_type == "relative":
            # 相对时间（如"3小时前"）
            now = datetime.now()
            delta = now - dt

            if delta.days > 0:
                return f"{delta.days}天前"
            elif delta.seconds >= 3600:
                hours = delta.seconds // 3600
                return f"{hours}小时前"
            elif delta.seconds >= 60:
                minutes = delta.seconds // 60
                return f"{minutes}分钟前"
            else:
                return "刚刚"
        else:
            return dt.strftime("%Y年%m月%d日 %H:%M")

    def format_amount(self, amount: Any, currency: str = "¥") -> str:
        """
        格式化金额

        Args:
            amount: 金额值
            currency: 货币符号

        Returns:
            格式化的金额字符串
        """
        if amount is None:
            return "N/A"

        try:
            amount_decimal = Decimal(str(amount))
            return f"{currency}{amount_decimal:,.2f}"
        except BaseException:
            return str(amount)

    def format_percentage(self, value: float, decimals: int = 1) -> str:
        """
        格式化百分比

        Args:
            value: 数值
            decimals: 小数位数

        Returns:
            格式化的百分比字符串
        """
        return f"{value:.{decimals}f}%"

    def generate_multi_language_response(self, data: Dict[str, Any], language: str = "zh") -> str:
        """
        生成多语言响应（预留接口）

        Args:
            data: 响应数据
            language: 语言代码（zh, en等）

        Returns:
            指定语言的响应文本
        """
        # 目前只支持中文，预留扩展接口
        if language == "zh":
            return self.generate_response(data)
        else:
            # TODO: 实现其他语言支持
            return self.generate_response(data)
