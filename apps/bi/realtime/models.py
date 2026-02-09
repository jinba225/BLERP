"""
实时大屏模型
"""
from django.db import models
from django.db.models import JSONField
from django.core.exceptions import ValidationError

from .models import Dashboard, DashboardWidget


class RealtimeDashboard(BaseModel):
    """实时大屏"""

    name = models.CharField("大屏名称", max_length=200, unique=True)
    description = models.TextField("描述", blank=True)
    cover_image = models.ImageField("封面图片", upload_to="realtime_covers/", null=True, blank=True)

    # 布局配置
    layout = models.JSONField("布局配置", default=dict, blank=True, help_text="组件布局配置")
    theme = models.CharField(
        "主题", max_length=50, default="default", help_text="default, dark, blue, green"
    )

    # 显示设置
    show_header = models.BooleanField("显示页头", default=True)
    show_footer = models.BooleanField("显示页脚", default=True)
    show_platform_tabs = models.BooleanField("显示平台标签页", default=True)

    # 刷新配置
    auto_refresh_enabled = models.BooleanField("自动刷新", default=True)
    refresh_interval = models.PositiveIntegerField("刷新间隔(秒)", default=60)

    # 访问控制
    is_public = models.BooleanField("是否公开", default=False, help_text="公开大屏对所有用户可见")
    allowed_users = models.ManyToManyField(
        "users.User", blank=True, related_name="accessible_dashboards", verbose_name="允许访问的用户"
    )

    # 创建者信息
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="created_realtime_dashboards",
        verbose_name="创建者",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    # 激活状态
    is_active = models.BooleanField("是否激活", default=True)

    class Meta:
        verbose_name = "实时大屏"
        verbose_name_plural = "实时大屏"
        db_table = "bi_realtime_dashboard"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


class RealtimeWidget(BaseModel):
    """实时大屏组件"""

    WIDGET_TYPES = [
        ("metric", "指标卡"),
        ("chart", "图表"),
        ("table", "表格"),
        ("list", "列表"),
        ("number", "数字卡"),
        ("text", "文本"),
        ("image", "图片"),
        ("video", "视频"),
        ("iframe", "iframe嵌入"),
    ]

    dashboard = models.ForeignKey(
        RealtimeDashboard, on_delete=models.CASCADE, related_name="widgets", verbose_name="大屏"
    )

    # 基础配置
    name = models.CharField("组件名称", max_length=200)
    widget_type = models.CharField("组件类型", max_length=20, choices=WIDGET_TYPES, default="metric")
    title = models.CharField("标题", max_length=200)
    description = models.TextField("描述", blank=True)
    icon = models.CharField("图标", max_length=100, blank=True)

    # 数据源配置
    data_source = models.CharField(
        "数据源", max_length=200, help_text="数据源类路径，如bi.services.realtimedata.RealtimeDataService"
    )
    data_params = models.JSONField("数据参数", default=dict, blank=True)

    # 显示配置
    display_config = models.JSONField("显示配置", default=dict, blank=True, help_text="图表类型、颜色、布局等")

    # 刷新配置
    refresh_enabled = models.BooleanField("启用刷新", default=True)
    refresh_interval = models.PositiveIntegerField(
        "刷新间隔(秒)",
        choices=[
            (30, "30秒"),
            (60, "1分钟"),
            (120, "2分钟"),
            (300, "5分钟"),
            (600, "10分钟"),
            (3600, "1小时"),
        ],
        default=60,
    )

    # 布局配置
    position = models.CharField(
        "位置", max_length=100, blank=True, help_text="大屏中的位置，如 top-left, top-center"
    )
    width = models.PositiveIntegerField("宽度", default=4, help_text="栅格系统宽度，最大12")
    height = models.PositiveIntegerField("高度", default=3, help_text="高度单位栅格数")
    order = models.PositiveIntegerField("顺序", default=0)
    col_span = models.PositiveIntegerField("跨列数", default=1, help_text="栅格跨列数，最大12")

    # 条件过滤
    show_conditions = models.JSONField("显示条件", default=dict, blank=True, help_text="数据过滤条件")

    class Meta:
        verbose_name = "实时大屏组件"
        verbose_name_plural = "实时大屏组件"
        db_table = "bi_realtime_widget"
        ordering = ["dashboard", "order"]
        unique_together = [["dashboard", "name"]]

    def __str__(self):
        return f"{self.dashboard.name} - {self.title}"


class RealtimeMetric(BaseModel):
    """实时指标"""

    widget = models.OneToOneField(
        RealtimeWidget, on_delete=models.CASCADE, related_name="metric", verbose_name="组件"
    )

    # 指标配置
    metric_name = models.CharField("指标名称", max_length=100)
    metric_key = models.CharField("指标键值", max_length=200, help_text="数据源中的键值，如sales.total_amount")
    metric_unit = models.CharField("指标单位", max_length=20, blank=True, default="个")
    metric_format = models.CharField(
        "格式", max_length=50, default="{value}", help_text="数值格式，如{value}、{value,000}、{value:00:00}"
    )

    # 阈值配置
    target_value = models.DecimalField(
        "目标值", max_digits=10, decimal_places=2, null=True, blank=True
    )
    warning_threshold = models.DecimalField(
        "警告阈值", max_digits=10, decimal_places=2, null=True, blank=True
    )
    danger_threshold = models.DecimalField(
        "危险阈值", max_digits=10, decimal_places=2, null=True, blank=True
    )

    # 趋势配置
    show_trend = models.BooleanField("显示趋势", default=True)
    trend_period = models.CharField(
        "趋势周期", max_length=20, default="24h", choices=["1h", "6h", "12h", "24h", "7d", "30d", "90d"]
    )

    # 颜色配置
    normal_color = models.CharField("正常颜色", max_length=7, default="#2ecc71")
    warning_color = models.CharField("警告颜色", max_length=7, default="#f59e0b")
    danger_color = models.CharField("危险颜色", max_length=7, default="#ef4444")

    # 附加配置
    decimal_places = models.PositiveIntegerField("小数位数", default=2)
    show_comparison = models.BooleanField("显示同比环比", default=True)
    show_yoy_comparison = models.BooleanField("显示同比", default=False)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "实时指标"
        verbose_name_plural = "实时指标"
        db_table = "bi_realtime_metric"
        ordering = ["widget", "order"]
        unique_together = [["widget", "metric_key"]]

    def __str__(self):
        return f"{self.metric_name}"


class DataDrilldown(BaseModel):
    """数据下钻取"""

    report = models.ForeignKey(
        "bi.Report", on_delete=models.CASCADE, related_name="drilldowns", verbose_name="报表"
    )

    # 钻取维度
    drilldown_dimensions = models.JSONField("钻取维度", default=list, blank=True, help_text="可钻取的维度")

    # 下钻取条件
    filters = models.JSONField("过滤条件", default=dict, blank=True)

    # 下钻取结果
    drilldown_data = models.JSONField("钻取数据", default=dict, blank=True)

    # 钻取路径
    current_path = models.JSONField("当前钻取路径", default=list, blank=True, help_text="当前钻取路径")

    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "数据下钻取"
        verbose_name_plural = "数据下钻取"
        db_table = "bi_data_drilldown"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.report.name} - 数据下钻取"
