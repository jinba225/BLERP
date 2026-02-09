"""
高级分析数据模型
"""
from django.db import models
from django.db.models import Count, Sum, Avg, F, Q, Func, Window
from django.db.models.functions import Trunc, Extract
from django.db.models.expressions import RowNumber
from django.utils import timezone

from core.models import BaseModel, Platform, Shop
from products.models import Product
from bi.models import SalesSummary, ProductSales, InventoryAnalysis, PlatformComparison, Dashboard


class TrendPrediction(BaseModel):
    """趋势预测数据"""

    PREDICTION_TYPES = [
        ("sales", "销售预测"),
        ("order", "订单预测"),
        ("inventory", "库存预测"),
        ("profit", "利润预测"),
    ]

    DATA_SOURCES = [
        ("historical", "历史数据"),
        ("ai", "AI预测"),
        ("hybrid", "混合模型"),
    ]

    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="trend_predictions", verbose_name="平台"
    )
    platform_account = models.ForeignKey(
        "ecomm_sync.PlatformAccount",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trend_predictions",
        verbose_name="平台账号",
    )

    # 预测配置
    prediction_type = models.CharField("预测类型", max_length=20, choices=PREDICTION_TYPES)
    data_source = models.CharField("数据源", max_length=20, choices=DATA_SOURCES, default="hybrid")

    # 时间维度
    prediction_date = models.DateField("预测日期", db_index=True)
    prediction_period = models.CharField("预测周期", max_length=20, default="daily")
    horizon_days = models.PositiveIntegerField("预测天数", default=30, help_text="预测未来多少天")

    # 预测结果
    predicted_value = models.DecimalField("预测值", max_digits=15, decimal_places=2, default=0)
    confidence = models.DecimalField(
        "置信度", max_digits=5, decimal_places=2, default=0, help_text="0-100百分比"
    )

    # 历史数据（用于对比）
    actual_value = models.DecimalField(
        "实际值", max_digits=15, decimal_places=2, null=True, blank=True
    )
    accuracy = models.DecimalField("准确率", max_digits=5, decimal_places=2, null=True, blank=True)

    # AI预测信息
    ai_model_version = models.CharField("AI模型版本", max_length=50, blank=True)
    ai_prediction_info = models.JSONField("AI预测信息", default=dict, blank=True)

    class Meta:
        verbose_name = "趋势预测"
        verbose_name_plural = "趋势预测"
        db_table = "bi_trend_prediction"
        ordering = ["-prediction_date"]
        indexes = [
            models.Index(fields=["platform", "prediction_type", "prediction_date"]),
            models.Index(fields=["prediction_type", "prediction_date", "-predicted_value"]),
        ]

    def __str__(self):
        return (
            f"{self.get_prediction_type_display()} - {self.platform.name} - {self.prediction_date}"
        )


class UserBehaviorAnalysis(BaseModel):
    """用户行为分析"""

    BEHAVIOR_TYPES = [
        ("browsing", "浏览行为"),
        ("search", "搜索行为"),
        ("purchase", "购买行为"),
        ("review", "评价行为"),
        ("return", "退货行为"),
        ("frequent_buyer", "频买用户"),
        ("churned", "流失用户"),
    ]

    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="user_behavior_analyses", verbose_name="平台"
    )
    platform_account = models.ForeignKey(
        "ecomm_sync.PlatformAccount",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_behavior_analyses",
        verbose_name="平台账号",
    )
    customer_email = models.EmailField("客户邮箱", db_index=True)

    # 行为数据
    behavior_type = models.CharField("行为类型", max_length=20, choices=BEHAVIOR_TYPES)
    behavior_date = models.DateField("行为日期", db_index=True)
    behavior_time = models.TimeField("行为时间", null=True, blank=True)

    # 商品信息
    product_id = models.CharField("商品ID", max_length=200, blank=True)
    product_name = models.CharField("商品名称", max_length=500, blank=True)
    product_price = models.DecimalField(
        "商品价格", max_digits=10, decimal_places=2, null=True, blank=True
    )

    # 交易信息
    order_id = models.CharField("订单ID", max_length=200, blank=True)
    order_amount = models.DecimalField(
        "订单金额", max_digits=10, decimal_places=2, null=True, blank=True
    )

    # 浏览数据
    page_views = models.PositiveIntegerField("页面浏览次数", default=0)
    duration_seconds = models.PositiveIntegerField("停留时长(秒)", default=0)
    bounce = models.BooleanField("跳出", default=False, help_text="True表示跳出")

    class Meta:
        verbose_name = "用户行为分析"
        verbose_name_plural = "用户行为分析"
        db_table = "bi_user_behavior_analysis"
        ordering = ["-behavior_date", "-behavior_time"]
        indexes = [
            models.Index(fields=["customer_email", "behavior_date"]),
            models.Index(fields=["behavior_type", "behavior_date"]),
            models.Index(fields=["behavior_date", "-behavior_type"]),
        ]

    def __str__(self):
        return f"{self.customer_email} - {self.get_behavior_type_display()} - {self.behavior_date}"


class CustomerSegmentation(BaseModel):
    """客户分群"""

    SEGMENT_TYPES = [
        ("high_value", "高价值客户"),
        ("frequent", "高频购买客户"),
        ("new", "新客户"),
        ("at_risk", "流失风险客户"),
        ("dormant", "休眠客户"),
        ("vip", "VIP客户"),
    ]

    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="customer_segmentations", verbose_name="平台"
    )
    segment_name = models.CharField("分群名称", max_length=200)
    segment_type = models.CharField("分群类型", max_length=20, choices=SEGMENT_TYPES)
    description = models.TextField("分群描述", blank=True)

    # 规则配置
    rules = models.JSONField("分群规则", default=dict, blank=True)

    # 分群结果
    customer_count = models.PositiveIntegerField("客户数量", default=0)
    avg_order_amount = models.DecimalField("平均订单金额", max_digits=10, decimal_places=2, default=0)
    avg_order_count = models.DecimalField("平均订单数", max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField("总金额", max_digits=15, decimal_places=2, default=0)
    churn_rate = models.DecimalField(
        "流失率", max_digits=5, decimal_places=2, default=0, help_text="百分比"
    )

    # 统计数据
    last_calculated_at = models.DateTimeField("最后计算时间", null=True, blank=True)

    class Meta:
        verbose_name = "客户分群"
        verbose_name_plural = "客户分群"
        db_table = "bi_customer_segmentation"
        ordering = ["platform", "customer_count"]
        unique_together = [["platform", "segment_name"]]
        indexes = [
            models.Index(fields=["platform", "segment_type"]),
            models.Index(fields=["churn_rate"]),
        ]

    def __str__(self):
        return f"{self.segment_name} - {self.platform.name} - {self.customer_count}个客户"


class RealtimeData(BaseModel):
    """实时数据缓存"""

    DATA_TYPES = [
        ("sales", "销售数据"),
        ("order", "订单数据"),
        ("inventory", "库存数据"),
        ("visitor", "访客数据"),
    ]

    data_type = models.CharField("数据类型", max_length=20, choices=DATA_TYPES, db_index=True)
    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="realtime_data", verbose_name="平台"
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="realtime_data",
        verbose_name="仓库",
    )

    # 数据内容
    data = models.JSONField("数据内容", default=dict, blank=True)

    # 数据统计
    data_count = models.PositiveIntegerField("数据条数", default=0)
    last_updated_at = models.DateTimeField("最后更新时间", auto_now=True, db_index=True)

    # 过期设置
    expires_at = models.DateTimeField("过期时间", null=True, blank=True, help_text="数据过期时间")

    class Meta:
        verbose_name = "实时数据"
        verbose_name_plural = "实时数据"
        db_table = "bi_realtime_data"
        ordering = ["-last_updated_at"]
        indexes = [
            models.Index(fields=["data_type", "-last_updated_at"]),
            models.Index(fields=["platform", "data_type", "-last_updated_at"]),
        ]

    def __str__(self):
        return f"{self.get_data_type_display()} - {self.platform.name}"


class RealtimeWidgetConfig(BaseModel):
    """实时大屏组件配置"""

    WIDGET_TYPES = [
        ("line_chart", "折线图"),
        ("bar_chart", "柱状图"),
        ("pie_chart", "饼图"),
        ("table", "表格"),
        ("metric_card", "指标卡"),
        ("map", "地图"),
        ("funnel", "漏斗图"),
        ("heatmap", "热力图"),
    ]

    WIDGET_REFRESH_INTERVALS = [
        (5, "5秒"),
        (30, "30秒"),
        (60, "1分钟"),
        (300, "5分钟"),
        (600, "10分钟"),
    ]

    dashboard = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name="widget_configs", verbose_name="仪表盘"
    )
    name = models.CharField("组件名称", max_length=200)
    widget_type = models.CharField("组件类型", max_length=20, choices=WIDGET_TYPES)
    title = models.CharField("标题", max_length=200)
    description = models.TextField("描述", blank=True)

    # 数据配置
    data_source = models.CharField(
        "数据源", max_length=200, help_text="数据源：如bi.services.realtimedata.RealtimeDataService"
    )
    data_params = models.JSONField("数据参数", default=dict, blank=True)
    data_refresh_interval = models.PositiveIntegerField(
        "刷新间隔(秒)", choices=WIDGET_REFRESH_INTERVALS, default=60
    )

    # 显示配置
    display_config = models.JSONField("显示配置", default=dict, blank=True, help_text="图表类型、颜色、布局等")
    layout_config = models.JSONField("布局配置", default=dict, blank=True)

    # 阈值配置
    thresholds_config = models.JSONField("阈值配置", default=dict, blank=True, help_text="告警阈值配置")

    class Meta:
        verbose_name = "实时大屏组件配置"
        verbose_name_plural = "实时大屏组件配置"
        db_table = "bi_realtime_widget_config"
        ordering = ["dashboard", "order"]

    def __str__(self):
        return f"{self.title} - {self.dashboard.name}"


class CustomerLTV(BaseModel):
    """客户生命周期价值（CLTV）模型"""

    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="cltv_data", verbose_name="平台"
    )
    customer_email = models.EmailField("客户邮箱", db_index=True)

    # CLTV阶段
    acquisition_channel = models.CharField("获客渠道", max_length=50, blank=True)
    first_purchase_date = models.DateField("首次购买日期", null=True, blank=True, db_index=True)

    # 累计指标
    total_orders = models.PositiveIntegerField("总订单数", default=0)
    total_amount = models.DecimalField("总消费金额", max_digits=15, decimal_places=2, default=0)
    avg_order_value = models.DecimalField("平均订单金额", max_digits=10, decimal_places=2, default=0)
    days_since_last_order = models.IntegerField("距上次订单天数", default=999, null=True, blank=True)

    # CLTV计算
    cltv_value = models.DecimalField("CLTV值", max_digits=12, decimal_places=2, default=0)
    cltv_segment = models.CharField("CLTV分群", max_length=20, default="", blank=True)

    # 预测指标
    predicted_cltv = models.DecimalField(
        "预测CLTV", max_digits=12, decimal_places=2, null=True, blank=True
    )
    cltv_growth_rate = models.DecimalField(
        "CLTV增长率", max_digits=5, decimal_places=2, null=True, blank=True
    )
    churn_probability = models.DecimalField(
        "流失概率", max_digits=5, decimal_places=2, null=True, blank=True
    )

    # 时间维度
    last_analyzed_at = models.DateTimeField("最后分析时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "客户生命周期价值"
        verbose_name_plural = "客户生命周期价值"
        db_table = "bi_customer_cltv"
        ordering = ["-cltv_value", "-created_at"]
        indexes = [
            models.Index(fields=["customer_email", "platform"]),
            models.Index(fields=["cltv_value", "-created_at"]),
            models.Index(fields=["first_purchase_date"]),
            models.Index(fields=["days_since_last_order"]),
        ]
        unique_together = [["platform", "customer_email"]]

    def __str__(self):
        return f"{self.customer_email} - CLTV: {self.cltv_value}"


class AIAssistant(BaseModel):
    """AI分析助手"""

    ANALYSIS_TYPES = [
        ("sales_forecast", "销售预测"),
        ("churn_prediction", "流失预测"),
        ("price_optimization", "价格优化"),
        ("inventory_prediction", "库存预测"),
        ("customer_segmentation", "客户分群"),
    ]

    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="ai_assistants", verbose_name="平台"
    )
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="ai_analyses", verbose_name="用户"
    )

    analysis_type = models.CharField("分析类型", max_length=50, choices=ANALYSIS_TYPES)
    analysis_date = models.DateTimeField("分析日期", default=timezone.now)

    # AI模型配置
    model_name = models.CharField("AI模型名称", max_length=100, blank=True)
    model_version = models.CharField("模型版本", max_length=50, blank=True)
    model_parameters = models.JSONField("模型参数", default=dict, blank=True)

    # 分析结果
    analysis_result = models.JSONField("分析结果", default=dict, blank=True)
    recommendations = models.JSONField("建议", default=list, blank=True)
    confidence_score = models.DecimalField("置信度", max_digits=5, decimal_places=2, default=0)

    # 执行信息
    started_at = models.DateTimeField("开始时间")
    completed_at = models.DateTimeField("完成时间", null=True, blank=True)
    status = models.CharField(
        "状态",
        max_length=20,
        default="pending",
        choices=[
            ("pending", "待处理"),
            ("processing", "处理中"),
            ("completed", "已完成"),
            ("failed", "失败"),
        ],
    )
    error_message = models.TextField("错误信息", blank=True)

    # 成本信息
    execution_time = models.FloatField("执行时间(秒)", null=True, blank=True)
    api_calls_count = models.PositiveIntegerField("API调用次数", default=0)
    data_processed = models.PositiveIntegerField("处理数据量", default=0)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "AI分析助手"
        verbose_name_plural = "AI分析助手"
        db_table = "bi_ai_assistant"
        ordering = ["-analysis_date", "-started_at"]
        indexes = [
            models.Index(fields=["platform", "analysis_type", "status"]),
            models.Index(fields=["user", "-analysis_date"]),
            models.Index(fields=["status", "-started_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_analysis_type_display()} - {self.analysis_date.strftime('%Y-%m-%d')}"


class ReportTemplate(BaseModel):
    """报表模板"""

    TEMPLATE_TYPES = [
        ("sales", "销售报表模板"),
        ("inventory", "库存报表模板"),
        ("platform_comparison", "平台对比报表模板"),
        ("cltv_analysis", "CLTV分析模板"),
        ("custom", "自定义报表模板"),
    ]

    name = models.CharField("模板名称", max_length=200)
    description = models.TextField("模板描述", blank=True)
    template_type = models.CharField("模板类型", max_length=20, choices=TEMPLATE_TYPES)

    # 报表配置
    filters = models.JSONField("过滤条件", default=list, blank=True)
    columns = models.JSONField("列配置", default=list, blank=True)
    group_by = models.JSONField("分组配置", default=list, blank=True)
    sort_by = models.JSONField("排序配置", default=list, blank=True)

    # 可视化配置
    chart_config = models.JSONField("图表配置", default=dict, blank=True)

    # 使用统计
    usage_count = models.PositiveIntegerField("使用次数", default=0)
    last_used_at = models.DateTimeField("最后使用时间", null=True, blank=True)
    is_popular = models.BooleanField("是否热门", default=False)

    created_by = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="created_templates", verbose_name="创建人"
    )

    class Meta:
        verbose_name = "报表模板"
        verbose_name_plural = "报表模板"
        db_table = "bi_report_template"
        ordering = ["-usage_count", "-last_used_at"]
        indexes = [
            models.Index(fields=["template_type", "is_popular"]),
            models.Index(fields=["created_by", "-usage_count"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class CustomReport(BaseModel):
    """自定义报表"""

    STATUS_CHOICES = [
        ("draft", "草稿"),
        ("active", "活跃"),
        ("archived", "已归档"),
    ]

    name = models.CharField("报表名称", max_length=200)
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="custom_reports",
        verbose_name="报表模板",
    )

    # 报表配置
    filters_config = models.JSONField("过滤条件配置", default=list, blank=True)
    columns_config = models.JSONField("列配置", default=list, blank=True)
    group_by_config = models.JSONField("分组配置", default=list, blank=True)
    sort_by_config = models.JSONField("排序配置", default=list, blank=True)

    # 定时配置
    is_scheduled = models.BooleanField("是否定时生成", default=False)
    schedule_crontab = models.CharField("调度Crontab", max_length=100, blank=True)
    last_generated_at = models.DateTimeField("最后生成时间", null=True, blank=True)

    # 访问控制
    is_public = models.BooleanField("是否公开", default=False)
    allowed_users = models.ManyToManyField(
        "users.User", blank=True, related_name="accessible_reports", verbose_name="允许访问的用户"
    )

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="created_custom_reports",
        verbose_name="创建人",
    )

    class Meta:
        verbose_name = "自定义报表"
        verbose_name_plural = "自定义报表"
        db_table = "bi_custom_report"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["template", "is_scheduled", "is_public"]),
            models.Index(fields=["created_by", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.name}"


class CustomReportData(BaseModel):
    """自定义报表数据"""

    report = models.ForeignKey(
        CustomReport, on_delete=models.CASCADE, related_name="data_records", verbose_name="报表"
    )

    # 报表数据
    data = models.JSONField("报表数据", default=dict, blank=True)
    row_count = models.PositiveIntegerField("数据行数", default=0)

    # 数据生成信息
    start_date = models.DateField("开始日期", null=True, blank=True)
    end_date = models.DateField("结束日期", null=True, blank=True)
    generated_at = models.DateTimeField("生成时间", auto_now_add=True)

    class Meta:
        verbose_name = "自定义报表数据"
        verbose_name_plural = "自定义报表数据"
        db_table = "bi_custom_report_data"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["report", "-generated_at"]),
        ]

    def __str__(self):
        return f"{self.report.name} - {self.generated_at.strftime('%Y-%m-%d %H:%M')}"
