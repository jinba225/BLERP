from django.db import models
from django.core.validators import URLValidator
from core.models import BaseModel, Platform, Shop
from products.models import Product


class EcommProduct(BaseModel):
    """采集的商品数据（原始数据）"""

    SYNC_STATUS_CHOICES = [
        ('pending', '待同步'),
        ('synced', '已同步'),
        ('failed', '同步失败'),
        ('delisted', '已下架'),
    ]

    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='ecomm_products', verbose_name='平台')
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
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='strategies', verbose_name='平台')

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
    platform = models.ForeignKey(Platform, on_delete=models.SET_NULL, null=True, blank=True, related_name='sync_logs', verbose_name='平台')
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


class PlatformAccount(BaseModel):
    """平台账号（认证信息统一管理）"""

    ACCOUNT_TYPES = [
        ('amazon', 'Amazon'),
        ('ebay', 'eBay'),
        ('aliexpress', '速卖通'),
        ('lazada', 'Lazada'),
        ('woo', 'WooCommerce'),
        ('shopify', 'Shopify'),
    ]

    account_type = models.CharField('账号类型', max_length=20, choices=ACCOUNT_TYPES)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='accounts', verbose_name='平台')
    account_name = models.CharField('账号名称', max_length=200)
    platform_user_id = models.CharField('平台用户ID', max_length=200, blank=True)
    auth_config = models.JSONField('认证配置', default=dict, help_text='加密存储的认证信息')
    is_active = models.BooleanField('是否启用', default=True)
    token_expires_at = models.DateTimeField('Token过期时间', null=True, blank=True)
    rate_limit_remaining = models.IntegerField('剩余调用次数', default=0, help_text='平台API剩余调用次数')
    rate_limit_reset_at = models.DateTimeField('限流重置时间', null=True, blank=True)
    last_synced_at = models.DateTimeField('最后同步时间', null=True, blank=True)
    last_error = models.TextField('最后错误', blank=True)

    class Meta:
        verbose_name = '平台账号'
        verbose_name_plural = '平台账号'
        db_table = 'ecomm_platform_account'
        indexes = [
            models.Index(fields=['account_type', 'is_active']),
            models.Index(fields=['platform', 'is_active']),
            models.Index(fields=['-last_synced_at']),
        ]

    def __str__(self):
        return self.account_name


class PlatformOrder(BaseModel):
    """平台订单（支持多平台）"""

    ORDER_STATUS_CHOICES = [
        ('pending', '待付款'),
        ('paid', '已付款'),
        ('processing', '处理中'),
        ('shipped', '已发货'),
        ('delivered', '已送达'),
        ('cancelled', '已取消'),
        ('refunded', '已退款'),
    ]

    SYNC_STATUS_CHOICES = [
        ('pending', '待同步'),
        ('synced', '已同步'),
        ('syncing', '同步中'),
        ('failed', '同步失败'),
    ]

    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='orders', verbose_name='平台')
    account = models.ForeignKey(PlatformAccount, on_delete=models.SET_NULL, null=True, related_name='orders', verbose_name='账号')
    platform_order_id = models.CharField('平台订单号', max_length=200, db_index=True)
    order_status = models.CharField('订单状态', max_length=20, choices=ORDER_STATUS_CHOICES)
    order_amount = models.DecimalField('订单金额', max_digits=10, decimal_places=2)
    currency = models.CharField('货币', max_length=10, default='CNY')
    buyer_email = models.EmailField('买家邮箱', blank=True)
    buyer_name = models.CharField('买家姓名', max_length=200, blank=True)
    buyer_phone = models.CharField('买家电话', max_length=50, blank=True)
    shipping_address = models.JSONField('收货地址', default=dict, blank=True)
    raw_data = models.JSONField('原始数据', default=dict, blank=True)

    sync_status = models.CharField('同步状态', max_length=20, choices=SYNC_STATUS_CHOICES, default='pending')
    synced_to_erp = models.BooleanField('已同步到ERP', default=False)
    synced_to_platform = models.BooleanField('已同步到平台', default=True)
    erp_order_id = models.CharField('ERP订单ID', max_length=200, blank=True, db_index=True)
    tracking_number = models.CharField('快递单号', max_length=200, blank=True)
    sync_error = models.TextField('同步错误', blank=True)

    class Meta:
        verbose_name = '平台订单'
        verbose_name_plural = '平台订单'
        db_table = 'ecomm_platform_order'
        unique_together = [['platform', 'platform_order_id']]
        indexes = [
            models.Index(fields=['platform', 'order_status']),
            models.Index(fields=['platform', 'sync_status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['buyer_email']),
        ]

    def __str__(self):
        return f"{self.platform.name} - {self.platform_order_id}"


class PlatformOrderItem(BaseModel):
    """平台订单商品"""

    order = models.ForeignKey(PlatformOrder, on_delete=models.CASCADE, related_name='items', verbose_name='订单')
    sku = models.CharField('SKU', max_length=100, db_index=True)
    product_name = models.CharField('商品名称', max_length=500)
    quantity = models.IntegerField('数量')
    unit_price = models.DecimalField('单价', max_digits=10, decimal_places=2)
    total_price = models.DecimalField('总价', max_digits=10, decimal_places=2)
    platform_product_id = models.CharField('平台商品ID', max_length=200, blank=True)
    raw_data = models.JSONField('原始数据', default=dict, blank=True)

    class Meta:
        verbose_name = '平台订单商品'
        verbose_name_plural = '平台订单商品'
        db_table = 'ecomm_platform_order_item'
        indexes = [
            models.Index(fields=['order', 'sku']),
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        return f"{self.order.platform_order_id} - {self.sku}"


class ProductListing(BaseModel):
    """产品Listing（多平台商品映射）"""

    LISTING_STATUS_CHOICES = [
        ('onsale', '在售'),
        ('offshelf', '已下架'),
        ('pending', '待审核'),
        ('rejected', '已拒绝'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='listings', verbose_name='商品')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='listings', verbose_name='平台')
    account = models.ForeignKey(PlatformAccount, on_delete=models.CASCADE, related_name='listings', verbose_name='账号')

    platform_product_id = models.CharField('平台商品ID', max_length=200, db_index=True)
    platform_sku = models.CharField('平台SKU', max_length=200, blank=True)
    listing_title = models.CharField('Listing标题', max_length=500, blank=True)

    listing_status = models.CharField('Listing状态', max_length=20, choices=LISTING_STATUS_CHOICES)
    price = models.DecimalField('价格', max_digits=10, decimal_places=2)
    quantity = models.IntegerField('库存数量', default=0)

    woo_product_id = models.PositiveIntegerField('WooCommerce产品ID', null=True, blank=True)

    sync_enabled = models.BooleanField('启用同步', default=True)
    auto_update_price = models.BooleanField('自动更新价格', default=False)
    auto_update_stock = models.BooleanField('自动更新库存', default=True)

    last_synced_at = models.DateTimeField('最后同步时间', null=True, blank=True)
    sync_error = models.TextField('同步错误', blank=True)

    class Meta:
        verbose_name = '产品Listing'
        verbose_name_plural = '产品Listing'
        db_table = 'ecomm_product_listing'
        unique_together = [['platform', 'account', 'platform_product_id']]
        indexes = [
            models.Index(fields=['product', 'platform', 'listing_status']),
            models.Index(fields=['platform', 'account', 'listing_status']),
            models.Index(fields=['-last_synced_at']),
        ]

    def __str__(self):
        return f"{self.product.code} - {self.platform.name}"


class StockSyncQueue(BaseModel):
    """库存同步队列"""

    SYNC_TYPES = [
        ('push', '推送到平台'),
        ('pull', '从平台拉取'),
    ]

    SYNC_STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('success', '成功'),
        ('failed', '失败'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_sync_queues', verbose_name='商品')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name='stock_sync_queues', verbose_name='平台')
    account = models.ForeignKey(PlatformAccount, on_delete=models.CASCADE, related_name='stock_sync_queues', verbose_name='账号')

    sync_type = models.CharField('同步类型', max_length=20, choices=SYNC_TYPES)
    quantity = models.IntegerField('库存数量')
    status = models.CharField('状态', max_length=20, choices=SYNC_STATUS_CHOICES, default='pending')
    error_message = models.TextField('错误信息', blank=True)

    retry_count = models.IntegerField('重试次数', default=0)
    max_retries = models.IntegerField('最大重试次数', default=3)

    processed_at = models.DateTimeField('处理时间', null=True, blank=True)

    class Meta:
        verbose_name = '库存同步队列'
        verbose_name_plural = '库存同步队列'
        db_table = 'ecomm_stock_sync_queue'
        indexes = [
            models.Index(fields=['platform', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['sync_type', 'status']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.code} - {self.platform.name} - {self.get_status_display()}"


class APICallLog(BaseModel):
    """API调用日志"""

    account = models.ForeignKey(PlatformAccount, on_delete=models.SET_NULL, null=True, related_name='api_logs', verbose_name='账号')
    platform = models.ForeignKey(Platform, on_delete=models.SET_NULL, null=True, related_name='api_logs', verbose_name='平台')

    endpoint = models.CharField('API端点', max_length=500)
    method = models.CharField('HTTP方法', max_length=10, choices=[('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), ('DELETE', 'DELETE')])

    request_data = models.JSONField('请求数据', default=dict, blank=True)
    response_status = models.IntegerField('响应状态码', null=True, blank=True)
    response_data = models.JSONField('响应数据', default=dict, blank=True)

    execution_time = models.FloatField('执行时间(秒)', default=0)
    success = models.BooleanField('是否成功', default=True)
    error_message = models.TextField('错误信息', blank=True)

    class Meta:
        verbose_name = 'API调用日志'
        verbose_name_plural = 'API调用日志'
        db_table = 'ecomm_api_call_log'
        indexes = [
            models.Index(fields=['platform', 'account', '-created_at']),
            models.Index(fields=['success', '-created_at']),
            models.Index(fields=['response_status', '-created_at']),
            models.Index(fields=['endpoint']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.platform.name} - {self.method} - {self.endpoint}"
