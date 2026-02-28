"""
BI模块URL配置
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.bi.views import (
    ApiPerformanceViewSet,
    DashboardViewSet,
    DashboardWidgetViewSet,
    DataExportViewSet,
    InventoryAnalysisViewSet,
    PlatformComparisonViewSet,
    ProductSalesViewSet,
    ReportViewSet,
    SalesSummaryViewSet,
    SystemHealthViewSet,
)

router = DefaultRouter()
router.register(r"reports", ReportViewSet, basename="report")
router.register(r"sales-summaries", SalesSummaryViewSet, basename="sales-summary")
router.register(r"product-sales", ProductSalesViewSet, basename="product-sales")
router.register(r"inventory-analysis", InventoryAnalysisViewSet, basename="inventory-analysis")
router.register(r"platform-comparisons", PlatformComparisonViewSet, basename="platform-comparison")
router.register(r"dashboards", DashboardViewSet, basename="dashboard")
router.register(r"dashboard-widgets", DashboardWidgetViewSet, basename="dashboard-widget")
router.register(r"exports", DataExportViewSet, basename="data-export")
router.register(r"system-health", SystemHealthViewSet, basename="system-health")
router.register(r"api-performance", ApiPerformanceViewSet, basename="api-performance")

app_name = "bi"

urlpatterns = [
    path("", include(router.urls)),
]
