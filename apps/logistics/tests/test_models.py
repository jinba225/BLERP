"""
物流模块测试

测试物流模型、适配器、服务等核心功能
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from logistics.adapters.factory import LogisticsAdapterFactory
from logistics.services.sync_service import LogisticsSyncService

from apps.logistics.models import LogisticsCompany, LogisticsCost, ShippingOrder, TrackingInfo


class LogisticsCompanyModelTest(TestCase):
    """物流公司模型测试"""

    def setUp(self):
        self.company = LogisticsCompany.objects.create(
            name="顺丰速运",
            code="SF",
            api_endpoint="https://sfapi.sf-express.com/std/service",
            tracking_url_template="https://www.sf-express.com/waybill/#search/all/{tracking_number}",
            tier="tier_1",
            is_active=True,
            api_config={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "check_word": "test_check_word",
            },
            website="https://www.sf-express.com",
        )

    def test_logistics_company_creation(self):
        """测试物流公司创建"""
        self.assertIsNotNone(self.company)
        self.assertEqual(self.company.name, "顺丰速运")
        self.assertEqual(self.company.code, "SF")
        self.assertTrue(self.company.is_active)
        self.assertEqual(self.company.tier, "tier_1")

    def test_logistics_company_unique_code(self):
        """测试物流公司代码唯一性"""
        # 尝试创建重复的code
        with self.assertRaises(Exception):
            LogisticsCompany.objects.create(
                name="顺丰速运2", code="SF", api_endpoint="https://test.com"
            )

    def test_logistics_company_api_config(self):
        """测试API配置"""
        self.assertEqual(self.company.api_config["client_id"], "test_client_id")
        self.assertEqual(self.company.api_config["client_secret"], "test_client_secret")

    def test_logistics_company_str(self):
        """测试物流公司字符串表示"""
        expected = "顺丰速运 (SF)"
        self.assertEqual(str(self.company), expected)


class ShippingOrderModelTest(TestCase):
    """物流订单模型测试"""

    def setUp(self):
        from apps.core.models import Platform
        from apps.ecomm_sync.models import PlatformOrder

        # 创建平台和平台订单（简化版）
        self.platform = Platform.objects.create(
            name="Amazon", code="amazon", platform_type="cross_border"
        )

        # 创建物流公司
        self.logistics_company = LogisticsCompany.objects.create(
            name="顺丰速运", code="SF", tier="tier_1", is_active=True
        )

        # 暂时跳过平台订单创建（需要更多依赖）
        # 直接创建物流订单
        self.shipping_order = ShippingOrder.objects.create(
            tracking_number="SF1234567890",
            logistics_company=self.logistics_company,
            shipping_status="shipped",
            shipping_cost=Decimal("15.50"),
            weight=Decimal("1.5"),
            shipped_at=timezone.now(),
        )

    def test_shipping_order_creation(self):
        """测试物流订单创建"""
        self.assertIsNotNone(self.shipping_order)
        self.assertEqual(self.shipping_order.tracking_number, "SF1234567890")
        self.assertEqual(self.shipping_order.shipping_status, "shipped")
        self.assertEqual(self.shipping_order.shipping_cost, Decimal("15.50"))
        self.assertEqual(self.shipping_order.weight, Decimal("1.5"))

    def test_shipping_order_status_choices(self):
        """测试物流订单状态选项"""
        valid_statuses = [
            "pending",
            "shipped",
            "in_transit",
            "out_for_delivery",
            "delivered",
            "failed",
            "returned",
            "cancelled",
        ]
        for status in valid_statuses:
            self.shipping_order.shipping_status = status
            self.shipping_order.save()
            self.assertEqual(self.shipping_order.shipping_status, status)

    def test_shipping_order_is_delivered_property(self):
        """测试是否已签收属性"""
        self.assertFalse(self.shipping_order.is_delivered)

        self.shipping_order.shipping_status = "delivered"
        self.shipping_order.save()

        # 重新获取对象
        shipping_order = ShippingOrder.objects.get(id=self.shipping_order.id)
        self.assertTrue(shipping_order.is_delivered)

    def test_shipping_order_days_in_transit(self):
        """测试运输天数"""
        self.shipping_order.delivered_at = self.shipping_order.shipped_at + timedelta(days=3)
        self.shipping_order.save()

        shipping_order = ShippingOrder.objects.get(id=self.shipping_order.id)
        self.assertEqual(shipping_order.days_in_transit, 3)


class TrackingInfoModelTest(TestCase):
    """物流轨迹模型测试"""

    def setUp(self):
        # 创建物流订单
        self.logistics_company = LogisticsCompany.objects.create(
            name="顺丰速运", code="SF", tier="tier_1", is_active=True
        )

        self.shipping_order = ShippingOrder.objects.create(
            tracking_number="SF1234567890",
            logistics_company=self.logistics_company,
            shipping_status="shipped",
        )

        # 创建物流轨迹
        self.tracking_info = TrackingInfo.objects.create(
            shipping_order=self.shipping_order,
            track_time=timezone.now(),
            track_status="已揽收",
            track_location="深圳",
            track_description="快件已揽收",
            operator="张三",
        )

    def test_tracking_info_creation(self):
        """测试物流轨迹创建"""
        self.assertIsNotNone(self.tracking_info)
        self.assertEqual(self.tracking_info.shipping_order, self.shipping_order)
        self.assertEqual(self.tracking_info.track_status, "已揽收")
        self.assertEqual(self.tracking_info.track_location, "深圳")
        self.assertEqual(self.tracking_info.operator, "张三")

    def test_tracking_info_str(self):
        """测试物流轨迹字符串表示"""
        expected = f"{self.shipping_order.tracking_number} - {self.tracking_info.track_time}"
        self.assertEqual(str(self.tracking_info), expected)


class LogisticsCostModelTest(TestCase):
    """物流成本模型测试"""

    def setUp(self):
        # 创建物流订单
        self.logistics_company = LogisticsCompany.objects.create(
            name="顺丰速运", code="SF", tier="tier_1", is_active=True
        )

        self.shipping_order = ShippingOrder.objects.create(
            tracking_number="SF1234567890",
            logistics_company=self.logistics_company,
            shipping_status="shipped",
            shipping_cost=Decimal("15.50"),
        )

        # 创建物流成本
        self.logistics_cost = LogisticsCost.objects.create(
            shipping_order=self.shipping_order,
            cost_type="freight",
            cost_amount=Decimal("12.00"),
            cost_date=timezone.now().date(),
        )

    def test_logistics_cost_creation(self):
        """测试物流成本创建"""
        self.assertIsNotNone(self.logistics_cost)
        self.assertEqual(self.logistics_cost.shipping_order, self.shipping_order)
        self.assertEqual(self.logistics_cost.cost_type, "freight")
        self.assertEqual(self.logistics_cost.cost_amount, Decimal("12.00"))

    def test_logistics_cost_type_choices(self):
        """测试物流成本类型选项"""
        valid_types = [
            "freight",
            "fuel_surcharge",
            "remote_area_fee",
            "cod_fee",
            "insurance",
            "package_fee",
            "other",
        ]
        for cost_type in valid_types:
            self.logistics_cost.cost_type = cost_type
            self.logistics_cost.save()
            self.assertEqual(self.logistics_cost.cost_type, cost_type)


class LogisticsAdapterFactoryTest(TestCase):
    """物流适配器工厂测试"""

    def setUp(self):
        self.company = LogisticsCompany.objects.create(
            name="顺丰速运",
            code="SF",
            tier="tier_1",
            is_active=True,
            api_config={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            },
        )

    def test_get_adapter(self):
        """测试获取适配器"""
        adapter = LogisticsAdapterFactory.get_adapter(self.company)
        self.assertIsNotNone(adapter)
        self.assertEqual(adapter.company, self.company)

    def test_get_adapter_invalid_code(self):
        """测试获取不存在的适配器"""
        with self.assertRaises(ValueError):
            company = LogisticsCompany.objects.create(
                name="不存在物流", code="INVALID", tier="tier_1", is_active=True
            )
            LogisticsAdapterFactory.get_adapter(company)

    def test_get_supported_codes(self):
        """测试获取支持的物流公司代码"""
        from logistics.adapters.sf.adapter import SFAdapter

        codes = LogisticsAdapterFactory.get_supported_codes()
        self.assertIn("SF", codes)
        self.assertIsInstance(codes, list)


class LogisticsSyncServiceTest(TestCase):
    """物流同步服务测试"""

    def setUp(self):
        self.service = LogisticsSyncService()

        # 创建测试数据
        self.logistics_company = LogisticsCompany.objects.create(
            name="顺丰速运",
            code="SF",
            tier="tier_1",
            is_active=True,
            api_config={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            },
        )

    def test_logistics_sync_service_initialization(self):
        """测试物流同步服务初始化"""
        self.assertIsNotNone(self.service)
        self.assertIsInstance(self.service.adapter_cache, dict)

    def test_map_logistics_status(self):
        """测试物流状态映射"""
        test_cases = [
            ("已揽收", "shipped"),
            ("运输中", "in_transit"),
            ("派送中", "out_for_delivery"),
            ("已签收", "delivered"),
            ("配送失败", "failed"),
            ("已退货", "returned"),
        ]

        for input_status, expected_status in test_cases:
            result = self.service._map_logistics_status(input_status)
            self.assertEqual(result, expected_status)

    def test_map_platform_status(self):
        """测试平台状态映射"""
        test_cases = [
            ("shipped", "processing"),
            ("in_transit", "shipped"),
            ("out_for_delivery", "shipped"),
            ("delivered", "shipped"),
            ("failed", "cancelled"),
            ("returned", "cancelled"),
            ("cancelled", "cancelled"),
        ]

        for input_status, expected_status in test_cases:
            result = self.service._map_platform_status(input_status)
            self.assertEqual(result, expected_status)
