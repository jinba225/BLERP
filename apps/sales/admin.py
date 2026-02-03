"""
Sales admin configuration.
"""
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import (
    Quote,
    QuoteItem,
    SalesOrder,
    SalesOrderItem,
    Delivery,
    DeliveryItem,
    SalesReturn,
    SalesReturnItem,
    SalesLoan,
    SalesLoanItem,
)
from .resources import (
    QuoteResource,
    SalesOrderResource,
    DeliveryResource,
    SalesReturnResource,
    SalesLoanResource,
)
# 打印模板模型已移至 core 模块
from core.models import PrintTemplate, DefaultTemplateMapping


class QuoteItemInline(admin.TabularInline):
    """
    Inline admin for quote items.
    """
    model = QuoteItem
    extra = 1
    fields = ('product', 'quantity', 'unit_price', 'discount_rate', 'line_total', 'lead_time', 'notes')
    readonly_fields = ('line_total',)


@admin.register(Quote)
class QuoteAdmin(ImportExportModelAdmin):
    """
    Admin configuration for Quote model with import/export support.
    """
    resource_class = QuoteResource
    list_display = (
        'quote_number',
        'quote_type',
        'customer',
        'quote_date',
        'valid_until',
        'total_amount',
        'currency',
        'status',
        'created_at',
    )
    list_filter = ('quote_type', 'status', 'currency', 'quote_date')
    search_fields = ('quote_number', 'customer__name', 'reference_number')
    readonly_fields = (
        'quote_number',
        'subtotal',
        'tax_amount',
        'discount_amount',
        'total_amount',
        'total_amount_cny',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )
    inlines = [QuoteItemInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('quote_number', 'quote_type', 'status', 'customer', 'contact_person')
        }),
        ('日期信息', {
            'fields': ('quote_date', 'valid_until')
        }),
        ('销售信息', {
            'fields': ('sales_rep',)
        }),
        ('财务信息', {
            'fields': (
                'currency',
                'exchange_rate',
                'subtotal',
                'tax_rate',
                'tax_amount',
                'discount_rate',
                'discount_amount',
                'total_amount',
                'total_amount_cny',
            )
        }),
        ('条款', {
            'fields': ('payment_terms', 'delivery_terms', 'warranty_terms')
        }),
        ('其他信息', {
            'fields': ('reference_number', 'notes', 'converted_order')
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            # Generate quote number if creating new quote
            from common.utils import DocumentNumberGenerator
            if not obj.quote_number:
                obj.quote_number = DocumentNumberGenerator.generate('QT')
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class SalesOrderItemInline(admin.TabularInline):
    """
    Inline admin for sales order items.
    """
    model = SalesOrderItem
    extra = 1
    fields = ('product', 'quantity', 'unit_price', 'discount_rate', 'line_total', 'delivered_quantity')
    readonly_fields = ('line_total',)


@admin.register(SalesOrder)
class SalesOrderAdmin(ImportExportModelAdmin):
    """
    Admin configuration for Sales Order model with import/export support.
    """
    resource_class = SalesOrderResource
    list_display = (
        'order_number',
        'customer',
        'order_date',
        'total_amount',
        'status',
        'payment_status',
        'created_at',
    )
    list_filter = ('status', 'payment_status', 'order_date')
    search_fields = ('order_number', 'customer__name', 'reference_number')
    readonly_fields = (
        'order_number',
        'subtotal',
        'tax_amount',
        'discount_amount',
        'total_amount',
        'created_at',
        'updated_at',
    )
    inlines = [SalesOrderItemInline]


class DeliveryItemInline(admin.TabularInline):
    """
    Inline admin for delivery items.
    """
    model = DeliveryItem
    extra = 1
    fields = ('order_item', 'quantity', 'batch_number', 'notes')


@admin.register(Delivery)
class DeliveryAdmin(ImportExportModelAdmin):
    """
    Admin configuration for Delivery model with import/export support.
    """
    resource_class = DeliveryResource
    list_display = (
        'delivery_number',
        'sales_order',
        'planned_date',
        'actual_date',
        'status',
        'created_at',
    )
    list_filter = ('status', 'planned_date', 'actual_date')
    search_fields = ('delivery_number', 'sales_order__order_number', 'tracking_number')
    readonly_fields = ('delivery_number', 'created_at', 'updated_at')
    inlines = [DeliveryItemInline]


class SalesReturnItemInline(admin.TabularInline):
    """
    Inline admin for sales return items.
    """
    model = SalesReturnItem
    extra = 1
    fields = ('order_item', 'quantity', 'unit_price', 'line_total', 'condition')
    readonly_fields = ('line_total',)


@admin.register(SalesReturn)
class SalesReturnAdmin(ImportExportModelAdmin):
    """
    Admin configuration for Sales Return model with import/export support.
    """
    resource_class = SalesReturnResource
    list_display = (
        'return_number',
        'sales_order',
        'return_date',
        'refund_amount',
        'status',
        'reason',
        'created_at',
    )
    list_filter = ('status', 'reason', 'return_date')
    search_fields = ('return_number', 'sales_order__order_number')
    readonly_fields = ('return_number', 'created_at', 'updated_at')
    inlines = [SalesReturnItemInline]


# ============================================
# 打印模板管理已移至 core 模块
# ============================================
# PrintTemplate 和 DefaultTemplateMapping 的 Admin 配置
# 已移动到 apps/core/admin.py
#
# 如需管理打印模板,请前往:
# - Admin 后台 → Core → 打印模板
# - Admin 后台 → Core → 默认模板配置


# ============================================
# 销售借用管理
# ============================================
class SalesLoanItemInline(admin.TabularInline):
    """
    Inline admin for sales loan items.
    """
    model = SalesLoanItem
    extra = 1
    fields = (
        'product',
        'quantity',
        'returned_quantity',
        'conversion_quantity',
        'conversion_unit_price',
        'batch_number',
        'specifications',
        'notes',
    )
    readonly_fields = ()


@admin.register(SalesLoan)
class SalesLoanAdmin(ImportExportModelAdmin):
    """
    Admin configuration for Sales Loan model with import/export support.
    """
    resource_class = SalesLoanResource
    list_display = (
        'loan_number',
        'customer',
        'salesperson',
        'loan_date',
        'expected_return_date',
        'status',
        'created_at',
    )
    list_filter = ('status', 'loan_date', 'expected_return_date')
    search_fields = ('loan_number', 'customer__name', 'purpose')
    readonly_fields = (
        'loan_number',
        'converted_order',
        'conversion_approved_by',
        'conversion_approved_at',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )
    inlines = [SalesLoanItemInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('loan_number', 'customer', 'salesperson', 'status')
        }),
        ('日期信息', {
            'fields': ('loan_date', 'expected_return_date')
        }),
        ('借用详情', {
            'fields': ('purpose', 'delivery_address', 'contact_person', 'contact_phone', 'notes')
        }),
        ('转销售信息', {
            'fields': (
                'converted_order',
                'conversion_approved_by',
                'conversion_approved_at',
                'conversion_notes',
            )
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            # Generate loan number if creating new loan
            from common.utils import DocumentNumberGenerator
            if not obj.loan_number:
                obj.loan_number = DocumentNumberGenerator.generate('sales_loan')
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

