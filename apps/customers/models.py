"""
Customer models for the ERP system.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from core.models import BaseModel, PAYMENT_METHOD_CHOICES

User = get_user_model()


class CustomerCategory(BaseModel):
    """
    Customer category model.
    """

    name = models.CharField("分类名称", max_length=100, unique=True)
    code = models.CharField("分类代码", max_length=50, unique=True)
    description = models.TextField("分类描述", blank=True)
    discount_rate = models.DecimalField("默认折扣率", max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField("是否启用", default=True)

    class Meta:
        verbose_name = "客户分类"
        verbose_name_plural = "客户分类"
        db_table = "customers_category"

    def __str__(self):
        return self.name


class Customer(BaseModel):
    """
    Customer model.
    """

    CUSTOMER_LEVELS = [
        ("A", "A级客户"),
        ("B", "B级客户"),
        ("C", "C级客户"),
        ("D", "D级客户"),
    ]

    STATUS_CHOICES = [
        ("active", "正常"),
        ("inactive", "停用"),
        ("potential", "潜在客户"),
        ("blacklist", "黑名单"),
    ]

    # Basic information
    name = models.CharField("客户名称", max_length=200)
    code = models.CharField("客户编码", max_length=100, unique=True)
    customer_level = models.CharField("客户等级", max_length=1, choices=CUSTOMER_LEVELS, default="C")
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="active")

    category = models.ForeignKey(
        CustomerCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customers",
        verbose_name="客户分类",
    )

    # Contact information (详细联系信息请参考CustomerContact模型)
    website = models.URLField("网站", blank=True)

    # Address information
    address = models.TextField("地址", blank=True)
    city = models.CharField("城市", max_length=100, blank=True)
    province = models.CharField("省份", max_length=100, blank=True)
    country = models.CharField("国家", max_length=100, default="中国")
    postal_code = models.CharField("邮政编码", max_length=20, blank=True)

    # Business information
    industry = models.CharField("行业", max_length=100, blank=True)
    business_license = models.CharField("营业执照号", max_length=100, blank=True)
    tax_number = models.CharField("税号", max_length=100, blank=True)
    bank_name = models.CharField("开户银行", max_length=200, blank=True)
    bank_account = models.CharField("银行账号", max_length=100, blank=True)

    # Sales information
    sales_rep = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customers",
        verbose_name="销售代表",
    )
    credit_limit = models.DecimalField("信用额度", max_digits=12, decimal_places=2, default=0)
    payment_terms = models.CharField(
        "付款方式", max_length=50, choices=PAYMENT_METHOD_CHOICES, blank=True
    )
    discount_rate = models.DecimalField("折扣率", max_digits=5, decimal_places=2, default=0)

    # Additional information
    source = models.CharField("客户来源", max_length=100, blank=True)
    notes = models.TextField("备注", blank=True)
    tags = models.CharField("标签", max_length=500, blank=True)

    class Meta:
        verbose_name = "客户"
        verbose_name_plural = "客户"
        db_table = "customers_customer"

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def display_name(self):
        """Return display name with primary contact person if available."""
        primary_contact = self.contacts.filter(is_primary=True).first()
        if primary_contact:
            return f"{self.name} ({primary_contact.name})"
        return self.name


class CustomerContact(BaseModel):
    """
    Customer contact model for multiple contacts per customer.
    """

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="contacts", verbose_name="客户"
    )
    name = models.CharField("姓名", max_length=100)
    position = models.CharField("职位", max_length=100, blank=True)
    department = models.CharField("部门", max_length=100, blank=True)
    phone = models.CharField("电话", max_length=20, blank=True)
    mobile = models.CharField("手机", max_length=20, blank=True)
    email = models.EmailField("邮箱", blank=True)
    is_primary = models.BooleanField("是否主要联系人", default=False)
    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "客户联系人"
        verbose_name_plural = "客户联系人"
        db_table = "customers_contact"

    def __str__(self):
        return f"{self.customer.name} - {self.name}"


class CustomerAddress(BaseModel):
    """
    Customer address model for multiple addresses per customer.
    """

    ADDRESS_TYPES = [
        ("billing", "账单地址"),
        ("shipping", "收货地址"),
        ("office", "办公地址"),
        ("warehouse", "仓库地址"),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="addresses", verbose_name="客户"
    )
    address_type = models.CharField("地址类型", max_length=20, choices=ADDRESS_TYPES, default="office")
    address = models.TextField("详细地址")
    city = models.CharField("城市", max_length=100)
    province = models.CharField("省份", max_length=100)
    country = models.CharField("国家", max_length=100, default="中国")
    postal_code = models.CharField("邮政编码", max_length=20, blank=True)
    is_default = models.BooleanField("是否默认地址", default=False)
    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "客户地址"
        verbose_name_plural = "客户地址"
        db_table = "customers_address"

    def __str__(self):
        return f"{self.customer.name} - {self.get_address_type_display()}"

    @property
    def full_address(self):
        """Return full formatted address."""
        parts = [self.country, self.province, self.city, self.address]
        return ", ".join([part for part in parts if part])


class CustomerCreditHistory(BaseModel):
    """
    Customer credit history model.
    """

    CREDIT_TYPES = [
        ("increase", "增加信用额度"),
        ("decrease", "减少信用额度"),
        ("freeze", "冻结信用"),
        ("unfreeze", "解冻信用"),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="credit_history", verbose_name="客户"
    )
    credit_type = models.CharField("信用操作", max_length=20, choices=CREDIT_TYPES)
    old_limit = models.DecimalField("原信用额度", max_digits=12, decimal_places=2)
    new_limit = models.DecimalField("新信用额度", max_digits=12, decimal_places=2)
    reason = models.TextField("操作原因")
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_credit_changes",
        verbose_name="批准人",
    )

    class Meta:
        verbose_name = "客户信用历史"
        verbose_name_plural = "客户信用历史"
        db_table = "customers_credit_history"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.name} - {self.get_credit_type_display()}"


class CustomerVisit(BaseModel):
    """
    Customer visit record model.
    """

    VISIT_TYPES = [
        ("phone", "电话拜访"),
        ("email", "邮件联系"),
        ("onsite", "上门拜访"),
        ("exhibition", "展会接触"),
        ("online", "在线沟通"),
    ]

    VISIT_PURPOSES = [
        ("sales", "销售拜访"),
        ("service", "售后服务"),
        ("collection", "催收款项"),
        ("relationship", "关系维护"),
        ("complaint", "投诉处理"),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="visits", verbose_name="客户"
    )
    visit_type = models.CharField("拜访方式", max_length=20, choices=VISIT_TYPES, default="phone")
    visit_purpose = models.CharField("拜访目的", max_length=20, choices=VISIT_PURPOSES, default="sales")
    visit_date = models.DateTimeField("拜访时间")
    visitor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_visits",
        verbose_name="拜访人",
    )
    contact_person = models.CharField("接待人", max_length=100, blank=True)
    content = models.TextField("拜访内容")
    result = models.TextField("拜访结果", blank=True)
    next_action = models.TextField("下次行动", blank=True)
    next_visit_date = models.DateTimeField("下次拜访时间", null=True, blank=True)

    class Meta:
        verbose_name = "客户拜访记录"
        verbose_name_plural = "客户拜访记录"
        db_table = "customers_visit"
        ordering = ["-visit_date"]

    def __str__(self):
        return f"{self.customer.name} - {self.visit_date.strftime('%Y-%m-%d')}"


# Alias for backward compatibility - used in sales module
Contact = CustomerContact
