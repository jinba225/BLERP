"""
Purchase models tests.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.products.models import Product, ProductCategory, Unit
from apps.purchase.models import (
    PurchaseInquiry,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
    PurchaseRequestItem,
)
from apps.suppliers.models import Supplier

User = get_user_model()


class PurchaseOrderModelTest(TestCase):
    """Purchase order model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.supplier = Supplier.objects.create(name="测试供应商", code="SUP001", created_by=self.user)

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

        self.order = PurchaseOrder.objects.create(
            order_number="PO2025110001",
            supplier=self.supplier,
            order_date=timezone.now().date(),
            required_date=timezone.now().date() + timedelta(days=7),
            created_by=self.user,
        )

    def test_order_creation(self):
        """Test purchase order creation."""
        self.assertEqual(self.order.order_number, "PO2025110001")
        self.assertEqual(self.order.supplier, self.supplier)
        self.assertEqual(self.order.status, "draft")

    def test_order_calculate_totals(self):
        """Test purchase order totals calculation."""
        # Add order items
        PurchaseOrderItem.objects.create(
            purchase_order=self.order,
            product=self.product,
            quantity=10,
            unit_price=Decimal("80.00"),
            created_by=self.user,
        )

        self.order.calculate_totals()
        self.order.save()

        # Expected: 10 * 80 = 800
        self.assertEqual(self.order.subtotal, Decimal("800.00"))

    def test_order_str_representation(self):
        """Test purchase order string representation."""
        expected = f"PO2025110001 - {self.supplier.name}"
        self.assertEqual(str(self.order), expected)


class PurchaseInquiryModelTest(TestCase):
    """Purchase inquiry model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.supplier = Supplier.objects.create(name="测试供应商", code="SUP001", created_by=self.user)

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

        self.inquiry = PurchaseInquiry.objects.create(
            inquiry_number="RFQ2025110001",
            inquiry_date=timezone.now().date(),
            required_date=timezone.now().date() + timedelta(days=7),
            created_by=self.user,
        )

    def test_inquiry_creation(self):
        """Test purchase inquiry creation."""
        self.assertEqual(self.inquiry.inquiry_number, "RFQ2025110001")
        self.assertEqual(self.inquiry.status, "draft")

    def test_inquiry_str_representation(self):
        """Test inquiry string representation."""
        # Inquiry __str__ returns inquiry_number - inquiry_date
        expected = f"RFQ2025110001 - {self.inquiry.inquiry_date}"
        self.assertEqual(str(self.inquiry), expected)


class PurchaseRequestModelTest(TestCase):
    """Purchase request model tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser_request",
            email="testuser_request@test.com",
            password="testpass123",
        )

        self.supplier = Supplier.objects.create(
            name="测试供应商", code="SUP002", is_active=True, created_by=self.user
        )

        self.category = ProductCategory.objects.create(
            name="测试分类", code="CAT002", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        self.product = Product.objects.create(
            name="测试产品",
            code="PROD002",
            category=self.category,
            unit=self.unit,
            created_by=self.user,
        )

        self.purchase_request = PurchaseRequest.objects.create(
            request_number="PR2025010001",
            requester=self.user,
            status="draft",
            request_date=timezone.now().date(),
            required_date=timezone.now().date() + timedelta(days=7),
            purpose="测试采购",
            created_by=self.user,
        )

        self.request_item = PurchaseRequestItem.objects.create(
            purchase_request=self.purchase_request,
            product=self.product,
            quantity=Decimal("10.00"),
            estimated_price=Decimal("100.00"),
            created_by=self.user,
        )

    def test_approve_and_convert_to_order_success(self):
        """Test successful approval and conversion to purchase order."""
        # Approve and convert
        order, message = self.purchase_request.approve_and_convert_to_order(
            approved_by_user=self.user, supplier_id=self.supplier.id
        )

        # Check request was approved
        self.purchase_request.refresh_from_db()
        self.assertEqual(self.purchase_request.status, "approved")
        self.assertIsNotNone(self.purchase_request.approved_by)
        self.assertIsNotNone(self.purchase_request.approved_at)
        self.assertEqual(self.purchase_request.converted_order, order)

        # Check order was created
        self.assertIsNotNone(order)
        self.assertEqual(order.supplier, self.supplier)
        self.assertEqual(order.status, "draft")
        self.assertEqual(order.buyer, self.user)

        # Check order items were created
        self.assertEqual(order.items.count(), 1)
        order_item = order.items.first()
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, Decimal("10.00"))
        self.assertEqual(order_item.unit_price, Decimal("100.00"))

        # Check success message
        self.assertIn("已自动生成采购订单", message)
        self.assertIn(order.order_number, message)

    def test_approve_and_convert_already_approved(self):
        """Test approval fails if already approved."""
        # First approval
        self.purchase_request.approve_and_convert_to_order(
            approved_by_user=self.user, supplier_id=self.supplier.id
        )

        # Try to approve again
        with self.assertRaises(ValueError) as context:
            self.purchase_request.approve_and_convert_to_order(
                approved_by_user=self.user, supplier_id=self.supplier.id
            )

        self.assertIn("已经审核过了", str(context.exception))

    def test_approve_and_convert_wrong_status(self):
        """Test approval fails if status is not draft."""
        self.purchase_request.status = "approved"  # 设置为已审核状态
        self.purchase_request.save()

        with self.assertRaises(ValueError) as context:
            self.purchase_request.approve_and_convert_to_order(
                approved_by_user=self.user, supplier_id=self.supplier.id
            )

        self.assertIn("只有草稿状态", str(context.exception))

    def test_approve_and_convert_no_items(self):
        """Test approval fails if request has no items."""
        # Delete items
        self.purchase_request.items.all().delete()

        with self.assertRaises(ValueError) as context:
            self.purchase_request.approve_and_convert_to_order(
                approved_by_user=self.user, supplier_id=self.supplier.id
            )

        self.assertIn("没有明细", str(context.exception))

    def test_approve_without_auto_create_order(self):
        """Test approval without auto-creating order."""
        order, message = self.purchase_request.approve_and_convert_to_order(
            approved_by_user=self.user,
            supplier_id=self.supplier.id,
            auto_create_order=False,
        )

        # Check request was approved but no order created
        self.purchase_request.refresh_from_db()
        self.assertEqual(self.purchase_request.status, "approved")
        self.assertIsNone(order)
        self.assertIsNone(self.purchase_request.converted_order)
        self.assertEqual(message, "采购申请单审核通过")
