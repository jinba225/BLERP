"""
Product models for the ERP system.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from mptt.models import MPTTModel, TreeForeignKey
from core.models import BaseModel

User = get_user_model()


class ProductCategory(MPTTModel, BaseModel):
    """
    Product category model with hierarchical structure.
    """
    name = models.CharField('分类名称', max_length=100)
    code = models.CharField('分类代码', max_length=50, unique=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='上级分类'
    )
    description = models.TextField('分类描述', blank=True)
    image = models.ImageField('分类图片', upload_to='categories/', blank=True)
    sort_order = models.PositiveIntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)

    class MPTTMeta:
        order_insertion_by = ['sort_order', 'name']

    class Meta:
        verbose_name = '产品分类'
        verbose_name_plural = '产品分类'
        db_table = 'products_category'

    def __str__(self):
        return self.name

    @property
    def full_name(self):
        """Return the full category path."""
        names = [ancestor.name for ancestor in self.get_ancestors(include_self=True)]
        return ' > '.join(names)


class Brand(BaseModel):
    """
    Product brand model.
    """
    name = models.CharField('品牌名称', max_length=100, unique=True)
    code = models.CharField('品牌代码', max_length=50, unique=True)
    description = models.TextField('品牌描述', blank=True)
    logo = models.ImageField('品牌Logo', upload_to='brands/', blank=True)
    website = models.URLField('官方网站', blank=True)
    country = models.CharField('国家/地区', max_length=50, blank=True)
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        verbose_name = '品牌'
        verbose_name_plural = '品牌'
        db_table = 'products_brand'

    def __str__(self):
        return self.name


class Unit(BaseModel):
    """
    Unit of measurement model.
    """
    UNIT_TYPES = [
        ('basic', '基本单位'),
        ('weight', '重量单位'),
        ('length', '长度单位'),
        ('area', '面积单位'),
        ('volume', '体积单位'),
        ('time', '时间单位'),
        ('count', '计数单位'),
    ]

    name = models.CharField('单位名称', max_length=50, unique=True)
    symbol = models.CharField('单位符号', max_length=10, unique=True)
    unit_type = models.CharField('单位类型', max_length=20, choices=UNIT_TYPES, default='basic')
    description = models.TextField('单位描述', blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    is_default = models.BooleanField(
        '是否默认',
        default=False,
        help_text='是否作为系统的默认计量单位'
    )

    class Meta:
        verbose_name = '计量单位'
        verbose_name_plural = '计量单位'
        db_table = 'products_unit'
        constraints = [
            models.UniqueConstraint(
                fields=['is_default'],
                condition=models.Q(is_default=True),
                name='single_default_unit',
                violation_error_message='只能有一个默认单位'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.symbol})"

    def save(self, *args, **kwargs):
        # 如果设置为默认单位，先取消其他单位的默认状态
        if self.is_default:
            Unit.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Product(BaseModel):
    """
    Product model.
    """
    PRODUCT_TYPES = [
        ('material', '原材料'),
        ('semi_finished', '半成品'),
        ('finished', '成品'),
        ('service', '服务'),
        ('virtual', '虚拟产品'),
    ]

    STATUS_CHOICES = [
        ('active', '正常'),
        ('inactive', '停用'),
        ('discontinued', '停产'),
        ('development', '开发中'),
    ]

    # Basic information
    name = models.CharField('产品名称', max_length=200)
    code = models.CharField('产品编码', max_length=100, unique=True)
    barcode = models.CharField('条形码', max_length=100, blank=True, unique=True, null=True)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='产品分类'
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='品牌'
    )
    product_type = models.CharField('产品类型', max_length=20, choices=PRODUCT_TYPES, default='finished')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='active')

    # Description and specifications
    description = models.TextField('产品描述', blank=True)
    specifications = models.TextField('产品规格', blank=True)
    model = models.CharField('型号', max_length=100, blank=True)
    
    # Units and measurements
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='基本单位'
    )
    weight = models.DecimalField('重量(kg)', max_digits=10, decimal_places=3, null=True, blank=True)
    length = models.DecimalField('长度(cm)', max_digits=10, decimal_places=2, null=True, blank=True)
    width = models.DecimalField('宽度(cm)', max_digits=10, decimal_places=2, null=True, blank=True)
    height = models.DecimalField('高度(cm)', max_digits=10, decimal_places=2, null=True, blank=True)

    # Pricing
    cost_price = models.DecimalField(
        '成本价', 
        max_digits=12, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    selling_price = models.DecimalField(
        '销售价', 
        max_digits=12, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Inventory settings
    track_inventory = models.BooleanField('是否进行库存管理', default=True, help_text='服务类产品通常不需要库存管理')
    min_stock = models.PositiveIntegerField('最小库存', default=0)
    max_stock = models.PositiveIntegerField('最大库存', default=0)
    reorder_point = models.PositiveIntegerField('再订货点', default=0)
    
    # Images and files
    main_image = models.ImageField('主图', upload_to='products/', blank=True)
    
    # Additional information
    warranty_period = models.PositiveIntegerField('保修期(月)', default=0)
    shelf_life = models.PositiveIntegerField('保质期(天)', null=True, blank=True)
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '产品'
        verbose_name_plural = '产品'
        db_table = 'products_product'

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def profit_margin(self):
        """Calculate profit margin percentage."""
        if self.cost_price == 0:
            return 0
        return ((self.selling_price - self.cost_price) / self.cost_price) * 100

    @property
    def volume(self):
        """Calculate product volume in cubic centimeters."""
        if self.length and self.width and self.height:
            return self.length * self.width * self.height
        return None


class ProductImage(BaseModel):
    """
    Product image model for multiple images per product.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='产品'
    )
    image = models.ImageField('图片', upload_to='products/images/')
    title = models.CharField('图片标题', max_length=200, blank=True)
    description = models.TextField('图片描述', blank=True)
    sort_order = models.PositiveIntegerField('排序', default=0)
    is_main = models.BooleanField('是否主图', default=False)

    class Meta:
        verbose_name = '产品图片'
        verbose_name_plural = '产品图片'
        db_table = 'products_image'
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.product.name} - 图片{self.id}"


class ProductAttribute(BaseModel):
    """
    Product attribute definition model.
    """
    ATTRIBUTE_TYPES = [
        ('text', '文本'),
        ('number', '数字'),
        ('boolean', '布尔值'),
        ('date', '日期'),
        ('choice', '选择'),
    ]

    name = models.CharField('属性名称', max_length=100)
    code = models.CharField('属性代码', max_length=50, unique=True)
    attribute_type = models.CharField('属性类型', max_length=20, choices=ATTRIBUTE_TYPES, default='text')
    description = models.TextField('属性描述', blank=True)
    is_required = models.BooleanField('是否必填', default=False)
    is_filterable = models.BooleanField('是否可筛选', default=False)
    sort_order = models.PositiveIntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        verbose_name = '产品属性'
        verbose_name_plural = '产品属性'
        db_table = 'products_attribute'
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class ProductAttributeValue(BaseModel):
    """
    Product attribute value model.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='attribute_values',
        verbose_name='产品'
    )
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name='属性'
    )
    value = models.TextField('属性值')

    class Meta:
        verbose_name = '产品属性值'
        verbose_name_plural = '产品属性值'
        db_table = 'products_attribute_value'
        unique_together = ['product', 'attribute']

    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}: {self.value}"


class ProductPrice(BaseModel):
    """
    Product price history model.
    """
    PRICE_TYPES = [
        ('cost', '成本价'),
        ('selling', '销售价'),
        ('wholesale', '批发价'),
        ('retail', '零售价'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='price_history',
        verbose_name='产品'
    )
    price_type = models.CharField('价格类型', max_length=20, choices=PRICE_TYPES)
    price = models.DecimalField('价格', max_digits=12, decimal_places=2)
    effective_date = models.DateField('生效日期')
    end_date = models.DateField('结束日期', null=True, blank=True)
    reason = models.TextField('调价原因', blank=True)
    is_active = models.BooleanField('是否生效', default=True)

    class Meta:
        verbose_name = '产品价格历史'
        verbose_name_plural = '产品价格历史'
        db_table = 'products_price_history'
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.product.name} - {self.get_price_type_display()}: ¥{self.price}"