"""
Finance admin configuration.
"""
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin, ImportExportMixin
from .models import (
    CustomerAccount,
    SupplierAccount,
    Payment,
    Invoice,
    InvoiceItem,
    TaxRate,
    Expense,
    Account,
    Journal,
    JournalEntry,
)
from .resources import (
    ExpenseResource,
    InvoiceResource,
    PaymentResource,
    AccountResource,
    JournalResource,
    JournalEntryResource,
)




@admin.register(CustomerAccount)
class CustomerAccountAdmin(admin.ModelAdmin):
    """
    Admin configuration for Customer Account model.
    """
    list_display = (
        'customer',
        'sales_order',
        'invoice_number',
        'invoice_date',
        'due_date',
        'invoice_amount',
        'paid_amount',
        'balance',
        'is_overdue',
    )
    list_filter = ('invoice_date', 'due_date')
    search_fields = ('customer__name', 'invoice_number', 'sales_order__order_number')
    readonly_fields = ('created_at', 'updated_at', 'is_overdue')


@admin.register(SupplierAccount)
class SupplierAccountAdmin(admin.ModelAdmin):
    """
    Admin configuration for Supplier Account model.
    """
    list_display = (
        'supplier',
        'purchase_order',
        'invoice_number',
        'invoice_date',
        'due_date',
        'invoice_amount',
        'paid_amount',
        'balance',
    )
    list_filter = ('invoice_date', 'due_date')
    search_fields = ('supplier__name', 'invoice_number', 'purchase_order__order_number')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Payment)
class PaymentAdmin(ImportExportModelAdmin):
    """
    Admin configuration for Payment model with import/export support.
    """
    resource_class = PaymentResource
    list_display = (
        'payment_number',
        'payment_type',
        'payment_method',
        'amount',
        'payment_date',
        'customer',
        'supplier',
        'status',
    )
    list_filter = ('payment_type', 'payment_method', 'status', 'payment_date')
    search_fields = ('payment_number', 'customer__name', 'supplier__name')
    readonly_fields = ('created_at', 'updated_at')




class InvoiceItemInline(admin.TabularInline):
    """
    Inline admin for invoice items.
    """
    model = InvoiceItem
    extra = 1
    fields = ('description', 'specification', 'unit', 'quantity', 'unit_price', 'amount', 'tax_rate', 'tax_amount')
    readonly_fields = ('amount', 'tax_amount')


@admin.register(Invoice)
class InvoiceAdmin(ImportExportModelAdmin):
    """
    Admin configuration for Invoice model with import/export support.
    """
    resource_class = InvoiceResource
    list_display = (
        'invoice_number',
        'invoice_type',
        'invoice_date',
        'customer',
        'supplier',
        'total_amount',
        'status',
    )
    list_filter = ('invoice_type', 'status', 'invoice_date')
    search_fields = ('invoice_number', 'invoice_code', 'customer__name', 'supplier__name', 'reference_number')
    readonly_fields = (
        'amount_excluding_tax',
        'tax_amount',
        'total_amount',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )
    inlines = [InvoiceItemInline]

    fieldsets = (
        ('基本信息', {
            'fields': ('invoice_number', 'invoice_code', 'invoice_type', 'status', 'invoice_date', 'tax_date')
        }),
        ('关联方', {
            'fields': ('customer', 'supplier')
        }),
        ('金额信息', {
            'fields': ('tax_rate', 'amount_excluding_tax', 'tax_amount', 'total_amount')
        }),
        ('关联业务单据', {
            'fields': ('reference_type', 'reference_id', 'reference_number')
        }),
        ('附件', {
            'fields': ('attachment',)
        }),
        ('备注', {
            'fields': ('remark',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """保存时自动设置创建人和更新人"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """保存明细时自动计算总额"""
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:
                instance.created_by = request.user
            instance.updated_by = request.user
            instance.save()
        formset.save_m2m()

        # 重新计算发票总额
        form.instance.calculate_totals()
        form.instance.save()


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    """
    Admin configuration for TaxRate model.
    """
    list_display = (
        'name',
        'code',
        'tax_type',
        'rate_display',
        'is_default',
        'is_active',
        'effective_date',
        'expiry_date',
    )
    list_filter = ('tax_type', 'is_default', 'is_active')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'tax_type', 'rate', 'sort_order')
        }),
        ('状态标记', {
            'fields': ('is_default', 'is_active')
        }),
        ('生效期间', {
            'fields': ('effective_date', 'expiry_date')
        }),
        ('说明', {
            'fields': ('description',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def rate_display(self, obj):
        """显示百分比形式的税率"""
        return f"{obj.rate_percent}%"
    rate_display.short_description = '税率'

    def save_model(self, request, obj, form, change):
        """保存时自动设置创建人和更新人"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Expense)
class ExpenseAdmin(ImportExportModelAdmin):
    """
    Admin configuration for Expense model with import/export support.
    """
    resource_class = ExpenseResource
    list_display = (
        'expense_number',
        'expense_date',
        'applicant',
        'department',
        'category',
        'amount',
        'status',
        'approved_by',
    )
    list_filter = ('status', 'category', 'expense_date', 'department')
    search_fields = ('expense_number', 'applicant__username', 'description')
    readonly_fields = ('expense_number', 'submitted_at', 'approved_at', 'paid_at', 'created_at', 'updated_at')

    fieldsets = (
        ('基本信息', {
            'fields': ('expense_number', 'expense_date', 'applicant', 'department')
        }),
        ('费用信息', {
            'fields': ('category', 'amount', 'payment_method', 'description')
        }),
        ('关联信息', {
            'fields': ('project', 'reference_number', 'payment_account', 'journal')
        }),
        ('状态信息', {
            'fields': ('status',)
        }),
        ('审批信息', {
            'fields': ('submitted_at', 'approved_by', 'approved_at', 'rejection_reason')
        }),
        ('支付信息', {
            'fields': ('paid_by', 'paid_at')
        }),
        ('备注', {
            'fields': ('notes',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """保存时自动设置创建人和更新人"""
        if not change:
            obj.created_by = request.user
            # 自动生成费用单号
            if not obj.expense_number:
                from core.utils.document_number import DocumentNumberGenerator
                obj.expense_number = DocumentNumberGenerator.generate('expense')
            # 默认申请人为当前用户
            if not obj.applicant:
                obj.applicant = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Account)
class AccountAdmin(ImportExportModelAdmin):
    """
    Admin configuration for Account model with import/export support.
    """
    resource_class = AccountResource
    list_display = ('code', 'name', 'account_type', 'parent', 'is_active')
    list_filter = ('account_type', 'is_active')
    search_fields = ('code', 'name', 'description')
    readonly_fields = ('created_at', 'updated_at')


class JournalEntryInline(admin.TabularInline):
    """
    Inline admin for journal entries.
    """
    model = JournalEntry
    extra = 2
    fields = ('account', 'debit_amount', 'credit_amount', 'description', 'sort_order')


@admin.register(Journal)
class JournalAdmin(ImportExportModelAdmin):
    """
    Admin configuration for Journal model with import/export support.
    """
    resource_class = JournalResource
    list_display = ('journal_number', 'journal_type', 'journal_date', 'total_debit', 'total_credit', 'status')
    list_filter = ('journal_type', 'status', 'journal_date')
    search_fields = ('journal_number', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [JournalEntryInline]


@admin.register(JournalEntry)
class JournalEntryAdmin(ImportExportModelAdmin):
    """
    Admin configuration for JournalEntry model with import/export support.
    """
    resource_class = JournalEntryResource
    list_display = ('journal', 'sort_order', 'account', 'debit_amount', 'credit_amount', 'description')
    list_filter = ('journal__journal_date',)
    search_fields = ('journal__journal_number', 'account__code', 'account__name', 'description')
    readonly_fields = ('created_at', 'updated_at')
