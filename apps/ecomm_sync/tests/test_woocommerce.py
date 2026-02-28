from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from ecomm_sync.woocommerce.api import WooCommerceAPI, WooCommerceAPIError
from ecomm_sync.woocommerce.batch_sync import WooCommerceBatchSync
from ecomm_sync.woocommerce.mapper import WooCommerceMapper

from apps.core.models import EcommProduct, Platform, ProductChangeLog
from apps.products.models import Product, ProductCategory, Unit

User = get_user_model()


class WooCommerceAPITest(TestCase):
    """WooCommerce API测试"""

    def setUp(self):
        """测试前准备数据"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        self.platform = Platform.objects.create(
            platform_type="taobao",
            name="淘宝",
            base_url="https://item.taobao.com",
        )

    def test_api_initialization(self):
        """测试API初始化"""
        from apps.ecomm_sync.models import WooShopConfig

        config = WooShopConfig.objects.create(
            shop_url="https://example.com",
            consumer_key="test_key",
            consumer_secret="test_secret",
            created_by=self.user,
        )

        api = WooCommerceAPI(config)

        self.assertEqual(api.base_url, "https://example.com/wp-json/wc/v3")
        self.assertEqual(api.consumer_key, "test_key")

    @patch("ecomm_sync.woocommerce.api.requests.Session")
    def test_get_products(self, mock_session):
        """测试获取产品列表"""
        from apps.ecomm_sync.models import WooShopConfig

        config = WooShopConfig.objects.create(
            shop_url="https://example.com",
            consumer_key="test_key",
            consumer_secret="test_secret",
            created_by=self.user,
        )

        mock_response = Mock()
        mock_response.json.return_value = [{"id": 1, "name": "Test Product"}]
        mock_response.raise_for_status = Mock()

        mock_session_instance = MagicMock()
        mock_session_instance.request.return_value = mock_response
        mock_session.return_value = mock_session_instance

        api = WooCommerceAPI(config)
        products = api.get_products()

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["name"], "Test Product")

    @patch("ecomm_sync.woocommerce.api.requests.Session.request")
    def test_api_error_handling(self, mock_request):
        """测试API错误处理"""
        from apps.ecomm_sync.models import WooShopConfig

        config = WooShopConfig.objects.create(
            shop_url="https://example.com",
            consumer_key="test_key",
            consumer_secret="test_secret",
            created_by=self.user,
        )

        class MockHTTPError(Exception):
            def __init__(self):
                self.response = Mock()
                self.response.status_code = 404
                super().__init__("Not Found")

        mock_response = Mock()
        mock_response.json.return_value = {"code": "woocommerce_rest_product_not_found"}
        mock_response.raise_for_status = Mock(side_effect=MockHTTPError())
        mock_request.return_value = mock_response

        api = WooCommerceAPI(config)

        with self.assertRaises(WooCommerceAPIError) as context:
            api.get_product(999)


class WooCommerceMapperTest(TestCase):
    """WooCommerce映射器测试"""

    def setUp(self):
        """测试前准备数据"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        self.platform = Platform.objects.create(
            platform_type="taobao",
            name="淘宝",
            base_url="https://item.taobao.com",
        )

        self.category = ProductCategory.objects.create(
            name="测试分类", code="TEST_CAT", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pc", created_by=self.user)

        self.product = Product.objects.create(
            name="测试产品",
            code="TEST001",
            product_type="finished",
            category=self.category,
            unit=self.unit,
            selling_price=99.99,
            cost_price=50.00,
            description="这是一个测试产品",
            track_inventory=True,
            min_stock=10,
            created_by=self.user,
        )

        self.ecomm_product = EcommProduct.objects.create(
            platform=self.platform,
            external_id="123456",
            external_url="https://item.taobao.com/item.htm?id=123456",
            product=self.product,
            raw_data={
                "title": "测试产品",
                "price": 99.99,
                "description": "详细描述",
                "brand": "测试品牌",
            },
            created_by=self.user,
        )

    def test_map_to_woo(self):
        """测试映射到WooCommerce"""
        woo_data = WooCommerceMapper.map_to_woo(self.ecomm_product)

        self.assertEqual(woo_data["name"], "测试产品")
        self.assertEqual(woo_data["sku"], "TEST001")
        self.assertEqual(woo_data["regular_price"], "99.99")
        self.assertEqual(woo_data["status"], "publish")
        self.assertEqual(woo_data["manage_stock"], True)
        self.assertEqual(woo_data["stock_quantity"], "10")

        meta_data = woo_data["meta_data"]
        external_url_meta = next((m for m in meta_data if m["key"] == "external_url"), None)
        self.assertIsNotNone(external_url_meta)
        self.assertEqual(external_url_meta["value"], "https://item.taobao.com/item.htm?id=123456")

    def test_map_status(self):
        """测试状态映射"""
        self.assertEqual(WooCommerceMapper._map_status("active"), "publish")
        self.assertEqual(WooCommerceMapper._map_status("inactive"), "draft")
        self.assertEqual(WooCommerceMapper._map_status("discontinued"), "private")
        self.assertEqual(WooCommerceMapper._map_status("unknown"), "draft")

    def test_extract_price_update(self):
        """测试提取价格更新"""
        price_update = WooCommerceMapper.extract_price_update(self.ecomm_product)

        self.assertEqual(price_update["regular_price"], "99.99")

    def test_extract_stock_update(self):
        """测试提取库存更新"""
        stock_update = WooCommerceMapper.extract_stock_update(self.ecomm_product)

        self.assertEqual(stock_update["manage_stock"], True)
        self.assertEqual(stock_update["stock_quantity"], "10")
        self.assertEqual(stock_update["stock_status"], "instock")

    def test_extract_status_update(self):
        """测试提取状态更新"""
        status_update = WooCommerceMapper.extract_status_update(self.ecomm_product)

        self.assertEqual(status_update["status"], "publish")


class WooCommerceBatchSyncTest(TestCase):
    """WooCommerce批量同步器测试"""

    def setUp(self):
        """测试前准备数据"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        self.platform = Platform.objects.create(
            platform_type="taobao",
            name="淘宝",
            base_url="https://item.taobao.com",
        )

        self.category = ProductCategory.objects.create(
            name="测试分类", code="TEST_CAT", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pc", created_by=self.user)

        self.product = Product.objects.create(
            name="测试产品",
            code="TEST001",
            product_type="finished",
            category=self.category,
            unit=self.unit,
            selling_price=99.99,
            cost_price=50.00,
            description="这是一个测试产品",
            track_inventory=True,
            min_stock=10,
            created_by=self.user,
        )

        self.ecomm_product = EcommProduct.objects.create(
            platform=self.platform,
            external_id="123456",
            external_url="https://item.taobao.com/item.htm?id=123456",
            product=self.product,
            raw_data={"title": "测试产品", "price": 99.99},
            created_by=self.user,
        )

    @patch("ecomm_sync.woocommerce.batch_sync.WooCommerceAPI.get_active")
    def test_sync_single_product_create(self, mock_get_active):
        """测试同步单个产品（创建）"""
        mock_api = MagicMock()
        mock_api.create_product.return_value = {"id": 123}
        mock_get_active.return_value = mock_api

        syncer = WooCommerceBatchSync()
        result = syncer.sync_single_product(self.ecomm_product, update_type="full")

        self.assertTrue(result["success"])
        self.assertEqual(result["woo_product_id"], 123)
        mock_api.create_product.assert_called_once()

        self.ecomm_product.refresh_from_db()
        self.assertEqual(self.ecomm_product.woo_product_id, 123)

    @patch("ecomm_sync.woocommerce.batch_sync.WooCommerceAPI.get_active")
    def test_sync_single_product_update(self, mock_get_active):
        """测试同步单个产品（更新）"""
        self.ecomm_product.woo_product_id = 123
        self.ecomm_product.save()

        mock_api = MagicMock()
        mock_api.update_product.return_value = {"id": 123}
        mock_get_active.return_value = mock_api

        syncer = WooCommerceBatchSync()
        result = syncer.sync_single_product(self.ecomm_product, update_type="full")

        self.assertTrue(result["success"])
        self.assertTrue(mock_api.update_product.called)
        call_args = mock_api.update_product.call_args
        self.assertEqual(call_args[0][0], 123)
        self.assertIn("name", call_args[0][1])

    @patch("ecomm_sync.woocommerce.batch_sync.WooCommerceAPI.get_active")
    def test_sync_batch_products(self, mock_get_active):
        """测试批量同步产品"""
        mock_api = MagicMock()
        mock_api.create_product.return_value = {"id": 123}
        mock_get_active.return_value = mock_api

        syncer = WooCommerceBatchSync()
        results = syncer.sync_batch_products([self.ecomm_product])

        self.assertEqual(results["total"], 1)
        self.assertEqual(results["succeeded"], 1)
        self.assertEqual(results["failed"], 0)

    @patch("ecomm_sync.woocommerce.batch_sync.WooCommerceAPI.get_active")
    def test_sync_change_logs(self, mock_get_active):
        """测试同步变更日志"""
        change_log = ProductChangeLog.objects.create(
            ecomm_product=self.ecomm_product,
            change_type="price",
            old_value={"price": 99.99},
            new_value={"price": 89.99},
            created_by=self.user,
        )

        mock_api = MagicMock()
        mock_api.update_product.return_value = {"id": 123}
        mock_get_active.return_value = mock_api

        syncer = WooCommerceBatchSync()
        results = syncer.sync_change_logs([change_log])

        self.assertEqual(results["total"], 1)
        self.assertEqual(results["succeeded"], 1)

        change_log.refresh_from_db()
        self.assertTrue(change_log.synced_to_woo)
        self.assertIsNotNone(change_log.woo_synced_at)

    def test_create_sync_log(self):
        """测试创建同步日志"""
        sync_log = WooCommerceBatchSync.create_sync_log(self.platform, "sync")

        self.assertEqual(sync_log.log_type, "sync")
        self.assertEqual(sync_log.platform, self.platform)
        self.assertEqual(sync_log.status, "running")

    def test_update_sync_log(self):
        """测试更新同步日志"""
        sync_log = WooCommerceBatchSync.create_sync_log(self.platform, "sync")

        WooCommerceBatchSync.update_sync_log(
            sync_log=sync_log,
            status="success",
            records_processed=100,
            records_succeeded=95,
            records_failed=5,
            error_message="部分失败",
            execution_time=120.5,
        )

        sync_log.refresh_from_db()
        self.assertEqual(sync_log.status, "success")
        self.assertEqual(sync_log.records_processed, 100)
        self.assertEqual(sync_log.records_succeeded, 95)
        self.assertEqual(sync_log.records_failed, 5)
        self.assertEqual(sync_log.error_message, "部分失败")
        self.assertEqual(sync_log.execution_time, 120.5)
