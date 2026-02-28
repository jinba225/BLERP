"""
Departments models tests.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.departments.models import Department, DepartmentBudget, Position

User = get_user_model()


class DepartmentModelTest(TestCase):
    """Test Department model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        self.manager = User.objects.create_user(
            username="manager", email="manager@example.com", password="pass123"
        )

    def test_department_creation(self):
        """Test department creation."""
        dept = Department.objects.create(
            name="技术部",
            code="TECH",
            manager=self.manager,
            description="技术研发部门",
            phone="010-12345678",
            email="tech@company.com",
            created_by=self.user,
        )

        self.assertEqual(dept.name, "技术部")
        self.assertEqual(dept.code, "TECH")
        self.assertEqual(dept.manager, self.manager)
        self.assertTrue(dept.is_active)

    def test_department_unique_code(self):
        """Test department code uniqueness."""
        Department.objects.create(name="技术部", code="TECH", created_by=self.user)

        # Try to create another department with same code
        with self.assertRaises(Exception):
            Department.objects.create(name="技术研发部", code="TECH", created_by=self.user)

    def test_department_hierarchy(self):
        """Test department hierarchy."""
        parent = Department.objects.create(name="技术部", code="TECH", created_by=self.user)

        child = Department.objects.create(
            name="前端开发组", code="TECH-FE", parent=parent, created_by=self.user
        )

        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())

    def test_department_full_name(self):
        """Test department full name path."""
        parent = Department.objects.create(name="技术部", code="TECH", created_by=self.user)

        child = Department.objects.create(
            name="研发部", code="TECH-DEV", parent=parent, created_by=self.user
        )

        grandchild = Department.objects.create(
            name="前端开发组", code="TECH-DEV-FE", parent=child, created_by=self.user
        )

        expected = "技术部 > 研发部 > 前端开发组"
        self.assertEqual(grandchild.full_name, expected)

    def test_department_get_employee_count(self):
        """Test get_employee_count method."""
        dept = Department.objects.create(name="技术部", code="TECH", created_by=self.user)

        # Create employees in this department
        User.objects.create_user(
            username="emp1",
            email="emp1@example.com",
            password="pass123",
            department=dept,
        )

        User.objects.create_user(
            username="emp2",
            email="emp2@example.com",
            password="pass123",
            department=dept,
        )

        self.assertEqual(dept.get_employee_count(), 2)

    def test_department_get_employee_count_with_subdepartments(self):
        """Test get_employee_count includes subdepartments."""
        parent = Department.objects.create(name="技术部", code="TECH", created_by=self.user)

        child = Department.objects.create(
            name="研发部", code="TECH-DEV", parent=parent, created_by=self.user
        )

        # Employee in parent department
        User.objects.create_user(
            username="emp1",
            email="emp1@example.com",
            password="pass123",
            department=parent,
        )

        # Employees in child department
        User.objects.create_user(
            username="emp2",
            email="emp2@example.com",
            password="pass123",
            department=child,
        )

        User.objects.create_user(
            username="emp3",
            email="emp3@example.com",
            password="pass123",
            department=child,
        )

        # Parent should count all 3 employees
        self.assertEqual(parent.get_employee_count(), 3)
        # Child should count only its 2 employees
        self.assertEqual(child.get_employee_count(), 2)

    def test_department_get_all_employees(self):
        """Test get_all_employees method."""
        dept = Department.objects.create(name="技术部", code="TECH", created_by=self.user)

        emp1 = User.objects.create_user(
            username="emp1",
            email="emp1@example.com",
            password="pass123",
            department=dept,
        )

        emp2 = User.objects.create_user(
            username="emp2",
            email="emp2@example.com",
            password="pass123",
            department=dept,
        )

        employees = dept.get_all_employees()
        self.assertEqual(employees.count(), 2)
        self.assertIn(emp1, employees)
        self.assertIn(emp2, employees)

    def test_department_str_representation(self):
        """Test department string representation."""
        dept = Department.objects.create(name="技术部", code="TECH", created_by=self.user)

        self.assertEqual(str(dept), "技术部")


class PositionModelTest(TestCase):
    """Test Position model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        self.department = Department.objects.create(name="技术部", code="TECH", created_by=self.user)

    def test_position_creation(self):
        """Test position creation."""
        position = Position.objects.create(
            name="高级工程师",
            code="SR-ENG",
            department=self.department,
            level="senior",
            description="高级软件工程师",
            requirements="5年以上开发经验",
            responsibilities="负责核心模块开发",
            min_salary=Decimal("15000.00"),
            max_salary=Decimal("25000.00"),
            created_by=self.user,
        )

        self.assertEqual(position.name, "高级工程师")
        self.assertEqual(position.code, "SR-ENG")
        self.assertEqual(position.department, self.department)
        self.assertEqual(position.level, "senior")
        self.assertTrue(position.is_active)

    def test_position_unique_code(self):
        """Test position code uniqueness."""
        Position.objects.create(
            name="高级工程师",
            code="SR-ENG",
            department=self.department,
            created_by=self.user,
        )

        # Try to create another position with same code
        with self.assertRaises(Exception):
            Position.objects.create(
                name="资深工程师",
                code="SR-ENG",
                department=self.department,
                created_by=self.user,
            )

    def test_position_levels(self):
        """Test all position levels."""
        levels = [
            "junior",
            "intermediate",
            "senior",
            "expert",
            "manager",
            "director",
            "vp",
            "president",
        ]

        for level in levels:
            position = Position.objects.create(
                name=f"{level}职位",
                code=f"POS-{level.upper()}",
                department=self.department,
                level=level,
                created_by=self.user,
            )
            self.assertEqual(position.level, level)

    def test_position_str_representation(self):
        """Test position string representation."""
        position = Position.objects.create(
            name="高级工程师",
            code="SR-ENG",
            department=self.department,
            created_by=self.user,
        )

        expected = "技术部 - 高级工程师"
        self.assertEqual(str(position), expected)


class DepartmentBudgetModelTest(TestCase):
    """Test DepartmentBudget model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )

        self.approver = User.objects.create_user(
            username="approver", email="approver@example.com", password="pass123"
        )

        self.department = Department.objects.create(name="技术部", code="TECH", created_by=self.user)

    def test_budget_creation(self):
        """Test department budget creation."""
        budget = DepartmentBudget.objects.create(
            department=self.department,
            budget_type="annual",
            year=2025,
            personnel_budget=Decimal("500000.00"),
            operational_budget=Decimal("200000.00"),
            equipment_budget=Decimal("150000.00"),
            other_budget=Decimal("50000.00"),
            created_by=self.user,
        )

        self.assertEqual(budget.department, self.department)
        self.assertEqual(budget.budget_type, "annual")
        self.assertEqual(budget.year, 2025)
        self.assertFalse(budget.is_approved)

    def test_budget_types(self):
        """Test all budget types."""
        types = ["annual", "quarterly", "monthly", "project"]

        for i, budget_type in enumerate(types):
            kwargs = {
                "department": self.department,
                "budget_type": budget_type,
                "year": 2025,
                "personnel_budget": Decimal("100000.00"),
                "created_by": self.user,
            }

            if budget_type == "quarterly":
                kwargs["quarter"] = 1
            elif budget_type == "monthly":
                kwargs["month"] = 1 + i

            budget = DepartmentBudget.objects.create(**kwargs)
            self.assertEqual(budget.budget_type, budget_type)

    def test_total_budget_property(self):
        """Test total_budget property calculation."""
        budget = DepartmentBudget.objects.create(
            department=self.department,
            budget_type="annual",
            year=2025,
            personnel_budget=Decimal("500000.00"),
            operational_budget=Decimal("200000.00"),
            equipment_budget=Decimal("150000.00"),
            other_budget=Decimal("50000.00"),
            created_by=self.user,
        )

        expected = Decimal("900000.00")
        self.assertEqual(budget.total_budget, expected)

    def test_total_actual_property(self):
        """Test total_actual property calculation."""
        budget = DepartmentBudget.objects.create(
            department=self.department,
            budget_type="annual",
            year=2025,
            personnel_budget=Decimal("500000.00"),
            personnel_actual=Decimal("480000.00"),
            operational_budget=Decimal("200000.00"),
            operational_actual=Decimal("210000.00"),
            equipment_budget=Decimal("150000.00"),
            equipment_actual=Decimal("145000.00"),
            other_budget=Decimal("50000.00"),
            other_actual=Decimal("55000.00"),
            created_by=self.user,
        )

        expected = Decimal("890000.00")
        self.assertEqual(budget.total_actual, expected)

    def test_variance_property(self):
        """Test variance property calculation."""
        budget = DepartmentBudget.objects.create(
            department=self.department,
            budget_type="annual",
            year=2025,
            personnel_budget=Decimal("500000.00"),
            personnel_actual=Decimal("480000.00"),
            operational_budget=Decimal("200000.00"),
            operational_actual=Decimal("210000.00"),
            equipment_budget=Decimal("150000.00"),
            equipment_actual=Decimal("145000.00"),
            other_budget=Decimal("50000.00"),
            other_actual=Decimal("55000.00"),
            created_by=self.user,
        )

        # Total budget: 900000, Total actual: 890000
        # Variance: 890000 - 900000 = -10000
        expected = Decimal("-10000.00")
        self.assertEqual(budget.variance, expected)

    def test_variance_percentage_property(self):
        """Test variance_percentage property calculation."""
        budget = DepartmentBudget.objects.create(
            department=self.department,
            budget_type="annual",
            year=2025,
            personnel_budget=Decimal("500000.00"),
            personnel_actual=Decimal("480000.00"),
            operational_budget=Decimal("200000.00"),
            operational_actual=Decimal("210000.00"),
            equipment_budget=Decimal("150000.00"),
            equipment_actual=Decimal("145000.00"),
            other_budget=Decimal("50000.00"),
            other_actual=Decimal("55000.00"),
            created_by=self.user,
        )

        # Variance: -10000, Total budget: 900000
        # Percentage: (-10000 / 900000) * 100 = -1.111...
        expected = Decimal("-10000.00") / Decimal("900000.00") * Decimal("100")
        self.assertAlmostEqual(float(budget.variance_percentage), float(expected), places=2)

    def test_variance_percentage_zero_budget(self):
        """Test variance_percentage with zero budget."""
        budget = DepartmentBudget.objects.create(
            department=self.department,
            budget_type="annual",
            year=2025,
            personnel_budget=Decimal("0.00"),
            operational_budget=Decimal("0.00"),
            equipment_budget=Decimal("0.00"),
            other_budget=Decimal("0.00"),
            created_by=self.user,
        )

        self.assertEqual(budget.variance_percentage, 0)

    def test_budget_approval(self):
        """Test budget approval."""
        budget = DepartmentBudget.objects.create(
            department=self.department,
            budget_type="annual",
            year=2025,
            personnel_budget=Decimal("500000.00"),
            created_by=self.user,
        )

        # Approve budget
        from django.utils import timezone

        budget.is_approved = True
        budget.approved_by = self.approver
        budget.approved_at = timezone.now()
        budget.save()

        self.assertTrue(budget.is_approved)
        self.assertEqual(budget.approved_by, self.approver)
        self.assertIsNotNone(budget.approved_at)

    def test_budget_str_representation(self):
        """Test budget string representation."""
        budget = DepartmentBudget.objects.create(
            department=self.department,
            budget_type="annual",
            year=2025,
            personnel_budget=Decimal("500000.00"),
            created_by=self.user,
        )

        expected = "技术部 - 年度预算 - 2025"
        self.assertEqual(str(budget), expected)
