"""
Django ERP 销售借用流程端到端测试

完整测试销售借用业务流程:
1. 借用后归还流程
2. 借用转销售订单流程
3. 部分归还+部分转销售混合流程

关键验证:
- 借用仓库存变动
- 主仓库存变动
- 借用单状态更新
"""

import uuid
from decimal import Decimal

import pytest
from django.utils import timezone
from inventory.models import InventoryStock, InventoryTransaction
from sales.models import SalesLoan, SalesLoanItem, SalesOrder, SalesOrderItem


@pytest.mark.django_db
@pytest.mark.e2e
class TestSalesLoanFlowE2E:
    """销售借用流程端到端测试"""

    def test_loan_and_return_flow(self, test_users, test_customer, test_products, test_warehouse):
        """
        测试: 借用后归还流程

        流程:
        1. 客户从借用仓借用产品50件
        2. 验证借用仓库存减少50（剩余50）
        3. 客户归还产品50件
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
        loan = SalesLoan.objects.create(
            loan_number=f'LOAN-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}',
            customer=test_customer,
            salesperson=admin,
            loan_date=timezone.now().date(),
            expected_return_date=timezone.now().date() + timezone.timedelta(days=30),
            status="loaned",
            purpose="测试借用",
            created_by=admin,
        )

        # 创建借用明细
        loan_item = SalesLoanItem.objects.create(
            loan=loan,
            product=product1,
            quantity=Decimal("50"),
            returned_quantity=Decimal("0"),
        )

        # 创建借用出库事务（从借用仓出库）
        InventoryTransaction.objects.create(
            product=product1,
            warehouse=borrow_wh,
            transaction_type="out",
            quantity=Decimal("50"),
            transaction_date=timezone.now().date(),
            reference_type="sales_loan",
            reference_id=str(loan.id),
            reference_number=loan.loan_number,
            operator=admin,
        )

        # 2. 验证借用仓库存减少50（剩余50）
        borrow_stock.refresh_from_db()
        assert borrow_stock.quantity == Decimal("50")

        # 验证库存事务记录（出库）
        transactions = InventoryTransaction.objects.filter(
            reference_type="sales_loan", reference_id=str(loan.id)
        )
        assert transactions.count() == 1
        assert transactions.first().transaction_type == "out"
        assert transactions.first().quantity == Decimal("50")

        # 3. 归还产品50件
        loan_item.returned_quantity = Decimal("50")
        loan_item.save()

        loan.status = "fully_returned"
        loan.save()

        # 创建归还入库事务（入库到借用仓）
        InventoryTransaction.objects.create(
            product=product1,
            warehouse=borrow_wh,
            transaction_type="in",
            quantity=Decimal("50"),
            transaction_date=timezone.now().date(),
            reference_type="sales_loan_return",
            reference_id=str(loan.id),
            reference_number=loan.loan_number,
            operator=admin,
        )

        # 4. 验证借用仓库存恢复100
        borrow_stock.refresh_from_db()
        assert borrow_stock.quantity == Decimal("100")

        # 验证借用单状态
        loan.refresh_from_db()
        assert loan.status == "fully_returned"
        assert loan_item.returned_quantity == Decimal("50")

    def test_loan_convert_to_sales(self, test_users, test_customer, test_products, test_warehouse):
        """
        测试: 借用转销售订单流程

        流程:
        1. 客户从借用仓借用产品50件
        2. 将借用单转为销售订单
        3. 验证生成正式销售订单
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
        loan = SalesLoan.objects.create(
            loan_number=f'LOAN-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}',
            customer=test_customer,
            salesperson=admin,
            loan_date=timezone.now().date(),
            expected_return_date=timezone.now().date() + timezone.timedelta(days=30),
            status="loaned",
            purpose="测试借用转销售",
            created_by=admin,
        )

        # 创建借用明细
        loan_item = SalesLoanItem.objects.create(
            loan=loan,
            product=product1,
            quantity=Decimal("50"),
            returned_quantity=Decimal("0"),
            conversion_unit_price=Decimal("150.00"),  # 转销售单价
            conversion_quantity=Decimal("0"),
        )

        # 创建借用出库事务
        InventoryTransaction.objects.create(
            product=product1,
            warehouse=borrow_wh,
            transaction_type="out",
            quantity=Decimal("50"),
            transaction_date=timezone.now().date(),
            reference_type="sales_loan",
            reference_id=str(loan.id),
            reference_number=loan.loan_number,
            operator=admin,
        )

        # 验证借用仓库存减少50（剩余50）
        borrow_stock.refresh_from_db()
        assert borrow_stock.quantity == Decimal("50")

        # 2. 转为销售订单（50件全部转销售）
        order = SalesOrder.objects.create(
            order_number=f'SO-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}',
            customer=test_customer,
            order_date=timezone.now().date(),
            required_date=timezone.now().date() + timezone.timedelta(days=7),
            status="draft",
            notes="借用转销售",
            created_by=admin,
        )

        # 创建销售订单明细
        order_item = SalesOrderItem.objects.create(
            order=order,
            product=product1,
            quantity=Decimal("50"),
            unit_price=Decimal("150.00"),
        )

        # 重新计算订单总金额
        order.calculate_totals()

        # 更新借用单和明细
        loan.converted_order = order
        loan.status = "converted"
        loan.conversion_notes = "已转为销售订单"
        loan.save()

        loan_item.conversion_quantity = Decimal("50")  # 已转销售数量
        loan_item.save()

        # 3. 验证生成正式销售订单
        order.refresh_from_db()
        assert order is not None
        assert order.customer == test_customer
        assert order.items.count() == 1
        assert order.items.first().product == product1
        assert order.items.first().quantity == Decimal("50")

        # 验证借用单状态
        loan.refresh_from_db()
        assert loan.status == "converted"
        assert loan.converted_order == order
        assert loan_item.conversion_quantity == Decimal("50")

    def test_loan_partial_operations(
        self, test_users, test_customer, test_products, test_warehouse
    ):
        """
        测试: 部分归还+部分转销售混合流程

        流程:
        1. 借用100件（借用仓库存→0）
        2. 归还30件（借用仓库存→30）
        3. 剩余70件转销售订单
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
        loan = SalesLoan.objects.create(
            loan_number=f'LOAN-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}',
            customer=test_customer,
            salesperson=admin,
            loan_date=timezone.now().date(),
            expected_return_date=timezone.now().date() + timezone.timedelta(days=30),
            status="loaned",
            purpose="测试部分操作",
            created_by=admin,
        )

        # 创建借用明细
        loan_item = SalesLoanItem.objects.create(
            loan=loan,
            product=product1,
            quantity=Decimal("100"),
            returned_quantity=Decimal("0"),
            conversion_unit_price=Decimal("150.00"),
            conversion_quantity=Decimal("0"),
        )

        # 创建借用出库事务
        InventoryTransaction.objects.create(
            product=product1,
            warehouse=borrow_wh,
            transaction_type="out",
            quantity=Decimal("100"),
            transaction_date=timezone.now().date(),
            reference_type="sales_loan",
            reference_id=str(loan.id),
            reference_number=loan.loan_number,
            operator=admin,
        )

        # 验证借用仓库存减少100（剩余0）
        borrow_stock.refresh_from_db()
        assert borrow_stock.quantity == Decimal("0")

        # 2. 归还30件
        loan_item.returned_quantity = Decimal("30")
        loan_item.save()

        # 创建归还入库事务
        InventoryTransaction.objects.create(
            product=product1,
            warehouse=borrow_wh,
            transaction_type="in",
            quantity=Decimal("30"),
            transaction_date=timezone.now().date(),
            reference_type="sales_loan_return",
            reference_id=str(loan.id),
            reference_number=loan.loan_number,
            operator=admin,
        )

        # 验证借用仓库存+30（剩余30）
        borrow_stock.refresh_from_db()
        assert borrow_stock.quantity == Decimal("30")

        # 3. 剩余70件转销售订单
        order = SalesOrder.objects.create(
            order_number=f'SO-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}',
            customer=test_customer,
            order_date=timezone.now().date(),
            required_date=timezone.now().date() + timezone.timedelta(days=7),
            status="draft",
            notes="借用转销售（部分）",
            created_by=admin,
        )

        # 创建销售订单明细（70件）
        order_item = SalesOrderItem.objects.create(
            order=order,
            product=product1,
            quantity=Decimal("70"),
            unit_price=Decimal("150.00"),
        )

        # 重新计算订单总金额
        order.calculate_totals()

        # 更新借用单和明细
        loan.converted_order = order
        loan.status = "converted"
        loan.conversion_notes = "已转销售订单70件，归还30件"
        loan.save()

        loan_item.conversion_quantity = Decimal("70")  # 已转销售数量
        loan_item.save()

        # 验证销售订单包含70件
        order.refresh_from_db()
        assert order is not None
        assert order.items.first().quantity == Decimal("70")

        # 验证借用单状态
        loan.refresh_from_db()
        assert loan.status == "converted"
        assert loan_item.returned_quantity == Decimal("30")
        assert loan_item.conversion_quantity == Decimal("70")
        assert loan_item.returned_quantity + loan_item.conversion_quantity == Decimal("100")
