"""
Django ERP 采购借用流程端到端测试

完整测试采购借用业务流程:
1. 借用后归还流程
2. 借用转采购流程
3. 部分归还+部分转采购混合流程

关键验证:
- 借用仓库存变动
- 主仓库存变动
- 借用单状态更新
"""

import uuid
from decimal import Decimal

import pytest
from core.tests.test_fixtures import FixtureFactory
from django.utils import timezone
from inventory.models import InventoryStock, InventoryTransaction
from purchase.models import Borrow, BorrowItem, PurchaseOrder, PurchaseOrderItem


@pytest.mark.django_db
@pytest.mark.e2e
class TestBorrowFlowE2E:
    """采购借用流程端到端测试"""

    def test_borrow_and_return_flow(self, test_users, test_supplier, test_products, test_warehouse):
        """
        测试: 借用后归还流程

        流程:
        1. 供应商从借用仓借用产品50件
        2. 验证借用仓库存减少50（剩余50）
        3. 供应商归还产品50件
        4. 验证借用仓库存恢复100
        """
        # 准备数据
        admin = test_users["admin"]
        warehouse, borrow_wh = test_warehouse
        product1, _, _ = test_products

        # 准备借用仓库存（100件）
        borrow_stock, _ = InventoryStock.objects.get_or_create(
            product=product1, warehouse=borrow_wh, defaults={"quantity": Decimal("0")}
        )
        borrow_stock.quantity = Decimal("100")
        borrow_stock.save()

        # 1. 创建借用单（借用50件）
        borrow = Borrow.objects.create(
            borrow_number=f'BRW-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}',
            supplier=test_supplier,
            buyer=admin,
            borrow_date=timezone.now().date(),
            expected_return_date=timezone.now().date() + timezone.timedelta(days=30),
            status="borrowed",
            purpose="测试借用",
            created_by=admin,
        )

        # 创建借用明细
        borrow_item = BorrowItem.objects.create(
            borrow=borrow,
            product=product1,
            quantity=50,
            borrowed_quantity=50,  # 累计已借用数量
            returned_quantity=0,
        )

        # 创建借用出库事务（从借用仓出库）
        InventoryTransaction.objects.create(
            product=product1,
            warehouse=borrow_wh,
            transaction_type="out",
            quantity=Decimal("50"),
            transaction_date=timezone.now().date(),
            reference_type="purchase_borrow",
            reference_id=str(borrow.id),
            reference_number=borrow.borrow_number,
            operator=admin,
        )

        # 2. 验证借用仓库存减少50（剩余50）
        borrow_stock.refresh_from_db()
        assert borrow_stock.quantity == Decimal("50")

        # 验证库存事务记录（出库）
        transactions = InventoryTransaction.objects.filter(
            reference_type="purchase_borrow", reference_id=str(borrow.id)
        )
        assert transactions.count() == 1
        assert transactions.first().transaction_type == "out"
        assert transactions.first().quantity == Decimal("50")

        # 3. 归还产品50件
        borrow_item.returned_quantity = 50
        borrow_item.save()

        borrow.status = "completed"
        borrow.save()

        # 创建归还入库事务（入库到借用仓）
        InventoryTransaction.objects.create(
            product=product1,
            warehouse=borrow_wh,
            transaction_type="in",
            quantity=Decimal("50"),
            transaction_date=timezone.now().date(),
            reference_type="purchase_borrow_return",
            reference_id=str(borrow.id),
            reference_number=borrow.borrow_number,
            operator=admin,
        )

        # 4. 验证借用仓库存恢复100
        borrow_stock.refresh_from_db()
        assert borrow_stock.quantity == Decimal("100")

        # 验证借用单状态
        borrow.refresh_from_db()
        assert borrow.status == "completed"
        assert borrow_item.returned_quantity == 50

    def test_borrow_convert_to_purchase(
        self, test_users, test_supplier, test_products, test_warehouse
    ):
        """
        测试: 借用转采购流程

        流程:
        1. 供应商从借用仓借用产品50件
        2. 将借用单转为采购订单
        3. 验证生成正式采购订单
        """
        # 准备数据
        admin = test_users["admin"]
        warehouse, borrow_wh = test_warehouse
        product1, _, _ = test_products

        # 准备借用仓库存（100件）
        borrow_stock, _ = InventoryStock.objects.get_or_create(
            product=product1, warehouse=borrow_wh, defaults={"quantity": Decimal("0")}
        )
        borrow_stock.quantity = Decimal("100")
        borrow_stock.save()

        # 1. 创建借用单（借用50件）
        borrow = Borrow.objects.create(
            borrow_number=f'BRW-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}',
            supplier=test_supplier,
            buyer=admin,
            borrow_date=timezone.now().date(),
            expected_return_date=timezone.now().date() + timezone.timedelta(days=30),
            status="borrowed",
            purpose="测试借用转采购",
            created_by=admin,
        )

        # 创建借用明细
        borrow_item = BorrowItem.objects.create(
            borrow=borrow,
            product=product1,
            quantity=50,
            borrowed_quantity=50,
            returned_quantity=0,
            conversion_unit_price=Decimal("100.00"),  # 转采购单价
            conversion_quantity=0,
        )

        # 创建借用出库事务
        InventoryTransaction.objects.create(
            product=product1,
            warehouse=borrow_wh,
            transaction_type="out",
            quantity=Decimal("50"),
            transaction_date=timezone.now().date(),
            reference_type="purchase_borrow",
            reference_id=str(borrow.id),
            reference_number=borrow.borrow_number,
            operator=admin,
        )

        # 验证借用仓库存减少50（剩余50）
        borrow_stock.refresh_from_db()
        assert borrow_stock.quantity == Decimal("50")

        # 2. 转为采购订单（50件全部转采购）
        order = PurchaseOrder.objects.create(
            order_number=f'PO-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}',
            supplier=test_supplier,
            order_date=timezone.now().date(),
            required_date=timezone.now().date() + timezone.timedelta(days=7),
            status="draft",
            notes="借用转采购",
            created_by=admin,
        )

        # 创建采购订单明细
        order_item = PurchaseOrderItem.objects.create(
            purchase_order=order,
            product=product1,
            quantity=Decimal("50"),
            unit_price=Decimal("100.00"),
        )

        # 重新计算订单总金额
        order.calculate_totals()

        # 更新借用单和明细
        borrow.converted_order = order
        borrow.status = "completed"
        borrow.conversion_notes = "已转为采购订单"
        borrow.save()

        borrow_item.conversion_quantity = 50  # 已转采购数量
        borrow_item.save()

        # 3. 验证生成正式采购订单
        order.refresh_from_db()
        assert order is not None
        assert order.supplier == test_supplier
        assert order.items.count() == 1
        assert order.items.first().product == product1
        assert order.items.first().quantity == Decimal("50")

        # 验证借用单状态
        borrow.refresh_from_db()
        assert borrow.status == "completed"
        assert borrow.converted_order == order
        assert borrow_item.conversion_quantity == 50

    def test_borrow_partial_operations(
        self, test_users, test_supplier, test_products, test_warehouse
    ):
        """
        测试: 部分归还+部分转采购混合流程

        流程:
        1. 借用100件（借用仓库存→0）
        2. 归还30件（借用仓库存→30）
        3. 剩余70件转采购订单
        """
        # 准备数据
        admin = test_users["admin"]
        warehouse, borrow_wh = test_warehouse
        product1, _, _ = test_products

        # 准备借用仓库存（100件）
        borrow_stock, _ = InventoryStock.objects.get_or_create(
            product=product1, warehouse=borrow_wh, defaults={"quantity": Decimal("0")}
        )
        borrow_stock.quantity = Decimal("100")
        borrow_stock.save()

        # 1. 创建借用单（借用100件）
        borrow = Borrow.objects.create(
            borrow_number=f'BRW-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}',
            supplier=test_supplier,
            buyer=admin,
            borrow_date=timezone.now().date(),
            expected_return_date=timezone.now().date() + timezone.timedelta(days=30),
            status="borrowed",
            purpose="测试部分操作",
            created_by=admin,
        )

        # 创建借用明细
        borrow_item = BorrowItem.objects.create(
            borrow=borrow,
            product=product1,
            quantity=100,
            borrowed_quantity=100,
            returned_quantity=0,
            conversion_unit_price=Decimal("100.00"),
            conversion_quantity=0,
        )

        # 创建借用出库事务
        InventoryTransaction.objects.create(
            product=product1,
            warehouse=borrow_wh,
            transaction_type="out",
            quantity=Decimal("100"),
            transaction_date=timezone.now().date(),
            reference_type="purchase_borrow",
            reference_id=str(borrow.id),
            reference_number=borrow.borrow_number,
            operator=admin,
        )

        # 验证借用仓库存减少100（剩余0）
        borrow_stock.refresh_from_db()
        assert borrow_stock.quantity == Decimal("0")

        # 2. 归还30件
        borrow_item.returned_quantity = 30
        borrow_item.save()

        # 创建归还入库事务
        InventoryTransaction.objects.create(
            product=product1,
            warehouse=borrow_wh,
            transaction_type="in",
            quantity=Decimal("30"),
            transaction_date=timezone.now().date(),
            reference_type="purchase_borrow_return",
            reference_id=str(borrow.id),
            reference_number=borrow.borrow_number,
            operator=admin,
        )

        # 验证借用仓库存+30（剩余30）
        borrow_stock.refresh_from_db()
        assert borrow_stock.quantity == Decimal("30")

        # 3. 剩余70件转采购订单
        order = PurchaseOrder.objects.create(
            order_number=f'PO-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}',
            supplier=test_supplier,
            order_date=timezone.now().date(),
            required_date=timezone.now().date() + timezone.timedelta(days=7),
            status="draft",
            notes="借用转采购（部分）",
            created_by=admin,
        )

        # 创建采购订单明细（70件）
        order_item = PurchaseOrderItem.objects.create(
            purchase_order=order,
            product=product1,
            quantity=Decimal("70"),
            unit_price=Decimal("100.00"),
        )

        # 重新计算订单总金额
        order.calculate_totals()

        # 更新借用单和明细
        borrow.converted_order = order
        borrow.status = "completed"
        borrow.conversion_notes = "已转采购订单70件，归还30件"
        borrow.save()

        borrow_item.conversion_quantity = 70  # 已转采购数量
        borrow_item.save()

        # 验证采购订单包含70件
        order.refresh_from_db()
        assert order is not None
        assert order.items.first().quantity == Decimal("70")

        # 验证借用单状态
        borrow.refresh_from_db()
        assert borrow.status == "completed"
        assert borrow_item.returned_quantity == 30
        assert borrow_item.conversion_quantity == 70
        assert borrow_item.returned_quantity + borrow_item.conversion_quantity == 100
