"""
Customers models tests.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.customers.models import (
    Customer,
    CustomerAddress,
    CustomerCategory,
    CustomerContact,
    CustomerCreditHistory,
    CustomerVisit,
)

User = get_user_model()


class CustomerCategoryModelTest(TestCase):
    """Test CustomerCategory model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

    def test_category_creation(self):
        """Test customer category creation."""
        category = CustomerCategory.objects.create(
            name="VIP客户",
            code="VIP001",
            description="重要客户分类",
            discount_rate=Decimal("10.00"),
            created_by=self.user,
        )

        self.assertEqual(category.name, "VIP客户")
        self.assertEqual(category.code, "VIP001")
        self.assertEqual(category.discount_rate, Decimal("10.00"))
        self.assertTrue(category.is_active)

    def test_category_unique_name(self):
        """Test category name uniqueness."""
        CustomerCategory.objects.create(name="VIP客户", code="VIP001", created_by=self.user)

        # Try to create another category with same name
        with self.assertRaises(Exception):
            CustomerCategory.objects.create(name="VIP客户", code="VIP002", created_by=self.user)

    def test_category_unique_code(self):
        """Test category code uniqueness."""
        CustomerCategory.objects.create(name="VIP客户", code="VIP001", created_by=self.user)

        # Try to create another category with same code
        with self.assertRaises(Exception):
            CustomerCategory.objects.create(name="普通客户", code="VIP001", created_by=self.user)

    def test_category_str_representation(self):
        """Test category string representation."""
        category = CustomerCategory.objects.create(
            name="VIP客户", code="VIP001", created_by=self.user
        )

        self.assertEqual(str(category), "VIP客户")


class CustomerModelTest(TestCase):
    """Test Customer model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.sales_rep = User.objects.create_user(
            username="salesrep", email="sales@test.com", password="testpass123"
        )

        self.category = CustomerCategory.objects.create(
            name="VIP客户", code="VIP001", discount_rate=Decimal("10.00"), created_by=self.user
        )

    def test_customer_creation(self):
        """Test customer creation."""
        customer = Customer.objects.create(
            name="测试公司",
            code="CUST001",
            customer_level="A",
            status="active",
            category=self.category,
            address="北京市朝阳区",
            city="北京",
            province="北京",
            sales_rep=self.sales_rep,
            credit_limit=Decimal("100000.00"),
            created_by=self.user,
        )

        self.assertEqual(customer.name, "测试公司")
        self.assertEqual(customer.code, "CUST001")
        self.assertEqual(customer.customer_level, "A")
        self.assertEqual(customer.status, "active")
        self.assertEqual(customer.category, self.category)
        self.assertEqual(customer.credit_limit, Decimal("100000.00"))

    def test_customer_unique_code(self):
        """Test customer code uniqueness."""
        Customer.objects.create(name="测试公司A", code="CUST001", created_by=self.user)

        # Try to create another customer with same code
        with self.assertRaises(Exception):
            Customer.objects.create(name="测试公司B", code="CUST001", created_by=self.user)

    def test_customer_levels(self):
        """Test all customer levels."""
        levels = ["A", "B", "C", "D"]

        for level in levels:
            customer = Customer.objects.create(
                name=f"测试客户-{level}级",
                code=f"CUST{level}",
                customer_level=level,
                created_by=self.user,
            )
            self.assertEqual(customer.customer_level, level)

    def test_customer_statuses(self):
        """Test all customer statuses."""
        statuses = ["active", "inactive", "potential", "blacklist"]

        for status in statuses:
            customer = Customer.objects.create(
                name=f"测试客户-{status}", code=f"CUST{status}", status=status, created_by=self.user
            )
            self.assertEqual(customer.status, status)

    def test_customer_display_name(self):
        """Test customer display name property."""
        # Without contact person
        customer1 = Customer.objects.create(name="测试公司", code="CUST001", created_by=self.user)
        self.assertEqual(customer1.display_name, "测试公司")

        # With primary contact person
        customer2 = Customer.objects.create(name="测试公司2", code="CUST002", created_by=self.user)
        CustomerContact.objects.create(
            customer=customer2, name="张三", is_primary=True, created_by=self.user
        )
        self.assertEqual(customer2.display_name, "测试公司2 (张三)")

    def test_customer_str_representation(self):
        """Test customer string representation."""
        customer = Customer.objects.create(name="测试公司", code="CUST001", created_by=self.user)

        expected = "CUST001 - 测试公司"
        self.assertEqual(str(customer), expected)


class CustomerContactModelTest(TestCase):
    """Test CustomerContact model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.customer = Customer.objects.create(name="测试公司", code="CUST001", created_by=self.user)

    def test_contact_creation(self):
        """Test customer contact creation."""
        contact = CustomerContact.objects.create(
            customer=self.customer,
            name="张三",
            position="销售经理",
            department="销售部",
            phone="010-12345678",
            mobile="13800138000",
            email="zhangsan@company.com",
            is_primary=True,
            notes="主要联系人",
            created_by=self.user,
        )

        self.assertEqual(contact.customer, self.customer)
        self.assertEqual(contact.name, "张三")
        self.assertEqual(contact.position, "销售经理")
        self.assertTrue(contact.is_primary)

    def test_multiple_contacts(self):
        """Test multiple contacts for one customer."""
        contact1 = CustomerContact.objects.create(
            customer=self.customer, name="张三", is_primary=True, created_by=self.user
        )

        contact2 = CustomerContact.objects.create(
            customer=self.customer, name="李四", is_primary=False, created_by=self.user
        )

        contacts = self.customer.contacts.all()
        self.assertEqual(contacts.count(), 2)
        self.assertIn(contact1, contacts)
        self.assertIn(contact2, contacts)

    def test_contact_str_representation(self):
        """Test contact string representation."""
        contact = CustomerContact.objects.create(
            customer=self.customer, name="张三", created_by=self.user
        )

        expected = "测试公司 - 张三"
        self.assertEqual(str(contact), expected)


class CustomerAddressModelTest(TestCase):
    """Test CustomerAddress model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.customer = Customer.objects.create(name="测试公司", code="CUST001", created_by=self.user)

    def test_address_creation(self):
        """Test customer address creation."""
        address = CustomerAddress.objects.create(
            customer=self.customer,
            address_type="office",
            address="朝阳区建国路1号",
            city="北京",
            province="北京",
            country="中国",
            postal_code="100000",
            is_default=True,
            created_by=self.user,
        )

        self.assertEqual(address.customer, self.customer)
        self.assertEqual(address.address_type, "office")
        self.assertEqual(address.city, "北京")
        self.assertTrue(address.is_default)

    def test_address_types(self):
        """Test all address types."""
        types = ["billing", "shipping", "office", "warehouse"]

        for i, address_type in enumerate(types):
            address = CustomerAddress.objects.create(
                customer=self.customer,
                address_type=address_type,
                address=f"测试地址{i}",
                city="北京",
                province="北京",
                created_by=self.user,
            )
            self.assertEqual(address.address_type, address_type)

    def test_multiple_addresses(self):
        """Test multiple addresses for one customer."""
        address1 = CustomerAddress.objects.create(
            customer=self.customer,
            address_type="office",
            address="办公地址",
            city="北京",
            province="北京",
            is_default=True,
            created_by=self.user,
        )

        address2 = CustomerAddress.objects.create(
            customer=self.customer,
            address_type="warehouse",
            address="仓库地址",
            city="天津",
            province="天津",
            is_default=False,
            created_by=self.user,
        )

        addresses = self.customer.addresses.all()
        self.assertEqual(addresses.count(), 2)
        self.assertIn(address1, addresses)
        self.assertIn(address2, addresses)

    def test_full_address_property(self):
        """Test full address property."""
        address = CustomerAddress.objects.create(
            customer=self.customer,
            address_type="office",
            address="朝阳区建国路1号",
            city="北京",
            province="北京",
            country="中国",
            created_by=self.user,
        )

        expected = "中国, 北京, 北京, 朝阳区建国路1号"
        self.assertEqual(address.full_address, expected)

    def test_address_str_representation(self):
        """Test address string representation."""
        address = CustomerAddress.objects.create(
            customer=self.customer,
            address_type="office",
            address="测试地址",
            city="北京",
            province="北京",
            created_by=self.user,
        )

        expected = "测试公司 - 办公地址"
        self.assertEqual(str(address), expected)


class CustomerCreditHistoryModelTest(TestCase):
    """Test CustomerCreditHistory model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.approver = User.objects.create_user(
            username="approver", email="approver@test.com", password="testpass123"
        )

        self.customer = Customer.objects.create(
            name="测试公司", code="CUST001", credit_limit=Decimal("50000.00"), created_by=self.user
        )

    def test_credit_history_creation(self):
        """Test credit history creation."""
        history = CustomerCreditHistory.objects.create(
            customer=self.customer,
            credit_type="increase",
            old_limit=Decimal("50000.00"),
            new_limit=Decimal("100000.00"),
            reason="客户信誉良好",
            approved_by=self.approver,
            created_by=self.user,
        )

        self.assertEqual(history.customer, self.customer)
        self.assertEqual(history.credit_type, "increase")
        self.assertEqual(history.old_limit, Decimal("50000.00"))
        self.assertEqual(history.new_limit, Decimal("100000.00"))
        self.assertEqual(history.approved_by, self.approver)

    def test_credit_types(self):
        """Test all credit types."""
        types = ["increase", "decrease", "freeze", "unfreeze"]

        for credit_type in types:
            history = CustomerCreditHistory.objects.create(
                customer=self.customer,
                credit_type=credit_type,
                old_limit=Decimal("50000.00"),
                new_limit=Decimal("100000.00"),
                reason=f"测试{credit_type}",
                created_by=self.user,
            )
            self.assertEqual(history.credit_type, credit_type)

    def test_credit_history_ordering(self):
        """Test credit history ordering by created_at desc."""
        # Create three history records
        history1 = CustomerCreditHistory.objects.create(
            customer=self.customer,
            credit_type="increase",
            old_limit=Decimal("0.00"),
            new_limit=Decimal("50000.00"),
            reason="初始额度",
            created_by=self.user,
        )

        history2 = CustomerCreditHistory.objects.create(
            customer=self.customer,
            credit_type="increase",
            old_limit=Decimal("50000.00"),
            new_limit=Decimal("100000.00"),
            reason="增加额度",
            created_by=self.user,
        )

        history3 = CustomerCreditHistory.objects.create(
            customer=self.customer,
            credit_type="freeze",
            old_limit=Decimal("100000.00"),
            new_limit=Decimal("100000.00"),
            reason="冻结额度",
            created_by=self.user,
        )

        # Get all history and verify ordering
        histories = list(CustomerCreditHistory.objects.filter(customer=self.customer))
        self.assertEqual(histories[0], history3)  # Latest first
        self.assertEqual(histories[1], history2)
        self.assertEqual(histories[2], history1)  # Oldest last

    def test_credit_history_str_representation(self):
        """Test credit history string representation."""
        history = CustomerCreditHistory.objects.create(
            customer=self.customer,
            credit_type="increase",
            old_limit=Decimal("50000.00"),
            new_limit=Decimal("100000.00"),
            reason="测试",
            created_by=self.user,
        )

        expected = "测试公司 - 增加信用额度"
        self.assertEqual(str(history), expected)


class CustomerVisitModelTest(TestCase):
    """Test CustomerVisit model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )

        self.visitor = User.objects.create_user(
            username="visitor", email="visitor@test.com", password="testpass123"
        )

        self.customer = Customer.objects.create(name="测试公司", code="CUST001", created_by=self.user)

    def test_visit_creation(self):
        """Test customer visit creation."""
        visit = CustomerVisit.objects.create(
            customer=self.customer,
            visit_type="onsite",
            visit_purpose="sales",
            visit_date=timezone.now(),
            visitor=self.visitor,
            contact_person="张三",
            content="讨论新产品合作",
            result="客户有意向",
            next_action="准备报价单",
            created_by=self.user,
        )

        self.assertEqual(visit.customer, self.customer)
        self.assertEqual(visit.visit_type, "onsite")
        self.assertEqual(visit.visit_purpose, "sales")
        self.assertEqual(visit.visitor, self.visitor)

    def test_visit_types(self):
        """Test all visit types."""
        types = ["phone", "email", "onsite", "exhibition", "online"]

        for visit_type in types:
            visit = CustomerVisit.objects.create(
                customer=self.customer,
                visit_type=visit_type,
                visit_purpose="sales",
                visit_date=timezone.now(),
                content=f"测试{visit_type}",
                created_by=self.user,
            )
            self.assertEqual(visit.visit_type, visit_type)

    def test_visit_purposes(self):
        """Test all visit purposes."""
        purposes = ["sales", "service", "collection", "relationship", "complaint"]

        for purpose in purposes:
            visit = CustomerVisit.objects.create(
                customer=self.customer,
                visit_type="phone",
                visit_purpose=purpose,
                visit_date=timezone.now(),
                content=f"测试{purpose}",
                created_by=self.user,
            )
            self.assertEqual(visit.visit_purpose, purpose)

    def test_visit_ordering(self):
        """Test visit ordering by visit_date desc."""
        # Create three visits
        visit1 = CustomerVisit.objects.create(
            customer=self.customer,
            visit_type="phone",
            visit_purpose="sales",
            visit_date=timezone.now() - timezone.timedelta(days=2),
            content="第一次拜访",
            created_by=self.user,
        )

        visit2 = CustomerVisit.objects.create(
            customer=self.customer,
            visit_type="onsite",
            visit_purpose="sales",
            visit_date=timezone.now() - timezone.timedelta(days=1),
            content="第二次拜访",
            created_by=self.user,
        )

        visit3 = CustomerVisit.objects.create(
            customer=self.customer,
            visit_type="phone",
            visit_purpose="service",
            visit_date=timezone.now(),
            content="第三次拜访",
            created_by=self.user,
        )

        # Get all visits and verify ordering
        visits = list(CustomerVisit.objects.filter(customer=self.customer))
        self.assertEqual(visits[0], visit3)  # Latest first
        self.assertEqual(visits[1], visit2)
        self.assertEqual(visits[2], visit1)  # Oldest last

    def test_visit_str_representation(self):
        """Test visit string representation."""
        visit_date = timezone.now()
        visit = CustomerVisit.objects.create(
            customer=self.customer,
            visit_type="phone",
            visit_purpose="sales",
            visit_date=visit_date,
            content="测试拜访",
            created_by=self.user,
        )

        expected = f"测试公司 - {visit_date.strftime('%Y-%m-%d')}"
        self.assertEqual(str(visit), expected)
