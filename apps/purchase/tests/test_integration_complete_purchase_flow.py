"""
Django ERP 采购流程完整集成测试

测试覆盖:
1. 完整采购正向流程（申请→订单→收货→库存→应付→付款）
2. 采购退货流程（退货→出库→库存→应付退款）
3. 分批收货和分批退货复杂场景

作者: Claude Code
日期: 2026-02-03
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.departments.models import Department
from apps.finance.models import Payment, SupplierAccount, SupplierAccountDetail
from apps.inventory.models import InventoryStock, InventoryTransaction, Location, Warehouse
from apps.products.models import Product, Unit
from apps.purchase.models import (
    PurchaseReceipt,
    PurchaseReceiptItem,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseReturn,
    PurchaseReturnItem,
)
from apps.suppliers.models import Supplier

User = get_user_model()


# ==================== 测试数据fixture ====================


def create_test_users():
    """创建测试用户"""
    users = {}
    users["test_user"] = User.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test_pass123",
        first_name="测试",
        last_name="用户",
    )
    users["approver"] = User.objects.create_user(
        username="approver",
        email="approver@example.com",
        password="approve_pass123",
        first_name="审核",
        last_name="人员",
    )
    users["warehouse_admin"] = User.objects.create_user(
        username="warehouse_admin",
        email="warehouse_admin@example.com",
        password="warehouse_pass123",
        first_name="仓库",
        last_name="管理员",
    )
    return users


def create_test_department(approver):
    """创建测试部门"""
    return Department.objects.create(name="采购部", code="PURCHASE", manager=approver)


def create_test_supplier():
    """创建测试供应商"""
    return Supplier.objects.create(
        name="测试供应商", code="SUP001", address="测试地址", city="测试城市", payment_terms="bank_transfer"
    )


def create_test_unit():
    """创建测试单位"""
    return Unit.objects.create(name="件", symbol="件", unit_type="count", is_default=True)


def create_test_products(unit):
    """创建测试产品"""
    product1 = Product.objects.create(
        name="产品A",
        code="PROD001",
        cost_price=Decimal("80.00"),
        selling_price=Decimal("100.00"),
        min_stock=10,
        unit=unit,
    )
    product2 = Product.objects.create(
        name="产品B",
        code="PROD002",
        cost_price=Decimal("150.00"),
        selling_price=Decimal("200.00"),
        min_stock=5,
        unit=unit,
    )
    return product1, product2


def create_test_warehouse(warehouse_admin):
    """创建测试仓库"""
    warehouse = Warehouse.objects.create(
        name="主仓库", code="WH001", warehouse_type="main", manager=warehouse_admin, is_active=True
    )
    location = Location.objects.create(
        warehouse=warehouse, code="A01", name="A区01排", is_active=True
    )
    return warehouse, location


# ==================== 测试用例1：完整采购正向流程 ====================


class Test1CompletePurchaseFlow(TestCase):
    """测试用例1: 完整采购正向流程（含分批入库）"""

    def setUp(self):
        """准备测试数据"""
        print("\n========== 测试数据准备开始 ==========")
        self.users = create_test_users()
        self.department = create_test_department(self.users["approver"])
        self.supplier = create_test_supplier()
        self.unit = create_test_unit()
        self.product1, self.product2 = create_test_products(self.unit)
        self.warehouse, self.location = create_test_warehouse(self.users["warehouse_admin"])
        self.today = timezone.now().date()
        print("✅ 测试数据准备完成")
        print("========== 测试数据准备完成 ==========\n")

    def test_1_to_9_complete_flow(self):
        """测试1-9：完整采购正向流程（所有步骤合并为一个测试）"""
        print("\n========== 测试1: 完整采购正向流程 ==========")

        # 1. 创建采购申请单
        request = PurchaseRequest.objects.create(
            request_number="PR2025001",
            requester=self.users["test_user"],
            department=self.department,
            request_date=self.today,
            required_date=self.today + timedelta(days=7),
            status="draft",
            created_by=self.users["test_user"],
        )

        PurchaseRequestItem.objects.create(
            purchase_request=request,
            product=self.product1,
            quantity=100,
            estimated_price=Decimal("100.00"),
            created_by=self.users["test_user"],
        )
        print("✅ 1.1 创建采购申请单")

        # 2. 审核并转换为采购订单
        order, _ = request.approve_and_convert_to_order(
            approved_by_user=self.users["approver"],
            supplier_id=self.supplier.id,
            warehouse_id=self.warehouse.id,
            auto_create_order=True,
        )
        print("✅ 1.2 审核并转换为采购订单")

        # 3. 审核采购订单
        order.approve_order(
            approved_by_user=self.users["approver"],
            warehouse=self.warehouse,
            auto_create_receipt=False,
        )
        print("✅ 1.3 审核采购订单")

        order_item1 = order.items.first()
        supplier_account = SupplierAccount.get_or_create_for_order(order)

        # 4. 创建第一次收货单（60件）
        receipt1 = PurchaseReceipt.objects.create(
            receipt_number="RCT2025001",
            purchase_order=order,
            warehouse=self.warehouse,
            receipt_date=self.today,
            status="received",
            created_by=self.users["test_user"],
        )

        PurchaseReceiptItem.objects.create(
            receipt=receipt1,
            order_item=order_item1,
            received_quantity=60,
            created_by=self.users["test_user"],
        )

        order_item1.received_quantity = 60
        order_item1.save()

        InventoryTransaction.objects.create(
            transaction_type="in",
            product=self.product1,
            warehouse=self.warehouse,
            quantity=60,
            unit_cost=Decimal("100.00"),
            reference_number=receipt1.receipt_number,
            operator=self.users["warehouse_admin"],
        )

        SupplierAccountDetail.objects.create(
            detail_number="SAD2025001",
            detail_type="receipt",
            supplier=self.supplier,
            purchase_order=order,
            receipt=receipt1,
            amount=Decimal("6000.00"),
            parent_account=supplier_account,
            business_date=self.today,
        )
        print("✅ 1.4 创建第一次收货单（60件）")

        # 5. 验证库存增加
        stock1 = InventoryStock.objects.get(product=self.product1, warehouse=self.warehouse)
        self.assertEqual(stock1.quantity, 60)
        print("✅ 1.5 验证库存增加: 60件")

        # 6. 验证应付账款
        supplier_account.aggregate_from_details()
        self.assertEqual(supplier_account.invoice_amount, Decimal("6000.00"))
        print("✅ 1.6 验证应付账款: ¥6000.00")

        # 7. 创建第二次收货单（40件）
        receipt2 = PurchaseReceipt.objects.create(
            receipt_number="RCT2025002",
            purchase_order=order,
            warehouse=self.warehouse,
            receipt_date=self.today,
            status="received",
            created_by=self.users["test_user"],
        )

        PurchaseReceiptItem.objects.create(
            receipt=receipt2,
            order_item=order_item1,
            received_quantity=40,
            created_by=self.users["test_user"],
        )

        order_item1.received_quantity = 100
        order_item1.save()

        order.status = "fully_received"
        order.save()

        InventoryTransaction.objects.create(
            transaction_type="in",
            product=self.product1,
            warehouse=self.warehouse,
            quantity=40,
            unit_cost=Decimal("100.00"),
            reference_number=receipt2.receipt_number,
            operator=self.users["warehouse_admin"],
        )

        SupplierAccountDetail.objects.create(
            detail_number="SAD2025002",
            detail_type="receipt",
            supplier=self.supplier,
            purchase_order=order,
            receipt=receipt2,
            amount=Decimal("4000.00"),
            parent_account=supplier_account,
            business_date=self.today,
        )

        supplier_account.aggregate_from_details()
        print("✅ 1.7 创建第二次收货单（40件）")

        # 8. 验证最终库存和应付
        stock1.refresh_from_db()
        self.assertEqual(stock1.quantity, 100)
        supplier_account.refresh_from_db()
        self.assertEqual(supplier_account.invoice_amount, Decimal("10000.00"))
        print("✅ 1.8 验证最终库存: 100件，应付: ¥10000.00")

        # 9. 手动核销应付账款
        details = SupplierAccountDetail.objects.filter(parent_account=supplier_account)
        payment = Payment.objects.create(
            payment_number="PAY2025001",
            payment_type="payment",
            payment_method="bank_transfer",
            supplier=self.supplier,
            amount=Decimal("10000.00"),
            payment_date=self.today,
            status="completed",
            processed_by=self.users["test_user"],
        )

        for detail in details:
            detail.allocate(detail.balance)

        supplier_account.record_payment(Decimal("10000.00"))

        self.assertEqual(supplier_account.balance, Decimal("0"))
        self.assertEqual(supplier_account.status, "paid")
        print("✅ 1.9 核销应付账款完成，余额: ¥0.00")

        print("\n✅✅✅ 测试1完成: 完整采购正向流程测试通过 ✅✅✅\n")


# ==================== 测试用例2：采购退货流程 ====================


class Test2PurchaseReturnFlow(TestCase):
    """测试用例2: 采购退货完整流程"""

    def setUp(self):
        """准备测试数据"""
        print("\n========== 测试数据准备开始 ==========")
        self.users = create_test_users()
        self.department = create_test_department(self.users["approver"])
        self.supplier = create_test_supplier()
        self.unit = create_test_unit()
        self.product1, self.product2 = create_test_products(self.unit)
        self.warehouse, self.location = create_test_warehouse(self.users["warehouse_admin"])
        self.today = timezone.now().date()
        print("✅ 测试数据准备完成")
        print("========== 测试数据准备完成 ==========\n")

    def test_1_to_6_complete_return_flow(self):
        """测试1-6：完整退货流程"""
        print("\n========== 测试2: 采购退货流程 ==========")

        # 先设置订单和收货数据
        request = PurchaseRequest.objects.create(
            request_number="PR2025002",
            requester=self.users["test_user"],
            department=self.department,
            request_date=self.today,
            status="draft",
            created_by=self.users["test_user"],
        )

        PurchaseRequestItem.objects.create(
            purchase_request=request,
            product=self.product1,
            quantity=100,
            estimated_price=Decimal("100.00"),
            created_by=self.users["test_user"],
        )

        order, _ = request.approve_and_convert_to_order(
            approved_by_user=self.users["approver"],
            supplier_id=self.supplier.id,
            warehouse_id=self.warehouse.id,
            auto_create_order=True,
        )

        order.approve_order(
            approved_by_user=self.users["approver"],
            warehouse=self.warehouse,
            auto_create_receipt=False,
        )

        order_item1 = order.items.first()
        supplier_account = SupplierAccount.get_or_create_for_order(order)

        # 收货100件
        receipt1 = PurchaseReceipt.objects.create(
            receipt_number="RCT2025003",
            purchase_order=order,
            warehouse=self.warehouse,
            receipt_date=self.today,
            status="received",
            created_by=self.users["test_user"],
        )

        PurchaseReceiptItem.objects.create(
            receipt=receipt1,
            order_item=order_item1,
            received_quantity=100,
            created_by=self.users["test_user"],
        )

        order_item1.received_quantity = 100
        order_item1.save()
        order.status = "fully_received"
        order.save()

        InventoryTransaction.objects.create(
            transaction_type="in",
            product=self.product1,
            warehouse=self.warehouse,
            quantity=100,
            unit_cost=Decimal("100.00"),
            reference_number=receipt1.receipt_number,
            operator=self.users["warehouse_admin"],
        )

        SupplierAccountDetail.objects.create(
            detail_number="SAD2025003",
            detail_type="receipt",
            supplier=self.supplier,
            purchase_order=order,
            receipt=receipt1,
            amount=Decimal("10000.00"),
            parent_account=supplier_account,
            business_date=self.today,
        )

        supplier_account.aggregate_from_details()
        print("✅ 前置：收货100件完成")

        # 2.1 创建退货单（20件）
        return_order = PurchaseReturn.objects.create(
            return_number="PRT2025001",
            purchase_order=order,
            receipt=receipt1,
            return_date=self.today,
            reason="quality",
            status="returned",
            shipped_date=self.today,
            created_by=self.users["test_user"],
        )

        PurchaseReturnItem.objects.create(
            purchase_return=return_order,
            order_item=order_item1,
            quantity=20,
            unit_price=Decimal("100.00"),
            line_total=Decimal("2000.00"),
            created_by=self.users["test_user"],
        )

        InventoryTransaction.objects.create(
            transaction_type="out",
            product=self.product1,
            warehouse=self.warehouse,
            quantity=20,
            unit_cost=Decimal("100.00"),
            reference_number=return_order.return_number,
            operator=self.users["warehouse_admin"],
        )

        SupplierAccountDetail.objects.create(
            detail_number="SAD2025004",
            detail_type="return",
            supplier=self.supplier,
            purchase_order=order,
            return_order=return_order,
            amount=Decimal("-2000.00"),
            parent_account=supplier_account,
            business_date=self.today,
        )

        supplier_account.aggregate_from_details()
        print("✅ 2.1 创建退货单（20件）")

        # 2.2 验证库存扣减
        stock1 = InventoryStock.objects.get(product=self.product1, warehouse=self.warehouse)
        self.assertEqual(stock1.quantity, 80)
        print("✅ 2.2 验证库存扣减: 80件")

        # 2.3 验证应付账款变化
        self.assertEqual(supplier_account.invoice_amount, Decimal("8000.00"))
        self.assertEqual(supplier_account.balance, Decimal("8000.00"))
        print("✅ 2.3 验证应付账款: ¥8000.00")

        # 2.4 模拟付款和退款
        # 先模拟全额付款10000元
        payment1 = Payment.objects.create(
            payment_number="PAY2025002",
            payment_type="payment",
            payment_method="bank_transfer",
            supplier=self.supplier,
            amount=Decimal("10000.00"),
            payment_date=self.today,
            status="completed",
            processed_by=self.users["test_user"],
        )

        details = SupplierAccountDetail.objects.filter(parent_account=supplier_account)
        for detail in details:
            detail.allocate(detail.balance)

        supplier_account.paid_amount = Decimal("10000.00")
        supplier_account.balance = Decimal("0.00")
        supplier_account.status = "paid"
        supplier_account.save()
        print("✅ 2.4 模拟全额付款: ¥10000.00")

        # 然后退货，需要退款2000元
        refund = Payment.objects.create(
            payment_number="PAY2025003",
            payment_type="receipt",
            supplier=self.supplier,
            amount=Decimal("2000.00"),
            payment_date=self.today,
            status="completed",
            processed_by=self.users["test_user"],
        )

        supplier_account.paid_amount = Decimal("8000.00")
        supplier_account.balance = Decimal("2000.00")
        supplier_account.status = "partially_paid"
        supplier_account.save()
        print("✅ 2.5 处理退款完成: ¥2000.00")

        print("\n✅✅✅ 测试2完成: 采购退货流程测试通过 ✅✅✅\n")


# ==================== 测试用例3：分批收货退货复杂场景 ====================


class Test3BatchProcessing(TestCase):
    """测试用例3: 分批收货 + 部分退货复杂场景"""

    def setUp(self):
        """准备测试数据"""
        print("\n========== 测试数据准备开始 ==========")
        self.users = create_test_users()
        self.department = create_test_department(self.users["approver"])
        self.supplier = create_test_supplier()
        self.unit = create_test_unit()
        self.product1, self.product2 = create_test_products(self.unit)
        self.warehouse, self.location = create_test_warehouse(self.users["warehouse_admin"])
        self.today = timezone.now().date()
        print("✅ 测试数据准备完成")
        print("========== 测试数据准备完成 ==========\n")

    def test_batch_scenario(self):
        """测试：分批收货 + 分批退货"""
        print("\n========== 测试3: 分批收货退货复杂场景 ==========")

        # 场景: 100件 → 第一次收货60件 → 第二次收货40件 → 第一次退货10件 → 第二次退货5件
        # 最终预期: 库存85件，应付8500元

        # 创建订单
        request = PurchaseRequest.objects.create(
            request_number="PR2025003",
            requester=self.users["test_user"],
            department=self.department,
            request_date=self.today,
            status="draft",
            created_by=self.users["test_user"],
        )

        PurchaseRequestItem.objects.create(
            purchase_request=request,
            product=self.product1,
            quantity=100,
            estimated_price=Decimal("100.00"),
            created_by=self.users["test_user"],
        )

        order, _ = request.approve_and_convert_to_order(
            approved_by_user=self.users["approver"],
            supplier_id=self.supplier.id,
            warehouse_id=self.warehouse.id,
            auto_create_order=True,
        )

        order.approve_order(
            approved_by_user=self.users["approver"],
            warehouse=self.warehouse,
            auto_create_receipt=False,
        )

        order_item1 = order.items.first()
        supplier_account = SupplierAccount.get_or_create_for_order(order)

        # 第一次收货60件
        receipt1 = PurchaseReceipt.objects.create(
            receipt_number="RCT2025005",
            purchase_order=order,
            warehouse=self.warehouse,
            receipt_date=self.today,
            status="received",
            created_by=self.users["test_user"],
        )

        PurchaseReceiptItem.objects.create(
            receipt=receipt1,
            order_item=order_item1,
            received_quantity=60,
            created_by=self.users["test_user"],
        )

        order_item1.received_quantity = 60
        order_item1.save()

        InventoryTransaction.objects.create(
            transaction_type="in",
            product=self.product1,
            warehouse=self.warehouse,
            quantity=60,
            unit_cost=Decimal("100.00"),
            reference_number=receipt1.receipt_number,
            operator=self.users["warehouse_admin"],
        )

        SupplierAccountDetail.objects.create(
            detail_number="SAD2025005",
            detail_type="receipt",
            supplier=self.supplier,
            purchase_order=order,
            receipt=receipt1,
            amount=Decimal("6000.00"),
            parent_account=supplier_account,
            business_date=self.today,
        )
        print("✅ 第一次收货: 60件，库存+60，应付+6000元")

        # 第二次收货40件
        receipt2 = PurchaseReceipt.objects.create(
            receipt_number="RCT2025006",
            purchase_order=order,
            warehouse=self.warehouse,
            receipt_date=self.today,
            status="received",
            created_by=self.users["test_user"],
        )

        PurchaseReceiptItem.objects.create(
            receipt=receipt2,
            order_item=order_item1,
            received_quantity=40,
            created_by=self.users["test_user"],
        )

        order_item1.received_quantity = 100
        order_item1.save()
        order.status = "fully_received"
        order.save()

        InventoryTransaction.objects.create(
            transaction_type="in",
            product=self.product1,
            warehouse=self.warehouse,
            quantity=40,
            unit_cost=Decimal("100.00"),
            reference_number=receipt2.receipt_number,
            operator=self.users["warehouse_admin"],
        )

        SupplierAccountDetail.objects.create(
            detail_number="SAD2025006",
            detail_type="receipt",
            supplier=self.supplier,
            purchase_order=order,
            receipt=receipt2,
            amount=Decimal("4000.00"),
            parent_account=supplier_account,
            business_date=self.today,
        )
        print("✅ 第二次收货: 40件，库存+40，应付+4000元")

        # 第一次退货10件
        return_order1 = PurchaseReturn.objects.create(
            return_number="PRT2025002",
            purchase_order=order,
            receipt=receipt1,
            return_date=self.today,
            reason="quality",
            status="returned",
            shipped_date=self.today,
            created_by=self.users["test_user"],
        )

        PurchaseReturnItem.objects.create(
            purchase_return=return_order1,
            order_item=order_item1,
            quantity=10,
            unit_price=Decimal("100.00"),
            line_total=Decimal("1000.00"),
            created_by=self.users["test_user"],
        )

        InventoryTransaction.objects.create(
            transaction_type="out",
            product=self.product1,
            warehouse=self.warehouse,
            quantity=10,
            unit_cost=Decimal("100.00"),
            reference_number=return_order1.return_number,
            operator=self.users["warehouse_admin"],
        )

        SupplierAccountDetail.objects.create(
            detail_number="SAD2025007",
            detail_type="return",
            supplier=self.supplier,
            purchase_order=order,
            return_order=return_order1,
            amount=Decimal("-1000.00"),
            parent_account=supplier_account,
            business_date=self.today,
        )
        print("✅ 第一次退货: 10件，库存-10，应付-1000元")

        # 第二次退货5件
        return_order2 = PurchaseReturn.objects.create(
            return_number="PRT2025003",
            purchase_order=order,
            receipt=receipt2,
            return_date=self.today,
            reason="damage",
            status="returned",
            shipped_date=self.today,
            created_by=self.users["test_user"],
        )

        PurchaseReturnItem.objects.create(
            purchase_return=return_order2,
            order_item=order_item1,
            quantity=5,
            unit_price=Decimal("100.00"),
            line_total=Decimal("500.00"),
            created_by=self.users["test_user"],
        )

        InventoryTransaction.objects.create(
            transaction_type="out",
            product=self.product1,
            warehouse=self.warehouse,
            quantity=5,
            unit_cost=Decimal("100.00"),
            reference_number=return_order2.return_number,
            operator=self.users["warehouse_admin"],
        )

        SupplierAccountDetail.objects.create(
            detail_number="SAD2025008",
            detail_type="return",
            supplier=self.supplier,
            purchase_order=order,
            return_order=return_order2,
            amount=Decimal("-500.00"),
            parent_account=supplier_account,
            business_date=self.today,
        )
        print("✅ 第二次退货: 5件，库存-5，应付-500元")

        # 验证最终状态
        supplier_account.aggregate_from_details()

        # 验证库存
        stock1 = InventoryStock.objects.get(product=self.product1, warehouse=self.warehouse)
        expected_inventory = 60 + 40 - 10 - 5  # 85
        self.assertEqual(stock1.quantity, expected_inventory)
        print(f"✅ 最终库存: {stock1.quantity}件（预期: {expected_inventory}件）")

        # 验证应付
        expected_account = 6000 + 4000 - 1000 - 500  # 8500
        self.assertEqual(supplier_account.invoice_amount, Decimal(str(expected_account)))
        self.assertEqual(supplier_account.balance, Decimal(str(expected_account)))
        print(f"✅ 最终应付: ¥{supplier_account.invoice_amount}（预期: ¥{expected_account}）")

        # 验证订单状态
        self.assertEqual(order.status, "fully_received")
        print(f"✅ 订单状态: {order.status}")

        print("\n✅✅✅ 测试3完成: 分批收货退货复杂场景测试通过 ✅✅✅\n")
