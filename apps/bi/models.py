"""
BI报表数据模型
"""
from core.models import BaseModel, Platform, Shop
from django.db import models
from ecomm_sync.models import PlatformAccount
from products.models import Product


class Report(BaseModel):
    """报表基础模型"""

    REPORT_TYPES = [
        ("sales", "销售报表"),
        ("order", "订单报表"),
        ("inventory", "库存报表"),
        ("platform", "平台对比报表"),
        ("product", "商品报表"),
        ("customer", "客户报表"),
    ]

    name = models.CharField("报表名称", max_length=200)
    report_type = models.CharField("报表类型", max_length=20, choices=REPORT_TYPES)
    description = models.TextField("报表描述", blank=True)
    platform = models.ForeignKey(
        Platform,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports",
        verbose_name="平台",
    )
    platform_account = models.ForeignKey(
        PlatformAccount,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports",
        verbose_name="平台账号",
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_reports",
        verbose_name="创建人",
    )

    # 报表配置
    filters_config = models.JSONField("过滤条件配置", default=dict, blank=True)
    columns_config = models.JSONField("列配置", default=list, blank=True)
    group_by = models.JSONField("分组配置", default=list, blank=True)
    sort_by = models.JSONField("排序配置", default=list, blank=True)

    # 调度配置
    is_scheduled = models.BooleanField("是否定时生成", default=False)
    schedule_crontab = models.CharField("调度Crontab", max_length=100, blank=True)
    last_generated_at = models.DateTimeField("最后生成时间", null=True, blank=True)

    class Meta:
        verbose_name = "报表"
        verbose_name_plural = "报表"
        db_table = "bi_report"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["report_type", "platform"]),
            models.Index(fields=["created_by"]),
        ]

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.name}"


class ReportData(BaseModel):
    """报表数据缓存"""

    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="data_records", verbose_name="报表"
    )
    data = models.JSONField("报表数据", default=dict)
    row_count = models.PositiveIntegerField("数据行数", default=0)

    # 数据生成信息
    start_date = models.DateField("开始日期", null=True, blank=True)
    end_date = models.DateField("结束日期", null=True, blank=True)
    generated_at = models.DateTimeField("生成时间", auto_now_add=True)

    class Meta:
        verbose_name = "报表数据"
        verbose_name_plural = "报表数据"
        db_table = "bi_report_data"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["report", "-generated_at"]),
        ]

    def __str__(self):
        return f"{self.report.name} - {self.generated_at.strftime('%Y-%m-%d %H:%M')}"


class SalesSummary(BaseModel):
    """销售汇总数据"""

    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="sales_summaries", verbose_name="平台"
    )
    platform_account = models.ForeignKey(
        PlatformAccount,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sales_summaries",
        verbose_name="平台账号",
    )

    # 时间维度
    report_date = models.DateField("报表日期", db_index=True)
    report_period = models.CharField(
        "报表周期", max_length=20, default="daily", help_text="daily=日, weekly=周, monthly=月"
    )

    # 销售指标
    total_orders = models.PositiveIntegerField("总订单数", default=0)
    total_amount = models.DecimalField("总金额", max_digits=15, decimal_places=2, default=0)
    total_quantity = models.PositiveIntegerField("总商品数", default=0)
    avg_order_value = models.DecimalField("平均订单金额", max_digits=10, decimal_places=2, default=0)

    # 订单状态分布
    paid_orders = models.PositiveIntegerField("已付款订单", default=0)
    shipped_orders = models.PositiveIntegerField("已发货订单", default=0)
    delivered_orders = models.PositiveIntegerField("已送达订单", default=0)
    cancelled_orders = models.PositiveIntegerField("已取消订单", default=0)
    refunded_orders = models.PositiveIntegerField("已退款订单", default=0)

    # 转化指标
    conversion_rate = models.DecimalField(
        "转化率", max_digits=5, decimal_places=2, default=0, help_text="百分比"
    )
    repeat_purchase_rate = models.DecimalField(
        "复购率", max_digits=5, decimal_places=2, default=0, help_text="百分比"
    )

    class Meta:
        verbose_name = "销售汇总"
        verbose_name_plural = "销售汇总"
        db_table = "bi_sales_summary"
        ordering = ["-report_date", "-created_at"]
        unique_together = [["platform", "platform_account", "report_date", "report_period"]]
        indexes = [
            models.Index(fields=["report_date", "-report_period"]),
        ]

    def __str__(self):
        return f"{self.platform.name} - {self.report_date}"


class ProductSales(BaseModel):
    """商品销售数据"""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="sales_data", verbose_name="商品"
    )
    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="product_sales", verbose_name="平台"
    )

    # 时间维度
    report_date = models.DateField("报表日期", db_index=True)
    report_period = models.CharField("报表周期", max_length=20, default="daily")

    # 销售指标
    sold_quantity = models.PositiveIntegerField("销售数量", default=0)
    sales_amount = models.DecimalField("销售金额", max_digits=12, decimal_places=2, default=0)
    profit = models.DecimalField("利润", max_digits=12, decimal_places=2, default=0)

    # 订单指标
    order_count = models.PositiveIntegerField("订单数", default=0)
    return_count = models.PositiveIntegerField("退货数", default=0)
    return_rate = models.DecimalField("退货率", max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name = "商品销售数据"
        verbose_name_plural = "商品销售数据"
        db_table = "bi_product_sales"
        ordering = ["-report_date", "-sales_amount"]
        unique_together = [["product", "platform", "report_date", "report_period"]]
        indexes = [
            models.Index(fields=["report_date", "-sales_amount"]),
            models.Index(fields=["product", "-report_date"]),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.report_date}"


class InventoryAnalysis(BaseModel):
    """库存分析数据"""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="inventory_analysis", verbose_name="商品"
    )
    shop = models.ForeignKey(
        Shop, on_delete=models.CASCADE, related_name="inventory_analysis", verbose_name="仓库"
    )
    platform = models.ForeignKey(
        Platform,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="inventory_analysis",
        verbose_name="平台",
    )

    # 库存指标
    current_stock = models.PositiveIntegerField("当前库存", default=0)
    safety_stock = models.PositiveIntegerField("安全库存", default=0)
    max_stock = models.PositiveIntegerField("最大库存", default=0)

    # 周转指标
    turnover_days = models.IntegerField("周转天数", default=0, help_text="库存周转天数")
    turnover_rate = models.DecimalField("周转率", max_digits=5, decimal_places=2, default=0)
    avg_daily_sales = models.DecimalField("日均销量", max_digits=10, decimal_places=2, default=0)

    # 预警指标
    stock_status = models.CharField(
        "库存状态",
        max_length=20,
        default="normal",
        choices=[("normal", "正常"), ("low", "低库存"), ("out", "缺货"), ("overstock", "积压")],
    )
    days_of_stock = models.IntegerField("可销天数", default=0, help_text="当前库存可销售天数")

    # 成本指标
    stock_value = models.DecimalField("库存价值", max_digits=15, decimal_places=2, default=0)
    avg_cost = models.DecimalField("平均成本", max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "库存分析"
        verbose_name_plural = "库存分析"
        db_table = "bi_inventory_analysis"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["stock_status"]),
            models.Index(fields=["days_of_stock"]),
            models.Index(fields=["product", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.get_stock_status_display()}"


class PlatformComparison(BaseModel):
    """平台对比数据"""

    report_date = models.DateField("报表日期", db_index=True)
    report_period = models.CharField("报表周期", max_length=20, default="daily")

    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="comparison_data", verbose_name="平台"
    )
    platform_account = models.ForeignKey(
        PlatformAccount,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="comparison_data",
        verbose_name="平台账号",
    )

    # 订单指标
    order_count = models.PositiveIntegerField("订单数", default=0)
    order_growth_rate = models.DecimalField("订单增长率", max_digits=5, decimal_places=2, default=0)

    # 销售指标
    sales_amount = models.DecimalField("销售金额", max_digits=15, decimal_places=2, default=0)
    sales_growth_rate = models.DecimalField("销售增长率", max_digits=5, decimal_places=2, default=0)

    # 转化指标
    conversion_rate = models.DecimalField("转化率", max_digits=5, decimal_places=2, default=0)
    avg_order_value = models.DecimalField("平均订单金额", max_digits=10, decimal_places=2, default=0)

    # 排名
    sales_rank = models.PositiveIntegerField("销售排名", null=True, blank=True)
    order_rank = models.PositiveIntegerField("订单排名", null=True, blank=True)

    class Meta:
        verbose_name = "平台对比"
        verbose_name_plural = "平台对比"
        db_table = "bi_platform_comparison"
        ordering = ["-report_date", "-sales_amount"]
        unique_together = [["platform", "platform_account", "report_date", "report_period"]]
        indexes = [
            models.Index(fields=["report_date", "-sales_amount"]),
            models.Index(fields=["report_date", "-order_count"]),
        ]

    def __str__(self):
        return f"{self.platform.name} - {self.report_date}"


class DashboardWidget(BaseModel):
    """仪表盘组件"""

    WIDGET_TYPES = [
        ("metric", "指标卡"),
        ("chart", "图表"),
        ("table", "表格"),
        ("list", "列表"),
    ]

    name = models.CharField("组件名称", max_length=200)
    widget_type = models.CharField("组件类型", max_length=20, choices=WIDGET_TYPES)
    title = models.CharField("标题", max_length=200)
    description = models.TextField("描述", blank=True)

    # 数据配置
    data_source = models.CharField("数据源", max_length=200, help_text="模型或查询方法")
    data_params = models.JSONField("数据参数", default=dict, blank=True)

    # 显示配置
    display_config = models.JSONField("显示配置", default=dict, blank=True, help_text="图表类型、颜色等")
    refresh_interval = models.PositiveIntegerField("刷新间隔(秒)", default=300, help_text="0表示不自动刷新")

    # 布局配置
    position = models.CharField("位置", max_length=100, blank=True, help_text="仪表盘中的位置")
    width = models.PositiveIntegerField("宽度", default=4, help_text="栅格系统宽度，最大12")
    height = models.PositiveIntegerField("高度", default=3)

    class Meta:
        verbose_name = "仪表盘组件"
        verbose_name_plural = "仪表盘组件"
        db_table = "bi_dashboard_widget"
        ordering = ["position", "created_at"]

    def __str__(self):
        return f"{self.title}"


class Dashboard(BaseModel):
    """仪表盘"""

    name = models.CharField("仪表盘名称", max_length=200)
    description = models.TextField("描述", blank=True)
    created_by = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="dashboards", verbose_name="创建人"
    )

    # 布局配置
    layout = models.JSONField("布局配置", default=dict, blank=True, help_text="组件布局")
    widgets = models.ManyToManyField(
        DashboardWidget,
        through="DashboardWidgetConfig",
        related_name="dashboards",
        verbose_name="组件",
    )

    # 访问控制
    is_public = models.BooleanField("是否公开", default=False, help_text="公开仪表盘对所有用户可见")
    allowed_users = models.ManyToManyField(
        "users.User", blank=True, related_name="accessible_dashboards", verbose_name="允许访问的用户"
    )

    class Meta:
        verbose_name = "仪表盘"
        verbose_name_plural = "仪表盘"
        db_table = "bi_dashboard"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class DashboardWidgetConfig(BaseModel):
    """仪表盘组件配置"""

    dashboard = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name="widget_configs", verbose_name="仪表盘"
    )
    widget = models.ForeignKey(
        DashboardWidget,
        on_delete=models.CASCADE,
        related_name="dashboard_configs",
        verbose_name="组件",
    )

    # 组件实例配置
    config = models.JSONField("组件配置", default=dict, blank=True)
    order = models.PositiveIntegerField("顺序", default=0)

    class Meta:
        verbose_name = "仪表盘组件配置"
        verbose_name_plural = "仪表盘组件配置"
        db_table = "bi_dashboard_widget_config"
        ordering = ["order"]
        unique_together = [["dashboard", "widget"]]

    def __str__(self):
        return f"{self.dashboard.name} - {self.widget.title}"
