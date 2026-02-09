"""
Inventory models tests.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from apps.inventory.models import (
    Warehouse, Location, InventoryStock, InventoryTransaction,
    StockAdjustment, StockTransfer, StockTransferItem,
    StockCount, StockCountItem,
    InboundOrder, InboundOrderItem,
    OutboundOrder, OutboundOrderItem
)
from apps.products.models import Product, ProductCategory, Unit

User = get_user_model()


class WarehouseModelTest(TestCase):
    """Warehouse model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.warehouse = Warehouse.objects.create(
            name='主仓库',
            code='WH001',
            warehouse_type='main',
            address='测试地址123号',
            manager=self.user,
            capacity=Decimal('1000.00'),
            created_by=self.user
        )

    def test_warehouse_creation(self):
        """Test warehouse creation."""
        self.assertEqual(self.warehouse.name, '主仓库')
        self.assertEqual(self.warehouse.code, 'WH001')
        self.assertEqual(self.warehouse.warehouse_type, 'main')
        self.assertTrue(self.warehouse.is_active)

    def test_warehouse_str_representation(self):
        """Test warehouse string representation."""
        expected = "WH001 - 主仓库"
        self.assertEqual(str(self.warehouse), expected)

    def test_warehouse_current_utilization(self):
        """Test warehouse utilization calculation."""
        # Warehouse with no stock should have 0% utilization
        utilization = self.warehouse.current_utilization
        self.assertEqual(utilization, 0)


class LocationModelTest(TestCase):
    """Location model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.warehouse = Warehouse.objects.create(
            name='主仓库',
            code='WH001',
            created_by=self.user
        )

        self.location = Location.objects.create(
            warehouse=self.warehouse,
            code='A01-01-01',
            name='A区1通道1货架1层',
            aisle='A01',
            shelf='01',
            level='01',
            capacity=Decimal('100.00'),
            created_by=self.user
        )

    def test_location_creation(self):
        """Test location creation."""
        self.assertEqual(self.location.code, 'A01-01-01')
        self.assertEqual(self.location.warehouse, self.warehouse)
        self.assertTrue(self.location.is_active)

    def test_location_str_representation(self):
        """Test location string representation."""
        expected = "WH001-A01-01-01"
        self.assertEqual(str(self.location), expected)

    def test_location_unique_together(self):
        """Test that warehouse + code must be unique."""
        # Creating location with same code in same warehouse should fail
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Location.objects.create(
                warehouse=self.warehouse,
                code='A01-01-01',  # Same code
                name='重复库位',
                created_by=self.user
            )


class InventoryStockModelTest(TestCase):
    """Inventory stock model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.category = ProductCategory.objects.create(
            name='测试分类',
            code='CAT001',
            created_by=self.user
        )

        self.unit = Unit.objects.create(
            name='件',
            symbol='pcs',
            created_by=self.user
        )

        self.product = Product.objects.create(
            name='测试产品',
            code='PROD001',
            category=self.category,
            unit=self.unit,
            cost_price=Decimal('50.00'),
            min_stock=10,
            created_by=self.user
        )

        self.warehouse = Warehouse.objects.create(
            name='主仓库',
            code='WH001',
            created_by=self.user
        )

        self.location = Location.objects.create(
            warehouse=self.warehouse,
            code='A01',
            name='A区',
            created_by=self.user
        )

        self.stock = InventoryStock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal('100.00'),
            reserved_quantity=Decimal('20.00'),
            cost_price=Decimal('50.00'),
            created_by=self.user
        )

    def test_stock_creation(self):
        """Test inventory stock creation."""
        self.assertEqual(self.stock.product, self.product)
        self.assertEqual(self.stock.warehouse, self.warehouse)
        self.assertEqual(self.stock.quantity, Decimal('100.00'))

    def test_available_quantity_calculation(self):
        """Test available quantity calculation."""
        # Available = Total - Reserved = 100 - 20 = 80
        self.assertEqual(self.stock.available_quantity, Decimal('80.00'))

    def test_is_low_stock_check(self):
        """Test low stock detection."""
        # Product min_stock is 10, current quantity is 100
        self.assertFalse(self.stock.is_low_stock)

        # Reduce quantity below minimum
        self.stock.quantity = Decimal('5.00')
        self.stock.save()
        self.assertTrue(self.stock.is_low_stock)

    def test_stock_str_representation(self):
        """Test stock string representation."""
        expected = f"{self.product.name} - {self.warehouse.name} - {self.stock.quantity}"
        self.assertEqual(str(self.stock), expected)


class InventoryTransactionModelTest(TestCase):
    """Inventory transaction model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.category = ProductCategory.objects.create(
            name='测试分类',
            code='CAT001',
            created_by=self.user
        )

        self.unit = Unit.objects.create(
            name='件',
            symbol='pcs',
            created_by=self.user
        )

        self.product = Product.objects.create(
            name='测试产品',
            code='PROD001',
            category=self.category,
            unit=self.unit,
            cost_price=Decimal('50.00'),
            created_by=self.user
        )

        self.warehouse = Warehouse.objects.create(
            name='主仓库',
            code='WH001',
            created_by=self.user
        )

        self.location = Location.objects.create(
            warehouse=self.warehouse,
            code='A01',
            name='A区',
            created_by=self.user
        )

    def test_transaction_creation_in(self):
        """Test inbound transaction creation."""
        transaction = InventoryTransaction.objects.create(
            transaction_type='in',
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal('100.00'),
            unit_cost=Decimal('50.00'),
            reference_type='purchase_order',
            reference_number='PO2025110001',
            operator=self.user,
            created_by=self.user
        )

        self.assertEqual(transaction.transaction_type, 'in')
        self.assertEqual(transaction.quantity, Decimal('100.00'))
        self.assertEqual(transaction.total_cost, Decimal('5000.00'))

    def test_transaction_updates_stock_on_inbound(self):
        """Test that inbound transaction updates stock."""
        # Initial stock should be 0
        initial_stocks = InventoryStock.objects.filter(
            product=self.product,
            warehouse=self.warehouse,
            location=self.location
        )
        self.assertEqual(initial_stocks.count(), 0)

        # Create inbound transaction
        InventoryTransaction.objects.create(
            transaction_type='in',
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal('100.00'),
            unit_cost=Decimal('50.00'),
            created_by=self.user
        )

        # Stock should be created with quantity 100
        stock = InventoryStock.objects.get(
            product=self.product,
            warehouse=self.warehouse,
            location=self.location
        )
        self.assertEqual(stock.quantity, Decimal('100.00'))

    def test_transaction_updates_stock_on_outbound(self):
        """Test that outbound transaction decreases stock."""
        # Create initial stock
        InventoryStock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal('100.00'),
            created_by=self.user
        )

        # Create outbound transaction
        InventoryTransaction.objects.create(
            transaction_type='out',
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal('30.00'),
            unit_cost=Decimal('50.00'),
            created_by=self.user
        )

        # Stock should be reduced to 70
        stock = InventoryStock.objects.get(
            product=self.product,
            warehouse=self.warehouse,
            location=self.location
        )
        self.assertEqual(stock.quantity, Decimal('70.00'))

    def test_transaction_str_representation(self):
        """Test transaction string representation."""
        transaction = InventoryTransaction.objects.create(
            transaction_type='in',
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('100.00'),
            unit_cost=Decimal('50.00'),
            created_by=self.user
        )

        expected = f"入库 - {self.product.name} - {transaction.quantity}"
        self.assertEqual(str(transaction), expected)


class StockAdjustmentModelTest(TestCase):
    """Stock adjustment model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.category = ProductCategory.objects.create(
            name='测试分类',
            code='CAT001',
            created_by=self.user
        )

        self.unit = Unit.objects.create(
            name='件',
            symbol='pcs',
            created_by=self.user
        )

        self.product = Product.objects.create(
            name='测试产品',
            code='PROD001',
            category=self.category,
            unit=self.unit,
            created_by=self.user
        )

        self.warehouse = Warehouse.objects.create(
            name='主仓库',
            code='WH001',
            created_by=self.user
        )

        # Create initial stock
        self.stock = InventoryStock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('100.00'),
            created_by=self.user
        )

    def test_adjustment_creation(self):
        """Test stock adjustment creation."""
        adjustment = StockAdjustment.objects.create(
            adjustment_number='ADJ2025110001',
            adjustment_type='decrease',
            warehouse=self.warehouse,
            product=self.product,
            original_quantity=Decimal('100.00'),
            adjusted_quantity=Decimal('95.00'),
            difference=Decimal('-5.00'),
            reason='damage',
            created_by=self.user
        )

        self.assertEqual(adjustment.adjustment_number, 'ADJ2025110001')
        self.assertEqual(adjustment.difference, Decimal('-5.00'))
        self.assertFalse(adjustment.is_approved)


class StockTransferModelTest(TestCase):
    """Stock transfer model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.warehouse_from = Warehouse.objects.create(
            name='源仓库',
            code='WH001',
            created_by=self.user
        )

        self.warehouse_to = Warehouse.objects.create(
            name='目标仓库',
            code='WH002',
            created_by=self.user
        )

        self.transfer = StockTransfer.objects.create(
            transfer_number='TF2025110001',
            from_warehouse=self.warehouse_from,
            to_warehouse=self.warehouse_to,
            status='draft',
            transfer_date=timezone.now().date(),
            created_by=self.user
        )

    def test_transfer_creation(self):
        """Test stock transfer creation."""
        self.assertEqual(self.transfer.transfer_number, 'TF2025110001')
        self.assertEqual(self.transfer.from_warehouse, self.warehouse_from)
        self.assertEqual(self.transfer.to_warehouse, self.warehouse_to)
        self.assertEqual(self.transfer.status, 'draft')

    def test_transfer_str_representation(self):
        """Test transfer string representation."""
        expected = f"TF2025110001 - 源仓库 → 目标仓库"
        self.assertEqual(str(self.transfer), expected)


class StockTransferItemModelTest(TestCase):
    """Stock transfer item model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.category = ProductCategory.objects.create(
            name='测试分类',
            code='CAT001',
            created_by=self.user
        )

        self.unit = Unit.objects.create(
            name='件',
            symbol='pcs',
            created_by=self.user
        )

        self.product = Product.objects.create(
            name='测试产品',
            code='PROD001',
            category=self.category,
            unit=self.unit,
            cost_price=Decimal('50.00'),
            created_by=self.user
        )

        self.warehouse_from = Warehouse.objects.create(
            name='源仓库',
            code='WH001',
            created_by=self.user
        )

        self.warehouse_to = Warehouse.objects.create(
            name='目标仓库',
            code='WH002',
            created_by=self.user
        )

        self.transfer = StockTransfer.objects.create(
            transfer_number='TF2025110001',
            from_warehouse=self.warehouse_from,
            to_warehouse=self.warehouse_to,
            transfer_date=timezone.now().date(),
            created_by=self.user
        )

        self.transfer_item = StockTransferItem.objects.create(
            transfer=self.transfer,
            product=self.product,
            requested_quantity=Decimal('50.00'),
            created_by=self.user
        )

    def test_transfer_item_creation(self):
        """Test transfer item creation."""
        self.assertEqual(self.transfer_item.product, self.product)
        self.assertEqual(self.transfer_item.requested_quantity, Decimal('50.00'))
        self.assertEqual(self.transfer_item.transfer, self.transfer)

    def test_transfer_item_str_representation(self):
        """Test transfer item string representation."""
        expected = f"{self.transfer.transfer_number} - {self.product.name}"
        self.assertEqual(str(self.transfer_item), expected)


class StockCountModelTest(TestCase):
    """Stock count model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.warehouse = Warehouse.objects.create(
            name='主仓库',
            code='WH001',
            created_by=self.user
        )

        self.stock_count = StockCount.objects.create(
            count_number='SC2025110001',
            count_type='full',
            warehouse=self.warehouse,
            status='planned',
            planned_date=timezone.now().date(),
            created_by=self.user
        )

    def test_stock_count_creation(self):
        """Test stock count creation."""
        self.assertEqual(self.stock_count.count_number, 'SC2025110001')
        self.assertEqual(self.stock_count.count_type, 'full')
        self.assertEqual(self.stock_count.warehouse, self.warehouse)
        self.assertEqual(self.stock_count.status, 'planned')

    def test_stock_count_str_representation(self):
        """Test stock count string representation."""
        expected = f"SC2025110001 - {self.warehouse.name}"
        self.assertEqual(str(self.stock_count), expected)


class StockCountItemModelTest(TestCase):
    """Stock count item model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.category = ProductCategory.objects.create(
            name='测试分类',
            code='CAT001',
            created_by=self.user
        )

        self.unit = Unit.objects.create(
            name='件',
            symbol='pcs',
            created_by=self.user
        )

        self.product = Product.objects.create(
            name='测试产品',
            code='PROD001',
            category=self.category,
            unit=self.unit,
            cost_price=Decimal('50.00'),
            created_by=self.user
        )

        self.warehouse = Warehouse.objects.create(
            name='主仓库',
            code='WH001',
            created_by=self.user
        )

        self.stock_count = StockCount.objects.create(
            count_number='SC2025110001',
            count_type='full',
            warehouse=self.warehouse,
            planned_date=timezone.now().date(),
            created_by=self.user
        )

        self.count_item = StockCountItem.objects.create(
            count=self.stock_count,
            product=self.product,
            system_quantity=Decimal('100.00'),
            counted_quantity=Decimal('98.00'),
            difference=Decimal('-2.00'),
            created_by=self.user
        )

    def test_count_item_creation(self):
        """Test count item creation."""
        self.assertEqual(self.count_item.product, self.product)
        self.assertEqual(self.count_item.system_quantity, Decimal('100.00'))
        self.assertEqual(self.count_item.counted_quantity, Decimal('98.00'))
        self.assertEqual(self.count_item.difference, Decimal('-2.00'))

    def test_count_item_str_representation(self):
        """Test count item string representation."""
        expected = f"{self.stock_count.count_number} - {self.product.name}"
        self.assertEqual(str(self.count_item), expected)


class InboundOrderModelTest(TestCase):
    """Inbound order model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.warehouse = Warehouse.objects.create(
            name='主仓库',
            code='WH001',
            created_by=self.user
        )

        self.inbound_order = InboundOrder.objects.create(
            order_number='IB2025110001',
            warehouse=self.warehouse,
            order_type='purchase',
            status='draft',
            order_date=timezone.now().date(),
            created_by=self.user
        )

    def test_inbound_order_creation(self):
        """Test inbound order creation."""
        self.assertEqual(self.inbound_order.order_number, 'IB2025110001')
        self.assertEqual(self.inbound_order.warehouse, self.warehouse)
        self.assertEqual(self.inbound_order.order_type, 'purchase')
        self.assertEqual(self.inbound_order.status, 'draft')

    def test_inbound_order_str_representation(self):
        """Test inbound order string representation."""
        expected = f"IB2025110001 - {self.warehouse.name}"
        self.assertEqual(str(self.inbound_order), expected)


class InboundOrderItemModelTest(TestCase):
    """Inbound order item model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.category = ProductCategory.objects.create(
            name='测试分类',
            code='CAT001',
            created_by=self.user
        )

        self.unit = Unit.objects.create(
            name='件',
            symbol='pcs',
            created_by=self.user
        )

        self.product = Product.objects.create(
            name='测试产品',
            code='PROD001',
            category=self.category,
            unit=self.unit,
            cost_price=Decimal('50.00'),
            created_by=self.user
        )

        self.warehouse = Warehouse.objects.create(
            name='主仓库',
            code='WH001',
            created_by=self.user
        )

        self.location = Location.objects.create(
            warehouse=self.warehouse,
            code='A01',
            name='A区',
            created_by=self.user
        )

        self.inbound_order = InboundOrder.objects.create(
            order_number='IB2025110001',
            warehouse=self.warehouse,
            order_type='purchase',
            order_date=timezone.now().date(),
            created_by=self.user
        )

        self.inbound_item = InboundOrderItem.objects.create(
            inbound_order=self.inbound_order,
            product=self.product,
            location=self.location,
            quantity=Decimal('100.00'),
            created_by=self.user
        )

    def test_inbound_item_creation(self):
        """Test inbound item creation."""
        self.assertEqual(self.inbound_item.product, self.product)
        self.assertEqual(self.inbound_item.quantity, Decimal('100.00'))
        self.assertEqual(self.inbound_item.location, self.location)

    def test_inbound_item_str_representation(self):
        """Test inbound item string representation."""
        expected = f"{self.inbound_order.order_number} - {self.product.name}"
        self.assertEqual(str(self.inbound_item), expected)


class OutboundOrderModelTest(TestCase):
    """Outbound order model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.warehouse = Warehouse.objects.create(
            name='主仓库',
            code='WH001',
            created_by=self.user
        )

        self.outbound_order = OutboundOrder.objects.create(
            order_number='OB2025110001',
            warehouse=self.warehouse,
            order_type='sales',
            status='draft',
            order_date=timezone.now().date(),
            created_by=self.user
        )

    def test_outbound_order_creation(self):
        """Test outbound order creation."""
        self.assertEqual(self.outbound_order.order_number, 'OB2025110001')
        self.assertEqual(self.outbound_order.warehouse, self.warehouse)
        self.assertEqual(self.outbound_order.order_type, 'sales')
        self.assertEqual(self.outbound_order.status, 'draft')

    def test_outbound_order_str_representation(self):
        """Test outbound order string representation."""
        expected = f"OB2025110001 - {self.warehouse.name}"
        self.assertEqual(str(self.outbound_order), expected)


class OutboundOrderItemModelTest(TestCase):
    """Outbound order item model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.category = ProductCategory.objects.create(
            name='测试分类',
            code='CAT001',
            created_by=self.user
        )

        self.unit = Unit.objects.create(
            name='件',
            symbol='pcs',
            created_by=self.user
        )

        self.product = Product.objects.create(
            name='测试产品',
            code='PROD001',
            category=self.category,
            unit=self.unit,
            cost_price=Decimal('50.00'),
            created_by=self.user
        )

        self.warehouse = Warehouse.objects.create(
            name='主仓库',
            code='WH001',
            created_by=self.user
        )

        self.location = Location.objects.create(
            warehouse=self.warehouse,
            code='A01',
            name='A区',
            created_by=self.user
        )

        self.outbound_order = OutboundOrder.objects.create(
            order_number='OB2025110001',
            warehouse=self.warehouse,
            order_type='sales',
            order_date=timezone.now().date(),
            created_by=self.user
        )

        self.outbound_item = OutboundOrderItem.objects.create(
            outbound_order=self.outbound_order,
            product=self.product,
            location=self.location,
            quantity=Decimal('50.00'),
            created_by=self.user
        )

    def test_outbound_item_creation(self):
        """Test outbound item creation."""
        self.assertEqual(self.outbound_item.product, self.product)
        self.assertEqual(self.outbound_item.quantity, Decimal('50.00'))
        self.assertEqual(self.outbound_item.location, self.location)

    def test_outbound_item_str_representation(self):
        """Test outbound item string representation."""
        expected = f"{self.outbound_order.order_number} - {self.product.name}"
        self.assertEqual(str(self.outbound_item), expected)
