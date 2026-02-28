"""
BI报表序列化器
"""

from rest_framework import serializers

from apps.bi.models import (
    ApiPerformance,
    Dashboard,
    DashboardWidget,
    DashboardWidgetConfig,
    InventoryAnalysis,
    PlatformComparison,
    ProductSales,
    Report,
    ReportData,
    SalesSummary,
    SystemHealth,
)


class ReportSerializer(serializers.ModelSerializer):
    """报表序列化器"""

    platform_name = serializers.CharField(source="platform.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Report
        fields = "__all__"


class ReportDataSerializer(serializers.ModelSerializer):
    """报表数据序列化器"""

    report_name = serializers.CharField(source="report.name", read_only=True)

    class Meta:
        model = ReportData
        fields = "__all__"


class SalesSummarySerializer(serializers.ModelSerializer):
    """销售汇总序列化器"""

    platform_name = serializers.CharField(source="platform.name", read_only=True)
    account_name = serializers.CharField(source="platform_account.account_name", read_only=True)

    class Meta:
        model = SalesSummary
        fields = "__all__"


class ProductSalesSerializer(serializers.ModelSerializer):
    """商品销售数据序列化器"""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_code = serializers.CharField(source="product.code", read_only=True)
    platform_name = serializers.CharField(source="platform.name", read_only=True)

    class Meta:
        model = ProductSales
        fields = "__all__"


class InventoryAnalysisSerializer(serializers.ModelSerializer):
    """库存分析序列化器"""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_code = serializers.CharField(source="product.code", read_only=True)
    shop_name = serializers.CharField(source="shop.name", read_only=True)
    platform_name = serializers.CharField(source="platform.name", read_only=True)
    stock_status_display = serializers.CharField(source="get_stock_status_display", read_only=True)

    class Meta:
        model = InventoryAnalysis
        fields = "__all__"


class PlatformComparisonSerializer(serializers.ModelSerializer):
    """平台对比序列化器"""

    platform_name = serializers.CharField(source="platform.name", read_only=True)
    account_name = serializers.CharField(source="platform_account.account_name", read_only=True)

    class Meta:
        model = PlatformComparison
        fields = "__all__"


class DashboardWidgetSerializer(serializers.ModelSerializer):
    """仪表盘组件序列化器"""

    widget_type_display = serializers.CharField(source="get_widget_type_display", read_only=True)

    class Meta:
        model = DashboardWidget
        fields = "__all__"


class DashboardSerializer(serializers.ModelSerializer):
    """仪表盘序列化器"""

    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    widgets_detail = DashboardWidgetSerializer(source="widgets", many=True, read_only=True)
    widget_count = serializers.SerializerMethodField()

    class Meta:
        model = Dashboard
        fields = "__all__"

    def get_widget_count(self, obj):
        return obj.widgets.count()


class DashboardWidgetConfigSerializer(serializers.ModelSerializer):
    """仪表盘组件配置序列化器"""

    widget_title = serializers.CharField(source="widget.title", read_only=True)
    widget_type = serializers.CharField(source="widget.widget_type", read_only=True)

    class Meta:
        model = DashboardWidgetConfig
        fields = "__all__"


class SystemHealthSerializer(serializers.ModelSerializer):
    """系统健康状态序列化器"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SystemHealth
        fields = "__all__"


class ApiPerformanceSerializer(serializers.ModelSerializer):
    """API性能监控序列化器"""

    class Meta:
        model = ApiPerformance
        fields = "__all__"
