from django.contrib import admin
from django.utils.html import format_html
from .models import (
    EcommPlatform, WooShopConfig, EcommProduct,
    SyncStrategy, SyncLog, ProductChangeLog
)


@admin.register(EcommPlatform)
class EcommPlatformAdmin(admin.ModelAdmin):
    """电商平台管理"""
    list_display = ['name', 'platform_type', 'base_url', 'is_active', 'created_at']
    list_filter = ['platform_type', 'is_active']
    search_fields = ['name', 'base_url']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WooShopConfig)
class WooShopConfigAdmin(admin.ModelAdmin):
    """WooCommerce配置管理"""
    list_display = ['shop_name', 'shop_url', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['shop_name', 'shop_url']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('shop_name', 'shop_url', 'is_active')
        }),
        ('API凭证', {
            'fields': ('consumer_key', 'consumer_secret'),
            'classes': ('collapse',),
        }),
        ('默认配置', {
            'fields': ('default_category_id',),
        }),
    )


@admin.register(EcommProduct)
class EcommProductAdmin(admin.ModelAdmin):
    """电商商品管理"""
    list_display = ['external_id', 'platform', 'product', 'sync_status', 'last_synced_at', 'is_delisted']
    list_filter = ['platform', 'sync_status', 'is_delisted']
    search_fields = ['external_id', 'external_url', 'product__name', 'product__code']
    readonly_fields = ['created_at', 'updated_at', 'last_scraped_at']
    date_hierarchy = 'last_synced_at'
    fieldsets = (
        ('平台信息', {
            'fields': ('platform', 'external_id', 'external_url', 'is_delisted')
        }),
        ('产品关联', {
            'fields': ('product',),
        }),
        ('同步状态', {
            'fields': ('sync_status', 'woo_product_id', 'last_synced_at', 'last_scraped_at')
        }),
        ('原始数据', {
            'fields': ('raw_data',),
            'classes': ('collapse',),
        }),
    )


@admin.register(SyncStrategy)
class SyncStrategyAdmin(admin.ModelAdmin):
    """同步策略管理"""
    list_display = ['name', 'platform', 'strategy_type', 'sync_interval_hours', 'batch_size', 'is_active', 'next_sync_at']
    list_filter = ['platform', 'strategy_type', 'is_active']
    search_fields = ['name']
    readonly_fields = ['last_sync_at', 'next_sync_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'platform', 'strategy_type', 'is_active')
        }),
        ('同步配置', {
            'fields': ('update_fields', 'sync_interval_hours', 'batch_size')
        }),
        ('同步记录', {
            'fields': ('last_sync_at', 'next_sync_at'),
        }),
    )


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    """同步日志管理"""
    list_display = ['id', 'log_type', 'platform', 'status', 'records_processed', 'records_succeeded', 'execution_time', 'created_at']
    list_filter = ['log_type', 'status', 'platform']
    search_fields = ['error_message']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ProductChangeLog)
class ProductChangeLogAdmin(admin.ModelAdmin):
    """商品变更日志管理"""
    list_display = ['id', 'ecomm_product', 'change_type', 'synced_to_woo', 'woo_synced_at', 'created_at']
    list_filter = ['change_type', 'synced_to_woo']
    search_fields = ['ecomm_product__external_id', 'ecomm_product__product__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
