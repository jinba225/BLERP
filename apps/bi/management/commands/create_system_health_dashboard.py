"""
创建系统健康状态监控仪表盘
"""

import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.bi.models import Dashboard, DashboardWidget

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """创建系统健康状态监控仪表盘"""

    help = "创建系统健康状态监控仪表盘"

    def handle(self, *args, **options):
        """执行命令"""
        User = get_user_model()

        # 获取第一个超级用户作为创建者
        try:
            creator = User.objects.filter(is_superuser=True).first()
            if not creator:
                self.stdout.write(self.style.ERROR("没有找到超级用户，请先创建一个超级用户"))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"获取用户失败: {e}"))
            return

        # 创建仪表盘
        dashboard, created = Dashboard.objects.get_or_create(
            name="系统健康状态监控",
            description="监控系统健康状态、API性能和资源使用情况",
            created_by=creator,
            is_public=True,
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"创建仪表盘: {dashboard.name}"))
        else:
            self.stdout.write(self.style.INFO(f"仪表盘已存在: {dashboard.name}"))

        # 创建系统健康状态组件
        widgets = [
            {
                "name": "系统状态概览",
                "widget_type": "metric",
                "title": "系统状态",
                "description": "显示系统整体健康状态",
                "data_source": "system_health",
                "data_params": {"endpoint": "/api/bi/system-health/latest/"},
                "display_config": {"color": "#4CAF50", "icon": "health"},
                "width": 4,
                "height": 3,
            },
            {
                "name": "API响应时间",
                "widget_type": "chart",
                "title": "API响应时间趋势",
                "description": "最近24小时API响应时间趋势",
                "data_source": "api_performance",
                "data_params": {
                    "endpoint": "/api/bi/api-performance/",
                    "time_range": "24h",
                    "limit": 100,
                },
                "display_config": {
                    "chart_type": "line",
                    "x_axis": "request_time",
                    "y_axis": "response_time",
                    "title": "API响应时间趋势",
                },
                "width": 8,
                "height": 4,
            },
            {
                "name": "系统资源使用",
                "widget_type": "chart",
                "title": "系统资源使用情况",
                "description": "CPU和内存使用率",
                "data_source": "system_health",
                "data_params": {
                    "endpoint": "/api/bi/system-health/",
                    "time_range": "24h",
                    "limit": 100,
                },
                "display_config": {
                    "chart_type": "line",
                    "x_axis": "record_time",
                    "y_axis": ["cpu_usage", "memory_usage"],
                    "title": "系统资源使用情况",
                },
                "width": 8,
                "height": 4,
            },
            {
                "name": "API错误统计",
                "widget_type": "metric",
                "title": "API错误数",
                "description": "最近24小时API错误数",
                "data_source": "api_performance",
                "data_params": {
                    "endpoint": "/api/bi/api-performance/error-endpoints/",
                    "time_range": "24h",
                },
                "display_config": {"color": "#f44336", "icon": "error"},
                "width": 4,
                "height": 3,
            },
            {
                "name": "慢API端点",
                "widget_type": "table",
                "title": "慢API端点",
                "description": "响应时间超过1秒的API端点",
                "data_source": "api_performance",
                "data_params": {
                    "endpoint": "/api/bi/api-performance/slow-endpoints/",
                    "threshold": 1000,
                    "limit": 20,
                },
                "display_config": {
                    "columns": ["endpoint", "method", "response_time", "status_code"],
                    "sort_by": ["response_time", "desc"],
                },
                "width": 12,
                "height": 6,
            },
            {
                "name": "系统健康状态摘要",
                "widget_type": "metric",
                "title": "系统健康状态摘要",
                "description": "系统健康状态统计",
                "data_source": "system_health",
                "data_params": {"endpoint": "/api/bi/system-health/status-summary/"},
                "display_config": {"color": "#2196F3", "icon": "info"},
                "width": 12,
                "height": 3,
            },
            {
                "name": "API性能摘要",
                "widget_type": "metric",
                "title": "API性能摘要",
                "description": "API性能统计",
                "data_source": "api_performance",
                "data_params": {"endpoint": "/api/bi/api-performance/performance-summary/"},
                "display_config": {"color": "#ff9800", "icon": "speed"},
                "width": 12,
                "height": 3,
            },
        ]

        # 创建或更新组件
        for widget_data in widgets:
            widget, widget_created = DashboardWidget.objects.get_or_create(
                name=widget_data["name"],
                widget_type=widget_data["widget_type"],
                title=widget_data["title"],
                description=widget_data["description"],
                data_source=widget_data["data_source"],
                data_params=widget_data["data_params"],
                display_config=widget_data["display_config"],
                width=widget_data["width"],
                height=widget_data["height"],
            )

            if widget_created:
                self.stdout.write(self.style.SUCCESS(f"创建组件: {widget.title}"))
            else:
                self.stdout.write(self.style.INFO(f"组件已存在: {widget.title}"))

            # 将组件添加到仪表盘中
            if widget not in dashboard.widgets.all():
                dashboard.widgets.add(widget)
                self.stdout.write(self.style.SUCCESS(f"将组件 {widget.title} 添加到仪表盘"))

        # 更新仪表盘布局
        layout = {
            "widgets": [
                {
                    "id": dashboard.widgets.filter(name="系统状态概览").first().id,
                    "position": {"x": 0, "y": 0, "width": 4, "height": 3},
                },
                {
                    "id": dashboard.widgets.filter(name="API错误统计").first().id,
                    "position": {"x": 4, "y": 0, "width": 4, "height": 3},
                },
                {
                    "id": dashboard.widgets.filter(name="API响应时间").first().id,
                    "position": {"x": 0, "y": 3, "width": 12, "height": 4},
                },
                {
                    "id": dashboard.widgets.filter(name="系统资源使用").first().id,
                    "position": {"x": 0, "y": 7, "width": 12, "height": 4},
                },
                {
                    "id": dashboard.widgets.filter(name="系统健康状态摘要").first().id,
                    "position": {"x": 0, "y": 11, "width": 12, "height": 3},
                },
                {
                    "id": dashboard.widgets.filter(name="API性能摘要").first().id,
                    "position": {"x": 0, "y": 14, "width": 12, "height": 3},
                },
                {
                    "id": dashboard.widgets.filter(name="慢API端点").first().id,
                    "position": {"x": 0, "y": 17, "width": 12, "height": 6},
                },
            ]
        }

        dashboard.layout = layout
        dashboard.save()

        self.stdout.write(self.style.SUCCESS("仪表盘布局已更新"))
        self.stdout.write(self.style.SUCCESS("系统健康状态监控仪表盘创建完成"))
