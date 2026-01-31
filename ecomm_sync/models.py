from django.db import models
from django.core.validators import URLValidator
from core.models import BaseModel
from products.models import Product


class EcommPlatform(BaseModel):
    """电商平台配置"""

    PLATFORM_TYPES = [
        ('taobao', '淘宝'),
        ('alibaba', '1688'),
    ]

    platform_type = models.CharField('平台类型', max_length=20, choices=PLATFORM_TYPES)
    name = models.CharField('平台名称', max_length=100)
    base_url = models.URLField('基础URL')
    is_active = models.BooleanField('是否启用', default=True)
    description = models.TextField('描述', blank=True)

    class Meta:
        verbose_name = '电商平台'
        verbose_name_plural = '电商平台'
        db_table = 'ecomm_platform'

    def __str__(self):
        return self.name


class WooShopConfig(BaseModel):
    """WooCommerce店铺配置"""

    shop_url = models.URLField('店铺URL')
    shop_name = models.CharField('店铺名称', max_length=200, blank=True)
    consumer_key = models.CharField('Consumer Key', max_length=200)
    consumer_secret = models.CharField('Consumer Secret', max_length=200)
    is_active = models.BooleanField('是否启用', default=True)
    default_category_id = models.PositiveIntegerField('默认分类ID', null=True, blank=True, help_text='WooCommerce中的默认商品分类ID')

    class Meta:
        verbose_name = 'WooCommerce配置'
        verbose_name_plural = 'WooCommerce配置'
        db_table = 'ecomm_woo_shop'

    def __str__(self):
        return self.shop_name or self.shop_url


class EcommProduct(BaseModel):
    """采集的商品数据（原始数据）"""

    SYNC_STATUS_CHOICES = [
        ('pending', '待同步'),
        ('synced', '已同步'),
        ('failed', '同步失败'),
        ('delisted', '已下架'),
    ]

    platform = models.ForeignKey(EcommPlatform, on_delete=models.CASCADE, related_name='products', verbose_name='平台')
    external_id = models.CharField('平台商品ID', max_length=200, db_index=True)
    external_url = models.URLField('商品链接', max_length=1000)
    raw_data = models.JSONField('原始数据', default=dict, blank=True)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name='ecomm_records', verbose_name='关联产品')
    sync_status = models.CharField('同步状态', max_length=20, choices=SYNC_STATUS_CHOICES, default='pending')
    woo_product_id = models.PositiveIntegerField('WooCommerce产品ID', null=True, blank=True, help_text='WooCommerce中的产品ID')
    last_synced_at = models.DateTimeField('最后同步时间', null=True, blank=True)
    last_scraped_at = models.DateTimeField('最后采集时间', null=True, blank=True)
    is_delisted = models.BooleanField('是否下架', default=False, help_text='平台商品是否已下架')

    class Meta:
        verbose_name = '电商商品'
        verbose_name_plural = '电商商品'
        db_table = 'ecomm_product'
        unique_together = [['platform', 'external_id']]
        indexes = [
            models.Index(fields=['platform', 'sync_status']),
            models.Index(fields=['external_id']),
            models.Index(fields=['sync_status']),
        ]

    def __str__(self):
        return f"{self.platform.name} - {self.external_id}"


class SyncStrategy(BaseModel):
    """同步策略配置"""

    STRATEGY_TYPES = [
        ('full', '全量同步'),
        ('incremental', '增量同步'),
        ('price_only', '仅价格'),
    ]

    name = models.CharField('策略名称', max_length=100)
    strategy_type = models.CharField('策略类型', max_length=20, choices=STRATEGY_TYPES)
    platform = models.ForeignKey(EcommPlatform, on_delete=models.CASCADE, related_name='strategies', verbose_name='平台')

    update_fields = models.JSONField('更新字段', default=list, help_text='如：["price", "stock", "status"]')
    sync_interval_hours = models.PositiveIntegerField('同步间隔(小时)', default=24)
    last_sync_at = models.DateTimeField('最后同步时间', null=True, blank=True)
    next_sync_at = models.DateTimeField('下次同步时间', null=True, blank=True)
    batch_size = models.PositiveIntegerField('批量大小', default=100, help_text='每次同步的商品数量')
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        verbose_name = '同步策略'
        verbose_name_plural = '同步策略'
        db_table = 'ecomm_sync_strategy'

    def __str__(self):
        return f"{self.name} - {self.get_strategy_type_display()}"


class SyncLog(BaseModel):
    """同步日志"""

    LOG_TYPES = [
        ('scrape', '采集'),
        ('transform', '转换'),
        ('sync', '同步到WooCommerce'),
        ('incremental', '增量同步'),
        ('full_sync', '全量同步'),
    ]

    STATUS_CHOICES = [
        ('running', '运行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('partial', '部分成功'),
    ]

    log_type = models.CharField('日志类型', max_length=20, choices=LOG_TYPES)
    platform = models.ForeignKey(EcommPlatform, on_delete=models.SET_NULL, null=True, blank=True, related_name='sync_logs', verbose_name='平台')
    strategy = models.ForeignKey(SyncStrategy, on_delete=models.SET_NULL, null=True, blank=True, related_name='sync_logs', verbose_name='同步策略')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='running')
    records_processed = models.PositiveIntegerField('处理记录数', default=0)
    records_succeeded = models.PositiveIntegerField('成功记录数', default=0)
    records_failed = models.PositiveIntegerField('失败记录数', default=0)
    error_message = models.TextField('错误信息', blank=True)
    execution_time = models.FloatField('执行时间(秒)', default=0)
    details = models.JSONField('详细信息', default=dict, blank=True, help_text='存储同步过程中的详细信息')

    class Meta:
        verbose_name = '同步日志'
        verbose_name_plural = '同步日志'
        db_table = 'ecomm_sync_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'status']),
            models.Index(fields=['platform', '-created_at']),
        ]

    def __str__(self):
        return f"{self.get_log_type_display()} - {self.get_status_display()}"


class ProductChangeLog(BaseModel):
    """商品变更日志（用于增量更新检测）"""

    CHANGE_TYPES = [
        ('price', '价格变更'),
        ('stock', '库存变更'),
        ('status', '状态变更'),
        ('detail', '详情变更'),
        ('new', '新增商品'),
        ('delisted', '下架商品'),
    ]

    ecomm_product = models.ForeignKey(EcommProduct, on_delete=models.CASCADE, related_name='change_logs', verbose_name='电商商品')
    change_type = models.CharField('变更类型', max_length=20, choices=CHANGE_TYPES)
    old_value = models.JSONField('原值', null=True, blank=True)
    new_value = models.JSONField('新值', null=True, blank=True)
    synced_to_woo = models.BooleanField('已同步Woo', default=False)
    woo_synced_at = models.DateTimeField('Woo同步时间', null=True, blank=True)

    class Meta:
        verbose_name = '商品变更日志'
        verbose_name_plural = '商品变更日志'
        db_table = 'ecomm_product_change_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ecomm_product', '-created_at']),
            models.Index(fields=['change_type', '-created_at']),
            models.Index(fields=['synced_to_woo', '-created_at']),
        ]

    def __str__(self):
        return f"{self.ecomm_product} - {self.get_change_type_display()}"
