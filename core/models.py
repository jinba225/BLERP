"""
Core models for the ERP system.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


# Payment method choices - shared across the system
PAYMENT_METHOD_CHOICES = [
    ('tt_100', 'T/T 100%'),
    ('net_30', 'NET 30 EOM.'),
    ('net_60', 'NET 60 EOM.'),
    ('30_70', '30% Adv,70% B4 SHPT.30%+70%'),
    ('cash', 'Cash'),
    ('be', 'B/E'),
]


class TimeStampedModel(models.Model):
    """
    Abstract base model with created and updated timestamps.
    """
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='创建人'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name='更新人'
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract base model with soft delete functionality.
    """
    is_deleted = models.BooleanField('是否删除', default=False)
    deleted_at = models.DateTimeField('删除时间', null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted',
        verbose_name='删除人'
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft delete the object."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the object."""
        super().delete(using=using, keep_parents=keep_parents)


class BaseModel(TimeStampedModel, SoftDeleteModel):
    """
    Base model combining timestamp and soft delete functionality.
    """
    class Meta:
        abstract = True


class Company(BaseModel):
    """
    Company information model.
    """
    name = models.CharField('公司名称', max_length=200)
    code = models.CharField('公司代码', max_length=50, unique=True)
    legal_representative = models.CharField('法定代表人', max_length=100, blank=True)
    registration_number = models.CharField('注册号', max_length=100, blank=True)
    tax_number = models.CharField('税号', max_length=100, blank=True)
    address = models.TextField('地址', blank=True)
    phone = models.CharField('电话', max_length=50, blank=True)
    fax = models.CharField('传真', max_length=50, blank=True)
    email = models.EmailField('邮箱', blank=True)
    website = models.URLField('网站', blank=True)
    logo = models.ImageField('公司Logo', upload_to='company/logos/', blank=True)
    description = models.TextField('公司描述', blank=True)
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        verbose_name = '公司信息'
        verbose_name_plural = '公司信息'
        db_table = 'core_company'

    def __str__(self):
        return self.name


class SystemConfig(BaseModel):
    """
    System configuration model.
    """
    CONFIG_TYPES = [
        ('system', '系统配置'),
        ('business', '业务配置'),
        ('ui', '界面配置'),
        ('security', '安全配置'),
    ]

    key = models.CharField('配置键', max_length=100, unique=True)
    value = models.TextField('配置值')
    config_type = models.CharField('配置类型', max_length=20, choices=CONFIG_TYPES, default='system')
    description = models.TextField('描述', blank=True)
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置'
        db_table = 'core_system_config'

    def __str__(self):
        return f"{self.key}: {self.value}"


class Attachment(BaseModel):
    """
    File attachment model.
    """
    ATTACHMENT_TYPES = [
        ('image', '图片'),
        ('document', '文档'),
        ('video', '视频'),
        ('audio', '音频'),
        ('other', '其他'),
    ]

    name = models.CharField('文件名', max_length=255)
    file = models.FileField('文件', upload_to='attachments/%Y/%m/%d/')
    file_type = models.CharField('文件类型', max_length=20, choices=ATTACHMENT_TYPES, default='other')
    file_size = models.PositiveIntegerField('文件大小(字节)', default=0)
    mime_type = models.CharField('MIME类型', max_length=100, blank=True)
    description = models.TextField('描述', blank=True)

    # Generic foreign key fields for linking to any model
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = '附件'
        verbose_name_plural = '附件'
        db_table = 'core_attachment'

    def __str__(self):
        return self.name

    @property
    def file_size_display(self):
        """Return human readable file size."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"


class AuditLog(models.Model):
    """
    Audit log model for tracking user actions.
    """
    ACTION_TYPES = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('view', '查看'),
        ('login', '登录'),
        ('logout', '登出'),
        ('export', '导出'),
        ('import', '导入'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='用户'
    )
    action = models.CharField('操作类型', max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField('模型名称', max_length=100, blank=True)
    object_id = models.CharField('对象ID', max_length=100, blank=True)
    object_repr = models.CharField('对象描述', max_length=200, blank=True)
    changes = models.JSONField('变更内容', default=dict, blank=True)
    ip_address = models.GenericIPAddressField('IP地址', null=True, blank=True)
    user_agent = models.TextField('用户代理', blank=True)
    timestamp = models.DateTimeField('时间戳', auto_now_add=True)

    class Meta:
        verbose_name = '审计日志'
        verbose_name_plural = '审计日志'
        db_table = 'core_audit_log'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"


class DocumentNumberSequence(models.Model):
    """
    Document number sequence model for generating unique document numbers.

    This model stores the current sequence number for each document type and date.
    Used by DocumentNumberGenerator to generate unique document numbers.
    """
    prefix = models.CharField('单据前缀', max_length=10, db_index=True)
    date_str = models.CharField('日期字符串', max_length=8, db_index=True, help_text='格式: YYYYMMDD')
    current_number = models.PositiveIntegerField('当前序号', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '单据号序列'
        verbose_name_plural = '单据号序列'
        db_table = 'core_document_number_sequence'
        unique_together = [['prefix', 'date_str']]
        ordering = ['-date_str', 'prefix']

    def __str__(self):
        return f"{self.prefix}{self.date_str}: {self.current_number}"


class Notification(models.Model):
    """
    Notification model for system notifications.
    """
    NOTIFICATION_TYPES = [
        ('info', '信息'),
        ('success', '成功'),
        ('warning', '警告'),
        ('error', '错误'),
    ]

    NOTIFICATION_CATEGORIES = [
        ('sales_return', '销售退货'),
        ('sales_order', '销售订单'),
        ('purchase_order', '采购订单'),
        ('inventory', '库存'),
        ('finance', '财务'),
        ('system', '系统'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='接收人'
    )
    title = models.CharField('标题', max_length=200)
    message = models.TextField('消息内容')
    notification_type = models.CharField('通知类型', max_length=20, choices=NOTIFICATION_TYPES, default='info')
    category = models.CharField('分类', max_length=30, choices=NOTIFICATION_CATEGORIES, default='system')

    # Reference to related object
    reference_type = models.CharField('关联类型', max_length=50, blank=True)
    reference_id = models.CharField('关联ID', max_length=100, blank=True)
    reference_url = models.CharField('关联链接', max_length=500, blank=True)

    is_read = models.BooleanField('是否已读', default=False)
    read_at = models.DateTimeField('阅读时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '通知'
        verbose_name_plural = '通知'
        db_table = 'core_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['recipient', 'category', '-created_at']),
        ]

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    @classmethod
    def create_notification(cls, recipient, title, message, notification_type='info',
                          category='system', reference_type='', reference_id='', reference_url=''):
        """
        Create a new notification.

        Args:
            recipient: User to receive the notification
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, success, warning, error)
            category: Category of notification
            reference_type: Type of related object
            reference_id: ID of related object
            reference_url: URL to related object

        Returns:
            Created notification instance
        """
        return cls.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            category=category,
            reference_type=reference_type,
            reference_id=reference_id,
            reference_url=reference_url
        )


# ============================================
# Print Template Models (moved from sales module)
# ============================================
from .models_print_template import PrintTemplate
from .models_template_mapping import DefaultTemplateMapping

# ============================================
# Dynamic Choice Options (统一选项管理)
# ============================================
from .models_choice import ChoiceOption, ChoiceOptionGroup


# ============================================
# Platform Models (统一平台和店铺管理)
# ============================================
class Platform(BaseModel):
    """
    统一平台配置模型：采集平台+跨境平台+电商平台
    
    替代原来分散在collect.Platform和ecomm_sync.EcommPlatform的定义
    """
    PLATFORM_TYPES = (
        ('collect', '采集平台'),
        ('cross', '跨境平台'),
        ('ecommerce', '电商平台'),
    )
    
    PLATFORM_CODES = (
        ('taobao', '淘宝'),
        ('1688', '1688'),
        ('shopee', 'Shopee'),
        ('tiktok', 'TikTok'),
        ('shopify', 'Shopify'),
        ('amazon', 'Amazon'),
        ('ebay', 'eBay'),
        ('lazada', 'Lazada'),
        ('woocommerce', 'WooCommerce'),
    )
    
    # 基础信息
    platform_name = models.CharField('平台名称', max_length=100)
    platform_code = models.CharField('平台编码', max_length=20, unique=True, choices=PLATFORM_CODES)
    platform_type = models.CharField('平台类型', max_length=20, choices=PLATFORM_TYPES)
    
    # API配置（采集/跨境/电商通用）
    api_key = models.CharField('API Key', max_length=128, blank=True, help_text='平台API密钥')
    api_secret = models.CharField('API Secret', max_length=128, blank=True, help_text='平台API密钥')
    api_url = models.URLField('API网关地址', max_length=256, blank=True)
    api_version = models.CharField('API版本', max_length=16, blank=True)
    
    # OAuth配置（部分平台需要）
    auth_type = models.CharField('认证方式', max_length=20, blank=True, help_text='如：oauth2, basic等')
    access_token = models.TextField('访问令牌', blank=True)
    refresh_token = models.TextField('刷新令牌', blank=True)
    token_expires_at = models.DateTimeField('令牌过期时间', null=True, blank=True)
    
    # 平台配置（JSON存储，避免过多字段）
    platform_config = models.JSONField('平台配置', default=dict, blank=True, help_text='平台级别的配置信息')
    
    is_active = models.BooleanField('是否启用', default=True)
    description = models.TextField('描述', blank=True)
    
    class Meta:
        verbose_name = '平台配置'
        verbose_name_plural = '平台配置'
        db_table = 'core_platform'
        indexes = [
            models.Index(fields=['platform_code', 'platform_type', 'is_active']),
            models.Index(fields=['platform_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.platform_name} ({self.platform_code})"


class Shop(BaseModel):
    """
    统一店铺配置模型：跨境平台店铺+电商平台店铺
    
    替代原来分散在collect.Shop和ecomm_sync.WooShopConfig的定义
    """
    # 基础信息
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='shops', verbose_name='所属平台')
    shop_name = models.CharField('店铺名称', max_length=200)
    shop_code = models.CharField('店铺编码', max_length=100, blank=True)
    shop_id = models.CharField('平台店铺ID', max_length=100, blank=True, db_index=True)
    
    # 店铺配置（JSON存储，避免过多字段）
    shop_config = models.JSONField('店铺配置', default=dict, blank=True, help_text='店铺级别的配置信息')
    
    # 货币和地区
    currency = models.CharField('货币', max_length=10, default='CNY')
    country = models.CharField('国家/地区', max_length=50, blank=True)
    
    # API凭证（如果与平台不同）
    api_key = models.CharField('店铺API Key', max_length=128, blank=True)
    api_secret = models.CharField('店铺API Secret', max_length=128, blank=True)
    
    # OAuth配置
    access_token = models.TextField('访问令牌', blank=True)
    refresh_token = models.TextField('刷新令牌', blank=True)
    token_expires_at = models.DateTimeField('令牌过期时间', null=True, blank=True)
    
    is_active = models.BooleanField('是否启用', default=True)
    description = models.TextField('描述', blank=True)
    
    class Meta:
        verbose_name = '店铺配置'
        verbose_name_plural = '店铺配置'
        db_table = 'core_shop'
        indexes = [
            models.Index(fields=['platform', 'is_active']),
            models.Index(fields=['shop_id']),
        ]
    
    def __str__(self):
        return f"{self.shop_name} ({self.platform.platform_name})"
