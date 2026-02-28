"""
Inventory business logic tests.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.inventory.models import (
    InboundOrder,
    InboundOrderItem,
    InventoryStock,
    InventoryTransaction,
    Location,
    OutboundOrder,
    OutboundOrderItem,
    StockAdjustment,
    StockCount,
    StockCountItem,
    StockTransfer,
    StockTransferItem,
    Warehouse,
)
from apps.products.models import Product, ProductCategory, Unit

User = get_user_model()


class InventoryTransactionTest(TestCase):
    """Test inventory transaction stock update logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.warehouse = Warehouse.objects.create(name="主仓库", code="WH001", created_by=self.user)

        self.location = Location.objects.create(
            warehouse=self.warehouse, code="A01", name="A区", created_by=self.user
        )

        self.category = ProductCategory.objects.create(
            name="测试分类", code="CAT001", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        self.product = Product.objects.create(
            name="测试产品",
            code="PROD001",
            category=self.category,
            unit=self.unit,
            cost_price=Decimal("50.00"),
            created_by=self.user,
        )

    def test_inbound_transaction_creates_stock(self):
        """Test inbound transaction creates stock if not exists."""
        # Initially no stock
        self.assertEqual(
            InventoryStock.objects.filter(
                product=self.product, warehouse=self.warehouse, location=self.location
            ).count(),
            0,
        )

        # Create inbound transaction
        transaction = InventoryTransaction.objects.create(
            transaction_type="in",
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal("100.00"),
            unit_cost=Decimal("50.00"),
            created_by=self.user,
        )

        # Verify stock created
        stock = InventoryStock.objects.get(
            product=self.product, warehouse=self.warehouse, location=self.location
        )
        self.assertEqual(stock.quantity, Decimal("100.00"))
        self.assertIsNotNone(stock.last_in_date)

    def test_inbound_transaction_updates_existing_stock(self):
        """Test inbound transaction updates existing stock."""
        # Create initial stock
        stock = InventoryStock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal("50.00"),
            created_by=self.user,
        )

        # Create inbound transaction
        InventoryTransaction.objects.create(
            transaction_type="in",
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal("30.00"),
            unit_cost=Decimal("50.00"),
            created_by=self.user,
        )

        # Verify stock updated
        stock.refresh_from_db()
        self.assertEqual(stock.quantity, Decimal("80.00"))

    def test_outbound_transaction_decreases_stock(self):
        """Test outbound transaction decreases stock."""
        # Create initial stock
        stock = InventoryStock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal("100.00"),
            created_by=self.user,
        )

        # Create outbound transaction
        InventoryTransaction.objects.create(
            transaction_type="out",
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal("30.00"),
            unit_cost=Decimal("50.00"),
            created_by=self.user,
        )

        # Verify stock decreased
        stock.refresh_from_db()
        self.assertEqual(stock.quantity, Decimal("70.00"))
        self.assertIsNotNone(stock.last_out_date)

    def test_return_transaction_increases_stock(self):
        """Test return transaction increases stock."""
        # Create initial stock
        stock = InventoryStock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal("100.00"),
            created_by=self.user,
        )

        # Create return transaction
        InventoryTransaction.objects.create(
            transaction_type="return",
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal("20.00"),
            unit_cost=Decimal("50.00"),
            created_by=self.user,
        )

        # Verify stock increased
        stock.refresh_from_db()
        self.assertEqual(stock.quantity, Decimal("120.00"))


class InboundOrderProcessTest(TestCase):
    """Test inbound order process logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.warehouse = Warehouse.objects.create(name="主仓库", code="WH001", created_by=self.user)

        self.location = Location.objects.create(
            warehouse=self.warehouse, code="A01", name="A区", created_by=self.user
        )

        self.category = ProductCategory.objects.create(
            name="测试分类", code="CAT001", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        self.product = Product.objects.create(
            name="测试产品",
            code="PROD001",
            category=self.category,
            unit=self.unit,
            cost_price=Decimal("50.00"),
            created_by=self.user,
        )

    def test_inbound_order_creation(self):
        """Test inbound order creation."""
        order = InboundOrder.objects.create(
            order_number="IB2025110001",
            warehouse=self.warehouse,
            order_type="purchase",
            order_date=timezone.now().date(),
            created_by=self.user,
        )

        # Add item
        item = InboundOrderItem.objects.create(
            inbound_order=order,
            product=self.product,
            location=self.location,
            quantity=Decimal("100.00"),
            created_by=self.user,
        )

        self.assertEqual(order.status, "draft")
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(item.quantity, Decimal("100.00"))

    def test_inbound_order_creates_transaction(self):
        """Test completing inbound order creates inventory transaction."""
        order = InboundOrder.objects.create(
            order_number="IB2025110001",
            warehouse=self.warehouse,
            order_type="purchase",
            status="approved",
            order_date=timezone.now().date(),
            created_by=self.user,
        )

        InboundOrderItem.objects.create(
            inbound_order=order,
            product=self.product,
            location=self.location,
            quantity=Decimal("100.00"),
            created_by=self.user,
        )

        # Manually create transaction (simulating approval process)
        for item in order.items.all():
            InventoryTransaction.objects.create(
                transaction_type="in",
                product=item.product,
                warehouse=order.warehouse,
                location=item.location,
                quantity=item.quantity,
                reference_type="inbound_order",
                reference_number=order.order_number,
                created_by=self.user,
            )

        # Verify transaction created and stock updated
        self.assertEqual(
            InventoryTransaction.objects.filter(reference_number=order.order_number).count(),
            1,
        )

        stock = InventoryStock.objects.get(
            product=self.product, warehouse=self.warehouse, location=self.location
        )
        self.assertEqual(stock.quantity, Decimal("100.00"))


class OutboundOrderProcessTest(TestCase):
    """Test outbound order process logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.warehouse = Warehouse.objects.create(name="主仓库", code="WH001", created_by=self.user)

        self.location = Location.objects.create(
            warehouse=self.warehouse, code="A01", name="A区", created_by=self.user
        )

        self.category = ProductCategory.objects.create(
            name="测试分类", code="CAT001", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        self.product = Product.objects.create(
            name="测试产品",
            code="PROD001",
            category=self.category,
            unit=self.unit,
            cost_price=Decimal("50.00"),
            created_by=self.user,
        )

        # Create initial stock
        InventoryStock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal("200.00"),
            created_by=self.user,
        )

    def test_outbound_order_creation(self):
        """Test outbound order creation."""
        order = OutboundOrder.objects.create(
            order_number="OB2025110001",
            warehouse=self.warehouse,
            order_type="sales",
            order_date=timezone.now().date(),
            created_by=self.user,
        )

        # Add item
        item = OutboundOrderItem.objects.create(
            outbound_order=order,
            product=self.product,
            location=self.location,
            quantity=Decimal("50.00"),
            created_by=self.user,
        )

        self.assertEqual(order.status, "draft")
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(item.quantity, Decimal("50.00"))

    def test_outbound_order_reduces_stock(self):
        """Test completing outbound order reduces stock."""
        order = OutboundOrder.objects.create(
            order_number="OB2025110001",
            warehouse=self.warehouse,
            order_type="sales",
            status="approved",
            order_date=timezone.now().date(),
            created_by=self.user,
        )

        OutboundOrderItem.objects.create(
            outbound_order=order,
            product=self.product,
            location=self.location,
            quantity=Decimal("50.00"),
            created_by=self.user,
        )

        # Manually create transaction (simulating approval process)
        for item in order.items.all():
            InventoryTransaction.objects.create(
                transaction_type="out",
                product=item.product,
                warehouse=order.warehouse,
                location=item.location,
                quantity=item.quantity,
                reference_type="outbound_order",
                reference_number=order.order_number,
                created_by=self.user,
            )

        # Verify stock reduced
        stock = InventoryStock.objects.get(
            product=self.product, warehouse=self.warehouse, location=self.location
        )
        self.assertEqual(stock.quantity, Decimal("150.00"))


class StockTransferProcessTest(TestCase):
    """Test stock transfer process logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.warehouse_from = Warehouse.objects.create(
            name="源仓库", code="WH001", created_by=self.user
        )

        self.warehouse_to = Warehouse.objects.create(
            name="目标仓库", code="WH002", created_by=self.user
        )

        self.location_from = Location.objects.create(
            warehouse=self.warehouse_from, code="A01", name="A区", created_by=self.user
        )

        self.location_to = Location.objects.create(
            warehouse=self.warehouse_to, code="B01", name="B区", created_by=self.user
        )

        self.category = ProductCategory.objects.create(
            name="测试分类", code="CAT001", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        self.product = Product.objects.create(
            name="测试产品",
            code="PROD001",
            category=self.category,
            unit=self.unit,
            cost_price=Decimal("50.00"),
            created_by=self.user,
        )

        # Create stock in source warehouse
        InventoryStock.objects.create(
            product=self.product,
            warehouse=self.warehouse_from,
            location=self.location_from,
            quantity=Decimal("100.00"),
            created_by=self.user,
        )

    def test_transfer_creation(self):
        """Test stock transfer creation."""
        transfer = StockTransfer.objects.create(
            transfer_number="TF2025110001",
            from_warehouse=self.warehouse_from,
            to_warehouse=self.warehouse_to,
            transfer_date=timezone.now().date(),
            created_by=self.user,
        )

        # Add transfer item
        item = StockTransferItem.objects.create(
            transfer=transfer,
            product=self.product,
            requested_quantity=Decimal("30.00"),
            created_by=self.user,
        )

        self.assertEqual(transfer.status, "draft")
        self.assertEqual(transfer.items.count(), 1)
        self.assertEqual(item.requested_quantity, Decimal("30.00"))

    def test_transfer_moves_stock(self):
        """Test completing transfer moves stock between warehouses."""
        transfer = StockTransfer.objects.create(
            transfer_number="TF2025110001",
            from_warehouse=self.warehouse_from,
            to_warehouse=self.warehouse_to,
            transfer_date=timezone.now().date(),
            status="approved",
            created_by=self.user,
        )

        StockTransferItem.objects.create(
            transfer=transfer,
            product=self.product,
            requested_quantity=Decimal("30.00"),
            shipped_quantity=Decimal("30.00"),
            received_quantity=Decimal("30.00"),
            created_by=self.user,
        )

        # Simulate transfer completion: out from source, in to destination
        for item in transfer.items.all():
            # Out from source
            InventoryTransaction.objects.create(
                transaction_type="out",
                product=item.product,
                warehouse=transfer.from_warehouse,
                location=self.location_from,
                quantity=item.received_quantity,
                reference_type="stock_transfer",
                reference_number=transfer.transfer_number,
                created_by=self.user,
            )

            # In to destination
            InventoryTransaction.objects.create(
                transaction_type="in",
                product=item.product,
                warehouse=transfer.to_warehouse,
                location=self.location_to,
                quantity=item.received_quantity,
                reference_type="stock_transfer",
                reference_number=transfer.transfer_number,
                created_by=self.user,
            )

        # Verify source stock reduced
        source_stock = InventoryStock.objects.get(
            product=self.product,
            warehouse=self.warehouse_from,
            location=self.location_from,
        )
        self.assertEqual(source_stock.quantity, Decimal("70.00"))

        # Verify destination stock increased
        dest_stock = InventoryStock.objects.get(
            product=self.product, warehouse=self.warehouse_to, location=self.location_to
        )
        self.assertEqual(dest_stock.quantity, Decimal("30.00"))


class StockCountProcessTest(TestCase):
    """Test stock count process logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.warehouse = Warehouse.objects.create(name="主仓库", code="WH001", created_by=self.user)

        self.location = Location.objects.create(
            warehouse=self.warehouse, code="A01", name="A区", created_by=self.user
        )

        self.category = ProductCategory.objects.create(
            name="测试分类", code="CAT001", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        self.product = Product.objects.create(
            name="测试产品",
            code="PROD001",
            category=self.category,
            unit=self.unit,
            cost_price=Decimal("50.00"),
            created_by=self.user,
        )

        # Create stock
        self.stock = InventoryStock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal("100.00"),
            created_by=self.user,
        )

    def test_stock_count_creation(self):
        """Test stock count creation."""
        count = StockCount.objects.create(
            count_number="SC2025110001",
            count_type="full",
            warehouse=self.warehouse,
            planned_date=timezone.now().date(),
            created_by=self.user,
        )

        # Add count item
        item = StockCountItem.objects.create(
            count=count,
            product=self.product,
            location=self.location,
            system_quantity=Decimal("100.00"),
            counted_quantity=Decimal("98.00"),
            difference=Decimal("-2.00"),
            created_by=self.user,
        )

        self.assertEqual(count.status, "planned")
        self.assertEqual(count.items.count(), 1)
        self.assertEqual(item.difference, Decimal("-2.00"))

    def test_stock_count_identifies_discrepancy(self):
        """Test stock count identifies quantity discrepancy."""
        count = StockCount.objects.create(
            count_number="SC2025110001",
            count_type="full",
            warehouse=self.warehouse,
            planned_date=timezone.now().date(),
            status="in_progress",
            created_by=self.user,
        )

        # System shows 100, but actually counted 95
        item = StockCountItem.objects.create(
            count=count,
            product=self.product,
            location=self.location,
            system_quantity=self.stock.quantity,
            counted_quantity=Decimal("95.00"),
            difference=Decimal("-5.00"),
            created_by=self.user,
        )

        # Verify discrepancy recorded
        self.assertEqual(item.system_quantity, Decimal("100.00"))
        self.assertEqual(item.counted_quantity, Decimal("95.00"))
        self.assertEqual(item.difference, Decimal("-5.00"))


class StockAdjustmentProcessTest(TestCase):
    """Test stock adjustment process logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.approver = User.objects.create_user(
            username="approver", email="approver@test.com", password="testpass123"
        )

        self.warehouse = Warehouse.objects.create(name="主仓库", code="WH001", created_by=self.user)

        self.location = Location.objects.create(
            warehouse=self.warehouse, code="A01", name="A区", created_by=self.user
        )

        self.category = ProductCategory.objects.create(
            name="测试分类", code="CAT001", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        self.product = Product.objects.create(
            name="测试产品",
            code="PROD001",
            category=self.category,
            unit=self.unit,
            cost_price=Decimal("50.00"),
            created_by=self.user,
        )

        # Create stock
        self.stock = InventoryStock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal("100.00"),
            created_by=self.user,
        )

    def test_adjustment_creation(self):
        """Test stock adjustment creation."""
        adjustment = StockAdjustment.objects.create(
            adjustment_number="ADJ2025110001",
            adjustment_type="decrease",
            warehouse=self.warehouse,
            product=self.product,
            location=self.location,
            original_quantity=Decimal("100.00"),
            adjusted_quantity=Decimal("95.00"),
            difference=Decimal("-5.00"),
            reason="damage",
            created_by=self.user,
        )

        self.assertFalse(adjustment.is_approved)
        self.assertEqual(adjustment.difference, Decimal("-5.00"))

    def test_adjustment_approval_updates_stock(self):
        """Test approving adjustment updates stock."""
        adjustment = StockAdjustment.objects.create(
            adjustment_number="ADJ2025110001",
            adjustment_type="decrease",
            warehouse=self.warehouse,
            product=self.product,
            location=self.location,
            original_quantity=Decimal("100.00"),
            adjusted_quantity=Decimal("95.00"),
            difference=Decimal("-5.00"),
            reason="damage",
            created_by=self.user,
        )

        # Simulate approval and transaction creation
        adjustment.is_approved = True
        adjustment.approved_by = self.approver
        adjustment.approved_at = timezone.now()
        adjustment.save()

        # Create adjustment transaction
        InventoryTransaction.objects.create(
            transaction_type="adjustment",
            product=adjustment.product,
            warehouse=adjustment.warehouse,
            location=adjustment.location,
            quantity=adjustment.difference,  # Use signed difference (-5.00 for decrease)
            reference_type="stock_adjustment",
            reference_number=adjustment.adjustment_number,
            created_by=self.approver,
        )

        # Verify stock updated
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("95.00"))

    def test_increase_adjustment(self):
        """Test increase adjustment increases stock."""
        adjustment = StockAdjustment.objects.create(
            adjustment_number="ADJ2025110002",
            adjustment_type="increase",
            warehouse=self.warehouse,
            product=self.product,
            location=self.location,
            original_quantity=Decimal("100.00"),
            adjusted_quantity=Decimal("110.00"),
            difference=Decimal("10.00"),
            reason="count_error",
            is_approved=True,
            approved_by=self.approver,
            approved_at=timezone.now(),
            created_by=self.user,
        )

        # Create adjustment transaction (increase)
        InventoryTransaction.objects.create(
            transaction_type="adjustment",  # Use adjustment type consistently
            product=adjustment.product,
            warehouse=adjustment.warehouse,
            location=adjustment.location,
            quantity=adjustment.difference,  # Positive difference (10.00 for increase)
            reference_type="stock_adjustment",
            reference_number=adjustment.adjustment_number,
            created_by=self.approver,
        )

        # Verify stock increased
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("110.00"))


class IntegrationTest(TestCase):
    """Test complete inventory workflow integration."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.warehouse = Warehouse.objects.create(name="主仓库", code="WH001", created_by=self.user)

        self.location = Location.objects.create(
            warehouse=self.warehouse, code="A01", name="A区", created_by=self.user
        )

        self.category = ProductCategory.objects.create(
            name="测试分类", code="CAT001", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        self.product = Product.objects.create(
            name="测试产品",
            code="PROD001",
            category=self.category,
            unit=self.unit,
            cost_price=Decimal("50.00"),
            created_by=self.user,
        )

    def test_complete_inventory_flow(self):
        """Test complete inventory flow: inbound → outbound → adjustment."""
        # 1. Inbound 100 units
        InventoryTransaction.objects.create(
            transaction_type="in",
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal("100.00"),
            unit_cost=Decimal("50.00"),
            created_by=self.user,
        )

        stock = InventoryStock.objects.get(
            product=self.product, warehouse=self.warehouse, location=self.location
        )
        self.assertEqual(stock.quantity, Decimal("100.00"))

        # 2. Outbound 30 units
        InventoryTransaction.objects.create(
            transaction_type="out",
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal("30.00"),
            unit_cost=Decimal("50.00"),
            created_by=self.user,
        )

        stock.refresh_from_db()
        self.assertEqual(stock.quantity, Decimal("70.00"))

        # 3. Return 10 units
        InventoryTransaction.objects.create(
            transaction_type="return",
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal("10.00"),
            unit_cost=Decimal("50.00"),
            created_by=self.user,
        )

        stock.refresh_from_db()
        self.assertEqual(stock.quantity, Decimal("80.00"))

        # 4. Adjustment -5 units (damage)
        InventoryTransaction.objects.create(
            transaction_type="adjustment",
            product=self.product,
            warehouse=self.warehouse,
            location=self.location,
            quantity=Decimal("-5.00"),  # Negative for decrease
            unit_cost=Decimal("50.00"),
            created_by=self.user,
        )

        stock.refresh_from_db()
        self.assertEqual(stock.quantity, Decimal("75.00"))

        # Verify all transactions recorded
        self.assertEqual(InventoryTransaction.objects.filter(product=self.product).count(), 4)
