"""
Purchase models for the ERP system.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from core.models import BaseModel, PAYMENT_METHOD_CHOICES
from django.utils import timezone

User = get_user_model()


class PurchaseOrder(BaseModel):
    """
    Purchase order model.
    """
    ORDER_STATUS = [
        ('draft', '草稿'),
        ('approved', '已审核'),
        ('partial_received', '部分收货'),
        ('fully_received', '全部收货'),
        ('invoiced', '已开票'),
        ('paid', '已付款'),
    ]

    PAYMENT_STATUS = [
        ('unpaid', '未付款'),
        ('partial', '部分付款'),
        ('paid', '已付款'),
        ('overdue', '逾期'),
    ]

    # Order information
    order_number = models.CharField('采购单号', max_length=100, unique=True)
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='purchase_orders',
        verbose_name='供应商'
    )
    status = models.CharField('订单状态', max_length=20, choices=ORDER_STATUS, default='draft')
    payment_status = models.CharField('付款状态', max_length=20, choices=PAYMENT_STATUS, default='unpaid')

    # Dates
    order_date = models.DateField('订单日期')
    required_date = models.DateField('要求交期', null=True, blank=True)
    promised_date = models.DateField('承诺交期', null=True, blank=True)
    received_date = models.DateField('收货日期', null=True, blank=True)

    # Purchase information
    buyer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders',
        verbose_name='采购员'
    )

    # Financial information
    subtotal = models.DecimalField('小计', max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField('税率(%)', max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField('税额', max_digits=12, decimal_places=2, default=0)
    discount_rate = models.DecimalField('折扣率(%)', max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField('折扣金额', max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField('运费', max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField('总金额', max_digits=12, decimal_places=2, default=0)
    currency = models.CharField('币种', max_length=10, default='CNY')

    # Delivery information
    delivery_address = models.TextField('收货地址', blank=True)
    delivery_contact = models.CharField('收货联系人', max_length=100, blank=True)
    delivery_phone = models.CharField('收货电话', max_length=20, blank=True)
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='收货仓库'
    )

    # Payment information
    payment_terms = models.CharField('付款方式', max_length=50, choices=PAYMENT_METHOD_CHOICES, blank=True)

    # Additional information
    reference_number = models.CharField('供应商订单号', max_length=100, blank=True)
    notes = models.TextField('备注', blank=True)
    internal_notes = models.TextField('内部备注', blank=True)

    # Platform integration - 平台集成
    platform = models.ForeignKey(
        'core.Platform',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders',
        verbose_name='电商平台'
    )
    platform_account = models.ForeignKey(
        'ecomm_sync.PlatformAccount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders',
        verbose_name='平台账号'
    )
    sync_to_platform = models.BooleanField('同步到平台', default=False,
                                      help_text='是否将采购商品同步到电商平台')
    platform_sync_status = models.CharField('平台同步状态', max_length=20,
                                          choices=[('pending', '待同步'), ('synced', '已同步'), ('syncing', '同步中'), ('failed', '同步失败')],
                                          default='pending',
                                          help_text='商品同步到电商平台的状态')
    last_synced_at = models.DateTimeField('最后同步时间', null=True, blank=True)
    sync_error = models.TextField('同步错误', blank=True)
    
    # Approval
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_purchase_orders',
        verbose_name='审核人'
    )
    approved_at = models.DateTimeField('审核时间', null=True, blank=True)

    class Meta:
        verbose_name = '采购订单'
        verbose_name_plural = '采购订单'
        db_table = 'purchase_order'
        ordering = ['-order_date', '-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.supplier.name if self.supplier else 'N/A'}"

    def approve_order(self, approved_by_user, warehouse=None, auto_create_receipt=True):
        """
        Approve the purchase order and optionally create receipt.

        注意：应付账款不再自动生成，需要在订单完成后手动申请付款。

        Args:
            approved_by_user: User who approves the order
            warehouse: Warehouse for receiving goods (optional)
            auto_create_receipt: Whether to automatically create receipt (default True)

        Returns:
            PurchaseReceipt or None: 如果 auto_create_receipt=True 返回收货单，否则返回 None
        """
        from core.utils.document_number import DocumentNumberGenerator

        if self.status != 'draft':
            raise ValueError('只有草稿状态的采购订单才能审核')

        # 验证所有明细是否都有单价
        for item in self.items.filter(is_deleted=False):
            if not item.unit_price or item.unit_price <= 0:
                raise ValueError(f'产品【{item.product.name}】必须确认单价才能审核通过')

        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()

        receipt = None
        if auto_create_receipt:
            # 获取仓库，如果都没有指定则使用主仓库
            receipt_warehouse = warehouse or self.warehouse
            if not receipt_warehouse:
                from inventory.models import Warehouse
                try:
                    receipt_warehouse = Warehouse.objects.filter(
                        warehouse_type='main',
                        is_active=True,
                        is_deleted=False
                    ).first()
                    if not receipt_warehouse:
                        # 如果没有主仓库，使用第一个可用仓库
                        receipt_warehouse = Warehouse.objects.filter(
                            is_active=True,
                            is_deleted=False
                        ).first()
                except:
                    pass

            # Create receipt
            receipt = PurchaseReceipt.objects.create(
                receipt_number=DocumentNumberGenerator.generate('receipt'),  # 使用 IN 前缀
                purchase_order=self,
                warehouse=receipt_warehouse,
                receipt_date=timezone.now().date(),
                status='pending',
                created_by=approved_by_user
            )

            # Create receipt items from order items
            for order_item in self.items.filter(is_deleted=False):
                PurchaseReceiptItem.objects.create(
                    receipt=receipt,
                    order_item=order_item,
                    received_quantity=0,
                    created_by=approved_by_user
                )

        return receipt

    def calculate_totals(self):
        """
        Calculate order totals from line items.
        """
        from decimal import Decimal

        # Calculate subtotal from all items
        self.subtotal = sum(
            item.line_total for item in self.items.filter(is_deleted=False)
        ) or Decimal('0')

        # Calculate tax amount
        if self.tax_rate > 0:
            self.tax_amount = self.subtotal * (self.tax_rate / 100)
        else:
            self.tax_amount = Decimal('0')

        # Calculate total amount (subtotal + tax + shipping - discount)
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount


class PurchaseOrderItem(BaseModel):
    """
    Purchase order item model.
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='采购订单'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        verbose_name='产品'
    )

    # Quantity and pricing
    quantity = models.IntegerField('数量', validators=[MinValueValidator(0)])
    unit_price = models.DecimalField('单价', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_rate = models.DecimalField('折扣率(%)', max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField('折扣金额', max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField('行总计', max_digits=12, decimal_places=2, default=0)

    # Additional information
    required_date = models.DateField('要求交期', null=True, blank=True)
    specifications = models.TextField('规格要求', blank=True)
    notes = models.TextField('备注', blank=True)
    sort_order = models.PositiveIntegerField('排序', default=0)

    # Delivery tracking
    received_quantity = models.IntegerField('已收货数量', default=0)

    class Meta:
        verbose_name = '采购订单明细'
        verbose_name_plural = '采购订单明细'
        db_table = 'purchase_order_item'
        ordering = ['id']

    def __str__(self):
        return f"{self.purchase_order.order_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        # Calculate line_total (quantity * unit_price - discount_amount)
        subtotal = self.quantity * self.unit_price
        self.line_total = subtotal - self.discount_amount
        super().save(*args, **kwargs)


class PurchaseRequest(BaseModel):
    """
    Purchase request model - 采购申请单.
    """
    REQUEST_STATUS = [
        ('draft', '草稿'),
        ('approved', '已审核'),
    ]

    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]

    request_number = models.CharField('申请单号', max_length=100, unique=True)
    requester = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchase_requests',
        verbose_name='申请人'
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='申请部门'
    )

    status = models.CharField('状态', max_length=20, choices=REQUEST_STATUS, default='draft')
    priority = models.CharField('优先级', max_length=20, choices=PRIORITY_CHOICES, default='normal')
    request_date = models.DateField('申请日期')
    required_date = models.DateField('需求日期', null=True, blank=True)

    purpose = models.TextField('采购目的', blank=True)
    justification = models.TextField('申请理由', blank=True)
    estimated_total = models.DecimalField('预估总额', max_digits=12, decimal_places=2, default=0)
    budget_code = models.CharField('预算科目', max_length=100, blank=True)

    notes = models.TextField('备注', blank=True)
    rejection_reason = models.TextField('拒绝原因', blank=True)

    # Approval
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_purchase_requests',
        verbose_name='审核人'
    )
    approved_at = models.DateTimeField('审核时间', null=True, blank=True)

    # Link to created order
    converted_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_request',
        verbose_name='转换的采购订单'
    )

    class Meta:
        verbose_name = '采购申请'
        verbose_name_plural = '采购申请'
        db_table = 'purchase_request'
        ordering = ['-request_date', '-created_at']

    def __str__(self):
        return f"{self.request_number} - {self.requester.get_full_name() if self.requester else 'N/A'}"

    def approve_and_convert_to_order(self, approved_by_user, supplier_id, warehouse_id=None, auto_create_order=None):
        """
        Approve the purchase request and automatically convert to purchase order.

        Args:
            approved_by_user: User who approved the request
            supplier_id: Supplier ID for the purchase order
            warehouse_id: Optional warehouse ID for the purchase order
            auto_create_order: Whether to auto-create order (if None, check system config)

        Returns:
            tuple: (PurchaseOrder or None, success_message)

        Raises:
            ValueError: If validation fails
        """
        from core.models import SystemConfig
        from core.utils import DocumentNumberGenerator

        # Validation
        if self.approved_by:
            raise ValueError('采购申请单已经审核过了')

        if self.status != 'draft':
            raise ValueError('只有草稿状态的采购申请单才能审核')

        if not self.items.exists():
            raise ValueError('采购申请单没有明细，无法审核')

        # Check if auto-create order
        if auto_create_order is None:
            config = SystemConfig.objects.filter(
                key='purchase_auto_create_order_on_approve',
                is_active=True
            ).first()
            auto_create_order = config.value.lower() == 'true' if config else True

        # Update approval info
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.status = 'approved'
        self.save()

        # If not auto-create, return early
        if not auto_create_order:
            return (None, '采购申请单审核通过')

        # Auto-create purchase order
        order = PurchaseOrder.objects.create(
            order_number=DocumentNumberGenerator.generate('purchase_order'),
            supplier_id=supplier_id,
            order_date=timezone.now().date(),
            required_date=self.required_date,
            buyer=approved_by_user,
            warehouse_id=warehouse_id,
            reference_number=self.request_number,
            notes=f'由采购申请单 {self.request_number} 自动转换\n申请用途：{self.purpose}',
            internal_notes=(
                f'申请部门：{self.department.name if self.department else "无"}\n'
                f'申请人：{self.requester.get_full_name() if self.requester else "无"}\n'
                f'申请理由：{self.justification}'
            ),
            created_by=approved_by_user,
            status='draft',  # 新订单为草稿状态
        )

        # Copy request items to order items
        for request_item in self.items.filter(is_deleted=False):
            PurchaseOrderItem.objects.create(
                purchase_order=order,
                product=request_item.product,
                quantity=request_item.quantity,
                unit_price=request_item.estimated_price or 0,
                notes=request_item.notes,
                sort_order=request_item.sort_order,
                created_by=approved_by_user,
            )

        # Calculate totals
        order.calculate_totals()
        order.save()

        # Update request link (status already set to 'approved')
        self.converted_order = order
        self.save()

        return (order, f'采购申请单审核通过，已自动生成采购订单 {order.order_number}')


class PurchaseRequestItem(BaseModel):
    """
    Purchase request item model.
    """
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='采购申请'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        verbose_name='产品'
    )

    quantity = models.IntegerField('申请数量', validators=[MinValueValidator(0)])
    estimated_price = models.DecimalField('预估单价', max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_total = models.DecimalField('预估总价', max_digits=12, decimal_places=2, default=0)

    preferred_supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='首选供应商'
    )

    specifications = models.TextField('规格要求', blank=True)
    notes = models.TextField('备注', blank=True)
    sort_order = models.PositiveIntegerField('排序', default=0)

    class Meta:
        verbose_name = '采购申请明细'
        verbose_name_plural = '采购申请明细'
        db_table = 'purchase_request_item'
        ordering = ['id']

    def __str__(self):
        return f"{self.purchase_request.request_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        # Calculate estimated_total
        if self.quantity and self.estimated_price:
            self.estimated_total = self.quantity * self.estimated_price
        else:
            self.estimated_total = 0
        super().save(*args, **kwargs)


class PurchaseInquiry(BaseModel):
    """
    Purchase inquiry (RFQ) model - 采购询价单.
    """
    INQUIRY_STATUS = [
        ('draft', '草稿'),
        ('sent', '已发送'),
        ('quoted', '已报价'),
        ('selected', '已选定'),
        ('ordered', '已转订单'),
        ('cancelled', '已取消'),
    ]

    inquiry_number = models.CharField('询价单号', max_length=100, unique=True)
    inquiry_date = models.DateField('询价日期')
    required_date = models.DateField('需求日期', null=True, blank=True)

    buyer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchase_inquiries',
        verbose_name='采购员'
    )

    status = models.CharField('状态', max_length=20, choices=INQUIRY_STATUS, default='draft')

    # Link to suppliers
    suppliers = models.ManyToManyField(
        'suppliers.Supplier',
        related_name='purchase_inquiries',
        verbose_name='询价供应商'
    )

    # Selected quotation
    selected_quotation = models.ForeignKey(
        'SupplierQuotation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='selected_inquiry',
        verbose_name='选定报价'
    )

    # Link to created order
    converted_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_inquiry',
        verbose_name='转换的采购订单'
    )

    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '采购询价单'
        verbose_name_plural = '采购询价单'
        db_table = 'purchase_inquiry'
        ordering = ['-inquiry_date', '-created_at']

    def __str__(self):
        return f"{self.inquiry_number} - {self.inquiry_date}"


class PurchaseInquiryItem(BaseModel):
    """
    Purchase inquiry item model.
    """
    inquiry = models.ForeignKey(
        PurchaseInquiry,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='询价单'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        verbose_name='产品'
    )

    quantity = models.IntegerField('询价数量', validators=[MinValueValidator(0)])
    target_price = models.DecimalField('目标价格', max_digits=10, decimal_places=2, null=True, blank=True)

    specifications = models.TextField('规格要求', blank=True)
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '询价单明细'
        verbose_name_plural = '询价单明细'
        db_table = 'purchase_inquiry_item'
        ordering = ['id']

    def __str__(self):
        return f"{self.inquiry.inquiry_number} - {self.product.name}"


class SupplierQuotation(BaseModel):
    """
    Supplier quotation model - 供应商报价单.
    """
    QUOTATION_STATUS = [
        ('pending', '待报价'),
        ('submitted', '已提交'),
        ('selected', '已选定'),
        ('rejected', '已拒绝'),
    ]

    quotation_number = models.CharField('报价单号', max_length=100, unique=True)
    inquiry = models.ForeignKey(
        PurchaseInquiry,
        on_delete=models.CASCADE,
        related_name='quotations',
        verbose_name='询价单'
    )
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.CASCADE,
        related_name='quotations',
        verbose_name='供应商'
    )

    quotation_date = models.DateField('报价日期', null=True, blank=True)
    valid_until = models.DateField('有效期至', null=True, blank=True)

    status = models.CharField('状态', max_length=20, choices=QUOTATION_STATUS, default='pending')

    # Total amount
    total_amount = models.DecimalField('报价总额', max_digits=12, decimal_places=2, default=0)

    # Terms
    payment_terms = models.CharField('付款条款', max_length=200, blank=True)
    delivery_terms = models.CharField('交货条款', max_length=200, blank=True)
    delivery_date = models.DateField('承诺交期', null=True, blank=True)

    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '供应商报价'
        verbose_name_plural = '供应商报价'
        db_table = 'supplier_quotation'
        ordering = ['-quotation_date', '-created_at']

    def __str__(self):
        return f"{self.quotation_number} - {self.supplier.name}"


class SupplierQuotationItem(BaseModel):
    """
    Supplier quotation item model.
    """
    quotation = models.ForeignKey(
        SupplierQuotation,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='报价单'
    )
    inquiry_item = models.ForeignKey(
        PurchaseInquiryItem,
        on_delete=models.CASCADE,
        verbose_name='询价明细'
    )

    unit_price = models.DecimalField('报价单价', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity = models.IntegerField('报价数量', validators=[MinValueValidator(0)])
    subtotal = models.DecimalField('小计', max_digits=12, decimal_places=2, default=0)

    delivery_date = models.DateField('交货日期', null=True, blank=True)
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '报价单明细'
        verbose_name_plural = '报价单明细'
        db_table = 'supplier_quotation_item'
        ordering = ['id']

    def __str__(self):
        return f"{self.quotation.quotation_number} - {self.inquiry_item.product.name}"

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class PurchaseReceipt(BaseModel):
    """
    Purchase receipt model - 采购收货单.
    """
    RECEIPT_STATUS = [
        ('pending', '待收货'),
        ('partial', '部分收货'),
        ('received', '已收货'),
    ]

    receipt_number = models.CharField('收货单号', max_length=100, unique=True)
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='receipts',
        verbose_name='采购订单'
    )
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='收货仓库'
    )

    receipt_date = models.DateField('收货日期')
    status = models.CharField('状态', max_length=20, choices=RECEIPT_STATUS, default='pending')

    # Delivery info
    delivery_note = models.CharField('送货单号', max_length=100, blank=True)
    carrier = models.CharField('承运商', max_length=100, blank=True)
    vehicle_number = models.CharField('车牌号', max_length=20, blank=True)
    driver_name = models.CharField('司机姓名', max_length=100, blank=True)
    driver_phone = models.CharField('司机电话', max_length=20, blank=True)

    notes = models.TextField('备注', blank=True)

    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_receipts',
        verbose_name='收货人'
    )

    @property
    def supplier(self):
        """通过采购订单获取供应商"""
        return self.purchase_order.supplier if self.purchase_order else None

    class Meta:
        verbose_name = '采购收货单'
        verbose_name_plural = '采购收货单'
        db_table = 'purchase_receipt'
        ordering = ['-receipt_date', '-created_at']

    def __str__(self):
        return f"{self.receipt_number} - {self.supplier.name}"


class PurchaseReceiptItem(BaseModel):
    """
    Purchase receipt item model.
    """
    receipt = models.ForeignKey(
        PurchaseReceipt,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='收货单'
    )
    order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.CASCADE,
        verbose_name='订单明细'
    )

    received_quantity = models.IntegerField('收货数量', default=0)

    batch_number = models.CharField('批次号', max_length=100, blank=True)
    serial_numbers = models.TextField('序列号', blank=True)
    expiry_date = models.DateField('过期日期', null=True, blank=True)
    notes = models.TextField('备注', blank=True)
    location = models.ForeignKey(
        'inventory.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='存放位置'
    )

    class Meta:
        verbose_name = '收货单明细'
        verbose_name_plural = '收货单明细'
        db_table = 'purchase_receipt_item'
        ordering = ['id']

    def __str__(self):
        return f"{self.receipt.receipt_number} - {self.order_item.product.name}"


class PurchaseReturn(BaseModel):
    """
    Purchase return model - 采购退货单.
    """
    RETURN_STATUS = [
        ('draft', '草稿'),
        ('pending', '待审核'),
        ('approved', '已审核'),
        ('returned', '已退货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    RETURN_REASON = [
        ('quality', '质量问题'),
        ('quantity', '数量不符'),
        ('damage', '货物损坏'),
        ('specification', '规格不符'),
        ('other', '其他原因'),
    ]

    return_number = models.CharField('退货单号', max_length=100, unique=True)
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='returns',
        verbose_name='采购订单'
    )
    receipt = models.ForeignKey(
        PurchaseReceipt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returns',
        verbose_name='收货单'
    )

    return_date = models.DateField('退货日期')
    shipped_date = models.DateField('发货日期', null=True, blank=True)
    status = models.CharField('状态', max_length=20, choices=RETURN_STATUS, default='draft')
    reason = models.CharField('退货原因', max_length=20, choices=RETURN_REASON)

    refund_amount = models.DecimalField('退款金额', max_digits=12, decimal_places=2, default=0)

    notes = models.TextField('备注', blank=True)

    # Approval
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_purchase_returns',
        verbose_name='审核人'
    )
    approved_at = models.DateTimeField('审核时间', null=True, blank=True)

    class Meta:
        verbose_name = '采购退货单'
        verbose_name_plural = '采购退货单'
        db_table = 'purchase_return'
        ordering = ['-return_date', '-created_at']

    def __str__(self):
        return f"{self.return_number} - {self.supplier.name if self.supplier else 'N/A'}"

    @property
    def supplier(self):
        """通过采购订单获取供应商"""
        return self.purchase_order.supplier if self.purchase_order else None


class PurchaseReturnItem(BaseModel):
    """
    Purchase return item model.
    """
    purchase_return = models.ForeignKey(
        PurchaseReturn,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='退货单'
    )
    order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.CASCADE,
        verbose_name='订单明细'
    )

    quantity = models.IntegerField('退货数量', validators=[MinValueValidator(0)])
    unit_price = models.DecimalField('单价', max_digits=10, decimal_places=2)
    line_total = models.DecimalField('行总计', max_digits=12, decimal_places=2, default=0)

    condition = models.CharField('货物状态', max_length=100, blank=True)
    batch_number = models.CharField('批次号', max_length=100, blank=True)
    serial_numbers = models.TextField('序列号', blank=True)
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '退货单明细'
        verbose_name_plural = '退货单明细'
        db_table = 'purchase_return_item'
        ordering = ['id']

    def __str__(self):
        return f"{self.purchase_return.return_number} - {self.product.name if self.product else 'N/A'}"

    @property
    def product(self):
        """通过订单明细获取产品"""
        return self.order_item.product if self.order_item else None

    def save(self, *args, **kwargs):
        # Calculate line_total
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)




class Borrow(BaseModel):
    """
    采购借用单 - 简化状态管理
    """
    BORROW_STATUS = [
        ('draft', '草稿'),
        ('approved', '已审核'),
        ('borrowed', '借用中'),
        ('completed', '已完成'),
    ]

    # 基本信息
    borrow_number = models.CharField('借用单号', max_length=100, unique=True)
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.CASCADE,
        related_name='borrows',
        verbose_name='供应商'
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='borrows_as_buyer',
        verbose_name='经办人'
    )

    # 状态管理（简化版）
    status = models.CharField('状态', max_length=20, choices=BORROW_STATUS, default='draft')

    # 审核信息
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_borrows',
        verbose_name='审核人'
    )
    approved_at = models.DateTimeField('审核时间', null=True, blank=True)

    # 日期管理（不需要逾期相关）
    borrow_date = models.DateField('借用日期')
    expected_return_date = models.DateField('预计归还日期', null=True, blank=True)

    # 转采购关联
    converted_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_borrow',
        verbose_name='转换的采购订单'
    )

    # 转采购审核信息
    conversion_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_borrow_conversions',
        verbose_name='转采购审核人'
    )
    conversion_approved_at = models.DateTimeField('转采购审核时间', null=True, blank=True)
    conversion_notes = models.TextField('转采购备注', blank=True)

    # 备注
    purpose = models.TextField('借用目的', blank=True)
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '采购借用单'
        verbose_name_plural = '采购借用单'
        db_table = 'purchase_borrow'
        ordering = ['-borrow_date', '-created_at']

    def __str__(self):
        return f"{self.borrow_number} - {self.supplier.name}"

    @property
    def total_borrowed_quantity(self):
        """总借用数量"""
        return sum(item.quantity for item in self.items.filter(is_deleted=False))

    @property
    def total_returned_quantity(self):
        """总归还数量"""
        return sum(item.returned_quantity for item in self.items.filter(is_deleted=False))

    @property
    def total_remaining_quantity(self):
        """总剩余数量（可转采购）"""
        return sum(item.remaining_quantity for item in self.items.filter(is_deleted=False))

    @property
    def is_fully_returned(self):
        """是否全部归还"""
        return self.total_remaining_quantity == 0

    @property
    def converted_orders(self):
        """
        获取所有由该借用单转换而来的采购订单

        Returns:
            QuerySet: 关联的采购订单列表
        """
        from .models import PurchaseOrder  # 避免循环导入
        return PurchaseOrder.objects.filter(
            notes__contains=self.borrow_number,
            is_deleted=False
        ).order_by('created_at')

    def approve_borrow(self, approved_by_user):
        """
        审核借用单（提交即审核，但不入库）

        审核通过后等待借用入库确认

        Args:
            approved_by_user: 审核人
        """
        if self.status != 'draft':
            raise ValueError('只有草稿状态的借用单才能审核')

        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()

    def confirm_borrow_receipt(self, user, items_to_receive=None):
        """
        借用入库确认（审核通过后才能入库）

        核心逻辑：
        1. 订单.累计已借用数量 += 本次借用数量
        2. 借用仓库存 += 本次借用数量（入库）
        3. 状态更新为 borrowed

        Args:
            user: 操作人
            items_to_receive: 本次入库的明细列表 [{'item_id': 1, 'quantity': 10}, ...]
                            如果为None，则全部入库
        """
        from inventory.models import Warehouse, InventoryTransaction

        if self.status not in ['approved', 'borrowed']:
            raise ValueError('只有已审核或借用中状态的借用单才能确认入库')

        # 获取借用仓
        try:
            borrow_warehouse = Warehouse.get_borrow_warehouse()
        except Warehouse.DoesNotExist:
            raise ValueError('借用仓不存在，请先创建借用仓')

        # 如果没有指定入库明细，则全部入库
        if items_to_receive is None:
            items_to_receive = [
                {'item_id': item.id, 'quantity': item.quantity - item.borrowed_quantity}
                for item in self.items.filter(is_deleted=False)
            ]

        # 处理每个明细的入库
        for data in items_to_receive:
            item = self.items.get(pk=data['item_id'])
            receive_qty = data['quantity']

            # 验证入库数量
            if receive_qty > item.borrowable_quantity:
                raise ValueError(
                    f'产品 {item.product.name} 的入库数量 {receive_qty} '
                    f'不能超过剩余可借用数量 {item.borrowable_quantity}'
                )

            # 更新累计已借用数量
            item.borrowed_quantity += receive_qty
            item.updated_by = user
            item.save()

            # 创建入库记录，入库到借用仓
            InventoryTransaction.objects.create(
                transaction_type='in',
                product=item.product,
                warehouse=borrow_warehouse,
                quantity=receive_qty,  # 正数表示入库
                reference_number=self.borrow_number,
                notes=f'采购借用单 {self.borrow_number} 借用入库',
                operator=user
            )

        # 更新借用单状态
        if self.status != 'borrowed':
            self.status = 'borrowed'
            self.updated_by = user
            self.save()

    # approve_conversion 方法已删除 - 转采购无需审核，直接在视图中生成订单

    def process_return(self, user, returned_items_data):
        """
        处理归还（支持部分归还）

        核心逻辑：
        1. 订单.累计已借用数量 -= 本次归还数量
        2. 借用仓库存 -= 本次归还数量（出库）
        3. 订单.已归还数量 += 本次归还数量

        Args:
            user: 处理人
            returned_items_data: 归还数据列表 [{'item_id': 1, 'quantity': 10}, ...]
        """
        from decimal import Decimal
        from inventory.models import Warehouse, InventoryTransaction

        if self.status != 'borrowed':
            raise ValueError('只有借用中状态的借用单才能处理归还')

        # 获取借用仓
        try:
            borrow_warehouse = Warehouse.get_borrow_warehouse()
        except Warehouse.DoesNotExist:
            raise ValueError('借用仓不存在，请先创建借用仓')

        for data in returned_items_data:
            item = self.items.get(pk=data['item_id'])
            return_qty = Decimal(str(data['quantity']))

            if return_qty > item.remaining_quantity:
                raise ValueError(f'产品 {item.product.name} 的归还数量不能超过剩余数量')

            # 核心逻辑：减少累计已借用数量
            item.borrowed_quantity -= return_qty
            # 增加已归还数量（用于记录）
            item.returned_quantity += return_qty
            item.updated_by = user
            item.save()

            # 创建出库记录，从借用仓出库
            InventoryTransaction.objects.create(
                transaction_type='out',
                product=item.product,
                warehouse=borrow_warehouse,
                quantity=-return_qty,  # 负数表示出库
                reference_number=self.borrow_number,
                notes=f'采购借用单 {self.borrow_number} 归还出库',
                operator=user
            )

        # 检查是否全部归还完毕
        if self.total_remaining_quantity == 0:
            self.status = 'completed'

        self.updated_by = user
        self.save()

    def convert_to_order(self, user, supplier_id, items_with_price, warehouse_id=None):
        """
        直接转采购订单（无需审核，简化流程）

        Args:
            user: 操作人
            supplier_id: 供应商ID
            items_with_price: 转换数据列表 [{'item_id': 1, 'quantity': 5, 'unit_price': 100}, ...]
            warehouse_id: 仓库ID（可选）

        Returns:
            PurchaseOrder: 生成的采购订单
        """
        from decimal import Decimal
        from core.utils.document_number import DocumentNumberGenerator
        from inventory.models import Warehouse

        if self.status != 'borrowed':
            raise ValueError('只有借用中状态的借用单才能转采购')

        if self.total_remaining_quantity == 0:
            raise ValueError('没有剩余数量可转采购')

        # 获取目标仓库（主仓）- 用于订单关联，不进行库存调拨
        if warehouse_id:
            from django.shortcuts import get_object_or_404
            target_warehouse = get_object_or_404(Warehouse, pk=warehouse_id, is_active=True, is_deleted=False)
        else:
            # 如果没有指定仓库，查找第一个主仓
            target_warehouse = Warehouse.objects.filter(
                warehouse_type='main',
                is_active=True,
                is_deleted=False
            ).first()
            if not target_warehouse:
                raise ValueError('找不到主仓，请先创建主仓或指定目标仓库')

        # 验证并更新明细（不进行库存调拨，调拨将在收货时进行）
        for data in items_with_price:
            item = self.items.get(pk=data['item_id'])
            convert_qty = Decimal(str(data['quantity']))
            unit_price = Decimal(str(data['unit_price']))

            if convert_qty > item.remaining_quantity:
                raise ValueError(f'产品 {item.product.name} 的转换数量不能超过剩余数量')
            if unit_price <= 0:
                raise ValueError('单价必须大于0')

            # 增加转采购数量
            item.conversion_quantity += convert_qty
            item.conversion_unit_price = unit_price
            # 减少累计已借用数量（转采购的部分不再归还）
            item.borrowed_quantity -= convert_qty
            item.updated_by = user
            item.save()

        # 创建采购订单
        order = PurchaseOrder.objects.create(
            order_number=DocumentNumberGenerator.generate('purchase_order'),
            supplier_id=supplier_id,
            buyer=self.buyer,
            order_date=timezone.now().date(),
            warehouse=target_warehouse,  # 使用目标仓库（主仓）
            status='draft',  # 草稿状态，需要审核
            notes=f'由借用单 {self.borrow_number} 转换而来\n{self.purpose}',
            created_by=user
        )

        # 创建订单明细
        total = Decimal('0')
        for data in items_with_price:
            item = self.items.get(pk=data['item_id'])
            convert_qty = Decimal(str(data['quantity']))
            unit_price = Decimal(str(data['unit_price']))

            # 合并规格和转换说明到notes
            notes_text = f'从借用单 {self.borrow_number} 转换'
            if item.specifications:
                notes_text = f'{notes_text}\n规格要求: {item.specifications}'

            order_item = PurchaseOrderItem.objects.create(
                purchase_order=order,
                product=item.product,
                quantity=convert_qty,
                unit_price=unit_price,
                notes=notes_text,
                created_by=user
            )
            total += order_item.line_total

        # 更新订单总金额
        order.total_amount = total
        order.subtotal = total
        order.save()

        # ========== 生成应付明细（正应付）==========
        from finance.models import SupplierAccount, SupplierAccountDetail

        # 获取或创建应付主单
        parent_account = SupplierAccount.get_or_create_for_order(order)

        # 为每个转采购明细生成应付明细
        for data in items_with_price:
            item = self.items.get(pk=data['item_id'])
            convert_qty = Decimal(str(data['quantity']))
            unit_price = Decimal(str(data['unit_price']))

            # 计算应付金额
            detail_amount = convert_qty * unit_price

            # 创建应付明细
            SupplierAccountDetail.objects.create(
                detail_number=DocumentNumberGenerator.generate('account_detail'),
                detail_type='receipt',  # 转采购视为收货正应付
                supplier_id=supplier_id,
                purchase_order=order,
                amount=detail_amount,
                allocated_amount=Decimal('0'),
                parent_account=parent_account,
                business_date=timezone.now().date(),
                notes=f'借用单 {self.borrow_number} 转采购，产品：{item.product.name}',
                created_by=user
            )

        # 自动归集应付主单
        parent_account.aggregate_from_details()

        # 更新借用单关联
        self.converted_order = order
        self.updated_by = user
        self.save()

        return order


class BorrowItem(BaseModel):
    """
    借用明细
    """
    borrow = models.ForeignKey(
        Borrow,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='借用单'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        verbose_name='产品'
    )

    # 数量管理
    quantity = models.IntegerField('借用数量', validators=[MinValueValidator(0)])
    borrowed_quantity = models.IntegerField(
        '累计已借用数量',
        default=0,
        help_text='借用入库确认时累计的已借用数量（用于归还和转采购限制）'
    )
    returned_quantity = models.IntegerField('已归还数量', default=0)

    # 物料追踪
    batch_number = models.CharField('批次号', max_length=100, blank=True)
    serial_numbers = models.TextField('序列号', blank=True, help_text='多个序列号用换行分隔')

    # 转采购时的定价（手动输入）
    conversion_unit_price = models.DecimalField(
        '转采购单价',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='转采购时手动输入的含税单价'
    )
    conversion_quantity = models.IntegerField(
        '转采购数量',
        default=0,
        help_text='已转采购的数量'
    )

    specifications = models.TextField('规格要求', blank=True)
    notes = models.TextField('备注', blank=True)
    sort_order = models.PositiveIntegerField('排序', default=0)

    class Meta:
        verbose_name = '借用明细'
        verbose_name_plural = '借用明细'
        db_table = 'purchase_borrow_item'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.borrow.borrow_number} - {self.product.name}"

    @property
    def borrowable_quantity(self):
        """剩余可借用数量 = 订单总采购量 - 累计已借用"""
        return max(0, self.quantity - self.borrowed_quantity)

    @property
    def remaining_quantity(self):
        """剩余未归还数量（可转采购）= 累计已借用 - 已归还 - 已转采购"""
        return max(0, self.borrowed_quantity - self.returned_quantity - self.conversion_quantity)

    @property
    def can_convert(self):
        """是否可转采购"""
        return self.remaining_quantity > 0

    @property
    def can_return(self):
        """是否可归还"""
        return self.remaining_quantity > 0


class PurchaseOrderItemPlatformMap(BaseModel):
    """
    采购订单商品与平台商品关联模型
    
    用于将采购订单中的商品与电商平台上的商品建立关联关系，
    以便支持采购商品自动同步到电商平台
    """
    
    SYNC_STATUS_CHOICES = [
        ('pending', '待同步'),
        ('synced', '已同步'),
        ('syncing', '同步中'),
        ('failed', '同步失败'),
    ]
    
    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.CASCADE,
        related_name='platform_maps',
        verbose_name='采购订单商品'
    )
    platform = models.ForeignKey(
        'core.Platform',
        on_delete=models.CASCADE,
        related_name='purchase_platform_maps',
        verbose_name='电商平台'
    )
    platform_account = models.ForeignKey(
        'ecomm_sync.PlatformAccount',
        on_delete=models.CASCADE,
        related_name='purchase_platform_maps',
        verbose_name='平台账号'
    )
    platform_product_id = models.CharField(
        '平台商品ID',
        max_length=200,
        db_index=True,
        help_text='电商平台上的商品ID'
    )
    platform_sku = models.CharField(
        '平台SKU',
        max_length=200,
        blank=True,
        help_text='电商平台上的SKU'
    )
    sync_enabled = models.BooleanField(
        '启用同步',
        default=True,
        help_text='是否启用自动同步到电商平台'
    )
    sync_status = models.CharField(
        '同步状态',
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default='pending',
        help_text='商品同步到电商平台的状态'
    )
    last_synced_at = models.DateTimeField(
        '最后同步时间',
        null=True,
        blank=True,
        help_text='上次成功同步到电商平台的时间'
    )
    sync_error = models.TextField(
        '同步错误',
        blank=True,
        help_text='同步失败时的错误信息'
    )
    
    class Meta:
        verbose_name = '采购订单商品平台映射'
        verbose_name_plural = '采购订单商品平台映射'
        db_table = 'purchase_order_item_platform_map'
        unique_together = [
            ['purchase_order_item', 'platform', 'platform_account', 'platform_product_id']
        ]
        indexes = [
            models.Index(fields=['platform', 'sync_status']),
            models.Index(fields=['sync_enabled', 'sync_status']),
            models.Index(fields=['-last_synced_at']),
            models.Index(fields=['purchase_order_item', 'platform']),
        ]
        ordering = ['-last_synced_at']
    
    def __str__(self):
        return f"{self.purchase_order_item} -> {self.platform.name}"
    
    @property
    def needs_sync(self):
        """是否需要同步"""
        return self.sync_enabled and self.sync_status in ['pending', 'failed']


class PurchaseSyncQueue(BaseModel):
    """
    采购商品同步队列
    
    用于管理采购商品的批量同步任务，支持异步处理和重试机制
    """
    
    SYNC_TYPES = [
        ('add', '新增'),
        ('update', '更新'),
        ('delete', '删除'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('success', '成功'),
        ('failed', '失败'),
    ]
    
    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.CASCADE,
        related_name='sync_queues',
        verbose_name='采购订单商品'
    )
    platform = models.ForeignKey(
        'core.Platform',
        on_delete=models.CASCADE,
        related_name='purchase_sync_queues',
        verbose_name='电商平台'
    )
    platform_account = models.ForeignKey(
        'ecomm_sync.PlatformAccount',
        on_delete=models.CASCADE,
        related_name='purchase_sync_queues',
        verbose_name='平台账号'
    )
    sync_type = models.CharField(
        '同步类型',
        max_length=20,
        choices=SYNC_TYPES,
        help_text='add=新增商品, update=更新商品信息, delete=删除商品'
    )
    sync_data = models.JSONField(
        '同步数据',
        default=dict,
        blank=True,
        help_text='要同步的商品数据（JSON格式）'
    )
    status = models.CharField(
        '状态',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    retry_count = models.IntegerField(
        '重试次数',
        default=0,
        help_text='已重试次数'
    )
    max_retries = models.IntegerField(
        '最大重试次数',
        default=3,
        help_text='最大重试次数'
    )
    error_message = models.TextField(
        '错误信息',
        blank=True,
        help_text='同步失败时的错误信息'
    )
    processed_at = models.DateTimeField(
        '处理时间',
        null=True,
        blank=True,
        help_text='任务开始处理的时间'
    )
    completed_at = models.DateTimeField(
        '完成时间',
        null=True,
        blank=True,
        help_text='任务完成的时间'
    )
    
    class Meta:
        verbose_name = '采购同步队列'
        verbose_name_plural = '采购同步队列'
        db_table = 'purchase_sync_queue'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['platform', 'status']),
            models.Index(fields=['sync_type', 'status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['retry_count', 'status']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.purchase_order_item} - {self.platform.name} - {self.get_status_display()}"
    
    @property
    def can_retry(self):
        """是否可以重试"""
        return self.status == 'failed' and self.retry_count < self.max_retries
    
    @property
    def is_completed(self):
        """是否已完成"""
        return self.status == 'success'

