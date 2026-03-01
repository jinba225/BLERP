"""
Django ERP 工作版E2E测试

使用正确的导入路径和字段名
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone


@pytest.mark.django_db
@pytest.mark.e2e
class TestWorkingE2E:
    """工作版端到端测试"""

    def test_purchase_order_creation(self):
        """测试创建采购订单"""
        from products.models import Product, ProductCategory, Unit
        from purchase.models import PurchaseOrder, PurchaseOrderItem
        from suppliers.models import Supplier

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

        # 创建供应商（只使用必填字段）
        supplier = Supplier.objects.create(name="测试供应商", code="SUP001")

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

    def test_sales_order_creation(self):
        """测试创建销售订单"""
        from customers.models import Customer
        from products.models import Product, ProductCategory, Unit
        from sales.models import SalesOrder, SalesOrderItem

        # 创建单位
        unit = Unit.objects.create(name="件", symbol="件", unit_type="count", is_default=True)

        # 创建分类
        category = ProductCategory.objects.create(name="测试分类2", code="CAT002")

        # 创建产品
        product = Product.objects.create(
            code="PROD002",
            name="测试产品2",
            unit=unit,
            category=category,
            cost_price=Decimal("100.00"),
            selling_price=Decimal("150.00"),
        )

        # 创建客户（只使用必填字段）
        customer = Customer.objects.create(name="测试客户", code="CUS001")

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
        print(f"✅ 销售订单创建成功: {order.order_number}, 总金额: {order.total_amount}")

    def test_inventory_stock_creation(self):
        """测试库存记录创建"""
        from inventory.models import InventoryStock, Warehouse
        from products.models import Product, ProductCategory, Unit

        # 创建仓库
        warehouse = Warehouse.objects.create(
            name="测试仓库", code="WH001", warehouse_type="main", is_active=True
        )

        # 创建单位
        unit = Unit.objects.create(name="件", symbol="件", unit_type="count", is_default=True)

        # 创建分类
        category = ProductCategory.objects.create(name="测试分类3", code="CAT003")

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
        print(f"✅ 库存记录创建成功: {product.name} = {stock.quantity}")

    def test_supplier_account_creation(self):
        """测试供应商应付账款创建"""
        from finance.models import SupplierAccount
        from purchase.models import PurchaseOrder
        from suppliers.models import Supplier

        # 创建供应商
        supplier = Supplier.objects.create(name="测试供应商2", code="SUP002")

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
        print(f"✅ 应付账款创建成功: {account.invoice_amount}")

    def test_complete_purchase_flow(self):
        """测试完整的采购流程"""
        from finance.models import SupplierAccount
        from products.models import Product, ProductCategory, Unit
        from purchase.models import PurchaseOrder, PurchaseOrderItem
        from suppliers.models import Supplier

        # 准备数据
        unit = Unit.objects.create(name="件", symbol="件", unit_type="count", is_default=True)

        category = ProductCategory.objects.create(name="完整测试分类", code="CAT_FULL")

        product = Product.objects.create(
            code="PRODFULL",
            name="完整测试产品",
            unit=unit,
            category=category,
            cost_price=Decimal("100.00"),
            selling_price=Decimal("150.00"),
        )

        supplier = Supplier.objects.create(name="完整测试供应商", code="SUPFULL")

        User = get_user_model()
        admin = User.objects.create_superuser(
            username="adminfull", email="adminfull@test.com", password="testpass123"
        )

        # 创建采购订单
        order = PurchaseOrder.objects.create(
            supplier=supplier,
            order_date=timezone.now().date(),
            status="approved",
            created_by=admin,
        )

        PurchaseOrderItem.objects.create(
            purchase_order=order,
            product=product,
            quantity=Decimal("100"),
            unit_price=Decimal("100.00"),
        )

        order.calculate_totals()

        # 创建应付账款
        account = SupplierAccount.objects.create(
            supplier=supplier,
            purchase_order=order,
            invoice_amount=order.total_amount,
            paid_amount=Decimal("0"),
            outstanding_amount=order.total_amount,
        )

        # 验证完整流程
        assert order.status == "approved"
        assert order.total_amount == Decimal("10000.00")
        assert account.invoice_amount == Decimal("10000.00")
        assert account.outstanding_amount == Decimal("10000.00")
        print("✅ 完整采购流程测试通过")
        print(f"  订单号: {order.order_number}")
        print(f"  订单金额: {order.total_amount}")
        print(f"  应付金额: {account.invoice_amount}")
