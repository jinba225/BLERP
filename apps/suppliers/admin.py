"""
Supplier admin configuration.
"""
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import (
    SupplierCategory, Supplier, SupplierContact,
    SupplierProduct, SupplierEvaluation
)
from .resources import SupplierResource, SupplierContactResource


@admin.register(SupplierCategory)
class SupplierCategoryAdmin(admin.ModelAdmin):
    """供应商分类管理"""
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    list_per_page = 50

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'description')
        }),
        ('状态', {
            'fields': ('is_active',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


class SupplierContactInline(admin.TabularInline):
    """供应商联系人内联编辑"""
    model = SupplierContact
    extra = 1
    fields = ['name', 'position', 'contact_type', 'phone', 'mobile', 'email', 'is_primary']


class SupplierProductInline(admin.TabularInline):
    """供应商产品内联编辑"""
    model = SupplierProduct
    extra = 0
    fields = ['product', 'price', 'currency', 'min_order_qty', 'lead_time', 'is_preferred']
    readonly_fields = []


@admin.register(Supplier)
class SupplierAdmin(ImportExportModelAdmin):
    """供应商管理 - 含导入导出功能"""
    resource_class = SupplierResource
    list_display = [
        'code', 'name', 'level',
        'buyer', 'is_approved', 'is_active', 'created_at'
    ]
    list_filter = ['level', 'is_active', 'is_approved', 'category', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 'updated_by',
        'average_rating', 'first_order_date', 'last_order_date'
    ]
    list_per_page = 50
    inlines = [SupplierContactInline, SupplierProductInline]

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'category', 'level')
        }),
        ('联系信息', {
            'fields': ('website',)
        }),
        ('地址信息', {
            'fields': ('address', 'city', 'province', 'country', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('业务信息', {
            'fields': ('tax_number', 'registration_number', 'legal_representative', 'business_license'),
            'classes': ('collapse',)
        }),
        ('财务信息', {
            'fields': ('payment_terms', 'currency', 'bank_name', 'bank_account'),
            'classes': ('collapse',)
        }),
        ('采购信息', {
            'fields': ('buyer', 'lead_time', 'min_order_amount')
        }),
        ('质量与评级', {
            'fields': (
                'quality_rating', 'delivery_rating', 'service_rating',
                'average_rating', 'certifications'
            )
        }),
        ('状态设置', {
            'fields': ('is_active', 'is_approved', 'notes')
        }),
        ('系统信息', {
            'fields': ('first_order_date', 'last_order_date', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def average_rating(self, obj):
        """显示平均评级"""
        return f"{obj.average_rating:.1f}"
    average_rating.short_description = '综合评级'


@admin.register(SupplierContact)
class SupplierContactAdmin(ImportExportModelAdmin):
    """供应商联系人管理 - 含导入导出功能"""
    resource_class = SupplierContactResource
    list_display = [
        'supplier', 'name', 'position', 'contact_type',
        'phone', 'mobile', 'email', 'is_primary', 'is_active'
    ]
    list_filter = ['contact_type', 'is_primary', 'is_active', 'created_at']
    search_fields = ['supplier__name', 'name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50


@admin.register(SupplierProduct)
class SupplierProductAdmin(admin.ModelAdmin):
    """供应商产品管理"""
    list_display = [
        'supplier', 'product', 'price', 'currency',
        'min_order_qty', 'lead_time', 'is_preferred', 'is_active'
    ]
    list_filter = ['is_preferred', 'is_active', 'currency', 'created_at']
    search_fields = ['supplier__name', 'product__name', 'supplier_product_code']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50


@admin.register(SupplierEvaluation)
class SupplierEvaluationAdmin(admin.ModelAdmin):
    """供应商评估管理"""
    list_display = [
        'supplier', 'evaluation_period', 'year', 'quarter', 'month',
        'overall_score', 'is_approved', 'evaluator', 'created_at'
    ]
    list_filter = ['evaluation_period', 'year', 'is_approved', 'created_at']
    search_fields = ['supplier__name', 'strengths', 'weaknesses']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'overall_score']
    list_per_page = 50

    fieldsets = (
        ('基本信息', {
            'fields': ('supplier', 'evaluation_period', 'year', 'quarter', 'month')
        }),
        ('评分', {
            'fields': ('quality_score', 'delivery_score', 'service_score', 'price_score', 'overall_score')
        }),
        ('评价内容', {
            'fields': ('strengths', 'weaknesses', 'recommendations')
        }),
        ('评估结果', {
            'fields': ('is_approved', 'evaluator')
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
