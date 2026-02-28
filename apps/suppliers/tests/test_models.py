"""
Suppliers models tests.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.products.models import Product, ProductCategory, Unit
from apps.suppliers.models import (
    Supplier,
    SupplierCategory,
    SupplierContact,
    SupplierEvaluation,
    SupplierProduct,
)

User = get_user_model()


class SupplierCategoryModelTest(TestCase):
    """Test SupplierCategory model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

    def test_category_creation(self):
        """Test supplier category creation."""
        category = SupplierCategory.objects.create(
            name="原材料供应商",
            code="RAW001",
            description="原材料供应商分类",
            created_by=self.user,
        )

        self.assertEqual(category.name, "原材料供应商")
        self.assertEqual(category.code, "RAW001")
        self.assertTrue(category.is_active)

    def test_category_unique_name(self):
        """Test category name uniqueness."""
        SupplierCategory.objects.create(name="原材料供应商", code="RAW001", created_by=self.user)

        # Try to create another category with same name
        with self.assertRaises(Exception):
            SupplierCategory.objects.create(name="原材料供应商", code="RAW002", created_by=self.user)

    def test_category_unique_code(self):
        """Test category code uniqueness."""
        SupplierCategory.objects.create(name="原材料供应商", code="RAW001", created_by=self.user)

        # Try to create another category with same code
        with self.assertRaises(Exception):
            SupplierCategory.objects.create(name="其他供应商", code="RAW001", created_by=self.user)

    def test_category_str_representation(self):
        """Test category string representation."""
        category = SupplierCategory.objects.create(
            name="原材料供应商", code="RAW001", created_by=self.user
        )

        self.assertEqual(str(category), "原材料供应商")


class SupplierModelTest(TestCase):
    """Test Supplier model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.buyer = User.objects.create_user(
            username="buyer", email="buyer@test.com", password="testpass123"
        )

        self.category = SupplierCategory.objects.create(
            name="原材料供应商", code="RAW001", created_by=self.user
        )

    def test_supplier_creation(self):
        """Test supplier creation."""
        supplier = Supplier.objects.create(
            name="测试供应商",
            code="SUP001",
            category=self.category,
            level="A",
            address="北京市海淀区",
            city="北京",
            province="北京",
            buyer=self.buyer,
            lead_time=15,
            min_order_amount=Decimal("5000.00"),
            quality_rating=Decimal("9.0"),
            delivery_rating=Decimal("8.5"),
            service_rating=Decimal("9.5"),
            created_by=self.user,
        )

        self.assertEqual(supplier.name, "测试供应商")
        self.assertEqual(supplier.code, "SUP001")
        self.assertEqual(supplier.level, "A")
        self.assertEqual(supplier.buyer, self.buyer)
        self.assertTrue(supplier.is_active)

    def test_supplier_unique_code(self):
        """Test supplier code uniqueness."""
        Supplier.objects.create(name="供应商A", code="SUP001", created_by=self.user)

        # Try to create another supplier with same code
        with self.assertRaises(Exception):
            Supplier.objects.create(name="供应商B", code="SUP001", created_by=self.user)

    def test_supplier_levels(self):
        """Test all supplier levels."""
        levels = ["A", "B", "C", "D"]

        for level in levels:
            supplier = Supplier.objects.create(
                name=f"测试供应商-{level}级",
                code=f"SUP{level}",
                level=level,
                created_by=self.user,
            )
            self.assertEqual(supplier.level, level)

    def test_average_rating_property(self):
        """Test average rating calculation."""
        # All ratings present
        supplier1 = Supplier.objects.create(
            name="供应商1",
            code="SUP001",
            quality_rating=Decimal("9.0"),
            delivery_rating=Decimal("8.0"),
            service_rating=Decimal("7.0"),
            created_by=self.user,
        )
        expected = (Decimal("9.0") + Decimal("8.0") + Decimal("7.0")) / 3
        self.assertEqual(supplier1.average_rating, expected)

        # Some ratings zero (should be excluded)
        supplier2 = Supplier.objects.create(
            name="供应商2",
            code="SUP002",
            quality_rating=Decimal("9.0"),
            delivery_rating=Decimal("0"),
            service_rating=Decimal("8.0"),
            created_by=self.user,
        )
        expected = (Decimal("9.0") + Decimal("8.0")) / 2
        self.assertEqual(supplier2.average_rating, expected)

        # All ratings zero
        supplier3 = Supplier.objects.create(
            name="供应商3",
            code="SUP003",
            quality_rating=Decimal("0"),
            delivery_rating=Decimal("0"),
            service_rating=Decimal("0"),
            created_by=self.user,
        )
        self.assertEqual(supplier3.average_rating, 0)

    def test_supplier_str_representation(self):
        """Test supplier string representation."""
        supplier = Supplier.objects.create(name="测试供应商", code="SUP001", created_by=self.user)

        expected = "SUP001 - 测试供应商"
        self.assertEqual(str(supplier), expected)


class SupplierContactModelTest(TestCase):
    """Test SupplierContact model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.supplier = Supplier.objects.create(name="测试供应商", code="SUP001", created_by=self.user)

    def test_contact_creation(self):
        """Test supplier contact creation."""
        contact = SupplierContact.objects.create(
            supplier=self.supplier,
            name="李四",
            position="销售经理",
            contact_type="sales",
            phone="010-87654321",
            mobile="13900139000",
            email="lisi@supplier.com",
            qq="12345678",
            wechat="lisi_wechat",
            is_primary=True,
            created_by=self.user,
        )

        self.assertEqual(contact.supplier, self.supplier)
        self.assertEqual(contact.name, "李四")
        self.assertEqual(contact.contact_type, "sales")
        self.assertTrue(contact.is_primary)
        self.assertTrue(contact.is_active)

    def test_contact_types(self):
        """Test all contact types."""
        types = ["primary", "finance", "technical", "sales", "other"]

        for i, contact_type in enumerate(types):
            contact = SupplierContact.objects.create(
                supplier=self.supplier,
                name=f"联系人{i}",
                contact_type=contact_type,
                created_by=self.user,
            )
            self.assertEqual(contact.contact_type, contact_type)

    def test_multiple_contacts(self):
        """Test multiple contacts for one supplier."""
        contact1 = SupplierContact.objects.create(
            supplier=self.supplier,
            name="张三",
            contact_type="primary",
            is_primary=True,
            created_by=self.user,
        )

        contact2 = SupplierContact.objects.create(
            supplier=self.supplier,
            name="李四",
            contact_type="finance",
            is_primary=False,
            created_by=self.user,
        )

        contacts = self.supplier.contacts.all()
        self.assertEqual(contacts.count(), 2)
        self.assertIn(contact1, contacts)
        self.assertIn(contact2, contacts)

    def test_contact_str_representation(self):
        """Test contact string representation."""
        contact = SupplierContact.objects.create(
            supplier=self.supplier, name="李四", created_by=self.user
        )

        expected = "测试供应商 - 李四"
        self.assertEqual(str(contact), expected)


class SupplierProductModelTest(TestCase):
    """Test SupplierProduct model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.supplier = Supplier.objects.create(name="测试供应商", code="SUP001", created_by=self.user)

        # Create product dependencies
        self.category = ProductCategory.objects.create(
            name="测试分类", code="CAT001", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        self.product = Product.objects.create(
            name="测试产品",
            code="PROD001",
            category=self.category,
            unit=self.unit,
            created_by=self.user,
        )

    def test_supplier_product_creation(self):
        """Test supplier product creation."""
        supplier_product = SupplierProduct.objects.create(
            supplier=self.supplier,
            product=self.product,
            supplier_product_code="SP001",
            supplier_product_name="供应商产品名称",
            price=Decimal("100.00"),
            currency="CNY",
            min_order_qty=Decimal("10.00"),
            lead_time=7,
            is_preferred=True,
            created_by=self.user,
        )

        self.assertEqual(supplier_product.supplier, self.supplier)
        self.assertEqual(supplier_product.product, self.product)
        self.assertEqual(supplier_product.price, Decimal("100.00"))
        self.assertTrue(supplier_product.is_preferred)
        self.assertTrue(supplier_product.is_active)

    def test_supplier_product_unique_together(self):
        """Test unique_together constraint for supplier and product."""
        # Create first supplier-product relationship
        SupplierProduct.objects.create(
            supplier=self.supplier,
            product=self.product,
            price=Decimal("100.00"),
            created_by=self.user,
        )

        # Try to create duplicate supplier-product relationship
        with self.assertRaises(Exception):
            SupplierProduct.objects.create(
                supplier=self.supplier,
                product=self.product,
                price=Decimal("90.00"),
                created_by=self.user,
            )

    def test_multiple_suppliers_same_product(self):
        """Test multiple suppliers can supply the same product."""
        supplier2 = Supplier.objects.create(name="供应商B", code="SUP002", created_by=self.user)

        sp1 = SupplierProduct.objects.create(
            supplier=self.supplier,
            product=self.product,
            price=Decimal("100.00"),
            created_by=self.user,
        )

        sp2 = SupplierProduct.objects.create(
            supplier=supplier2,
            product=self.product,
            price=Decimal("95.00"),
            created_by=self.user,
        )

        self.assertEqual(sp1.product, sp2.product)
        self.assertNotEqual(sp1.supplier, sp2.supplier)

    def test_supplier_product_str_representation(self):
        """Test supplier product string representation."""
        supplier_product = SupplierProduct.objects.create(
            supplier=self.supplier,
            product=self.product,
            price=Decimal("100.00"),
            created_by=self.user,
        )

        expected = "测试供应商 - 测试产品"
        self.assertEqual(str(supplier_product), expected)


class SupplierEvaluationModelTest(TestCase):
    """Test SupplierEvaluation model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.evaluator = User.objects.create_user(
            username="evaluator", email="evaluator@test.com", password="testpass123"
        )

        self.supplier = Supplier.objects.create(name="测试供应商", code="SUP001", created_by=self.user)

    def test_evaluation_creation(self):
        """Test supplier evaluation creation."""
        evaluation = SupplierEvaluation.objects.create(
            supplier=self.supplier,
            evaluation_period="quarterly",
            year=2025,
            quarter=1,
            quality_score=Decimal("90.00"),
            delivery_score=Decimal("85.00"),
            service_score=Decimal("88.00"),
            price_score=Decimal("92.00"),
            strengths="质量稳定",
            weaknesses="交货周期偏长",
            recommendations="改进物流",
            evaluator=self.evaluator,
            created_by=self.user,
        )

        self.assertEqual(evaluation.supplier, self.supplier)
        self.assertEqual(evaluation.evaluation_period, "quarterly")
        self.assertEqual(evaluation.year, 2025)
        self.assertEqual(evaluation.quarter, 1)
        self.assertEqual(evaluation.evaluator, self.evaluator)

    def test_evaluation_periods(self):
        """Test all evaluation periods."""
        periods = ["monthly", "quarterly", "annual"]

        for period in periods:
            year = 2025
            kwargs = {
                "supplier": self.supplier,
                "evaluation_period": period,
                "year": year,
                "quality_score": Decimal("90.00"),
                "delivery_score": Decimal("85.00"),
                "service_score": Decimal("88.00"),
                "price_score": Decimal("92.00"),
                "created_by": self.user,
            }

            if period == "monthly":
                kwargs["month"] = 1
            elif period == "quarterly":
                kwargs["quarter"] = 1

            evaluation = SupplierEvaluation.objects.create(**kwargs)
            self.assertEqual(evaluation.evaluation_period, period)

    def test_overall_score_auto_calculation(self):
        """Test overall score automatic calculation on save."""
        evaluation = SupplierEvaluation.objects.create(
            supplier=self.supplier,
            evaluation_period="quarterly",
            year=2025,
            quarter=1,
            quality_score=Decimal("80.00"),
            delivery_score=Decimal("90.00"),
            service_score=Decimal("70.00"),
            price_score=Decimal("85.00"),
            created_by=self.user,
        )

        # Expected: 80*0.3 + 90*0.3 + 70*0.2 + 85*0.2
        # = 24 + 27 + 14 + 17 = 82.0
        expected_score = Decimal("82.0")
        self.assertEqual(evaluation.overall_score, expected_score)

    def test_overall_score_update_on_modification(self):
        """Test overall score recalculated when scores change."""
        evaluation = SupplierEvaluation.objects.create(
            supplier=self.supplier,
            evaluation_period="quarterly",
            year=2025,
            quarter=1,
            quality_score=Decimal("80.00"),
            delivery_score=Decimal("80.00"),
            service_score=Decimal("80.00"),
            price_score=Decimal("80.00"),
            created_by=self.user,
        )

        # Initial overall score should be 80.0
        self.assertEqual(evaluation.overall_score, Decimal("80.0"))

        # Update scores
        evaluation.quality_score = Decimal("90.00")
        evaluation.delivery_score = Decimal("85.00")
        evaluation.save()

        # Expected: 90*0.3 + 85*0.3 + 80*0.2 + 80*0.2
        # = 27 + 25.5 + 16 + 16 = 84.5
        expected_score = Decimal("84.5")
        self.assertEqual(evaluation.overall_score, expected_score)

    def test_different_period_same_supplier(self):
        """Test different evaluation periods for same supplier."""
        eval1 = SupplierEvaluation.objects.create(
            supplier=self.supplier,
            evaluation_period="quarterly",
            year=2025,
            quarter=1,
            quality_score=Decimal("90.00"),
            delivery_score=Decimal("85.00"),
            service_score=Decimal("88.00"),
            price_score=Decimal("92.00"),
            created_by=self.user,
        )

        eval2 = SupplierEvaluation.objects.create(
            supplier=self.supplier,
            evaluation_period="quarterly",
            year=2025,
            quarter=2,
            quality_score=Decimal("92.00"),
            delivery_score=Decimal("88.00"),
            service_score=Decimal("90.00"),
            price_score=Decimal("85.00"),
            created_by=self.user,
        )

        evaluations = self.supplier.evaluations.all()
        self.assertEqual(evaluations.count(), 2)
        self.assertIn(eval1, evaluations)
        self.assertIn(eval2, evaluations)

    def test_evaluation_str_representation(self):
        """Test evaluation string representation."""
        evaluation = SupplierEvaluation.objects.create(
            supplier=self.supplier,
            evaluation_period="quarterly",
            year=2025,
            quarter=1,
            quality_score=Decimal("90.00"),
            delivery_score=Decimal("85.00"),
            service_score=Decimal("88.00"),
            price_score=Decimal("92.00"),
            created_by=self.user,
        )

        expected = "测试供应商 - 季度评估 - 2025"
        self.assertEqual(str(evaluation), expected)
