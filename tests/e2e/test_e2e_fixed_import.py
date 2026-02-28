"""
Django ERP 简化版E2E测试（修复导入路径）

使用正确的导入路径：from purchase.models import XXX（不带apps前缀）
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone


@pytest.mark.django_db
@pytest.mark.e2e
class TestFixedImportE2E:
    """修复导入路径的端到端测试"""

    def test_purchase_order_flow(self):
        """测试完整的采购订单流程"""
        from products.models import Category, Product, Unit
        from purchase.models import PurchaseOrder, PurchaseOrderItem
        from suppliers.models import Supplier

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
        print(f"✅ 采购订单流程测试通过: {order.order_number}, 总金额: {order.total_amount}")

    def test_sales_order_flow(self):
        """测试完整的销售订单流程"""
        from customers.models import Customer
        from products.models import Category, Product, Unit
        from sales.models import SalesOrder, SalesOrderItem

        # 创建单位
        unit = Unit.objects.create(name="件", symbol="件", unit_type="count", is_default=True)

        # 创建分类
        category = Category.objects.create(name="测试分类", code="CAT002")

        # 创建产品
        product = Product.objects.create(
            code="PROD002",
            name="测试产品2",
            unit=unit,
            category=category,
            cost_price=Decimal("100.00"),
            selling_price=Decimal("150.00"),
        )

        # 创建客户
        customer = Customer.objects.create(
            name="测试客户", code="CUS001", contact="李四", phone="13900139000"
        )

        # 创建用户
        User = get_user_model()
        admin = User.objects.create_superuser(
            username="admin2", email="admin2@test.com", password="testpass123"
        )

        # 创建销售订单
        order = SalesOrder.objects.create(
            customer=customer,
            order_date=timezone.now().date(),
            status="pending",
            created_by=admin,
        )

        # 创建订单明细
        SalesOrderItem.objects.create(
            sales_order=order,
            product=product,
            quantity=Decimal("50"),
            unit_price=Decimal("150.00"),
        )

        # 重新计算总金额
        order.calculate_totals()

        # 验证
        assert order.status == "pending"
        assert order.items.count() == 1
        assert order.total_amount == Decimal("7500.00")
        print(f"✅ 销售订单流程测试通过: {order.order_number}")

    def test_inventory_stock_flow(self):
        """测试库存流程"""
        from inventory.models import InventoryStock, Warehouse
        from products.models import Category, Product, Unit

        # 创建仓库
        warehouse = Warehouse.objects.create(
            name="测试仓库", code="WH001", warehouse_type="main", is_active=True
        )

        # 创建单位
        unit = Unit.objects.create(name="件", symbol="件", unit_type="count", is_default=True)

        # 创建分类
        category = Category.objects.create(name="测试分类", code="CAT003")

        # 创建产品
        product = Product.objects.create(
            code="PROD003",
            name="测试产品3",
            unit=unit,
            category=category,
            cost_price=Decimal("100.00"),
            selling_price=Decimal("150.00"),
        )

        # 创建库存记录
        stock = InventoryStock.objects.create(
            product=product, warehouse=warehouse, quantity=Decimal("100")
        )

        # 验证
        assert stock.product == product
        assert stock.warehouse == warehouse
        assert stock.quantity == Decimal("100")
        print(f"✅ 库存流程测试通过: {product.name} = {stock.quantity}")

    def test_supplier_account_flow(self):
        """测试供应商应付账款流程"""
        from finance.models import SupplierAccount
        from purchase.models import PurchaseOrder
        from suppliers.models import Supplier

        # 创建供应商
        supplier = Supplier.objects.create(
            name="测试供应商", code="SUP002", contact="张三", phone="13800138000"
        )

        # 创建用户
        User = get_user_model()
        admin = User.objects.create_superuser(
            username="admin3", email="admin3@test.com", password="testpass123"
        )

        # 创建采购订单
        order = PurchaseOrder.objects.create(
            supplier=supplier,
            order_date=timezone.now().date(),
            total_amount=Decimal("10000.00"),
            status="approved",
            created_by=admin,
        )

        # 创建应付账款
        account = SupplierAccount.objects.create(
            supplier=supplier,
            purchase_order=order,
            invoice_amount=Decimal("10000.00"),
            paid_amount=Decimal("0"),
            outstanding_amount=Decimal("10000.00"),
        )

        # 验证
        assert account.supplier == supplier
        assert account.purchase_order == order
        assert account.invoice_amount == Decimal("10000.00")
        assert account.outstanding_amount == Decimal("10000.00")
        print(f"✅ 应付账款流程测试通过: {account.invoice_amount}")
