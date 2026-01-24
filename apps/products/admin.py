"""
Product admin configuration.
"""
from django.contrib import admin
from django.utils.html import format_html
from mptt.admin import MPTTModelAdmin
from import_export.admin import ImportExportModelAdmin
from .models import (
    ProductCategory, Brand, Unit, Product, ProductImage,
    ProductAttribute, ProductAttributeValue, ProductPrice
)
from .resources import ProductCategoryResource, ProductResource


@admin.register(ProductCategory)
class ProductCategoryAdmin(ImportExportModelAdmin, MPTTModelAdmin):
    """产品分类管理 - 含导入导出功能"""
    resource_class = ProductCategoryResource
    list_display = ['name', 'code', 'parent', 'sort_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    list_per_page = 50

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'parent', 'description')
        }),
        ('显示设置', {
            'fields': ('image', 'sort_order', 'is_active')
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """品牌管理"""
    list_display = ['name', 'code', 'country', 'website', 'is_active', 'created_at']
    list_filter = ['is_active', 'country', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    list_per_page = 50

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'description')
        }),
        ('品牌详情', {
            'fields': ('logo', 'website', 'country')
        }),
        ('状态', {
            'fields': ('is_active',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    """计量单位管理"""
    list_display = ['name', 'symbol', 'unit_type', 'is_active', 'created_at']
    list_filter = ['unit_type', 'is_active', 'created_at']
    search_fields = ['name', 'symbol', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    list_per_page = 50

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'symbol', 'unit_type', 'description')
        }),
        ('状态', {
            'fields': ('is_active',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


class ProductImageInline(admin.TabularInline):
    """产品图片内联编辑"""
    model = ProductImage
    extra = 1
    fields = ['image', 'title', 'sort_order', 'is_main']
    readonly_fields = []


class ProductAttributeValueInline(admin.TabularInline):
    """产品属性值内联编辑"""
    model = ProductAttributeValue
    extra = 0
    fields = ['attribute', 'value']
    readonly_fields = []


class ProductPriceInline(admin.TabularInline):
    """产品价格历史内联编辑"""
    model = ProductPrice
    extra = 0
    fields = ['price_type', 'price', 'effective_date', 'end_date', 'is_active']
    readonly_fields = []


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    """产品管理 - 含导入导出功能"""
    resource_class = ProductResource
    list_display = [
        'code', 'name', 'category', 'brand', 'product_type',
        'unit', 'selling_price', 'cost_price', 'status', 'created_at'
    ]
    list_filter = ['product_type', 'status', 'category', 'brand', 'created_at']
    search_fields = ['name', 'code', 'barcode', 'model', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'profit_margin', 'volume']
    list_per_page = 50
    inlines = [ProductImageInline, ProductAttributeValueInline, ProductPriceInline]

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'barcode', 'category', 'brand', 'product_type', 'status')
        }),
        ('描述与规格', {
            'fields': ('description', 'specifications', 'model')
        }),
        ('单位与尺寸', {
            'fields': ('unit', 'weight', 'length', 'width', 'height', 'volume')
        }),
        ('价格信息', {
            'fields': ('cost_price', 'selling_price', 'profit_margin')
        }),
        ('库存设置', {
            'fields': ('min_stock', 'max_stock', 'reorder_point'),
            'classes': ('collapse',)
        }),
        ('图片', {
            'fields': ('main_image',)
        }),
        ('其他信息', {
            'fields': ('warranty_period', 'shelf_life', 'notes'),
            'classes': ('collapse',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def profit_margin(self, obj):
        """显示利润率"""
        return f"{obj.profit_margin:.2f}%"
    profit_margin.short_description = '利润率'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """产品图片管理"""
    list_display = ['product', 'title', 'is_main', 'sort_order', 'created_at']
    list_filter = ['is_main', 'created_at']
    search_fields = ['product__name', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    """产品属性管理"""
    list_display = ['name', 'code', 'attribute_type', 'is_required', 'is_filterable', 'sort_order', 'is_active']
    list_filter = ['attribute_type', 'is_required', 'is_filterable', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    list_per_page = 50

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'attribute_type', 'description')
        }),
        ('设置', {
            'fields': ('is_required', 'is_filterable', 'sort_order', 'is_active')
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    """产品属性值管理"""
    list_display = ['product', 'attribute', 'value', 'created_at']
    list_filter = ['attribute', 'created_at']
    search_fields = ['product__name', 'attribute__name', 'value']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50


@admin.register(ProductPrice)
class ProductPriceAdmin(admin.ModelAdmin):
    """产品价格历史管理"""
    list_display = ['product', 'price_type', 'price', 'effective_date', 'end_date', 'is_active', 'created_at']
    list_filter = ['price_type', 'is_active', 'effective_date', 'created_at']
    search_fields = ['product__name', 'reason']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    list_per_page = 50

    fieldsets = (
        ('基本信息', {
            'fields': ('product', 'price_type', 'price')
        }),
        ('生效日期', {
            'fields': ('effective_date', 'end_date', 'is_active')
        }),
        ('调价说明', {
            'fields': ('reason',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
