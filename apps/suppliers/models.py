"""
Supplier models for the ERP system.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db.models import Sum
from core.models import BaseModel, PAYMENT_METHOD_CHOICES

User = get_user_model()


class SupplierCategory(BaseModel):
    """
    Supplier category model.
    """
    name = models.CharField('分类名称', max_length=100, unique=True)
    code = models.CharField('分类代码', max_length=50, unique=True)
    description = models.TextField('分类描述', blank=True)
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        verbose_name = '供应商分类'
        verbose_name_plural = '供应商分类'
        db_table = 'suppliers_category'

    def __str__(self):
        return self.name


class Supplier(BaseModel):
    """
    Supplier model.
    """
    SUPPLIER_LEVELS = [
        ('A', 'A级供应商'),
        ('B', 'B级供应商'),
        ('C', 'C级供应商'),
        ('D', 'D级供应商'),
    ]

    # Basic information
    name = models.CharField('供应商名称', max_length=200)
    code = models.CharField('供应商编码', max_length=100, unique=True)
    category = models.ForeignKey(
        SupplierCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='供应商分类'
    )
    level = models.CharField('供应商等级', max_length=1, choices=SUPPLIER_LEVELS, default='C')

    # Contact information (详细联系信息请参考SupplierContact模型)
    website = models.URLField('网站', blank=True)

    # Address information
    address = models.TextField('地址', blank=True)
    city = models.CharField('城市', max_length=100, blank=True)
    province = models.CharField('省份', max_length=100, blank=True)
    country = models.CharField('国家', max_length=100, default='中国')
    postal_code = models.CharField('邮政编码', max_length=20, blank=True)
    
    # Business information
    tax_number = models.CharField('税号', max_length=100, blank=True)
    registration_number = models.CharField('注册号', max_length=100, blank=True)
    legal_representative = models.CharField('法定代表人', max_length=100, blank=True)
    business_license = models.FileField('营业执照', upload_to='suppliers/licenses/', blank=True)
    
    # Financial information
    payment_terms = models.CharField('付款方式', max_length=50, choices=PAYMENT_METHOD_CHOICES, blank=True)
    currency = models.CharField('币种', max_length=10, default='CNY')
    bank_name = models.CharField('开户银行', max_length=100, blank=True)
    bank_account = models.CharField('银行账号', max_length=50, blank=True)
    
    # Purchase information
    buyer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suppliers',
        verbose_name='采购员'
    )
    lead_time = models.PositiveIntegerField('交货周期(天)', default=0)
    min_order_amount = models.DecimalField('最小订单金额', max_digits=12, decimal_places=2, default=0)
    
    # Quality and certification
    quality_rating = models.DecimalField('质量评级', max_digits=3, decimal_places=1, default=0, help_text='0-10分')
    delivery_rating = models.DecimalField('交货评级', max_digits=3, decimal_places=1, default=0, help_text='0-10分')
    service_rating = models.DecimalField('服务评级', max_digits=3, decimal_places=1, default=0, help_text='0-10分')
    certifications = models.TextField('认证资质', blank=True)
    
    # Status and settings
    is_active = models.BooleanField('是否启用', default=True)
    is_approved = models.BooleanField('是否已审核', default=False)
    notes = models.TextField('备注', blank=True)
    
    # Timestamps
    first_order_date = models.DateField('首次采购日期', null=True, blank=True)
    last_order_date = models.DateField('最后采购日期', null=True, blank=True)

    class Meta:
        verbose_name = '供应商'
        verbose_name_plural = '供应商'
        db_table = 'suppliers_supplier'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['level']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def total_orders(self):
        """Get total number of purchase orders."""
        return self.purchase_orders.count()

    @property
    def total_purchase_amount(self):
        """Get total purchase amount."""
        return self.purchase_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0

    @property
    def average_rating(self):
        """Calculate average rating."""
        ratings = [self.quality_rating, self.delivery_rating, self.service_rating]
        valid_ratings = [r for r in ratings if r > 0]
        return sum(valid_ratings) / len(valid_ratings) if valid_ratings else 0


class SupplierContact(BaseModel):
    """
    Supplier contact model for multiple contacts per supplier.
    """
    CONTACT_TYPES = [
        ('primary', '主要联系人'),
        ('finance', '财务联系人'),
        ('technical', '技术联系人'),
        ('sales', '销售联系人'),
        ('other', '其他'),
    ]

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name='供应商'
    )
    name = models.CharField('姓名', max_length=100)
    position = models.CharField('职位', max_length=100, blank=True)
    contact_type = models.CharField('联系人类型', max_length=20, choices=CONTACT_TYPES, default='other')
    phone = models.CharField('电话', max_length=20, blank=True)
    mobile = models.CharField('手机', max_length=20, blank=True)
    email = models.EmailField('邮箱', blank=True)
    qq = models.CharField('QQ', max_length=20, blank=True)
    wechat = models.CharField('微信', max_length=50, blank=True)
    notes = models.TextField('备注', blank=True)
    is_primary = models.BooleanField('是否主要联系人', default=False)
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        verbose_name = '供应商联系人'
        verbose_name_plural = '供应商联系人'
        db_table = 'suppliers_contact'

    def __str__(self):
        return f"{self.supplier.name} - {self.name}"


class SupplierProduct(BaseModel):
    """
    Supplier product model for supplier-specific product information.
    """
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='供应商'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        verbose_name='产品'
    )
    supplier_product_code = models.CharField('供应商产品编码', max_length=100, blank=True)
    supplier_product_name = models.CharField('供应商产品名称', max_length=200, blank=True)
    price = models.DecimalField('采购价格', max_digits=12, decimal_places=2)
    currency = models.CharField('币种', max_length=10, default='CNY')
    min_order_qty = models.DecimalField('最小订购量', max_digits=12, decimal_places=2, default=1)
    lead_time = models.PositiveIntegerField('交货周期(天)', default=0)
    is_preferred = models.BooleanField('是否首选供应商', default=False)
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        verbose_name = '供应商产品'
        verbose_name_plural = '供应商产品'
        db_table = 'suppliers_product'
        unique_together = ['supplier', 'product']

    def __str__(self):
        return f"{self.supplier.name} - {self.product.name}"


class SupplierEvaluation(BaseModel):
    """
    Supplier evaluation model.
    """
    EVALUATION_PERIODS = [
        ('monthly', '月度评估'),
        ('quarterly', '季度评估'),
        ('annual', '年度评估'),
    ]

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name='供应商'
    )
    evaluation_period = models.CharField('评估周期', max_length=20, choices=EVALUATION_PERIODS)
    year = models.PositiveIntegerField('年份')
    quarter = models.PositiveIntegerField('季度', null=True, blank=True)
    month = models.PositiveIntegerField('月份', null=True, blank=True)
    
    # Evaluation scores (0-100)
    quality_score = models.DecimalField('质量得分', max_digits=5, decimal_places=2, default=0)
    delivery_score = models.DecimalField('交货得分', max_digits=5, decimal_places=2, default=0)
    service_score = models.DecimalField('服务得分', max_digits=5, decimal_places=2, default=0)
    price_score = models.DecimalField('价格得分', max_digits=5, decimal_places=2, default=0)
    
    # Comments and recommendations
    strengths = models.TextField('优势', blank=True)
    weaknesses = models.TextField('不足', blank=True)
    recommendations = models.TextField('改进建议', blank=True)
    
    # Overall assessment
    overall_score = models.DecimalField('综合得分', max_digits=5, decimal_places=2, default=0)
    is_approved = models.BooleanField('是否通过评估', default=True)
    
    # Evaluator
    evaluator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='评估人'
    )

    class Meta:
        verbose_name = '供应商评估'
        verbose_name_plural = '供应商评估'
        db_table = 'suppliers_evaluation'
        unique_together = ['supplier', 'evaluation_period', 'year', 'quarter', 'month']

    def __str__(self):
        return f"{self.supplier.name} - {self.get_evaluation_period_display()} - {self.year}"

    def save(self, *args, **kwargs):
        # Calculate overall score as weighted average
        from decimal import Decimal
        self.overall_score = (
            self.quality_score * Decimal('0.3') +
            self.delivery_score * Decimal('0.3') +
            self.service_score * Decimal('0.2') +
            self.price_score * Decimal('0.2')
        )
        super().save(*args, **kwargs)