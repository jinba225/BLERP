"""
Django ERP 简化版E2E测试（手动Django setup）

在测试文件开头手动设置Django环境
"""

import os
import sys
from decimal import Decimal

import django
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")

# 添加apps目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

django.setup()


@pytest.mark.django_db
@pytest.mark.e2e
class TestManualSetupE2E:
    """手动Django setup的端到端测试"""

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
        assert order.status == "pending"
        assert order.items.count() == 1
        assert order.total_amount == Decimal("10000.00")
        print(f"✅ 采购订单创建成功: {order.order_number}, 总金额: {order.total_amount}")
