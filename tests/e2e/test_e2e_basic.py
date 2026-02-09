"""
Django ERP 基础E2E测试

验证基本的业务流程和数据模型
"""

from decimal import Decimal

import pytest
from django.db.models import Sum
from django.utils import timezone


@pytest.mark.django_db
@pytest.mark.e2e
class TestBasicE2E:
    """基础端到端测试"""

    def test_create_purchase_order(self, test_users, test_supplier, test_products, test_warehouse):
        """测试创建采购订单"""
        from apps.purchase.models import PurchaseOrder, PurchaseOrderItem

        admin = test_users["admin"]
        product1, product2, _ = test_products
        warehouse, _ = test_warehouse

        # 创建采购订单
        order = PurchaseOrder.objects.create(
            supplier=test_supplier,
            order_date=timezone.now().date(),
            expected_date=timezone.now().date() + timezone.timedelta(days=7),
            status="pending",
            created_by=admin,
        )

        # 创建订单明细
        PurchaseOrderItem.objects.create(
            purchase_order=order,
            product=product1,
            quantity=Decimal("100"),
            unit_price=Decimal("100.00"),
        )

        PurchaseOrderItem.objects.create(
            purchase_order=order,
            product=product2,
            quantity=Decimal("50"),
            unit_price=Decimal("150.00"),
        )

        # 重新计算总金额
        order.calculate_totals()

        # 验证
        assert order.status == "pending"
        assert order.items.count() == 2
        assert order.total_amount == Decimal("17500.00")
        print(f"✅ 采购订单创建成功: {order.order_number}, 总金额: {order.total_amount}")

    def test_create_sales_order(self, test_users, test_customer, test_products):
        """测试创建销售订单"""
        from apps.sales.models import SalesOrder, SalesOrderItem

        admin = test_users["admin"]
        product1, product2, _ = test_products

        # 创建销售订单
        order = SalesOrder.objects.create(
            customer=test_customer,
            order_date=timezone.now().date(),
            status="pending",
            created_by=admin,
        )

        # 创建订单明细
        SalesOrderItem.objects.create(
            sales_order=order,
            product=product1,
            quantity=Decimal("100"),
            unit_price=Decimal("150.00"),
        )

        SalesOrderItem.objects.create(
            sales_order=order,
            product=product2,
            quantity=Decimal("50"),
            unit_price=Decimal("200.00"),
        )

        # 重新计算总金额
        order.calculate_totals()

        # 验证
        assert order.status == "pending"
        assert order.items.count() == 2
        assert order.total_amount == Decimal("25000.00")
        print(f"✅ 销售订单创建成功: {order.order_number}, 总金额: {order.total_amount}")

    def test_inventory_stock_creation(self, test_products, test_warehouse):
        """测试库存记录创建"""
        from apps.inventory.models import InventoryStock

        warehouse, _ = test_warehouse
        product1, _, _ = test_products

        # 创建库存记录
        stock, created = InventoryStock.objects.get_or_create(
            product=product1, warehouse=warehouse, defaults={"quantity": Decimal("100")}
        )

        # 验证
        assert stock.product == product1
        assert stock.warehouse == warehouse
        assert stock.quantity == Decimal("100")
        print(f"✅ 库存记录创建成功: {product1.name} = {stock.quantity}")

    def test_supplier_account_creation(self, test_users, test_supplier):
        """测试供应商应付账款创建"""
        from apps.finance.models import SupplierAccount
        from apps.purchase.models import PurchaseOrder

        admin = test_users["admin"]

        # 创建采购订单
        order = PurchaseOrder.objects.create(
            supplier=test_supplier,
            order_date=timezone.now().date(),
            total_amount=Decimal("10000.00"),
            status="approved",
            created_by=admin,
        )

        # 创建应付账款
        account = SupplierAccount.objects.create(
            supplier=test_supplier,
            purchase_order=order,
            invoice_amount=Decimal("10000.00"),
            paid_amount=Decimal("0"),
            outstanding_amount=Decimal("10000.00"),
        )

        # 验证
        assert account.supplier == test_supplier
        assert account.purchase_order == order
        assert account.invoice_amount == Decimal("10000.00")
        assert account.outstanding_amount == Decimal("10000.00")
        print(f"✅ 应付账款创建成功: {account.invoice_amount}")

    def test_customer_account_creation(self, test_users, test_customer):
        """测试客户应收账款创建"""
        from apps.finance.models import CustomerAccount
        from apps.sales.models import SalesOrder

        admin = test_users["admin"]

        # 创建销售订单
        order = SalesOrder.objects.create(
            customer=test_customer,
            order_date=timezone.now().date(),
            total_amount=Decimal("15000.00"),
            status="confirmed",
            created_by=admin,
        )

        # 创建应收账款
        account = CustomerAccount.objects.create(
            customer=test_customer,
            sales_order=order,
            invoice_amount=Decimal("15000.00"),
            received_amount=Decimal("0"),
            outstanding_amount=Decimal("15000.00"),
        )

        # 验证
        assert account.customer == test_customer
        assert account.sales_order == order
        assert account.invoice_amount == Decimal("15000.00")
        assert account.outstanding_amount == Decimal("15000.00")
        print(f"✅ 应收账款创建成功: {account.invoice_amount}")

    def test_fixture_factory(
        self, test_users, test_supplier, test_customer, test_products, test_warehouse
    ):
        """测试FixtureFactory工厂类"""
        from apps.core.tests.test_fixtures import FixtureFactory

        admin = test_users["admin"]
        product1, _, _ = test_products

        # 使用工厂创建产品
        new_product = FixtureFactory.create_product(
            code="FACTORY001",
            name="工厂测试产品",
            cost_price=Decimal("80.00"),
            selling_price=Decimal("120.00"),
        )

        # 验证
        assert new_product.code == "FACTORY001"
        assert new_product.name == "工厂测试产品"
        assert new_product.cost_price == Decimal("80.00")
        assert new_product.selling_price == Decimal("120.00")
        print(f"✅ FixtureFactory测试成功: {new_product.name}")
