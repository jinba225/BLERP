"""
Inventory模块 - 服务层测试
测试StockAdjustmentService, StockTransferService, StockCountService, InboundOrderService业务逻辑
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from inventory.services import (
    InboundOrderService,
    StockAdjustmentService,
    StockCountService,
    StockTransferService,
)

from apps.departments.models import Department
from apps.inventory.models import (
    InboundOrder,
    InboundOrderItem,
    InventoryStock,
    InventoryTransaction,
    StockAdjustment,
    StockCount,
    StockCountItem,
    StockTransfer,
    StockTransferItem,
    Warehouse,
)
from apps.products.models import Brand, Product, ProductCategory, Unit

User = get_user_model()


class InventoryServiceTestCaseBase(TestCase):
    """Inventory服务测试基类 - 准备测试数据"""

    def setUp(self):
        """测试前准备 - 创建测试数据"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            employee_id="EMP001",
        )

        # 创建部门
        self.department = Department.objects.create(
            name="仓储部", code="WAREHOUSE", created_by=self.user
        )
        self.user.department = self.department
        self.user.save()

        # 创建仓库
        self.warehouse1 = Warehouse.objects.create(name="主仓库", code="WH001", created_by=self.user)

        self.warehouse2 = Warehouse.objects.create(name="分仓库", code="WH002", created_by=self.user)

        # 创建产品分类
        self.product_category = ProductCategory.objects.create(
            name="激光设备", code="LASER", created_by=self.user
        )

        # 创建品牌
        self.brand = Brand.objects.create(name="测试品牌", code="BRAND001", created_by=self.user)

        # 创建单位
        self.unit = Unit.objects.create(name="台", symbol="台", created_by=self.user)

        # 创建测试产品
        self.product1 = Product.objects.create(
            name="激光镜片",
            code="PRD001",
            specifications="高精度激光镜片",
            category=self.product_category,
            brand=self.brand,
            unit=self.unit,
            cost_price=Decimal("5000.00"),
            selling_price=Decimal("8000.00"),
            status="active",
            created_by=self.user,
        )

        self.product2 = Product.objects.create(
            name="激光管",
            code="PRD002",
            specifications="CO2激光管",
            category=self.product_category,
            brand=self.brand,
            unit=self.unit,
            cost_price=Decimal("3000.00"),
            selling_price=Decimal("5000.00"),
            status="active",
            created_by=self.user,
        )

        # 创建初始库存
        self.stock1 = InventoryStock.objects.create(
            product=self.product1,
            warehouse=self.warehouse1,
            quantity=Decimal("100"),
            cost_price=Decimal("5000.00"),
            created_by=self.user,
        )

        self.stock2 = InventoryStock.objects.create(
            product=self.product2,
            warehouse=self.warehouse1,
            quantity=Decimal("50"),
            cost_price=Decimal("3000.00"),
            created_by=self.user,
        )


class StockAdjustmentServiceTestCase(InventoryServiceTestCaseBase):
    """StockAdjustmentService服务测试"""

    def test_create_adjustment_basic(self):
        """测试创建基础库存调整"""
        adjustment_data = {
            "warehouse": self.warehouse1,
            "product": self.product1,
            "adjustment_type": "increase",
            "original_quantity": Decimal("100.0000"),
            "adjusted_quantity": Decimal("110.0000"),
            "difference": Decimal("10.0000"),
            "reason": "count_error",
            "notes": "盘点发现多出10台",
        }

        adjustment = StockAdjustmentService.create_adjustment(self.user, adjustment_data)

        # 验证调整单创建成功
        self.assertIsNotNone(adjustment.id)
        self.assertEqual(adjustment.warehouse, self.warehouse1)
        self.assertEqual(adjustment.product, self.product1)
        self.assertEqual(adjustment.difference, Decimal("10.0000"))
        self.assertEqual(adjustment.created_by, self.user)

        # 验证单据号自动生成
        self.assertIsNotNone(adjustment.adjustment_number)
        self.assertTrue(adjustment.adjustment_number.startswith("ADJ"))

    def test_create_adjustment_with_custom_number(self):
        """测试创建调整单时指定单据号"""
        adjustment_data = {
            "adjustment_number": "ADJ_CUSTOM_001",
            "warehouse": self.warehouse1,
            "product": self.product1,
            "adjustment_type": "decrease",
            "original_quantity": Decimal("100.0000"),
            "adjusted_quantity": Decimal("95.0000"),
            "difference": Decimal("-5.0000"),
            "reason": "damage",
        }

        adjustment = StockAdjustmentService.create_adjustment(self.user, adjustment_data)

        # 验证使用了指定的单据号
        self.assertEqual(adjustment.adjustment_number, "ADJ_CUSTOM_001")

    def test_approve_adjustment_increase(self):
        """测试审核增加库存的调整单"""
        # 创建调整单（增加库存）
        adjustment_data = {
            "warehouse": self.warehouse1,
            "product": self.product1,
            "adjustment_type": "increase",
            "original_quantity": Decimal("100.0000"),
            "adjusted_quantity": Decimal("110.0000"),
            "difference": Decimal("10.0000"),
            "reason": "count_error",
        }
        adjustment = StockAdjustmentService.create_adjustment(self.user, adjustment_data)

        original_stock_qty = self.stock1.quantity

        # 审核调整单
        approved_adjustment = StockAdjustmentService.approve_adjustment(adjustment, self.user)

        # 验证调整单已审核
        self.assertTrue(approved_adjustment.is_approved)
        self.assertEqual(approved_adjustment.approved_by, self.user)
        self.assertIsNotNone(approved_adjustment.approved_at)

        # 验证库存已更新
        self.stock1.refresh_from_db()
        self.assertEqual(self.stock1.quantity, original_stock_qty + Decimal("10.0000"))

        # 验证事务记录已创建
        transaction = InventoryTransaction.objects.filter(
            reference_number=adjustment.adjustment_number
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.quantity, Decimal("10.0000"))
        self.assertEqual(transaction.transaction_type, "adjustment")

    def test_approve_adjustment_decrease(self):
        """测试审核减少库存的调整单"""
        # 创建调整单（减少库存）
        adjustment_data = {
            "warehouse": self.warehouse1,
            "product": self.product1,
            "adjustment_type": "decrease",
            "original_quantity": Decimal("100.0000"),
            "adjusted_quantity": Decimal("95.0000"),
            "difference": Decimal("-5.0000"),
            "reason": "damage",
        }
        adjustment = StockAdjustmentService.create_adjustment(self.user, adjustment_data)

        original_stock_qty = self.stock1.quantity

        # 审核调整单
        StockAdjustmentService.approve_adjustment(adjustment, self.user)

        # 验证库存已减少
        self.stock1.refresh_from_db()
        self.assertEqual(self.stock1.quantity, original_stock_qty - Decimal("5.0000"))


class StockTransferServiceTestCase(InventoryServiceTestCaseBase):
    """StockTransferService服务测试"""

    def test_create_transfer_basic(self):
        """测试创建基础库存调拨"""
        transfer_data = {
            "from_warehouse": self.warehouse1,
            "to_warehouse": self.warehouse2,
            "transfer_date": date.today(),
            "expected_arrival_date": date.today(),
            "notes": "调拨测试",
        }

        items_data = [
            {
                "product_id": self.product1.id,
                "requested_quantity": Decimal("10.0000"),
                "unit_cost": Decimal("5000.00"),
            },
            {
                "product_id": self.product2.id,
                "requested_quantity": Decimal("5.0000"),
                "unit_cost": Decimal("3000.00"),
            },
        ]

        transfer = StockTransferService.create_transfer(self.user, transfer_data, items_data)

        # 验证调拨单创建成功
        self.assertIsNotNone(transfer.id)
        self.assertEqual(transfer.from_warehouse, self.warehouse1)
        self.assertEqual(transfer.to_warehouse, self.warehouse2)
        self.assertEqual(transfer.status, "draft")
        self.assertEqual(transfer.created_by, self.user)

        # 验证单据号自动生成
        self.assertIsNotNone(transfer.transfer_number)
        self.assertTrue(transfer.transfer_number.startswith("TRF"))

        # 验证调拨明细
        self.assertEqual(transfer.items.count(), 2)

    def test_update_transfer_basic(self):
        """测试更新调拨单"""
        # 创建调拨单
        transfer_data = {
            "from_warehouse": self.warehouse1,
            "to_warehouse": self.warehouse2,
            "transfer_date": date.today(),
        }
        items_data = [
            {
                "product_id": self.product1.id,
                "requested_quantity": Decimal("10.0000"),
                "unit_cost": Decimal("5000.00"),
            },
        ]
        transfer = StockTransferService.create_transfer(self.user, transfer_data, items_data)
        original_number = transfer.transfer_number

        # 更新调拨单
        update_data = {"notes": "已更新备注"}
        new_items_data = [
            {
                "product_id": self.product1.id,
                "requested_quantity": Decimal("15.0000"),
                "unit_cost": Decimal("5000.00"),
            },
            {
                "product_id": self.product2.id,
                "requested_quantity": Decimal("5.0000"),
                "unit_cost": Decimal("3000.00"),
            },
        ]

        updated_transfer = StockTransferService.update_transfer(
            transfer, self.user, update_data, new_items_data
        )

        # 验证更新成功
        self.assertEqual(updated_transfer.id, transfer.id)
        self.assertEqual(updated_transfer.transfer_number, original_number)
        self.assertEqual(updated_transfer.notes, "已更新备注")
        self.assertEqual(updated_transfer.items.count(), 2)

    def test_ship_transfer(self):
        """测试调拨单发货"""
        # 创建调拨单
        transfer_data = {
            "from_warehouse": self.warehouse1,
            "to_warehouse": self.warehouse2,
            "transfer_date": date.today(),
        }
        items_data = [
            {
                "product_id": self.product1.id,
                "requested_quantity": Decimal("10.0000"),
                "unit_cost": Decimal("5000.00"),
            },
        ]
        transfer = StockTransferService.create_transfer(self.user, transfer_data, items_data)

        original_stock_qty = self.stock1.quantity

        # 发货
        shipped_quantities = {transfer.items.first().id: Decimal("10.0000")}
        shipped_transfer = StockTransferService.ship_transfer(
            transfer, self.user, shipped_quantities
        )

        # 验证状态已更新
        self.assertEqual(shipped_transfer.status, "in_transit")

        # 验证明细已更新
        item = shipped_transfer.items.first()
        self.assertEqual(item.shipped_quantity, Decimal("10.0000"))

        # 验证源仓库库存已扣减
        self.stock1.refresh_from_db()
        self.assertEqual(self.stock1.quantity, original_stock_qty - Decimal("10.0000"))

        # 验证出库事务记录已创建
        transaction = InventoryTransaction.objects.filter(
            reference_number=transfer.transfer_number, transaction_type="out"
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.quantity, Decimal("10.0000"))

    def test_receive_transfer(self):
        """测试调拨单收货"""
        # 创建并发货调拨单
        transfer_data = {
            "from_warehouse": self.warehouse1,
            "to_warehouse": self.warehouse2,
            "transfer_date": date.today(),
        }
        items_data = [
            {
                "product_id": self.product1.id,
                "requested_quantity": Decimal("10.0000"),
                "unit_cost": Decimal("5000.00"),
            },
        ]
        transfer = StockTransferService.create_transfer(self.user, transfer_data, items_data)
        shipped_quantities = {transfer.items.first().id: Decimal("10.0000")}
        StockTransferService.ship_transfer(transfer, self.user, shipped_quantities)

        # 收货
        received_quantities = {transfer.items.first().id: Decimal("10.0000")}
        received_transfer = StockTransferService.receive_transfer(
            transfer, self.user, received_quantities
        )

        # 验证状态已更新
        self.assertEqual(received_transfer.status, "completed")
        self.assertIsNotNone(received_transfer.actual_arrival_date)

        # 验证明细已更新
        item = received_transfer.items.first()
        self.assertEqual(item.received_quantity, Decimal("10.0000"))

        # 验证目标仓库库存已增加
        dest_stock = InventoryStock.objects.filter(
            product=self.product1, warehouse=self.warehouse2, is_deleted=False
        ).first()
        self.assertIsNotNone(dest_stock)
        self.assertEqual(dest_stock.quantity, Decimal("10.0000"))

        # 验证入库事务记录已创建
        transaction = InventoryTransaction.objects.filter(
            reference_number=transfer.transfer_number, transaction_type="in"
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.quantity, Decimal("10.0000"))


class StockCountServiceTestCase(InventoryServiceTestCaseBase):
    """StockCountService服务测试"""

    def test_create_count_basic(self):
        """测试创建基础库存盘点"""
        count_data = {
            "warehouse": self.warehouse1,
            "count_type": "full",
            "planned_date": date.today(),
            "notes": "月度盘点",
        }

        items_data = [
            {
                "product_id": self.product1.id,
                "counted_quantity": Decimal("98.0000"),
            },
            {
                "product_id": self.product2.id,
                "counted_quantity": Decimal("50.0000"),
            },
        ]

        count = StockCountService.create_count(self.user, count_data, items_data)

        # 验证盘点单创建成功
        self.assertIsNotNone(count.id)
        self.assertEqual(count.warehouse, self.warehouse1)
        self.assertEqual(count.status, "planned")
        self.assertEqual(count.created_by, self.user)

        # 验证单据号自动生成
        self.assertIsNotNone(count.count_number)
        self.assertTrue(count.count_number.startswith("CNT"))

        # 验证盘点明细
        self.assertEqual(count.items.count(), 2)

        # 验证system_quantity自动获取
        item1 = count.items.get(product=self.product1)
        self.assertEqual(item1.system_quantity, Decimal("100.0000"))  # 来自self.stock1
        self.assertEqual(item1.counted_quantity, Decimal("98.0000"))

    def test_create_count_with_counters(self):
        """测试创建盘点单并指定盘点人"""
        # 创建盘点人
        counter = User.objects.create_user(
            username="counter1", password="pass123", employee_id="EMP002"
        )

        count_data = {
            "warehouse": self.warehouse1,
            "count_type": "cycle",
            "planned_date": date.today(),
        }

        items_data = [
            {"product_id": self.product1.id, "counted_quantity": Decimal("100.0000")},
        ]

        count = StockCountService.create_count(
            self.user, count_data, items_data, counter_ids=[counter.id]
        )

        # 验证盘点人已设置
        self.assertEqual(count.counters.count(), 1)
        self.assertIn(counter, count.counters.all())

    def test_update_count_basic(self):
        """测试更新盘点单"""
        # 创建盘点单
        count_data = {
            "warehouse": self.warehouse1,
            "count_type": "spot",
            "planned_date": date.today(),
        }
        items_data = [{"product_id": self.product1.id, "counted_quantity": Decimal("98.0000")}]
        count = StockCountService.create_count(self.user, count_data, items_data)

        # 更新盘点单
        update_data = {"notes": "已复核"}
        new_items_data = [
            {"product_id": self.product1.id, "counted_quantity": Decimal("99.0000")},
            {"product_id": self.product2.id, "counted_quantity": Decimal("50.0000")},
        ]

        updated_count = StockCountService.update_count(
            count, self.user, update_data, new_items_data
        )

        # 验证更新成功
        self.assertEqual(updated_count.notes, "已复核")
        self.assertEqual(updated_count.items.count(), 2)


class InboundOrderServiceTestCase(InventoryServiceTestCaseBase):
    """InboundOrderService服务测试"""

    def test_create_inbound_basic(self):
        """测试创建基础入库单"""
        inbound_data = {
            "warehouse": self.warehouse1,
            "order_date": date.today(),
            "order_type": "purchase",
            "notes": "采购入库",
        }

        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("20.0000"),
            },
            {
                "product": self.product2,
                "quantity": Decimal("10.0000"),
            },
        ]

        inbound = InboundOrderService.create_inbound(self.user, inbound_data, items_data)

        # 验证入库单创建成功
        self.assertIsNotNone(inbound.id)
        self.assertEqual(inbound.warehouse, self.warehouse1)
        self.assertEqual(inbound.status, "draft")
        self.assertEqual(inbound.created_by, self.user)

        # 验证单据号自动生成
        self.assertIsNotNone(inbound.order_number)
        self.assertTrue(inbound.order_number.startswith("IBO"))

        # 验证入库明细
        self.assertEqual(inbound.items.count(), 2)

    def test_create_inbound_with_custom_number(self):
        """测试创建入库单时指定单据号"""
        inbound_data = {
            "order_number": "IBO_CUSTOM_001",
            "warehouse": self.warehouse1,
            "order_date": date.today(),
            "order_type": "purchase",
        }

        items_data = [
            {"product": self.product1, "quantity": Decimal("10.0000")},
        ]

        inbound = InboundOrderService.create_inbound(self.user, inbound_data, items_data)

        # 验证使用了指定的单据号
        self.assertEqual(inbound.order_number, "IBO_CUSTOM_001")
