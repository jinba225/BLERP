"""
Django ERP 最简化E2E测试

只测试最基本的模型创建和关联
"""

from decimal import Decimal

import pytest
from django.utils import timezone


@pytest.mark.django_db
@pytest.mark.e2e
class TestMinimalE2E:
    """最简化端到端测试"""

    def test_create_product_and_unit(self):
        """测试创建产品和单位"""
        from products.models import Product, ProductCategory, Unit

        # 创建单位
        unit = Unit.objects.create(name="件", symbol="件", unit_type="count", is_default=True)

        # 创建分类
        category = ProductCategory.objects.create(name="测试分类", code="CAT001")

        # 创建产品
        product = Product.objects.create(
            code="PROD001",
            name="测试产品",
            unit=unit,
            category=category,
            cost_price=Decimal("100.00"),
            selling_price=Decimal("150.00"),
        )

        # 验证
        assert product.code == "PROD001"
        assert product.name == "测试产品"
        assert product.unit == unit
        assert product.category == category
        print(f"✅ 产品创建成功: {product.name}")

    def test_create_supplier(self):
        """测试创建供应商"""
        from suppliers.models import Supplier

        supplier = Supplier.objects.create(name="测试供应商", code="SUP001")

        assert supplier.code == "SUP001"
        assert supplier.name == "测试供应商"
        print(f"✅ 供应商创建成功: {supplier.name}")

    def test_create_customer(self):
        """测试创建客户"""
        from customers.models import Customer

        customer = Customer.objects.create(name="测试客户", code="CUS001")

        assert customer.code == "CUS001"
        assert customer.name == "测试客户"
        print(f"✅ 客户创建成功: {customer.name}")

    def test_create_warehouse(self):
        """测试创建仓库"""
        from inventory.models import Warehouse

        warehouse = Warehouse.objects.create(
            name="测试仓库", code="WH001", warehouse_type="main", is_active=True
        )

        assert warehouse.code == "WH001"
        assert warehouse.name == "测试仓库"
        print(f"✅ 仓库创建成功: {warehouse.name}")

    def test_create_purchase_order(self):
        """测试创建采购订单"""
        from django.contrib.auth import get_user_model
        from products.models import Product, ProductCategory, Unit
        from purchase.models import PurchaseOrder, PurchaseOrderItem
        from suppliers.models import Supplier

        # 准备数据
        unit = Unit.objects.create(name="件", symbol="件", unit_type="count")

        category = ProductCategory.objects.create(name="测试分类", code="CAT002")

        product = Product.objects.create(code="PROD002", name="测试产品2", unit=unit, category=category)

        supplier = Supplier.objects.create(name="测试供应商2", code="SUP002")

        User = get_user_model()
        admin = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="testpass123"
        )

        # 创建采购订单
        order = PurchaseOrder.objects.create(
            supplier=supplier, order_date=timezone.now().date(), created_by=admin
        )

        # 创建订单明细
        PurchaseOrderItem.objects.create(
            purchase_order=order,
            product=product,
            quantity=Decimal("10"),
            unit_price=Decimal("100.00"),
        )

        order.calculate_totals()

        # 验证
        assert order.supplier == supplier
        assert order.items.count() == 1
        assert order.total_amount == Decimal("1000.00")
        print(f"✅ 采购订单创建成功: {order.order_number}, 总金额: {order.total_amount}")

    def test_create_sales_order(self):
        """测试创建销售订单"""
        from customers.models import Customer
        from django.contrib.auth import get_user_model
        from products.models import Product, ProductCategory, Unit
        from sales.models import SalesOrder, SalesOrderItem

        # 准备数据
        unit = Unit.objects.create(name="件", symbol="件", unit_type="count")

        category = ProductCategory.objects.create(name="测试分类3", code="CAT003")

        product = Product.objects.create(code="PROD003", name="测试产品3", unit=unit, category=category)

        customer = Customer.objects.create(name="测试客户3", code="CUS003")

        User = get_user_model()
        admin = User.objects.create_superuser(
            username="admin2", email="admin2@test.com", password="testpass123"
        )

        # 创建销售订单
        order = SalesOrder.objects.create(
            customer=customer, order_date=timezone.now().date(), created_by=admin
        )

        # 创建订单明细
        SalesOrderItem.objects.create(
            order=order,
            product=product,
            quantity=Decimal("10"),
            unit_price=Decimal("150.00"),
        )

        order.calculate_totals()

        # 验证
        assert order.customer == customer
        assert order.items.count() == 1
        assert order.total_amount == Decimal("1500.00")
        print(f"✅ 销售订单创建成功: {order.order_number}, 总金额: {order.total_amount}")
