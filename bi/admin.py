"""
BI模块Admin配置
"""
from django.contrib import admin
from .models import (
    Report, ReportData, SalesSummary, ProductSales,
    InventoryAnalysis, PlatformComparison, Dashboard,
    DashboardWidget, DashboardWidgetConfig
)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'platform', 'created_by', 'is_scheduled', 'last_generated_at']
    list_filter = ['report_type', 'platform', 'is_scheduled']
    search_fields = ['name', 'description']


@admin.register(ReportData)
class ReportDataAdmin(admin.ModelAdmin):
    list_display = ['report', 'generated_at', 'row_count']
    list_filter = ['report', 'generated_at']
    readonly_fields = ['data', 'generated_at']


@admin.register(SalesSummary)
class SalesSummaryAdmin(admin.ModelAdmin):
    list_display = ['report_date', 'platform', 'total_orders', 'total_amount', 'conversion_rate']
    list_filter = ['platform', 'report_period', 'report_date']
    date_hierarchy = 'report_date'


@admin.register(ProductSales)
class ProductSalesAdmin(admin.ModelAdmin):
    list_display = ['product', 'platform', 'report_date', 'sold_quantity', 'sales_amount']
    list_filter = ['platform', 'report_date', 'report_period']
    search_fields = ['product__name', 'product__code']


@admin.register(InventoryAnalysis)
class InventoryAnalysisAdmin(admin.ModelAdmin):
    list_display = ['product', 'shop', 'current_stock', 'stock_status', 'turnover_days']
    list_filter = ['stock_status', 'shop', 'platform']
    search_fields = ['product__name', 'product__code']


@admin.register(PlatformComparison)
class PlatformComparisonAdmin(admin.ModelAdmin):
    list_display = ['report_date', 'platform', 'order_count', 'sales_amount', 'sales_rank']
    list_filter = ['platform', 'report_period', 'report_date']
    date_hierarchy = 'report_date'


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['title', 'widget_type', 'data_source', 'refresh_interval']
    list_filter = ['widget_type']


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'is_public']
    filter_horizontal = ['allowed_users']


@admin.register(DashboardWidgetConfig)
class DashboardWidgetConfigAdmin(admin.ModelAdmin):
    list_display = ['dashboard', 'widget', 'order']
    list_filter = ['dashboard']
