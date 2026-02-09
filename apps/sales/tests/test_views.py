"""
Sales views tests.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.customers.models import Customer
from apps.products.models import Product, ProductCategory, Unit
from apps.sales.models import Quote, QuoteItem, SalesOrder, SalesOrderItem

User = get_user_model()


class SalesOrderListViewTest(TestCase):
    """Test sales order list view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )
        self.client.login(username="testuser", email="testuser@test.com", password="testpass123")

        self.customer = Customer.objects.create(name="测试客户", code="CUS001", created_by=self.user)

        # Create test orders
        for i in range(3):
            SalesOrder.objects.create(
                order_number=f"SO202511000{i+1}",
                customer=self.customer,
                order_date=timezone.now().date(),
                created_by=self.user,
            )

    def test_order_list_view_loads(self):
        """Test that order list view loads successfully."""
        response = self.client.get(reverse("sales:order_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "销售订单")

    def test_order_list_shows_orders(self):
        """Test that order list displays orders."""
        response = self.client.get(reverse("sales:order_list"))
        self.assertEqual(response.status_code, 200)
        # Should show all 3 orders
        self.assertContains(response, "SO2025110001")
        self.assertContains(response, "SO2025110002")
        self.assertContains(response, "SO2025110003")

    def test_order_list_requires_login(self):
        """Test that order list requires authentication."""
        self.client.logout()
        response = self.client.get(reverse("sales:order_list"))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)


class SalesOrderDetailViewTest(TestCase):
    """Test sales order detail view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )
        self.client.login(username="testuser", email="testuser@test.com", password="testpass123")

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

        SalesOrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=10,
            unit_price=Decimal("100.00"),
            created_by=self.user,
        )

    def test_order_detail_view_loads(self):
        """Test that order detail view loads successfully."""
        response = self.client.get(reverse("sales:order_detail", kwargs={"pk": self.order.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.order.order_number)
        self.assertContains(response, self.customer.name)

    def test_order_detail_shows_items(self):
        """Test that order detail displays order items."""
        response = self.client.get(reverse("sales:order_detail", kwargs={"pk": self.order.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_order_detail_404_for_nonexistent(self):
        """Test that nonexistent order returns 404."""
        response = self.client.get(reverse("sales:order_detail", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, 404)


class QuoteListViewTest(TestCase):
    """Test quote list view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )
        self.client.login(username="testuser", email="testuser@test.com", password="testpass123")

        self.customer = Customer.objects.create(name="测试客户", code="CUS001", created_by=self.user)

        # Create test quotes
        for i in range(2):
            Quote.objects.create(
                quote_number=f"QT202511000{i+1}",
                customer=self.customer,
                quote_date=timezone.now().date(),
                valid_until=timezone.now().date(),
                created_by=self.user,
            )

    def test_quote_list_view_loads(self):
        """Test that quote list view loads successfully."""
        response = self.client.get(reverse("sales:quote_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "报价单")

    def test_quote_list_shows_quotes(self):
        """Test that quote list displays quotes."""
        response = self.client.get(reverse("sales:quote_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "QT2025110001")
        self.assertContains(response, "QT2025110002")


class QuoteDetailViewTest(TestCase):
    """Test quote detail view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )
        self.client.login(username="testuser", email="testuser@test.com", password="testpass123")

        self.customer = Customer.objects.create(name="测试客户", code="CUS001", created_by=self.user)

        self.quote = Quote.objects.create(
            quote_number="QT2025110001",
            customer=self.customer,
            quote_date=timezone.now().date(),
            valid_until=timezone.now().date(),
            created_by=self.user,
        )

    def test_quote_detail_view_loads(self):
        """Test that quote detail view loads successfully."""
        response = self.client.get(reverse("sales:quote_detail", kwargs={"pk": self.quote.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.quote.quote_number)


class SearchFilterTest(TestCase):
    """Test search and filter functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )
        self.client.login(username="testuser", email="testuser@test.com", password="testpass123")

        self.customer1 = Customer.objects.create(name="客户A", code="CUSA", created_by=self.user)

        self.customer2 = Customer.objects.create(name="客户B", code="CUSB", created_by=self.user)

        # Create orders for different customers
        SalesOrder.objects.create(
            order_number="SO2025110001",
            customer=self.customer1,
            order_date=timezone.now().date(),
            status="draft",
            created_by=self.user,
        )

        SalesOrder.objects.create(
            order_number="SO2025110002",
            customer=self.customer2,
            order_date=timezone.now().date(),
            status="confirmed",
            created_by=self.user,
        )

    def test_search_by_order_number(self):
        """Test search by order number."""
        response = self.client.get(reverse("sales:order_list") + "?search=SO2025110001")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SO2025110001")
        # Should not contain other order
        self.assertNotContains(response, "SO2025110002")

    def test_filter_by_status(self):
        """Test filter by order status."""
        response = self.client.get(reverse("sales:order_list") + "?status=draft")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SO2025110001")
        # Confirmed order should not appear
        self.assertNotContains(response, "SO2025110002")
