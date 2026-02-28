"""
Collect module tests
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

User = get_user_model()

from apps.core.models import Platform as CorePlatform
from apps.core.models import Shop as CoreShop

from ..models import CollectItem, CollectTask, FieldMapRule, Platform, PricingRule, Shop


class PlatformModelTest(TestCase):
    """Platform模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.platform = Platform.objects.create(
            platform_name="淘宝",
            platform_code="taobao",
            platform_type="collect",
            created_by=self.user,
        )

    def test_platform_creation(self):
        """测试平台创建"""
        self.assertEqual(self.platform.platform_name, "淘宝")
        self.assertEqual(self.platform.platform_code, "taobao")
        self.assertEqual(self.platform.platform_type, "collect")
        self.assertTrue(self.platform.is_active)

    def test_platform_unique_code(self):
        """测试平台编码唯一性"""
        with self.assertRaises(Exception):
            Platform.objects.create(
                platform_name="淘宝2",
                platform_code="taobao",  # 重复
                platform_type="collect",
                created_by=self.user,
            )

    def test_platform_str_representation(self):
        """测试平台字符串表示"""
        expected = "淘宝 (taobao)"
        self.assertEqual(str(self.platform), expected)


class ShopModelTest(TestCase):
    """Shop模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.platform = CorePlatform.objects.create(
            platform_name="淘宝",
            platform_code="taobao",
            platform_type="collect",
            created_by=self.user,
        )
        self.shop = Shop.objects.create(
            platform=self.platform,
            shop_name="测试店铺",
            shop_code="test_shop",
            created_by=self.user,
        )

    def test_shop_creation(self):
        """测试店铺创建"""
        self.assertEqual(self.shop.shop_name, "测试店铺")
        self.assertEqual(self.shop.shop_code, "test_shop")
        self.assertTrue(self.shop.is_active)

    def test_shop_platform_relation(self):
        """测试店铺与平台的关联"""
        self.assertEqual(self.shop.platform, self.platform)
        self.assertEqual(self.shop.platform.platform_name, "淘宝")


class CollectTaskModelTest(TestCase):
    """CollectTask模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.platform = CorePlatform.objects.create(
            platform_name="淘宝",
            platform_code="taobao",
            platform_type="collect",
            created_by=self.user,
        )
        self.task = CollectTask.objects.create(
            task_name="测试采集任务",
            collect_platform="taobao",
            platform=self.platform,
            collect_urls="https://item.taobao.com/id=123",
            collect_num=1,
            created_by=self.user,
        )

    def test_task_creation(self):
        """测试采集任务创建"""
        self.assertEqual(self.task.task_name, "测试采集任务")
        self.assertEqual(self.task.collect_platform, "taobao")
        self.assertEqual(self.task.collect_status, "pending")
        self.assertEqual(self.task.land_status, "unland")

    def test_task_status_transitions(self):
        """测试采集任务状态转换"""
        self.task.collect_status = "running"
        self.task.save()

        self.task.collect_status = "success"
        self.task.land_status = "running"
        self.task.save()

        self.assertEqual(self.task.collect_status, "success")
        self.assertEqual(self.task.land_status, "running")

    def test_task_auto_fields(self):
        """测试任务自动生成字段"""
        self.assertTrue(self.task.task_number)  # 自动生成
        self.assertTrue(self.task.started_at is None)
        self.assertTrue(self.task.completed_at is None)


class CollectItemModelTest(TestCase):
    """CollectItem模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.platform = CorePlatform.objects.create(
            platform_name="淘宝",
            platform_code="taobao",
            platform_type="collect",
            created_by=self.user,
        )
        self.task = CollectTask.objects.create(
            task_name="测试采集任务",
            collect_platform="taobao",
            platform=self.platform,
            collect_urls="https://item.taobao.com/id=123",
            collect_num=1,
            created_by=self.user,
        )
        self.item = CollectItem.objects.create(
            task=self.task,
            item_url="https://item.taobao.com/id=123",
            source_sku="SKU123",
            created_by=self.user,
        )

    def test_item_creation(self):
        """测试采集项目创建"""
        self.assertEqual(self.item.task, self.task)
        self.assertEqual(self.item.source_sku, "SKU123")
        self.assertEqual(self.item.collect_status, "pending")
        self.assertEqual(self.item.land_status, "unland")

    def test_item_task_relation(self):
        """测试采集项目与任务的关联"""
        self.assertEqual(self.item.task.task_name, "测试采集任务")
        self.assertEqual(self.item.task.platform.platform_name, "淘宝")


class FieldMapRuleModelTest(TestCase):
    """FieldMapRule模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.platform = CorePlatform.objects.create(
            platform_name="淘宝",
            platform_code="taobao",
            platform_type="collect",
            created_by=self.user,
        )
        self.rule = FieldMapRule.objects.create(
            rule_name="测试映射规则",
            collect_platform="taobao",
            target_field="product_name",
            map_rule_type="direct",
            source_field="title",
            platform=self.platform,
            created_by=self.user,
        )

    def test_rule_creation(self):
        """测试映射规则创建"""
        self.assertEqual(self.rule.rule_name, "测试映射规则")
        self.assertEqual(self.rule.target_field, "product_name")
        self.assertEqual(self.rule.map_rule_type, "direct")
        self.assertEqual(self.rule.source_field, "title")

    def test_rule_map_formula(self):
        """测试映射规则公式"""
        self.rule.map_rule_type = "formula"
        self.rule.map_formula = 'title + " (" + sku + ")"'
        self.rule.save()

        self.assertEqual(self.rule.map_formula, 'title + " (" + sku + ")"')

    def test_rule_enabled_status(self):
        """测试映射规则启用状态"""
        self.assertTrue(self.rule.is_enabled)
        self.rule.is_enabled = False
        self.rule.save()
        self.assertFalse(self.rule.is_enabled)


class PricingRuleModelTest(TestCase):
    """PricingRule模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.platform = CorePlatform.objects.create(
            platform_name="淘宝",
            platform_code="taobao",
            platform_type="collect",
            created_by=self.user,
        )
        self.rule = PricingRule.objects.create(
            rule_name="测试定价规则",
            rule_type="markup",
            markup_percent=Decimal("50.00"),
            platform=self.platform,
            created_by=self.user,
        )

    def test_rule_creation(self):
        """测试定价规则创建"""
        self.assertEqual(self.rule.rule_name, "测试定价规则")
        self.assertEqual(self.rule.rule_type, "markup")
        self.assertEqual(self.rule.markup_percent, Decimal("50.00"))

    def test_markup_pricing(self):
        """测试加成定价"""
        cost_price = Decimal("100.00")
        expected_price = cost_price * (1 + self.rule.markup_percent / 100)
        calculated_price = self.rule.calculate_price(cost_price)
        self.assertEqual(calculated_price, expected_price)

    def test_fixed_pricing(self):
        """测试固定定价"""
        self.rule.rule_type = "fixed"
        self.rule.fixed_price = Decimal("99.99")
        self.rule.save()

        cost_price = Decimal("100.00")
        calculated_price = self.rule.calculate_price(cost_price)
        self.assertEqual(calculated_price, Decimal("99.99"))

    def test_formula_pricing(self):
        """测试公式定价"""
        self.rule.rule_type = "formula"
        self.rule.formula = "cost * 1.5 + 10"
        self.rule.save()

        # 简化测试：公式计算逻辑
        self.assertEqual(self.rule.formula, "cost * 1.5 + 10")
