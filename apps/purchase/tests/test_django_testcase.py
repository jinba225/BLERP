"""
Django ERP 使用Django TestCase的测试

验证模型是否可以正常使用
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone


class PurchaseOrderTestCase(TestCase):
    """采购订单测试"""

    def test_purchase_order_creation(self):
        """测试创建采购订单"""
        from apps.products.models import Category, Product, Unit
        from apps.purchase.models import PurchaseOrder, PurchaseOrderItem
        from apps.suppliers.models import Supplier

        # 创建单位
        unit = Unit.objects.create(name="件", symbol="件", unit_type="count", is_default=True)

        # 创建分类
        category = Category.objects.create(name="测试分类", code="CAT001")

        # 创建产品
        product = Product.objects.create(
            code="PROD001",
            name="测试产品",
            unit=unit,
            category=category,
            cost_price=Decimal("100.00"),
            selling_price=Decimal("150.00"),
        )

        # 创建供应商
        supplier = Supplier.objects.create(
            name="测试供应商", code="SUP001", contact="张三", phone="13800138000"
        )

        # 创建用户
        User = get_user_model()
        admin = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="testpass123"
        )

        # 创建采购订单
        order = PurchaseOrder.objects.create(
            supplier=supplier,
            order_date=timezone.now().date(),
            expected_date=timezone.now().date() + timezone.timedelta(days=7),
            status="pending",
            created_by=admin,
        )

        # 创建订单明细
        PurchaseOrderItem.objects.create(
            purchase_order=order,
            product=product,
            quantity=Decimal("100"),
            unit_price=Decimal("100.00"),
        )

        # 重新计算总金额
        order.calculate_totals()

        # 验证
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total_amount, Decimal("10000.00"))
        print(f"✅ 采购订单创建成功: {order.order_number}, 总金额: {order.total_amount}")
