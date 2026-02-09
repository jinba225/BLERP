"""
BI模块测试
"""
from decimal import Decimal

import pytest
from bi.services import InventoryReportService, ReportGenerator, SalesReportService

from apps.bi.models import Dashboard, DashboardWidget, Report


@pytest.mark.django_db
class TestSalesReportService:
    """测试销售报表服务"""

    def test_calculate_conversion_rate_empty_queryset(self):
        """测试计算转化率（空查询集）"""
        from apps.ecomm_sync.models import PlatformOrder

        service = SalesReportService()

        # 测试空查询集
        queryset = PlatformOrder.objects.none()
        rate = service._calculate_conversion_rate(queryset)
        assert rate == Decimal("0")

    def test_calculate_repeat_purchase_rate(self):
        """测试计算复购率（空查询集）"""
        from apps.ecomm_sync.models import PlatformOrder

        service = SalesReportService()

        # 测试空查询集
        queryset = PlatformOrder.objects.none()
        rate = service._calculate_repeat_purchase_rate(queryset)
        assert rate == Decimal("0")


@pytest.mark.django_db
class TestInventoryReportService:
    """测试库存分析服务"""

    def test_determine_stock_status(self):
        """测试确定库存状态"""
        service = InventoryReportService()

        # 测试缺货
        assert service._determine_stock_status(0, 10, 0) == "out"

        # 测试低库存
        assert service._determine_stock_status(5, 10, 5) == "low"

        # 测试积压
        assert service._determine_stock_status(1000, 10, 90) == "overstock"

        # 测试正常
        assert service._determine_stock_status(50, 10, 20) == "normal"


@pytest.mark.django_db
class TestReportModels:
    """测试报表模型"""

    def test_create_report(self):
        """测试创建报表"""
        from apps.core.models import Platform

        platform = Platform.objects.create(name="测试平台")

        report = Report.objects.create(
            name="测试销售报表", report_type="sales", platform=platform, description="这是一个测试报表"
        )

        assert report.id is not None
        assert report.name == "测试销售报表"
        assert report.report_type == "sales"

    def test_create_dashboard(self):
        """测试创建仪表盘"""
        from apps.users.models import User

        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        dashboard = Dashboard.objects.create(
            name="测试仪表盘", description="这是一个测试仪表盘", created_by=user, is_public=True
        )

        assert dashboard.id is not None
        assert dashboard.name == "测试仪表盘"
        assert dashboard.is_public is True

    def test_create_dashboard_widget(self):
        """测试创建仪表盘组件"""
        widget = DashboardWidget.objects.create(
            name="销售总额",
            widget_type="metric",
            title="总销售额",
            data_source="SalesSummary",
            data_params={"period": "daily"},
            width=4,
            height=3,
        )

        assert widget.id is not None
        assert widget.widget_type == "metric"
        assert widget.width == 4


@pytest.mark.django_db
class TestReportGenerator:
    """测试报表生成器"""

    def test_service_initialization(self):
        """测试服务初始化"""
        generator = ReportGenerator()

        assert generator.sales_service is not None
        assert generator.inventory_service is not None
        assert generator.platform_service is not None
