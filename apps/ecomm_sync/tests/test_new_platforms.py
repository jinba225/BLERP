"""
测试Jumia和Cdiscount平台适配器
"""
from unittest.mock import MagicMock, Mock, patch

import pytest
from ecomm_sync.adapters.cdiscount.adapter import CdiscountAdapter
from ecomm_sync.adapters.jumia.adapter import JumiaAdapter

from apps.ecomm_sync.models import Platform, PlatformAccount


class TestJumiaAdapter:
    """测试Jumia适配器"""

    @pytest.fixture
    def mock_account(self):
        """创建模拟平台账号"""
        mock_platform = Mock(spec=Platform)
        mock_account = Mock(spec=PlatformAccount)
        mock_account.account_type = "jumia"
        mock_account.auth_config = {
            "seller_id": "test_seller_id",
            "api_key": "test_api_key",
            "secret_key": "test_secret_key",
        }
        return mock_account

    @pytest.fixture
    def adapter(self, mock_account):
        """创建Jumia适配器实例"""
        return JumiaAdapter(mock_account)

    def test_init(self, mock_account):
        """测试适配器初始化"""
        adapter = JumiaAdapter(mock_account)
        assert adapter.seller_id == "test_seller_id"
        assert adapter.api_key == "test_api_key"
        assert adapter.secret_key == "test_secret_key"
        assert adapter.base_url == "https://sellercenter-api.jumia.com"

    def test_init_missing_config(self):
        """测试缺少配置时的初始化"""
        mock_account = Mock(spec=PlatformAccount)
        mock_account.account_type = "jumia"
        mock_account.auth_config = {}

        with pytest.raises(ValueError, match="API配置不完整"):
            JumiaAdapter(mock_account)

    @patch("ecomm_sync.adapters.jumia.adapter.BaseAdapter._make_request")
    def test_test_connection(self, mock_request, adapter):
        """测试连接"""
        mock_request.return_value = {"success": True}

        result = adapter.test_connection()
        assert result is True

    @patch("ecomm_sync.adapters.jumia.adapter.BaseAdapter._make_request")
    def test_get_products(self, mock_request, adapter):
        """测试获取商品列表"""
        mock_request.return_value = {
            "data": {
                "products": [
                    {
                        "product_id": "prod_1",
                        "sku": "sku_1",
                        "name": "Product 1",
                        "description": "Test product",
                        "price": {"amount": 100.0, "currency": "USD"},
                        "stock": 50,
                        "status": "active",
                        "images": ["img1.jpg", "img2.jpg"],
                    }
                ]
            }
        }

        products = adapter.get_products(limit=10)
        assert len(products) == 1
        assert products[0]["id"] == "prod_1"
        assert products[0]["sku"] == "sku_1"
        assert products[0]["price"] == 100.0

    @patch("ecomm_sync.adapters.jumia.adapter.BaseAdapter._make_request")
    def test_get_orders(self, mock_request, adapter):
        """测试获取订单列表"""
        mock_request.return_value = {
            "data": {
                "orders": [
                    {
                        "order_id": "order_1",
                        "status": "paid",
                        "total_amount": 200.0,
                        "currency": "USD",
                        "buyer_email": "test@example.com",
                        "buyer_name": "Test Buyer",
                        "buyer_phone": "+1234567890",
                        "shipping_address": {
                            "address_line1": "123 Test St",
                            "city": "Test City",
                            "state": "Test State",
                            "country_code": "US",
                            "postal_code": "12345",
                        },
                        "created_at": "2024-01-01T00:00:00Z",
                        "items": [
                            {
                                "sku": "sku_1",
                                "product_name": "Product 1",
                                "quantity": 2,
                                "unit_price": 100.0,
                                "product_id": "prod_1",
                            }
                        ],
                    }
                ]
            }
        }

        orders = adapter.get_orders(limit=10)
        assert len(orders) == 1
        assert orders[0]["order_id"] == "order_1"
        assert orders[0]["status"] == "paid"
        assert orders[0]["amount"] == 200.0

    def test_map_order_status(self, adapter):
        """测试订单状态映射"""
        assert adapter._map_order_status("new") == "pending"
        assert adapter._map_order_status("payment_pending") == "pending"
        assert adapter._map_order_status("paid") == "paid"
        assert adapter._map_order_status("processing") == "processing"
        assert adapter._map_order_status("shipped") == "shipped"
        assert adapter._map_order_status("delivered") == "delivered"
        assert adapter._map_order_status("cancelled") == "cancelled"

    def test_map_product_status(self, adapter):
        """测试商品状态映射"""
        assert adapter._map_product_status("active") == "onsale"
        assert adapter._map_product_status("enabled") == "onsale"
        assert adapter._map_product_status("published") == "onsale"
        assert adapter._map_product_status("inactive") == "offshelf"
        assert adapter._map_product_status("disabled") == "offshelf"


class TestCdiscountAdapter:
    """测试Cdiscount适配器"""

    @pytest.fixture
    def mock_account(self):
        """创建模拟平台账号"""
        mock_platform = Mock(spec=Platform)
        mock_account = Mock(spec=PlatformAccount)
        mock_account.account_type = "cdiscount"
        mock_account.auth_config = {
            "seller_id": "test_seller_id",
            "api_key": "test_api_key",
            "secret_key": "test_secret_key",
        }
        return mock_account

    @pytest.fixture
    def adapter(self, mock_account):
        """创建Cdiscount适配器实例"""
        return CdiscountAdapter(mock_account)

    def test_init(self, mock_account):
        """测试适配器初始化"""
        adapter = CdiscountAdapter(mock_account)
        assert adapter.seller_id == "test_seller_id"
        assert adapter.api_key == "test_api_key"
        assert adapter.secret_key == "test_secret_key"
        assert adapter.base_url == "https://api.cdiscount.com"

    def test_init_missing_config(self):
        """测试缺少配置时的初始化"""
        mock_account = Mock(spec=PlatformAccount)
        mock_account.account_type = "cdiscount"
        mock_account.auth_config = {}

        with pytest.raises(ValueError, match="API配置不完整"):
            CdiscountAdapter(mock_account)

    @patch("ecomm_sync.adapters.cdiscount.adapter.BaseAdapter._make_request")
    def test_test_connection(self, mock_request, adapter):
        """测试连接"""
        mock_request.return_value = {"success": True}

        result = adapter.test_connection()
        assert result is True

    @patch("ecomm_sync.adapters.cdiscount.adapter.BaseAdapter._make_request")
    def test_get_products(self, mock_request, adapter):
        """测试获取商品列表"""
        mock_request.return_value = {
            "data": {
                "products": [
                    {
                        "product_id": "prod_1",
                        "sku": "sku_1",
                        "name": "Product 1",
                        "description": "Test product",
                        "price": {"amount": 50.0, "currency": "EUR"},
                        "stock": 30,
                        "status": "active",
                        "images": ["img1.jpg", "img2.jpg"],
                    }
                ]
            }
        }

        products = adapter.get_products(limit=10)
        assert len(products) == 1
        assert products[0]["id"] == "prod_1"
        assert products[0]["sku"] == "sku_1"
        assert products[0]["price"] == 50.0
        assert products[0]["currency"] == "EUR"

    @patch("ecomm_sync.adapters.cdiscount.adapter.BaseAdapter._make_request")
    def test_get_orders(self, mock_request, adapter):
        """测试获取订单列表"""
        mock_request.return_value = {
            "data": {
                "orders": [
                    {
                        "order_id": "order_1",
                        "status": "payment_validated",
                        "total_amount": 100.0,
                        "currency": "EUR",
                        "buyer_email": "test@example.com",
                        "buyer_name": "Test Buyer",
                        "buyer_phone": "+33123456789",
                        "shipping_address": {
                            "address_line1": "123 Rue de Test",
                            "city": "Paris",
                            "state": "Ile-de-France",
                            "country_code": "FR",
                            "postal_code": "75001",
                        },
                        "created_at": "2024-01-01T00:00:00Z",
                        "items": [
                            {
                                "sku": "sku_1",
                                "product_name": "Product 1",
                                "quantity": 2,
                                "unit_price": 50.0,
                                "product_id": "prod_1",
                            }
                        ],
                    }
                ]
            }
        }

        orders = adapter.get_orders(limit=10)
        assert len(orders) == 1
        assert orders[0]["order_id"] == "order_1"
        assert orders[0]["status"] == "paid"
        assert orders[0]["amount"] == 100.0

    def test_map_order_status(self, adapter):
        """测试订单状态映射"""
        assert adapter._map_order_status("created") == "pending"
        assert adapter._map_order_status("payment_pending") == "pending"
        assert adapter._map_order_status("payment_validated") == "paid"
        assert adapter._map_order_status("processing") == "processing"
        assert adapter._map_order_status("shipped") == "shipped"
        assert adapter._map_order_status("delivered") == "delivered"
        assert adapter._map_order_status("cancelled") == "cancelled"

    def test_map_product_status(self, adapter):
        """测试商品状态映射"""
        assert adapter._map_product_status("active") == "onsale"
        assert adapter._map_product_status("online") == "onsale"
        assert adapter._map_product_status("published") == "onsale"
        assert adapter._map_product_status("inactive") == "offshelf"
        assert adapter._map_product_status("offline") == "offshelf"
