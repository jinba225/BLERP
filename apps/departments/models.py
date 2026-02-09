"""
Department models for the ERP system.
"""
from django.db import models
from django.contrib.auth import get_user_model
from mptt.models import MPTTModel, TreeForeignKey
from core.models import BaseModel

User = get_user_model()


class Department(MPTTModel, BaseModel):
    """
    Department model with hierarchical structure using MPTT.
    """

    name = models.CharField("部门名称", max_length=100)
    code = models.CharField("部门代码", max_length=50, unique=True)
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="上级部门",
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
        verbose_name="部门经理",
    )
    description = models.TextField("部门描述", blank=True)
    phone = models.CharField("联系电话", max_length=20, blank=True)
    email = models.EmailField("邮箱", blank=True)
    address = models.TextField("办公地址", blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_active = models.BooleanField("是否启用", default=True)

    class MPTTMeta:
        order_insertion_by = ["sort_order", "name"]

    class Meta:
        verbose_name = "部门"
        verbose_name_plural = "部门"
        db_table = "departments_department"

    def __str__(self):
        return self.name

    @property
    def full_name(self):
        """Return the full department path."""
        names = [ancestor.name for ancestor in self.get_ancestors(include_self=True)]
        return " > ".join(names)

    def get_employee_count(self):
        """Get the number of employees in this department and its subdepartments."""
        from users.models import User

        department_ids = [dept.id for dept in self.get_descendants(include_self=True)]
        return User.objects.filter(department_id__in=department_ids, is_active=True).count()

    def get_all_employees(self):
        """Get all employees in this department and its subdepartments."""
        from users.models import User

        department_ids = [dept.id for dept in self.get_descendants(include_self=True)]
        return User.objects.filter(department_id__in=department_ids, is_active=True)


class Position(BaseModel):
    """
    Position/Job title model.
    """

    POSITION_LEVELS = [
        ("junior", "初级"),
        ("intermediate", "中级"),
        ("senior", "高级"),
        ("expert", "专家"),
        ("manager", "经理"),
        ("director", "总监"),
        ("vp", "副总裁"),
        ("president", "总裁"),
    ]

    name = models.CharField("职位名称", max_length=100)
    code = models.CharField("职位代码", max_length=50, unique=True)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="positions", verbose_name="所属部门"
    )
    level = models.CharField("职位级别", max_length=20, choices=POSITION_LEVELS, default="junior")
    description = models.TextField("职位描述", blank=True)
    requirements = models.TextField("任职要求", blank=True)
    responsibilities = models.TextField("工作职责", blank=True)
    min_salary = models.DecimalField("最低薪资", max_digits=10, decimal_places=2, null=True, blank=True)
    max_salary = models.DecimalField("最高薪资", max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField("是否启用", default=True)

    class Meta:
        verbose_name = "职位"
        verbose_name_plural = "职位"
        db_table = "departments_position"

    def __str__(self):
        return f"{self.department.name} - {self.name}"

    def get_employee_count(self):
        """Get the number of employees in this position."""
        from users.models import User

        return User.objects.filter(position=self.name, is_active=True).count()


class DepartmentBudget(BaseModel):
    """
    Department budget model.
    """

    BUDGET_TYPES = [
        ("annual", "年度预算"),
        ("quarterly", "季度预算"),
        ("monthly", "月度预算"),
        ("project", "项目预算"),
    ]

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="budgets", verbose_name="部门"
    )
    budget_type = models.CharField("预算类型", max_length=20, choices=BUDGET_TYPES)
    year = models.PositiveIntegerField("年份")
    quarter = models.PositiveIntegerField("季度", null=True, blank=True)
    month = models.PositiveIntegerField("月份", null=True, blank=True)

    # Budget amounts
    personnel_budget = models.DecimalField("人员预算", max_digits=12, decimal_places=2, default=0)
    operational_budget = models.DecimalField("运营预算", max_digits=12, decimal_places=2, default=0)
    equipment_budget = models.DecimalField("设备预算", max_digits=12, decimal_places=2, default=0)
    other_budget = models.DecimalField("其他预算", max_digits=12, decimal_places=2, default=0)

    # Actual amounts
    personnel_actual = models.DecimalField("人员实际", max_digits=12, decimal_places=2, default=0)
    operational_actual = models.DecimalField("运营实际", max_digits=12, decimal_places=2, default=0)
    equipment_actual = models.DecimalField("设备实际", max_digits=12, decimal_places=2, default=0)
    other_actual = models.DecimalField("其他实际", max_digits=12, decimal_places=2, default=0)

    notes = models.TextField("备注", blank=True)
    is_approved = models.BooleanField("是否批准", default=False)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_department_budgets",
        verbose_name="批准人",
    )
    approved_at = models.DateTimeField("批准时间", null=True, blank=True)

    class Meta:
        verbose_name = "部门预算"
        verbose_name_plural = "部门预算"
        db_table = "departments_budget"
        unique_together = ["department", "budget_type", "year", "quarter", "month"]

    def __str__(self):
        return f"{self.department.name} - {self.get_budget_type_display()} - {self.year}"

    @property
    def total_budget(self):
        """Calculate total budget amount."""
        return (
            self.personnel_budget
            + self.operational_budget
            + self.equipment_budget
            + self.other_budget
        )

    @property
    def total_actual(self):
        """Calculate total actual amount."""
        return (
            self.personnel_actual
            + self.operational_actual
            + self.equipment_actual
            + self.other_actual
        )

    @property
    def variance(self):
        """Calculate budget variance."""
        return self.total_actual - self.total_budget

    @property
    def variance_percentage(self):
        """Calculate budget variance percentage."""
        if self.total_budget == 0:
            return 0
        return (self.variance / self.total_budget) * 100
