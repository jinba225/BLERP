"""
Sales business logic tests.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import timedelta

from apps.sales.models import (
    SalesOrder, SalesOrderItem,
    Quote, QuoteItem,
    Delivery, DeliveryItem,
    SalesReturn, SalesReturnItem
)
from apps.customers.models import Customer
from apps.products.models import Product, ProductCategory, Unit
from apps.inventory.models import Warehouse, InventoryStock, InventoryTransaction
from apps.finance.models import CustomerAccount

User = get_user_model()


class QuoteToOrderConversionTest(TestCase):
    """Test quote to order conversion logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser', email='testuser@test.com',
            password='testpass123'
        )

        self.customer = Customer.objects.create(
            name='测试客户',
            code='CUS001',
            created_by=self.user
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
            selling_price=Decimal('100.00'),
            created_by=self.user
        )

        # Create quote
        self.quote = Quote.objects.create(
            quote_number='QT2025110001',
            customer=self.customer,
            quote_date=timezone.now().date(),
            valid_until=timezone.now().date() + timedelta(days=30),
            tax_rate=Decimal('13.00'),
            created_by=self.user
        )

        # Add quote item
        QuoteItem.objects.create(
            quote=self.quote,
            product=self.product,
            quantity=10,
            unit_price=Decimal('100.00'),
            line_total=Decimal('1000.00'),
            created_by=self.user
        )
        
        # Ensure quote totals are calculated
        self.quote.calculate_totals()
        self.quote.save()

    def test_quote_to_order_conversion(self):
        """Test converting quote to order."""
        # Convert quote to order
        order = self.quote.convert_to_order()

        # Verify order creation
        self.assertIsNotNone(order)
        self.assertIsInstance(order, SalesOrder)
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.total_amount, self.quote.total_amount)

        # Verify quote status updated
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, 'converted')
        self.assertEqual(self.quote.converted_order, order)

        # Verify items copied
        self.assertEqual(order.items.count(), 1)
        order_item = order.items.first()
        quote_item = self.quote.items.first()
        self.assertEqual(order_item.product, quote_item.product)
        self.assertEqual(order_item.quantity, quote_item.quantity)
        self.assertEqual(order_item.unit_price, quote_item.unit_price)

    def test_quote_cannot_be_converted_twice(self):
        """Test that a quote cannot be converted twice."""
        # First conversion
        order1 = self.quote.convert_to_order()

        # Second conversion should return the same order
        order2 = self.quote.convert_to_order()

        self.assertEqual(order1.pk, order2.pk)

    def test_empty_quote_conversion(self):
        """Test converting an empty quote."""
        empty_quote = Quote.objects.create(
            quote_number='QT2025110002',
            customer=self.customer,
            quote_date=timezone.now().date(),
            valid_until=timezone.now().date() + timedelta(days=30),
            created_by=self.user
        )

        order = empty_quote.convert_to_order()

        # Should create order even if empty
        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 0)


class OrderApprovalTest(TestCase):
    """Test sales order approval logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser', email='testuser@test.com',
            password='testpass123'
        )

        self.approver = User.objects.create_user(
            username='approver', email='approver@test.com',
            password='testpass123'
        )

        self.customer = Customer.objects.create(
            name='测试客户',
            code='CUS001',
            created_by=self.user
        )

        self.warehouse = Warehouse.objects.create(
            name='测试仓库',
            code='WH001',
            is_active=True,
            created_by=self.user
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
            selling_price=Decimal('100.00'),
            created_by=self.user
        )

        # Create sales order
        self.order = SalesOrder.objects.create(
            order_number='SO2025110001',
            customer=self.customer,
            order_date=timezone.now().date(),
            payment_terms='net_30',
            created_by=self.user,
        )

        # Add order item
        SalesOrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=10,
            unit_price=Decimal('100.00'),
            created_by=self.user
        )

        self.order.calculate_totals()
        self.order.save()

    def test_order_approval_with_delivery(self):
        """Test order approval with automatic delivery creation."""
        # Approve order with delivery creation
        delivery, customer_account = self.order.approve_order(
            approved_by_user=self.approver,
            warehouse=self.warehouse,
            auto_create_delivery=True
        )

        # Verify order status updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmed')
        self.assertEqual(self.order.approved_by, self.approver)
        self.assertIsNotNone(self.order.approved_at)

        # Verify delivery created
        self.assertIsNotNone(delivery)
        self.assertEqual(delivery.sales_order, self.order)
        self.assertEqual(delivery.warehouse, self.warehouse)
        self.assertEqual(delivery.items.count(), 1)

        # Verify customer account created
        self.assertIsNotNone(customer_account)
        self.assertEqual(customer_account.customer, self.customer)
        self.assertEqual(customer_account.sales_order, self.order)
        self.assertEqual(customer_account.balance, self.order.total_amount)

    def test_order_approval_without_delivery(self):
        """Test order approval without delivery creation."""
        # Approve order without delivery
        delivery, customer_account = self.order.approve_order(
            approved_by_user=self.approver,
            auto_create_delivery=False
        )

        # Verify order approved
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmed')

        # Verify no delivery created
        self.assertIsNone(delivery)

        # Verify customer account created
        self.assertIsNotNone(customer_account)

    def test_cannot_approve_without_items(self):
        """Test that orders without items cannot be approved."""
        # Create empty order
        empty_order = SalesOrder.objects.create(
            order_number='SO2025110002',
            customer=self.customer,
            order_date=timezone.now().date(),
            created_by=self.user,
        )

        # Try to approve
        with self.assertRaises(ValueError) as context:
            empty_order.approve_order(approved_by_user=self.approver)

        self.assertIn('没有明细', str(context.exception))

    def test_cannot_approve_twice(self):
        """Test that orders cannot be approved twice."""
        # First approval
        self.order.approve_order(
            approved_by_user=self.approver,
            auto_create_delivery=False
        )

        # Second approval should fail
        with self.assertRaises(ValueError) as context:
            self.order.approve_order(
                approved_by_user=self.approver,
                auto_create_delivery=False
            )

        self.assertIn('已经审核过了', str(context.exception))

    def test_payment_terms_due_date_calculation(self):
        """Test due date calculation based on payment terms."""
        # Test net_30
        order_net30 = SalesOrder.objects.create(
            order_number='SO2025110003',
            customer=self.customer,
            order_date=timezone.now().date(),
            payment_terms='net_30',
            created_by=self.user,
        )
        SalesOrderItem.objects.create(
            order=order_net30,
            product=self.product,
            quantity=5,
            unit_price=Decimal('100.00'),
            created_by=self.user
        )
        order_net30.calculate_totals()
        order_net30.save()

        delivery, account = order_net30.approve_order(
            approved_by_user=self.approver,
            auto_create_delivery=False
        )

        expected_due_date = timezone.now().date() + timedelta(days=30)
        self.assertEqual(account.due_date, expected_due_date)


class OrderUnapprovalTest(TestCase):
    """Test sales order unapproval logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser', email='testuser@test.com',
            password='testpass123'
        )

        self.approver = User.objects.create_user(
            username='approver', email='approver@test.com',
            password='testpass123'
        )

        self.customer = Customer.objects.create(
            name='测试客户',
            code='CUS001',
            created_by=self.user
        )

        self.warehouse = Warehouse.objects.create(
            name='测试仓库',
            code='WH001',
            is_active=True,
            created_by=self.user
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
            selling_price=Decimal('100.00'),
            created_by=self.user
        )

        # Create and approve order
        self.order = SalesOrder.objects.create(
            order_number='SO2025110001',
            customer=self.customer,
            order_date=timezone.now().date(),
            created_by=self.user,
        )

        SalesOrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=10,
            unit_price=Decimal('100.00'),
            created_by=self.user
        )

        self.order.calculate_totals()
        self.order.save()

        # Approve with delivery
        self.delivery, self.customer_account = self.order.approve_order(
            approved_by_user=self.approver,
            warehouse=self.warehouse,
            auto_create_delivery=True
        )

    def test_unapprove_order(self):
        """Test unapproving an order."""
        # Unapprove order
        self.order.unapprove_order()

        # Verify order status reset
        self.order.refresh_from_db()
        self.assertIsNone(self.order.approved_by)
        self.assertIsNone(self.order.approved_at)
        self.assertEqual(self.order.status, 'draft')

        # Verify delivery soft deleted
        self.delivery.refresh_from_db()
        self.assertTrue(self.delivery.is_deleted)

        # Verify customer account deleted
        self.assertEqual(
            CustomerAccount.objects.filter(pk=self.customer_account.pk).count(),
            0
        )

    def test_cannot_unapprove_unapproved_order(self):
        """Test that unapproved orders cannot be unapproved."""
        # Create new order (not approved)
        new_order = SalesOrder.objects.create(
            order_number='SO2025110002',
            customer=self.customer,
            order_date=timezone.now().date(),
            created_by=self.user,
        )

        # Try to unapprove
        with self.assertRaises(ValueError) as context:
            new_order.unapprove_order()

        self.assertIn('未审核', str(context.exception))

    def test_cannot_unapprove_shipped_order(self):
        """Test that shipped orders cannot be unapproved."""
        # Mark order as shipped
        self.order.status = 'shipped'
        self.order.save()

        # Try to unapprove
        with self.assertRaises(ValueError) as context:
            self.order.unapprove_order()

        self.assertIn('无法撤销审核', str(context.exception))


class DeliveryProcessTest(TestCase):
    """Test delivery process logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser', email='testuser@test.com',
            password='testpass123'
        )

        self.customer = Customer.objects.create(
            name='测试客户',
            code='CUS001',
            created_by=self.user
        )

        self.warehouse = Warehouse.objects.create(
            name='测试仓库',
            code='WH001',
            is_active=True,
            created_by=self.user
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
            selling_price=Decimal('100.00'),
            created_by=self.user
        )

        # Create inventory stock
        InventoryStock.objects.create(
            warehouse=self.warehouse,
            product=self.product,
            quantity=100,
            created_by=self.user
        )

        # Create order
        self.order = SalesOrder.objects.create(
            order_number='SO2025110001',
            customer=self.customer,
            order_date=timezone.now().date(),
            status='confirmed',
            created_by=self.user,
        )

        SalesOrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=10,
            unit_price=Decimal('100.00'),
            created_by=self.user
        )

        # Create delivery
        self.delivery = Delivery.objects.create(
            delivery_number='DN2025110001',
            sales_order=self.order,
            warehouse=self.warehouse,
            planned_date=timezone.now().date(),
            shipping_address='测试地址',
            created_by=self.user
        )

        self.delivery_item = DeliveryItem.objects.create(
            delivery=self.delivery,
            order_item=self.order.items.first(),
            quantity=10,
            created_by=self.user
        )

    def test_delivery_item_creation(self):
        """Test delivery item creation."""
        self.assertEqual(self.delivery.items.count(), 1)
        self.assertEqual(self.delivery_item.quantity, 10)
        self.assertEqual(self.delivery_item.order_item.product, self.product)


class SalesReturnProcessTest(TestCase):
    """Test sales return process logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser', email='testuser@test.com',
            password='testpass123'
        )

        self.approver = User.objects.create_user(
            username='approver', email='approver@test.com',
            password='testpass123'
        )

        self.customer = Customer.objects.create(
            name='测试客户',
            code='CUS001',
            created_by=self.user
        )

        self.warehouse = Warehouse.objects.create(
            name='测试仓库',
            code='WH001',
            created_by=self.user
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
            selling_price=Decimal('100.00'),
            created_by=self.user
        )

        # Create completed order
        self.order = SalesOrder.objects.create(
            order_number='SO2025110001',
            customer=self.customer,
            order_date=timezone.now().date(),
            status='completed',
            created_by=self.user,
        )

        self.order_item = SalesOrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=10,
            unit_price=Decimal('100.00'),
            delivered_quantity=10,
            created_by=self.user
        )

    def test_return_creation(self):
        """Test sales return creation."""
        sales_return = SalesReturn.objects.create(
            return_number='SR2025110001',
            sales_order=self.order,
            reason='defective',
            return_date=timezone.now().date(),
            created_by=self.user
        )

        # Add return item
        return_item = SalesReturnItem.objects.create(
            return_order=sales_return,
            order_item=self.order_item,
            quantity=5,
            unit_price=Decimal('100.00'),
            created_by=self.user
        )

        self.assertEqual(sales_return.status, 'pending')
        self.assertEqual(sales_return.items.count(), 1)
        self.assertEqual(return_item.quantity, 5)

    def test_partial_return(self):
        """Test partial product return."""
        sales_return = SalesReturn.objects.create(
            return_number='SR2025110001',
            sales_order=self.order,
            reason='defective',
            return_date=timezone.now().date(),
            created_by=self.user
        )

        # Return only 5 out of 10
        SalesReturnItem.objects.create(
            return_order=sales_return,
            order_item=self.order_item,
            quantity=5,
            unit_price=Decimal('100.00'),
            created_by=self.user
        )

        # Verify partial return
        self.assertEqual(sales_return.items.first().quantity, 5)
        # Original order item still has 10
        self.assertEqual(self.order_item.quantity, 10)


class IntegrationTest(TestCase):
    """Integration tests for complete business flows."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser', email='testuser@test.com',
            password='testpass123'
        )

        self.customer = Customer.objects.create(
            name='测试客户',
            code='CUS001',
            created_by=self.user
        )

        self.warehouse = Warehouse.objects.create(
            name='测试仓库',
            code='WH001',
            is_active=True,
            created_by=self.user
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
            selling_price=Decimal('100.00'),
            created_by=self.user
        )

    def test_complete_sales_flow(self):
        """Test complete sales flow from quote to order."""
        # 1. Create quote
        quote = Quote.objects.create(
            quote_number='QT2025110001',
            customer=self.customer,
            quote_date=timezone.now().date(),
            valid_until=timezone.now().date() + timedelta(days=30),
            created_by=self.user
        )

        QuoteItem.objects.create(
            quote=quote,
            product=self.product,
            quantity=10,
            unit_price=Decimal('100.00'),
            created_by=self.user
        )

        # 2. Convert to order
        order = quote.convert_to_order()
        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 1)

        # 3. Approve order
        delivery, customer_account = order.approve_order(
            approved_by_user=self.user,
            warehouse=self.warehouse,
            auto_create_delivery=True
        )

        # Verify complete flow
        self.assertEqual(quote.status, 'converted')
        self.assertEqual(order.status, 'confirmed')
        self.assertIsNotNone(delivery)
        self.assertIsNotNone(customer_account)
