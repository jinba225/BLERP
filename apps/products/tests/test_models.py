"""
Products models tests.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.products.models import Brand, Product, ProductCategory, Unit

User = get_user_model()


class ProductCategoryModelTest(TestCase):
    """Test ProductCategory model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

    def test_category_creation(self):
        """Test product category creation."""
        category = ProductCategory.objects.create(name="电子产品", code="ELEC001", created_by=self.user)

        self.assertEqual(category.name, "电子产品")
        self.assertEqual(category.code, "ELEC001")
        self.assertTrue(category.is_active)

    def test_category_hierarchy(self):
        """Test category hierarchy."""
        parent = ProductCategory.objects.create(name="电子产品", code="ELEC001", created_by=self.user)

        child = ProductCategory.objects.create(
            name="计算机", code="COMP001", parent=parent, created_by=self.user
        )

        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())

    def test_category_full_name(self):
        """Test category full name path."""
        parent = ProductCategory.objects.create(name="电子产品", code="ELEC001", created_by=self.user)

        child = ProductCategory.objects.create(
            name="计算机", code="COMP001", parent=parent, created_by=self.user
        )

        grandchild = ProductCategory.objects.create(
            name="笔记本电脑", code="LAPTOP001", parent=child, created_by=self.user
        )

        expected = "电子产品 > 计算机 > 笔记本电脑"
        self.assertEqual(grandchild.full_name, expected)

    def test_category_str_representation(self):
        """Test category string representation."""
        category = ProductCategory.objects.create(name="电子产品", code="ELEC001", created_by=self.user)

        self.assertEqual(str(category), "电子产品")


class BrandModelTest(TestCase):
    """Test Brand model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

    def test_brand_creation(self):
        """Test brand creation."""
        brand = Brand.objects.create(name="Apple", code="APPLE", country="美国", created_by=self.user)

        self.assertEqual(brand.name, "Apple")
        self.assertEqual(brand.code, "APPLE")
        self.assertEqual(brand.country, "美国")
        self.assertTrue(brand.is_active)

    def test_brand_unique_name(self):
        """Test brand name uniqueness."""
        Brand.objects.create(name="Apple", code="APPLE001", created_by=self.user)

        # Try to create another brand with same name
        with self.assertRaises(Exception):
            Brand.objects.create(name="Apple", code="APPLE002", created_by=self.user)

    def test_brand_str_representation(self):
        """Test brand string representation."""
        brand = Brand.objects.create(name="Apple", code="APPLE", created_by=self.user)

        self.assertEqual(str(brand), "Apple")


class UnitModelTest(TestCase):
    """Test Unit model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

    def test_unit_creation(self):
        """Test unit creation."""
        unit = Unit.objects.create(name="件", symbol="pcs", unit_type="count", created_by=self.user)

        self.assertEqual(unit.name, "件")
        self.assertEqual(unit.symbol, "pcs")
        self.assertEqual(unit.unit_type, "count")
        self.assertTrue(unit.is_active)

    def test_unit_unique_name(self):
        """Test unit name uniqueness."""
        Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        # Try to create another unit with same name
        with self.assertRaises(Exception):
            Unit.objects.create(name="件", symbol="piece", created_by=self.user)

    def test_unit_unique_symbol(self):
        """Test unit symbol uniqueness."""
        Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        # Try to create another unit with same symbol
        with self.assertRaises(Exception):
            Unit.objects.create(name="个", symbol="pcs", created_by=self.user)

    def test_unit_str_representation(self):
        """Test unit string representation."""
        unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

        expected = "件 (pcs)"
        self.assertEqual(str(unit), expected)


class ProductModelTest(TestCase):
    """Test Product model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.category = ProductCategory.objects.create(
            name="电子产品", code="ELEC001", created_by=self.user
        )

        self.brand = Brand.objects.create(name="Apple", code="APPLE", created_by=self.user)

        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

    def test_product_creation(self):
        """Test product creation."""
        product = Product.objects.create(
            name="iPhone 15 Pro",
            code="IP15PRO",
            category=self.category,
            brand=self.brand,
            unit=self.unit,
            product_type="finished",
            cost_price=Decimal("5000.00"),
            selling_price=Decimal("7999.00"),
            created_by=self.user,
        )

        self.assertEqual(product.name, "iPhone 15 Pro")
        self.assertEqual(product.code, "IP15PRO")
        self.assertEqual(product.category, self.category)
        self.assertEqual(product.brand, self.brand)
        self.assertEqual(product.unit, self.unit)
        self.assertEqual(product.status, "active")

    def test_product_unique_code(self):
        """Test product code uniqueness."""
        Product.objects.create(
            name="iPhone 15 Pro",
            code="IP15PRO",
            category=self.category,
            unit=self.unit,
            created_by=self.user,
        )

        # Try to create another product with same code
        with self.assertRaises(Exception):
            Product.objects.create(
                name="iPhone 15 Pro Max",
                code="IP15PRO",
                category=self.category,
                unit=self.unit,
                created_by=self.user,
            )

    def test_product_profit_margin(self):
        """Test product profit margin calculation."""
        product = Product.objects.create(
            name="iPhone 15 Pro",
            code="IP15PRO",
            category=self.category,
            unit=self.unit,
            cost_price=Decimal("5000.00"),
            selling_price=Decimal("7999.00"),
            created_by=self.user,
        )

        # Expected: (7999 - 5000) / 5000 * 100 = 59.98%
        # Note: This is markup (based on cost), not margin (based on selling price)
        expected_margin = (
            (Decimal("7999.00") - Decimal("5000.00")) / Decimal("5000.00") * Decimal("100")
        )
        self.assertAlmostEqual(float(product.profit_margin), float(expected_margin), places=2)

    def test_product_zero_cost_price(self):
        """Test product with zero cost price."""
        product = Product.objects.create(
            name="Free Sample",
            code="SAMPLE001",
            category=self.category,
            unit=self.unit,
            cost_price=Decimal("0.00"),
            selling_price=Decimal("0.00"),
            created_by=self.user,
        )

        self.assertEqual(product.cost_price, Decimal("0.00"))
        self.assertEqual(product.selling_price, Decimal("0.00"))

    def test_product_dimensions(self):
        """Test product dimensions."""
        product = Product.objects.create(
            name="iPhone 15 Pro",
            code="IP15PRO",
            category=self.category,
            unit=self.unit,
            weight=Decimal("0.221"),
            length=Decimal("14.67"),
            width=Decimal("7.15"),
            height=Decimal("0.83"),
            created_by=self.user,
        )

        self.assertEqual(product.weight, Decimal("0.221"))
        self.assertEqual(product.length, Decimal("14.67"))
        self.assertEqual(product.width, Decimal("7.15"))
        self.assertEqual(product.height, Decimal("0.83"))

    def test_product_inventory_settings(self):
        """Test product inventory settings."""
        product = Product.objects.create(
            name="iPhone 15 Pro",
            code="IP15PRO",
            category=self.category,
            unit=self.unit,
            min_stock=10,
            max_stock=100,
            reorder_point=20,
            created_by=self.user,
        )

        self.assertEqual(product.min_stock, 10)
        self.assertEqual(product.max_stock, 100)
        self.assertEqual(product.reorder_point, 20)

    def test_product_str_representation(self):
        """Test product string representation."""
        product = Product.objects.create(
            name="iPhone 15 Pro",
            code="IP15PRO",
            category=self.category,
            unit=self.unit,
            created_by=self.user,
        )

        expected = "IP15PRO - iPhone 15 Pro"
        self.assertEqual(str(product), expected)


class ProductTypesTest(TestCase):
    """Test different product types."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.category = ProductCategory.objects.create(
            name="测试分类", code="CAT001", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

    def test_material_product(self):
        """Test material product type."""
        product = Product.objects.create(
            name="钢材",
            code="STEEL001",
            category=self.category,
            unit=self.unit,
            product_type="material",
            created_by=self.user,
        )

        self.assertEqual(product.product_type, "material")

    def test_semi_finished_product(self):
        """Test semi-finished product type."""
        product = Product.objects.create(
            name="半成品组件",
            code="SEMI001",
            category=self.category,
            unit=self.unit,
            product_type="semi_finished",
            created_by=self.user,
        )

        self.assertEqual(product.product_type, "semi_finished")

    def test_finished_product(self):
        """Test finished product type."""
        product = Product.objects.create(
            name="成品",
            code="FINISH001",
            category=self.category,
            unit=self.unit,
            product_type="finished",
            created_by=self.user,
        )

        self.assertEqual(product.product_type, "finished")

    def test_service_product(self):
        """Test service product type."""
        product = Product.objects.create(
            name="安装服务",
            code="SERV001",
            category=self.category,
            unit=self.unit,
            product_type="service",
            created_by=self.user,
        )

        self.assertEqual(product.product_type, "service")

    def test_virtual_product(self):
        """Test virtual product type."""
        product = Product.objects.create(
            name="软件许可",
            code="VIRT001",
            category=self.category,
            unit=self.unit,
            product_type="virtual",
            created_by=self.user,
        )

        self.assertEqual(product.product_type, "virtual")


class ProductStatusTest(TestCase):
    """Test product status transitions."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.category = ProductCategory.objects.create(
            name="测试分类", code="CAT001", created_by=self.user
        )

        self.unit = Unit.objects.create(name="件", symbol="pcs", created_by=self.user)

    def test_active_status(self):
        """Test active status."""
        product = Product.objects.create(
            name="活跃产品",
            code="ACTIVE001",
            category=self.category,
            unit=self.unit,
            status="active",
            created_by=self.user,
        )

        self.assertEqual(product.status, "active")

    def test_inactive_status(self):
        """Test inactive status."""
        product = Product.objects.create(
            name="停用产品",
            code="INACTIVE001",
            category=self.category,
            unit=self.unit,
            status="inactive",
            created_by=self.user,
        )

        self.assertEqual(product.status, "inactive")

    def test_discontinued_status(self):
        """Test discontinued status."""
        product = Product.objects.create(
            name="停产产品",
            code="DISC001",
            category=self.category,
            unit=self.unit,
            status="discontinued",
            created_by=self.user,
        )

        self.assertEqual(product.status, "discontinued")

    def test_development_status(self):
        """Test development status."""
        product = Product.objects.create(
            name="开发中产品",
            code="DEV001",
            category=self.category,
            unit=self.unit,
            status="development",
            created_by=self.user,
        )

        self.assertEqual(product.status, "development")
