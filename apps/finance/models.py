"""
Finance models for the ERP system.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import BaseModel

User = get_user_model()


class Account(BaseModel):
    """
    Chart of accounts model.
    """
    ACCOUNT_TYPES = [
        ('asset', '资产'),
        ('liability', '负债'),
        ('equity', '所有者权益'),
        ('revenue', '收入'),
        ('expense', '费用'),
        ('cost', '成本'),
    ]

    ACCOUNT_CATEGORIES = [
        ('current_asset', '流动资产'),
        ('fixed_asset', '固定资产'),
        ('current_liability', '流动负债'),
        ('long_term_liability', '长期负债'),
        ('operating_revenue', '营业收入'),
        ('operating_expense', '营业费用'),
        ('financial_expense', '财务费用'),
        ('other', '其他'),
    ]

    # Account information
    code = models.CharField('科目代码', max_length=20, unique=True)
    name = models.CharField('科目名称', max_length=100)
    account_type = models.CharField('科目类型', max_length=20, choices=ACCOUNT_TYPES)
    category = models.CharField('科目分类', max_length=30, choices=ACCOUNT_CATEGORIES, blank=True)
    
    # Hierarchy
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='上级科目'
    )
    level = models.PositiveIntegerField('科目级别', default=1)
    
    # Properties
    is_leaf = models.BooleanField('是否末级科目', default=True)
    is_active = models.BooleanField('是否启用', default=True)
    allow_manual_entry = models.BooleanField('允许手工录入', default=True)
    
    # Balance information
    opening_balance = models.DecimalField('期初余额', max_digits=15, decimal_places=2, default=0)
    current_balance = models.DecimalField('当前余额', max_digits=15, decimal_places=2, default=0)
    
    description = models.TextField('科目说明', blank=True)

    class Meta:
        verbose_name = '会计科目'
        verbose_name_plural = '会计科目'
        db_table = 'finance_account'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_name(self):
        """Return full account path."""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name


class Journal(BaseModel):
    """
    Journal/Voucher model.
    """
    JOURNAL_TYPES = [
        ('general', '记账凭证'),
        ('cash', '现金凭证'),
        ('bank', '银行凭证'),
        ('transfer', '转账凭证'),
        ('adjustment', '调整凭证'),
    ]

    JOURNAL_STATUS = [
        ('draft', '草稿'),
        ('posted', '已过账'),
        ('cancelled', '已作废'),
    ]

    # Journal information
    journal_number = models.CharField('凭证号', max_length=50, unique=True)
    journal_type = models.CharField('凭证类型', max_length=20, choices=JOURNAL_TYPES, default='general')
    status = models.CharField('状态', max_length=20, choices=JOURNAL_STATUS, default='draft')
    
    # Dates
    journal_date = models.DateField('凭证日期')
    period = models.CharField('会计期间', max_length=7)  # YYYY-MM format
    
    # Reference information
    reference_type = models.CharField('关联类型', max_length=50, blank=True)
    reference_id = models.CharField('关联单据ID', max_length=100, blank=True)
    reference_number = models.CharField('关联单据号', max_length=100, blank=True)
    
    # Financial information
    total_debit = models.DecimalField('借方合计', max_digits=15, decimal_places=2, default=0)
    total_credit = models.DecimalField('贷方合计', max_digits=15, decimal_places=2, default=0)
    
    # Personnel
    prepared_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prepared_journals',
        verbose_name='制单人'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_journals',
        verbose_name='审核人'
    )
    posted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posted_journals',
        verbose_name='过账人'
    )
    posted_at = models.DateTimeField('过账时间', null=True, blank=True)
    
    description = models.TextField('摘要', blank=True)
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '记账凭证'
        verbose_name_plural = '记账凭证'
        db_table = 'finance_journal'
        ordering = ['-journal_date', '-journal_number']

    def __str__(self):
        return f"{self.journal_number} - {self.journal_date}"

    @property
    def is_balanced(self):
        """Check if journal is balanced."""
        return self.total_debit == self.total_credit


class JournalEntry(BaseModel):
    """
    Journal entry model for individual account entries.
    """
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name='凭证'
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        verbose_name='科目'
    )
    debit_amount = models.DecimalField('借方金额', max_digits=15, decimal_places=2, default=0)
    credit_amount = models.DecimalField('贷方金额', max_digits=15, decimal_places=2, default=0)
    description = models.CharField('摘要', max_length=200, blank=True)
    
    # Auxiliary accounting
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='客户'
    )
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='供应商'
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='部门'
    )
    project = models.CharField('项目', max_length=100, blank=True)
    
    sort_order = models.PositiveIntegerField('排序', default=0)

    class Meta:
        verbose_name = '凭证分录'
        verbose_name_plural = '凭证分录'
        db_table = 'finance_journal_entry'
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.journal.journal_number} - {self.account.name}"


class CustomerAccount(BaseModel):
    """
    Customer account receivable model.
    """
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='accounts',
        verbose_name='客户'
    )
    sales_order = models.ForeignKey(
        'sales.SalesOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='销售订单'
    )
    invoice_number = models.CharField('发票号', max_length=100, blank=True)
    invoice_date = models.DateField('发票日期', null=True, blank=True)
    due_date = models.DateField('到期日期', null=True, blank=True)
    
    # Amounts
    invoice_amount = models.DecimalField('发票金额', max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField('已付金额', max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField('余额', max_digits=12, decimal_places=2, default=0)
    
    currency = models.CharField('币种', max_length=10, default='CNY')
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '客户账款'
        verbose_name_plural = '客户账款'
        db_table = 'finance_customer_account'

    def __str__(self):
        return f"{self.customer.name} - {self.balance}"

    @property
    def is_overdue(self):
        """Check if payment is overdue."""
        from django.utils import timezone
        if self.due_date and self.balance > 0:
            return timezone.now().date() > self.due_date
        return False


class SupplierAccount(BaseModel):
    """
    供应商应付账款主单模型。

    业务流程：
    1. 收货/退货时自动生成应付明细（SupplierAccountDetail）
    2. 应付主单自动归集所有明细的汇总数据
    3. 付款时核销应付明细，主单自动更新

    核心公式：
    - 订单实际应付 = 累计正应付 + 累计负应付
    - 订单未付金额 = 实际应付 - 累计已核销
    """
    ACCOUNT_STATUS = [
        ('pending', '待付款'),
        ('partially_paid', '部分付款'),
        ('paid', '已付清'),
        ('overdue', '已逾期'),
    ]

    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='accounts',
        verbose_name='供应商'
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='refund_accounts',
        verbose_name='客户（退款）',
        help_text='销售退货退款时使用'
    )
    purchase_order = models.ForeignKey(
        'purchase.PurchaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supplier_accounts',
        verbose_name='采购订单'
    )
    sales_return = models.ForeignKey(
        'sales.SalesReturn',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supplier_accounts',
        verbose_name='销售退货单',
        help_text='销售退货退款时使用'
    )
    invoice = models.ForeignKey(
        'finance.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supplier_accounts',
        verbose_name='关联发票'
    )

    # Legacy fields (保留向后兼容)
    invoice_number = models.CharField('发票号', max_length=100, blank=True)
    invoice_date = models.DateField('发票日期', null=True, blank=True)
    due_date = models.DateField('到期日期', null=True, blank=True)

    # Status
    status = models.CharField('状态', max_length=20, choices=ACCOUNT_STATUS, default='pending')

    # Amounts（自动归集字段）
    invoice_amount = models.DecimalField('实际应付金额', max_digits=12, decimal_places=2, default=0, help_text='累计正应付+累计负应付')
    paid_amount = models.DecimalField('已核销金额', max_digits=12, decimal_places=2, default=0, help_text='累计已核销金额')
    balance = models.DecimalField('未付余额', max_digits=12, decimal_places=2, default=0, help_text='实际应付-已核销')

    currency = models.CharField('币种', max_length=10, default='CNY')
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '供应商账款'
        verbose_name_plural = '供应商账款'
        db_table = 'finance_supplier_account'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['supplier', 'status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        if self.supplier:
            return f"{self.supplier.name} - {self.invoice_number or 'N/A'} - ¥{self.balance}"
        elif self.customer:
            return f"退款-{self.customer.name} - {self.invoice_number or 'N/A'} - ¥{self.balance}"
        return f"{self.invoice_number or 'N/A'} - ¥{self.balance}"

    @property
    def is_overdue(self):
        """检查是否逾期"""
        from django.utils import timezone
        if self.due_date and self.balance > 0:
            return timezone.now().date() > self.due_date
        return False

    @property
    def payment_ratio(self):
        """付款比例"""
        if self.invoice_amount > 0:
            return (self.paid_amount / self.invoice_amount) * 100
        return 0

    def update_status(self):
        """根据付款情况更新状态"""
        if self.balance <= 0:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partially_paid'
        elif self.is_overdue:
            self.status = 'overdue'
        else:
            self.status = 'pending'

    def record_payment(self, payment_amount):
        """
        记录付款。

        Args:
            payment_amount: 付款金额

        Returns:
            bool: 是否成功
        """
        from decimal import Decimal
        payment_amount = Decimal(str(payment_amount))

        if payment_amount <= 0:
            return False

        if payment_amount > self.balance:
            return False

        self.paid_amount += payment_amount
        self.balance -= payment_amount
        self.update_status()
        self.save()
        return True

    def aggregate_from_details(self):
        """
        从应付明细自动归集数据到主单。

        核心公式：
        - 实际应付 = 累计正应付 + 累计负应付
        - 已核销金额 = 累计已核销
        - 未付余额 = 实际应付 - 已核销
        """
        from decimal import Decimal

        # 获取所有明细
        details = self.details.filter(is_deleted=False)

        # 累计正应付（收货）
        total_positive = details.filter(detail_type='receipt').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')

        # 累计负应付（退货）
        total_negative = details.filter(detail_type='return').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')

        # 实际应付 = 正应付 + 负应付
        self.invoice_amount = total_positive + total_negative

        # 已核销金额
        self.paid_amount = details.aggregate(
            total=models.Sum('allocated_amount')
        )['total'] or Decimal('0')

        # 未付余额 = 实际应付 - 已核销
        self.balance = self.invoice_amount - self.paid_amount

        # 更新状态
        self.update_status()
        self.save()

    @classmethod
    def get_or_create_for_order(cls, purchase_order):
        """
        获取或创建订单的应付主单。

        Args:
            purchase_order: 采购订单

        Returns:
            SupplierAccount: 应付主单
        """
        # 尝试获取已存在的主单
        account = cls.objects.filter(
            purchase_order=purchase_order,
            supplier=purchase_order.supplier,
            is_deleted=False
        ).first()

        if not account:
            # 创建新的主单
            from common.utils import DocumentNumberGenerator
            account = cls.objects.create(
                invoice_number=DocumentNumberGenerator.generate('supplier_account'),
                supplier=purchase_order.supplier,
                purchase_order=purchase_order,
                invoice_amount=Decimal('0'),
                paid_amount=Decimal('0'),
                balance=Decimal('0'),
                status='pending',
                notes=f'采购订单 {purchase_order.order_number} 应付账款'
            )

        return account


class SupplierAccountDetail(BaseModel):
    """
    供应商应付明细模型（独立核销单元）。

    业务逻辑：
    1. 每次收货自动生成一条正应付明细
    2. 每次退货（扣已收货）自动生成一条负应付明细
    3. 应付明细独立核销，支持分批付款
    4. 应付主单自动归集所有明细的汇总数据

    核心公式：
    - 订单实际应付 = 累计正应付 + 累计负应付
    - 订单未付金额 = 实际应付 - 累计已核销
    """
    DETAIL_TYPES = [
        ('receipt', '收货正应付'),
        ('return', '退货负应付'),
    ]

    DETAIL_STATUS = [
        ('pending', '待核销'),
        ('partial', '部分核销'),
        ('allocated', '已核销'),
    ]

    # 基础信息
    detail_number = models.CharField('明细单号', max_length=100, unique=True)
    detail_type = models.CharField('明细类型', max_length=20, choices=DETAIL_TYPES)
    status = models.CharField('状态', max_length=20, choices=DETAIL_STATUS, default='pending')

    # 关联方
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.CASCADE,
        related_name='account_details',
        verbose_name='供应商'
    )
    purchase_order = models.ForeignKey(
        'purchase.PurchaseOrder',
        on_delete=models.CASCADE,
        related_name='account_details',
        verbose_name='采购订单'
    )

    # 关联业务单据（二选一）
    receipt = models.ForeignKey(
        'purchase.PurchaseReceipt',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='account_details',
        verbose_name='收货单',
        help_text='收货正应付时关联'
    )
    return_order = models.ForeignKey(
        'purchase.PurchaseReturn',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='account_details',
        verbose_name='退货单',
        help_text='退货负应付时关联'
    )

    # 金额信息
    amount = models.DecimalField('应付金额', max_digits=12, decimal_places=2, help_text='正应付为正，负应付为负')
    allocated_amount = models.DecimalField('已核销金额', max_digits=12, decimal_places=2, default=0)

    # 关联应付主单
    parent_account = models.ForeignKey(
        'SupplierAccount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='details',
        verbose_name='应付主单',
        help_text='归集到应付主单'
    )

    # 业务日期
    business_date = models.DateField('业务日期', help_text='收货/退货日期')

    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '供应商应付明细'
        verbose_name_plural = '供应商应付明细'
        db_table = 'finance_supplier_account_detail'
        ordering = ['-business_date', '-created_at']
        indexes = [
            models.Index(fields=['supplier', 'status']),
            models.Index(fields=['purchase_order', 'detail_type']),
            models.Index(fields=['receipt']),
            models.Index(fields=['return_order']),
            models.Index(fields=['parent_account']),
        ]

    def __str__(self):
        sign = '+' if self.amount > 0 else ''
        return f"{self.detail_number} - {self.get_detail_type_display()} - {sign}¥{self.amount}"

    @property
    def balance(self):
        """未核销余额"""
        return self.amount - self.allocated_amount

    @property
    def is_fully_allocated(self):
        """是否已全额核销"""
        return self.balance == 0

    def allocate(self, amount):
        """
        核销金额。

        Args:
            amount: 核销金额

        Returns:
            bool: 是否成功
        """
        from decimal import Decimal
        amount = Decimal(str(amount))

        if amount <= 0:
            return False

        if amount > self.balance:
            return False

        self.allocated_amount += amount
        if self.is_fully_allocated:
            self.status = 'allocated'
        else:
            self.status = 'partial'
        self.save()
        return True


class Payment(BaseModel):
    """
    Payment model for both receivables and payables.
    """
    PAYMENT_TYPES = [
        ('receipt', '收款'),
        ('payment', '付款'),
    ]

    PAYMENT_METHODS = [
        ('cash', '现金'),
        ('bank_transfer', '电汇'),
        ('acceptance_draft', '承兑汇票'),
        ('other', '其它'),
    ]

    PAYMENT_STATUS = [
        ('pending', '待处理'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
        ('failed', '失败'),
    ]

    # Payment information
    payment_number = models.CharField('付款单号', max_length=100, unique=True)
    payment_type = models.CharField('付款类型', max_length=20, choices=PAYMENT_TYPES)
    payment_method = models.CharField('付款方式', max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField('状态', max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Parties
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='客户'
    )
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='供应商'
    )
    
    # Financial information
    amount = models.DecimalField('金额', max_digits=12, decimal_places=2)
    currency = models.CharField('币种', max_length=10, default='CNY')
    exchange_rate = models.DecimalField('汇率', max_digits=10, decimal_places=4, default=1)
    
    # Dates
    payment_date = models.DateField('付款日期')
    value_date = models.DateField('起息日期', null=True, blank=True)
    
    # Bank information
    bank_account = models.CharField('银行账户', max_length=100, blank=True)
    bank_name = models.CharField('银行名称', max_length=100, blank=True)
    transaction_reference = models.CharField('交易参考号', max_length=100, blank=True)
    
    # Reference information
    reference_type = models.CharField('关联类型', max_length=50, blank=True)
    reference_id = models.CharField('关联单据ID', max_length=100, blank=True)
    reference_number = models.CharField('关联单据号', max_length=100, blank=True)
    
    # Personnel
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='处理人'
    )
    
    description = models.TextField('摘要', blank=True)
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '付款记录'
        verbose_name_plural = '付款记录'
        db_table = 'finance_payment'
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"{self.payment_number} - {self.amount}"


class CustomerPrepayment(BaseModel):
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='prepayments', verbose_name='客户')
    amount = models.DecimalField('预收金额', max_digits=12, decimal_places=2)
    balance = models.DecimalField('剩余余额', max_digits=12, decimal_places=2)
    currency = models.CharField('币种', max_length=10, default='CNY')
    received_date = models.DateField('收到日期')
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '客户预收款'
        verbose_name_plural = '客户预收款'
        db_table = 'finance_customer_prepayment'

    def __str__(self):
        return f"{self.customer.name} - {self.balance}"


class SupplierPrepayment(BaseModel):
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.CASCADE, related_name='prepayments', verbose_name='供应商')
    amount = models.DecimalField('预付金额', max_digits=12, decimal_places=2)
    balance = models.DecimalField('剩余余额', max_digits=12, decimal_places=2)
    currency = models.CharField('币种', max_length=10, default='CNY')
    paid_date = models.DateField('付款日期')
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '供应商预付款'
        verbose_name_plural = '供应商预付款'
        db_table = 'finance_supplier_prepayment'

    def __str__(self):
        return f"{self.supplier.name} - {self.balance}"

class Budget(BaseModel):
    """
    Budget model for financial planning.
    """
    BUDGET_TYPES = [
        ('annual', '年度预算'),
        ('quarterly', '季度预算'),
        ('monthly', '月度预算'),
        ('project', '项目预算'),
    ]

    BUDGET_STATUS = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('approved', '已批准'),
        ('active', '执行中'),
        ('closed', '已关闭'),
    ]

    # Budget information
    budget_name = models.CharField('预算名称', max_length=200)
    budget_code = models.CharField('预算代码', max_length=50, unique=True)
    budget_type = models.CharField('预算类型', max_length=20, choices=BUDGET_TYPES)
    status = models.CharField('状态', max_length=20, choices=BUDGET_STATUS, default='draft')
    
    # Period
    fiscal_year = models.PositiveIntegerField('财政年度')
    start_date = models.DateField('开始日期')
    end_date = models.DateField('结束日期')
    
    # Responsibility
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        verbose_name='责任部门'
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='预算负责人'
    )
    
    # Approval
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_finance_budgets',
        verbose_name='批准人'
    )
    approved_at = models.DateTimeField('批准时间', null=True, blank=True)
    
    description = models.TextField('预算说明', blank=True)

    class Meta:
        verbose_name = '预算'
        verbose_name_plural = '预算'
        db_table = 'finance_budget'

    def __str__(self):
        return f"{self.budget_code} - {self.budget_name}"


class BudgetLine(BaseModel):
    """
    Budget line item model.
    """
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name='预算'
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        verbose_name='科目'
    )
    
    # Budget amounts
    budgeted_amount = models.DecimalField('预算金额', max_digits=15, decimal_places=2, default=0)
    actual_amount = models.DecimalField('实际金额', max_digits=15, decimal_places=2, default=0)
    committed_amount = models.DecimalField('承诺金额', max_digits=15, decimal_places=2, default=0)
    
    # Breakdown by period
    q1_budget = models.DecimalField('第一季度预算', max_digits=15, decimal_places=2, default=0)
    q2_budget = models.DecimalField('第二季度预算', max_digits=15, decimal_places=2, default=0)
    q3_budget = models.DecimalField('第三季度预算', max_digits=15, decimal_places=2, default=0)
    q4_budget = models.DecimalField('第四季度预算', max_digits=15, decimal_places=2, default=0)
    
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '预算明细'
        verbose_name_plural = '预算明细'
        db_table = 'finance_budget_line'
        unique_together = ['budget', 'account']

    def __str__(self):
        return f"{self.budget.budget_code} - {self.account.name}"

    @property
    def variance(self):
        """Calculate budget variance."""
        return self.actual_amount - self.budgeted_amount

    @property
    def variance_percentage(self):
        """Calculate budget variance percentage."""
        if self.budgeted_amount == 0:
            return 0
        return (self.variance / self.budgeted_amount) * 100


class Invoice(BaseModel):
    """
    统一发票模型 (采购发票 + 销售发票)
    """
    INVOICE_TYPES = [
        ('purchase', '采购发票'),
        ('sales', '销售发票'),
    ]

    INVOICE_STATUS = [
        ('draft', '草稿'),
        ('issued', '已开具'),
        ('received', '已收到'),
        ('verified', '已认证'),
        ('cancelled', '已作废'),
    ]

    # 发票基本信息
    invoice_number = models.CharField('发票号码', max_length=100, unique=True, db_index=True)
    invoice_type = models.CharField('发票类型', max_length=20, choices=INVOICE_TYPES)
    invoice_code = models.CharField('发票代码', max_length=50, blank=True)
    status = models.CharField('状态', max_length=20, choices=INVOICE_STATUS, default='draft')

    # 关联方信息
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name='供应商'
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name='客户'
    )

    # 日期信息
    invoice_date = models.DateField('开票日期')
    tax_date = models.DateField('税务日期', null=True, blank=True)

    # 金额信息
    amount_excluding_tax = models.DecimalField('不含税金额', max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField('税率(%)', max_digits=5, decimal_places=2, default=13)
    tax_amount = models.DecimalField('税额', max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField('价税合计', max_digits=12, decimal_places=2, default=0)

    # 关联业务单据
    reference_type = models.CharField('关联类型', max_length=50, blank=True)  # 'purchase_order', 'sales_order'
    reference_id = models.CharField('关联单据ID', max_length=100, blank=True)
    reference_number = models.CharField('关联单据号', max_length=100, blank=True)

    # 发票图片/PDF
    attachment = models.FileField('发票附件', upload_to='invoices/%Y/%m/', blank=True, null=True)

    # 备注
    remark = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '发票'
        verbose_name_plural = '发票'
        db_table = 'finance_invoice'
        ordering = ['-invoice_date', '-created_at']
        indexes = [
            models.Index(fields=['invoice_type', 'status']),
            models.Index(fields=['invoice_date']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.get_invoice_type_display()}"

    def calculate_totals(self):
        """计算发票金额"""
        from decimal import Decimal
        # 从明细汇总
        items_total = sum([item.amount for item in self.items.all()], Decimal('0'))
        self.amount_excluding_tax = items_total
        self.tax_amount = self.amount_excluding_tax * (self.tax_rate / Decimal('100'))
        self.total_amount = self.amount_excluding_tax + self.tax_amount


class InvoiceItem(BaseModel):
    """
    发票明细
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='发票'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='产品'
    )

    # 产品描述
    description = models.CharField('品名', max_length=200)
    specification = models.CharField('规格型号', max_length=200, blank=True)
    unit = models.CharField('单位', max_length=50, blank=True)

    # 数量和金额
    quantity = models.IntegerField('数量')
    unit_price = models.DecimalField('单价', max_digits=12, decimal_places=2)
    amount = models.DecimalField('金额', max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField('税率(%)', max_digits=5, decimal_places=2, default=13)
    tax_amount = models.DecimalField('税额', max_digits=12, decimal_places=2, default=0)

    sort_order = models.PositiveIntegerField('排序', default=0)

    class Meta:
        verbose_name = '发票明细'
        verbose_name_plural = '发票明细'
        db_table = 'finance_invoice_item'
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description}"

    def save(self, *args, **kwargs):
        """保存时自动计算金额"""
        from decimal import Decimal
        self.amount = self.quantity * self.unit_price
        self.tax_amount = self.amount * (self.tax_rate / Decimal('100'))
        super().save(*args, **kwargs)


class FinancialReport(BaseModel):
    """
    财务报表模型

    用于存储生成的财务报表数据，支持历史查询和对比分析。
    """
    REPORT_TYPES = [
        ('balance_sheet', '资产负债表'),
        ('income_statement', '利润表'),
        ('cash_flow', '现金流量表'),
        ('trial_balance', '科目余额表'),
        ('account_ledger', '科目明细账'),
    ]

    report_type = models.CharField('报表类型', max_length=30, choices=REPORT_TYPES)
    report_date = models.DateField('报表日期', help_text='资产负债表的截止日期')
    start_date = models.DateField('开始日期', null=True, blank=True, help_text='利润表和现金流量表的起始日期')
    end_date = models.DateField('结束日期', null=True, blank=True, help_text='利润表和现金流量表的截止日期')

    # 报表数据（JSON格式存储）
    report_data = models.JSONField('报表数据', help_text='JSON格式存储报表详细数据')

    # 报表摘要（便于快速查询）
    total_assets = models.DecimalField('总资产', max_digits=15, decimal_places=2, default=0, null=True, blank=True)
    total_liabilities = models.DecimalField('总负债', max_digits=15, decimal_places=2, default=0, null=True, blank=True)
    total_equity = models.DecimalField('所有者权益', max_digits=15, decimal_places=2, default=0, null=True, blank=True)
    net_profit = models.DecimalField('净利润', max_digits=15, decimal_places=2, default=0, null=True, blank=True)

    # 生成信息
    generated_at = models.DateTimeField('生成时间', auto_now_add=True)
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='生成人'
    )

    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '财务报表'
        verbose_name_plural = '财务报表'
        db_table = 'finance_financial_report'
        ordering = ['-report_date', '-created_at']
        indexes = [
            models.Index(fields=['report_type', 'report_date']),
            models.Index(fields=['report_date']),
        ]

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.report_date}"


class TaxRate(BaseModel):
    """
    税率管理模型

    用于管理系统中使用的各种税率，如增值税、营业税等。
    支持多种税率类型和税率档次，便于订单、发票等业务单据使用。
    """
    TAX_TYPES = [
        ('vat', '增值税'),
        ('consumption', '消费税'),
        ('business', '营业税'),
        ('customs', '关税'),
        ('income', '所得税'),
        ('other', '其他'),
    ]

    # 基础信息
    name = models.CharField('税率名称', max_length=100, unique=True, help_text='例如：增值税13%、增值税9%')
    code = models.CharField('税率代码', max_length=50, unique=True, help_text='例如：VAT_13、VAT_9')
    tax_type = models.CharField('税种', max_length=20, choices=TAX_TYPES, default='vat')

    # 税率值（以小数形式存储，如0.13表示13%）
    rate = models.DecimalField(
        '税率',
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0'))],
        help_text='税率值（0-1之间的小数，如0.13表示13%）'
    )

    # 状态标记
    is_default = models.BooleanField('是否默认税率', default=False, help_text='每种税种只能有一个默认税率')
    is_active = models.BooleanField('是否启用', default=True)

    # 适用说明
    description = models.TextField('适用说明', blank=True, help_text='说明该税率的适用范围和条件')
    effective_date = models.DateField('生效日期', null=True, blank=True, help_text='税率开始生效的日期')
    expiry_date = models.DateField('失效日期', null=True, blank=True, help_text='税率失效的日期（如果有）')

    # 排序
    sort_order = models.PositiveIntegerField('排序', default=0, help_text='数字越小越靠前')

    class Meta:
        verbose_name = '税率'
        verbose_name_plural = '税率'
        db_table = 'finance_tax_rate'
        ordering = ['tax_type', 'sort_order', '-rate']
        indexes = [
            models.Index(fields=['tax_type', 'is_active']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f"{self.name} ({self.rate_percent}%)"

    @property
    def rate_percent(self):
        """返回百分比形式的税率"""
        return float(self.rate * 100)

    def save(self, *args, **kwargs):
        """保存时确保默认税率的唯一性"""
        if self.is_default:
            # 如果设置为默认税率，取消同一税种的其他默认税率
            TaxRate.objects.filter(
                tax_type=self.tax_type,
                is_default=True,
                is_deleted=False
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

class Expense(BaseModel):
    """
    费用报销单模型

    用于管理企业日常费用支出，包括：
    - 差旅费、交通费、餐饮费
    - 办公费、通讯费、水电费
    - 其他管理费用和销售费用
    """
    EXPENSE_STATUS = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('approved', '已审批'),
        ('rejected', '已拒绝'),
        ('paid', '已支付'),
        ('cancelled', '已取消'),
    ]

    EXPENSE_CATEGORY = [
        ('travel', '差旅费'),
        ('transportation', '交通费'),
        ('meal', '餐饮费'),
        ('office', '办公费'),
        ('communication', '通讯费'),
        ('utilities', '水电费'),
        ('entertainment', '业务招待费'),
        ('training', '培训费'),
        ('maintenance', '维修费'),
        ('advertising', '广告费'),
        ('other', '其他费用'),
    ]

    PAYMENT_METHOD = [
        ('cash', '现金'),
        ('bank_transfer', '银行转账'),
        ('company_card', '公司卡'),
        ('personal_advance', '个人垫付'),
    ]

    # 基本信息
    expense_number = models.CharField('费用单号', max_length=100, unique=True)
    expense_date = models.DateField('费用日期', help_text='费用发生日期')

    # 申请人信息
    applicant = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='expenses',
        verbose_name='申请人'
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='申请部门'
    )

    # 费用信息
    category = models.CharField('费用类别', max_length=20, choices=EXPENSE_CATEGORY)
    amount = models.DecimalField(
        '费用金额',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='费用总金额'
    )

    # 支付信息
    payment_method = models.CharField('支付方式', max_length=20, choices=PAYMENT_METHOD, default='personal_advance')

    # 关联信息
    project = models.CharField('关联项目', max_length=200, blank=True, help_text='费用关联的项目名称')
    reference_number = models.CharField('参考单号', max_length=100, blank=True, help_text='关联的其他单据号')

    # 状态
    status = models.CharField('状态', max_length=20, choices=EXPENSE_STATUS, default='draft')

    # 审批信息
    submitted_at = models.DateTimeField('提交时间', null=True, blank=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_expenses',
        verbose_name='审批人'
    )
    approved_at = models.DateTimeField('审批时间', null=True, blank=True)
    rejection_reason = models.TextField('拒绝原因', blank=True)

    # 支付信息
    paid_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paid_expenses',
        verbose_name='支付人'
    )
    paid_at = models.DateTimeField('支付时间', null=True, blank=True)
    payment_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='支付科目',
        help_text='支付费用使用的会计科目（如银行存款、库存现金）'
    )

    # 会计凭证关联
    journal = models.ForeignKey(
        Journal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        verbose_name='关联凭证'
    )

    # 附件和备注
    description = models.TextField('费用说明', help_text='详细说明费用用途和明细')
    notes = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '费用报销单'
        verbose_name_plural = '费用报销单'
        db_table = 'finance_expense'
        ordering = ['-expense_date', '-created_at']
        indexes = [
            models.Index(fields=['applicant', 'status']),
            models.Index(fields=['expense_date']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.expense_number} - {self.get_category_display()} - ¥{self.amount}"

    def submit(self, user=None):
        """提交费用申请"""
        if self.status != 'draft':
            raise ValueError('只有草稿状态的费用单才能提交')

        from django.utils import timezone
        self.status = 'submitted'
        self.submitted_at = timezone.now()
        if user:
            self.updated_by = user
        self.save()

    def approve(self, approved_by_user):
        """审批通过"""
        if self.status != 'submitted':
            raise ValueError('只有已提交状态的费用单才能审批')

        from django.utils import timezone
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.updated_by = approved_by_user
        self.save()

    def reject(self, rejected_by_user, reason):
        """审批拒绝"""
        if self.status != 'submitted':
            raise ValueError('只有已提交状态的费用单才能拒绝')

        from django.utils import timezone
        self.status = 'rejected'
        self.approved_by = rejected_by_user
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.updated_by = rejected_by_user
        self.save()

    def mark_paid(self, paid_by_user, payment_account=None, auto_create_journal=True):
        """
        标记为已支付，并可选择性自动生成会计凭证

        Args:
            paid_by_user: 支付操作人
            payment_account: 支付使用的会计科目（如银行存款）
            auto_create_journal: 是否自动生成会计凭证

        Returns:
            Journal: 生成的会计凭证（如果auto_create_journal=True）
        """
        if self.status != 'approved':
            raise ValueError('只有已审批状态的费用单才能支付')

        from django.utils import timezone
        from core.utils.document_number import DocumentNumberGenerator

        self.status = 'paid'
        self.paid_by = paid_by_user
        self.paid_at = timezone.now()
        self.payment_account = payment_account
        self.updated_by = paid_by_user
        self.save()

        journal = None
        if auto_create_journal:
            # 自动生成会计凭证
            # 借: 费用科目（根据category确定）
            # 贷: 支付科目（payment_account）

            # 确定费用科目（根据费用类别映射到会计科目）
            expense_account_map = {
                'travel': '6601',  # 销售费用-差旅费
                'transportation': '6601',  # 销售费用-交通费
                'meal': '6601',  # 销售费用-餐饮费
                'office': '6602',  # 管理费用-办公费
                'communication': '6602',  # 管理费用-通讯费
                'utilities': '6602',  # 管理费用-水电费
                'entertainment': '6601',  # 销售费用-业务招待费
                'training': '6602',  # 管理费用-培训费
                'maintenance': '6602',  # 管理费用-维修费
                'advertising': '6601',  # 销售费用-广告费
                'other': '6602',  # 管理费用-其他
            }

            expense_account_code = expense_account_map.get(self.category, '6602')

            try:
                expense_account = Account.objects.get(code=expense_account_code, is_deleted=False)

                # 如果没有指定支付科目，默认使用银行存款
                if not payment_account:
                    payment_account = Account.objects.get(code='1002', is_deleted=False)  # 银行存款

                # 创建凭证
                journal = Journal.objects.create(
                    journal_number=DocumentNumberGenerator.generate('journal'),
                    journal_date=self.expense_date,
                    period=self.expense_date.strftime('%Y-%m'),
                    journal_type='general',
                    description=f'{self.get_category_display()} - {self.description[:50]}',
                    reference_type='Expense',
                    reference_id=str(self.pk),
                    reference_number=self.expense_number,
                    total_debit=self.amount,
                    total_credit=self.amount,
                    status='posted',
                    prepared_by=paid_by_user,
                    posted_by=paid_by_user,
                    posted_at=timezone.now(),
                    created_by=paid_by_user,
                    updated_by=paid_by_user,
                )

                # 借方: 费用科目
                JournalEntry.objects.create(
                    journal=journal,
                    account=expense_account,
                    debit_amount=self.amount,
                    credit_amount=Decimal('0'),
                    description=f'{self.get_category_display()}',
                    department=self.department,
                    created_by=paid_by_user,
                    updated_by=paid_by_user,
                )

                # 贷方: 支付科目
                JournalEntry.objects.create(
                    journal=journal,
                    account=payment_account,
                    debit_amount=Decimal('0'),
                    credit_amount=self.amount,
                    description=f'支付{self.get_category_display()}',
                    created_by=paid_by_user,
                    updated_by=paid_by_user,
                )

                self.journal = journal
                self.save()

            except Account.DoesNotExist:
                # 如果科目不存在，不生成凭证
                pass

        return journal
