"""
测试5个新平台适配器：Shopee, TikTok Shop, Temu, Wish, MercadoLibre
"""
import pytest
from unittest.mock import Mock, patch
from ecomm_sync.adapters.shopee.adapter import ShopeeAdapter
from ecomm_sync.adapters.tiktok.adapter import TikTokAdapter
from ecomm_sync.adapters.temu.adapter import TemuAdapter
from ecomm_sync.adapters.wish.adapter import WishAdapter
from ecomm_sync.adapters.mercadolibre.adapter import MercadoLibreAdapter
from apps.ecomm_sync.models import PlatformAccount, Platform


class TestShopeeAdapter:
    """测试Shopee适配器"""

    @pytest.fixture
    def mock_account(self):
        mock_platform = Mock(spec=Platform)
        mock_account = Mock(spec=PlatformAccount)
        mock_account.account_type = 'shopee'
        mock_account.auth_config = {
            'partner_id': 'test_partner_id',
            'shop_id': 'test_shop_id',
            'partner_key': 'test_partner_key',
            'region': 'sg'
        }
        return mock_account

    @pytest.fixture
    def adapter(self, mock_account):
        return ShopeeAdapter(mock_account)

    def test_init(self, mock_account):
        adapter = ShopeeAdapter(mock_account)
        assert adapter.partner_id == 'test_partner_id'
        assert adapter.shop_id == 'test_shop_id'

    @patch('ecomm_sync.adapters.shopee.adapter.BaseAdapter._make_request')
    def test_test_connection(self, mock_request, adapter):
        mock_request.return_value = {}
        result = adapter.test_connection()
        assert result is True

    def test_map_order_status(self, adapter):
        assert adapter._map_order_status('UNPAID') == 'pending'
        assert adapter._map_order_status('PAID') == 'paid'
        assert adapter._map_order_status('SHIPPED') == 'shipped'
        assert adapter._map_order_status('COMPLETED') == 'delivered'


class TestTikTokAdapter:
    """测试TikTok Shop适配器"""

    @pytest.fixture
    def mock_account(self):
        mock_platform = Mock(spec=Platform)
        mock_account = Mock(spec=PlatformAccount)
        mock_account.account_type = 'tiktok'
        mock_account.auth_config = {
            'app_key': 'test_app_key',
            'app_secret': 'test_app_secret',
            'shop_id': 'test_shop_id',
            'access_token': 'test_token'
        }
        return mock_account

    @pytest.fixture
    def adapter(self, mock_account):
        return TikTokAdapter(mock_account)

    def test_init(self, mock_account):
        adapter = TikTokAdapter(mock_account)
        assert adapter.app_key == 'test_app_key'
        assert adapter.shop_id == 'test_shop_id'

    @patch('ecomm_sync.adapters.tiktok.adapter.BaseAdapter._make_request')
    def test_test_connection(self, mock_request, adapter):
        mock_request.return_value = {'code': 0}
        result = adapter.test_connection()
        assert result is True

    def test_map_order_status(self, adapter):
        assert adapter._map_order_status('UNPAID') == 'pending'
        assert adapter._map_order_status('AWAITING_SHIPMENT') == 'paid'
        assert adapter._map_order_status('IN_TRANSIT') == 'shipped'
        assert adapter._map_order_status('DELIVERED') == 'delivered'


class TestTemuAdapter:
    """测试Temu适配器"""

    @pytest.fixture
    def mock_account(self):
        mock_platform = Mock(spec=Platform)
        mock_account = Mock(spec=PlatformAccount)
        mock_account.account_type = 'temu'
        mock_account.auth_config = {
            'access_key': 'test_access_key',
            'access_secret': 'test_access_secret',
            'seller_id': 'test_seller_id'
        }
        return mock_account

    @pytest.fixture
    def adapter(self, mock_account):
        return TemuAdapter(mock_account)

    def test_init(self, mock_account):
        adapter = TemuAdapter(mock_account)
        assert adapter.access_key == 'test_access_key'
        assert adapter.seller_id == 'test_seller_id'

    @patch('ecomm_sync.adapters.temu.adapter.BaseAdapter._make_request')
    def test_test_connection(self, mock_request, adapter):
        mock_request.return_value = {'success': True}
        result = adapter.test_connection()
        assert result is True

    def test_map_order_status(self, adapter):
        assert adapter._map_order_status('PENDING') == 'pending'
        assert adapter._map_order_status('PAID') == 'paid'
        assert adapter._map_order_status('SHIPPED') == 'shipped'
        assert adapter._map_order_status('DELIVERED') == 'delivered'


class TestWishAdapter:
    """测试Wish适配器"""

    @pytest.fixture
    def mock_account(self):
        mock_platform = Mock(spec=Platform)
        mock_account = Mock(spec=PlatformAccount)
        mock_account.account_type = 'wish'
        mock_account.auth_config = {
            'api_key': 'test_api_key',
            'merchant_id': 'test_merchant_id'
        }
        return mock_account

    @pytest.fixture
    def adapter(self, mock_account):
        return WishAdapter(mock_account)

    def test_init(self, mock_account):
        adapter = WishAdapter(mock_account)
        assert adapter.api_key == 'test_api_key'
        assert adapter.merchant_id == 'test_merchant_id'

    @patch('ecomm_sync.adapters.wish.adapter.BaseAdapter._make_request')
    def test_test_connection(self, mock_request, adapter):
        mock_request.return_value = {'code': 0}
        result = adapter.test_connection()
        assert result is True

    def test_map_order_status(self, adapter):
        assert adapter._map_order_status('APPROVED') == 'pending'
        assert adapter._map_order_status('IN_PROGRESS') == 'processing'
        assert adapter._map_order_status('SHIPPED') == 'shipped'
        assert adapter._map_order_status('COMPLETED') == 'delivered'

    def test_map_product_status(self, adapter):
        assert adapter._map_product_status(True) == 'onsale'
        assert adapter._map_product_status(False) == 'offshelf'


class TestMercadoLibreAdapter:
    """测试MercadoLibre适配器"""

    @pytest.fixture
    def mock_account(self):
        mock_platform = Mock(spec=Platform)
        mock_account = Mock(spec=PlatformAccount)
        mock_account.account_type = 'mercadolibre'
        mock_account.auth_config = {
            'access_token': 'test_access_token',
            'seller_id': 'test_seller_id',
            'site_id': 'MLB'
        }
        return mock_account

    @pytest.fixture
    def adapter(self, mock_account):
        return MercadoLibreAdapter(mock_account)

    def test_init(self, mock_account):
        adapter = MercadoLibreAdapter(mock_account)
        assert adapter.access_token == 'test_access_token'
        assert adapter.seller_id == 'test_seller_id'

    @patch('ecomm_sync.adapters.mercadolibre.adapter.BaseAdapter._make_request')
    def test_test_connection(self, mock_request, adapter):
        mock_request.return_value = {'id': '123'}
        result = adapter.test_connection()
        assert result is True

    def test_map_order_status(self, adapter):
        assert adapter._map_order_status('payment_required') == 'pending'
        assert adapter._map_order_status('payment_received') == 'processing'
        assert adapter._map_order_status('shipped') == 'shipped'
        assert adapter._map_order_status('delivered') == 'delivered'

    def test_map_product_status(self, adapter):
        assert adapter._map_product_status('active') == 'onsale'
        assert adapter._map_product_status('paused') == 'onsale'
        assert adapter._map_product_status('closed') == 'onsale'
        assert adapter._map_product_status('inactive') == 'offshelf'
        assert adapter._map_product_status('deleted') == 'offshelf'
