from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.ecomm_sync.models import (
    EcommPlatform, WooShopConfig, EcommProduct,
    SyncStrategy, SyncLog, ProductChangeLog
)
from apps.products.models import Product, ProductCategory, Unit

User = get_user_model()


class EcommPlatformModelTest(TestCase):
    """电商平台模型测试"""

    def setUp(self):
        """测试前准备数据"""
        self.platform = Platform.objects.create(
            platform_type='taobao',
            name='测试淘宝',
            base_url='https://item.taobao.com',
        )

    def test_platform_creation(self):
        """测试平台创建"""
        self.assertEqual(self.platform.name, '测试淘宝')
        self.assertEqual(self.platform.platform_type, 'taobao')
        self.assertTrue(self.platform.is_active)

    def test_platform_str(self):
        """测试平台字符串表示"""
        self.assertEqual(str(self.platform), '测试淘宝')


class EcommProductModelTest(TestCase):
    """电商商品模型测试"""

    def setUp(self):
        """测试前准备数据"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        self.platform = Platform.objects.create(
            platform_type='taobao',
            name='淘宝',
            base_url='https://item.taobao.com',
        )

    def test_product_creation(self):
        """测试电商商品创建"""
        ecomm_product = EcommProduct.objects.create(
            platform=self.platform,
            external_id='123456',
            external_url='https://item.taobao.com/item.htm?id=123456',
            raw_data={'title': '测试商品', 'price': 99.99},
            created_by=self.user
        )

        self.assertEqual(ecomm_product.external_id, '123456')
        self.assertEqual(ecomm_product.sync_status, 'pending')
        self.assertFalse(ecomm_product.is_delisted)


class SyncStrategyModelTest(TestCase):
    """同步策略模型测试"""

    def setUp(self):
        """测试前准备数据"""
        self.platform = Platform.objects.create(
            platform_type='taobao',
            name='淘宝',
            base_url='https://item.taobao.com',
        )

    def test_strategy_creation(self):
        """测试策略创建"""
        strategy = SyncStrategy.objects.create(
            platform=self.platform,
            name='测试策略',
            strategy_type='incremental',
            update_fields=['price', 'stock'],
            sync_interval_hours=24,
            batch_size=100
        )

        self.assertEqual(strategy.name, '测试策略')
        self.assertEqual(strategy.strategy_type, 'incremental')
        self.assertEqual(strategy.sync_interval_hours, 24)
        self.assertTrue(strategy.is_active)


class SyncLogModelTest(TestCase):
    """同步日志模型测试"""

    def setUp(self):
        """测试前准备数据"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        self.platform = Platform.objects.create(
            platform_type='taobao',
            name='淘宝',
            base_url='https://item.taobao.com',
        )

    def test_log_creation(self):
        """测试日志创建"""
        log = SyncLog.objects.create(
            log_type='sync',
            platform=self.platform,
            status='success',
            records_processed=100,
            records_succeeded=95,
            records_failed=5,
            execution_time=120.5,
            created_by=self.user
        )

        self.assertEqual(log.log_type, 'sync')
        self.assertEqual(log.status, 'success')
        self.assertEqual(log.records_processed, 100)
        self.assertEqual(log.execution_time, 120.5)


class ProductChangeLogModelTest(TestCase):
    """商品变更日志模型测试"""

    def setUp(self):
        """测试前准备数据"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        self.platform = Platform.objects.create(
            platform_type='taobao',
            name='淘宝',
            base_url='https://item.taobao.com',
        )
        self.ecomm_product = EcommProduct.objects.create(
            platform=self.platform,
            external_id='123456',
            external_url='https://item.taobao.com/item.htm?id=123456',
            created_by=self.user
        )

    def test_change_log_creation(self):
        """测试变更日志创建"""
        change_log = ProductChangeLog.objects.create(
            ecomm_product=self.ecomm_product,
            change_type='price',
            old_value={'price': 99.99},
            new_value={'price': 89.99},
            created_by=self.user
        )

        self.assertEqual(change_log.change_type, 'price')
        self.assertFalse(change_log.synced_to_woo)
        self.assertEqual(change_log.old_value, {'price': 99.99})
        self.assertEqual(change_log.new_value, {'price': 89.99})
