"""
Sales models tests.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.customers.models import Customer
from apps.inventory.models import Warehouse
from apps.products.models import Product, ProductCategory, Unit
from apps.sales.models import Delivery, Quote, SalesOrder, SalesOrderItem, SalesReturn

User = get_user_model()


class SalesOrderModelTest(TestCase):
    """Sales order model tests."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        # Create test customer
        self.customer = Customer.objects.create(name="测试客户", code="CUS001", created_by=self.user)

        # Create test category
        self.category = ProductCategory.objects.create(
            name="测试分类", code="CAT001", created_by=self.user
        )

        # Create test unit
        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        # Create test product
        self.product = Product.objects.create(
            name="测试产品",
            code="PROD001",
            category=self.category,
            specifications="标准规格",
            unit=self.unit,
            selling_price=Decimal("100.00"),
            cost_price=Decimal("80.00"),
            created_by=self.user,
        )

        # Create test warehouse
        self.warehouse = Warehouse.objects.create(name="测试仓库", code="WH001", created_by=self.user)

        # Create test sales order
        self.order = SalesOrder.objects.create(
            order_number="SO2025110001",
            customer=self.customer,
            order_date=timezone.now().date(),
            required_date=timezone.now().date() + timedelta(days=7),
            tax_rate=Decimal("13.00"),
            created_by=self.user,
        )

    def test_order_creation(self):
        """Test sales order creation."""
        self.assertEqual(self.order.order_number, "SO2025110001")
        self.assertEqual(self.order.customer, self.customer)
        self.assertEqual(self.order.status, "draft")
        self.assertEqual(self.order.payment_status, "unpaid")

    def test_order_calculate_totals(self):
        """Test sales order totals calculation."""
        # Add order items
        item1 = SalesOrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=10,
            unit_price=Decimal("100.00"),  # 含税单价
            created_by=self.user,
        )
        item2 = SalesOrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=5,
            unit_price=Decimal("100.00"),  # 含税单价
            created_by=self.user,
        )

        # Calculate totals
        self.order.calculate_totals()
        self.order.save()

        # Expected: 10*100 + 5*100 = 1500
        self.assertEqual(self.order.subtotal, Decimal("1500.00"))
        self.assertEqual(self.order.total_amount, Decimal("1500.00"))

    def test_order_calculate_with_discount(self):
        """Test sales order calculation with discount."""
        # Add order item
        SalesOrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=10,
            unit_price=Decimal("100.00"),
            created_by=self.user,
        )

        # Apply 10% discount
        self.order.discount_rate = Decimal("10.00")
        self.order.calculate_totals()
        self.order.save()

        # Expected: 1000 * 0.9 = 900
        self.assertEqual(self.order.subtotal, Decimal("1000.00"))
        self.assertEqual(self.order.discount_amount, Decimal("100.00"))
        self.assertEqual(self.order.total_amount, Decimal("900.00"))

    def test_order_calculate_with_shipping(self):
        """Test sales order calculation with shipping cost."""
        # Add order item
        SalesOrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=10,
            unit_price=Decimal("100.00"),
            created_by=self.user,
        )

        # Add shipping cost
        self.order.shipping_cost = Decimal("50.00")
        self.order.calculate_totals()
        self.order.save()

        # Expected: 1000 + 50 = 1050
        self.assertEqual(self.order.subtotal, Decimal("1000.00"))
        self.assertEqual(self.order.total_amount, Decimal("1050.00"))

    def test_order_is_overdue(self):
        """Test sales order overdue check."""
        # Set required date to yesterday
        self.order.required_date = timezone.now().date() - timedelta(days=1)
        self.order.status = "confirmed"
        self.assertTrue(self.order.is_overdue)

        # Set required date to tomorrow
        self.order.required_date = timezone.now().date() + timedelta(days=1)
        self.assertFalse(self.order.is_overdue)

        # Completed orders are not overdue
        self.order.status = "completed"
        self.order.required_date = timezone.now().date() - timedelta(days=1)
        self.assertFalse(self.order.is_overdue)

    def test_order_str_representation(self):
        """Test sales order string representation."""
        expected = f"SO2025110001 - {self.customer.name}"
        self.assertEqual(str(self.order), expected)


class SalesOrderItemModelTest(TestCase):
    """Sales order item model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.customer = Customer.objects.create(name="测试客户", code="CUS001", created_by=self.user)

        self.category = ProductCategory.objects.create(
            name="测试分类", code="CAT001", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        self.product = Product.objects.create(
            name="测试产品",
            code="PROD001",
            category=self.category,
            unit=self.unit,
            selling_price=Decimal("100.00"),
            created_by=self.user,
        )

        self.order = SalesOrder.objects.create(
            order_number="SO2025110001",
            customer=self.customer,
            order_date=timezone.now().date(),
            created_by=self.user,
        )

    def test_item_creation(self):
        """Test sales order item creation."""
        item = SalesOrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=10,
            unit_price=Decimal("100.00"),
            created_by=self.user,
        )

        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 10)
        self.assertEqual(item.unit_price, Decimal("100.00"))

    def test_item_line_total_calculation(self):
        """Test sales order item line total calculation."""
        item = SalesOrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=10,
            unit_price=Decimal("100.00"),
            created_by=self.user,
        )

        # Expected: 10 * 100 = 1000
        self.assertEqual(item.line_total, Decimal("1000.00"))

    def test_item_discount_calculation(self):
        """Test sales order item discount calculation."""
        item = SalesOrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=10,
            unit_price=Decimal("100.00"),
            discount_rate=Decimal("10.00"),  # 10% discount
            created_by=self.user,
        )

        # Expected: 10 * 100 * 0.9 = 900
        self.assertEqual(item.discount_amount, Decimal("100.00"))
        self.assertEqual(item.line_total, Decimal("900.00"))


class QuoteModelTest(TestCase):
    """Quote model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.customer = Customer.objects.create(name="测试客户", code="CUS001", created_by=self.user)

        self.quote = Quote.objects.create(
            quote_number="QT2025110001",
            customer=self.customer,
            quote_date=timezone.now().date(),
            valid_until=timezone.now().date() + timedelta(days=30),
            created_by=self.user,
        )

    def test_quote_creation(self):
        """Test quote creation."""
        self.assertEqual(self.quote.quote_number, "QT2025110001")
        self.assertEqual(self.quote.customer, self.customer)
        self.assertEqual(self.quote.status, "draft")

    def test_quote_str_representation(self):
        """Test quote string representation."""
        expected = f"QT2025110001 - {self.customer.name}"
        self.assertEqual(str(self.quote), expected)


class DeliveryModelTest(TestCase):
    """Delivery model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.customer = Customer.objects.create(name="测试客户", code="CUS001", created_by=self.user)

        self.warehouse = Warehouse.objects.create(name="测试仓库", code="WH001", created_by=self.user)

        self.order = SalesOrder.objects.create(
            order_number="SO2025110001",
            customer=self.customer,
            order_date=timezone.now().date(),
            status="confirmed",
            created_by=self.user,
        )

        self.delivery = Delivery.objects.create(
            delivery_number="DN2025110001",
            sales_order=self.order,
            warehouse=self.warehouse,
            planned_date=timezone.now().date(),
            created_by=self.user,
        )

    def test_delivery_creation(self):
        """Test delivery creation."""
        self.assertEqual(self.delivery.delivery_number, "DN2025110001")
        self.assertEqual(self.delivery.sales_order, self.order)
        self.assertEqual(self.delivery.status, "preparing")

    def test_delivery_str_representation(self):
        """Test delivery string representation."""
        expected = f"DN2025110001 - {self.customer.name}"
        self.assertEqual(str(self.delivery), expected)


class SalesReturnModelTest(TestCase):
    """Sales return model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.customer = Customer.objects.create(name="测试客户", code="CUS001", created_by=self.user)

        self.order = SalesOrder.objects.create(
            order_number="SO2025110001",
            customer=self.customer,
            order_date=timezone.now().date(),
            status="completed",
            created_by=self.user,
        )

        self.return_order = SalesReturn.objects.create(
            return_number="SR2025110001",
            sales_order=self.order,
            reason="defective",
            return_date=timezone.now().date(),
            created_by=self.user,
        )

    def test_return_creation(self):
        """Test sales return creation."""
        self.assertEqual(self.return_order.return_number, "SR2025110001")
        self.assertEqual(self.return_order.sales_order, self.order)
        self.assertEqual(self.return_order.status, "pending")
        self.assertEqual(self.return_order.reason, "defective")

    def test_return_str_representation(self):
        """Test sales return string representation."""
        expected = f"SR2025110001 - {self.customer.name}"
        self.assertEqual(str(self.return_order), expected)


class SalesOrderCalculationEdgeCasesTest(TestCase):
    """Test edge cases in sales order calculations."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.customer = Customer.objects.create(name="测试客户", code="CUS001", created_by=self.user)

        self.category = ProductCategory.objects.create(
            name="测试分类", code="CAT001", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        self.product = Product.objects.create(
            name="测试产品",
            code="PROD001",
            category=self.category,
            unit=self.unit,
            selling_price=Decimal("100.00"),
            created_by=self.user,
        )

    def test_empty_order_calculation(self):
        """Test calculation for order without items."""
        order = SalesOrder.objects.create(
            order_number="SO2025110001",
            customer=self.customer,
            order_date=timezone.now().date(),
            created_by=self.user,
        )

        self.assertEqual(order.subtotal, Decimal("0.00"))
        self.assertEqual(order.total_amount, Decimal("0.00"))

    def test_zero_quantity_item(self):
        """Test handling of zero quantity items."""
        order = SalesOrder.objects.create(
            order_number="SO2025110001",
            customer=self.customer,
            order_date=timezone.now().date(),
            created_by=self.user,
        )

        item = SalesOrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=0,
            unit_price=Decimal("100.00"),
            created_by=self.user,
        )

        self.assertEqual(item.line_total, Decimal("0.00"))

    def test_high_precision_calculation(self):
        """Test high precision decimal calculations."""
        order = SalesOrder.objects.create(
            order_number="SO2025110001",
            customer=self.customer,
            order_date=timezone.now().date(),
            tax_rate=Decimal("13.00"),
            created_by=self.user,
        )

        # Create item with fractional quantity
        SalesOrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=Decimal("3.333"),
            unit_price=Decimal("99.99"),
            created_by=self.user,
        )

        order.calculate_totals()
        order.save()

        # Expected: 3.333 * 99.99 = 333.2667 -> 333.27 (rounded to 2 decimals)
        expected_subtotal = Decimal("333.27")
        self.assertAlmostEqual(float(order.subtotal), float(expected_subtotal), places=2)

    def test_multiple_discounts(self):
        """Test calculation with both line and order discounts."""
        order = SalesOrder.objects.create(
            order_number="SO2025110001",
            customer=self.customer,
            order_date=timezone.now().date(),
            discount_rate=Decimal("10.00"),  # Order level 10% discount
            created_by=self.user,
        )

        # Add item with 5% line discount
        SalesOrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=10,
            unit_price=Decimal("100.00"),
            discount_rate=Decimal("5.00"),  # Line level 5% discount
            created_by=self.user,
        )

        # Calculate and refresh order to get calculated values
        order.calculate_totals()
        order.save()
        order.refresh_from_db()

        # Line total after line discount: 1000 * 0.95 = 950
        # Order total after order discount: 950 * 0.9 = 855
        self.assertEqual(order.subtotal, Decimal("950.00"))
        self.assertEqual(order.total_amount, Decimal("855.00"))
