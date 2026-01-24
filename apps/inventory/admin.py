"""
Inventory admin configuration.
"""
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import (
    Warehouse, Location, InventoryStock, InventoryTransaction,
    StockAdjustment, StockTransfer, StockTransferItem,
    StockCount, StockCountItem
)
from .resources import (
    WarehouseResource,
    StockMovementResource,
    StockAdjustmentResource,
)


class LocationInline(admin.TabularInline):
    """库位内联编辑"""
    model = Location
    extra = 1
    fields = ['code', 'name', 'aisle', 'shelf', 'level', 'position', 'is_active']


@admin.register(Warehouse)
class WarehouseAdmin(ImportExportModelAdmin):
    """仓库管理 - 含导入导出功能"""
    resource_class = WarehouseResource
    list_display = ['code', 'name', 'warehouse_type', 'manager', 'phone', 'capacity', 'is_active', 'created_at']
    list_filter = ['warehouse_type', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'address']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    list_per_page = 50
    inlines = [LocationInline]

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'warehouse_type', 'address')
        }),
        ('管理信息', {
            'fields': ('manager', 'phone', 'capacity')
        }),
        ('状态', {
            'fields': ('is_active',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """库位管理"""
    list_display = ['warehouse', 'code', 'name', 'aisle', 'shelf', 'level', 'position', 'capacity', 'is_active']
    list_filter = ['warehouse', 'is_active', 'created_at']
    search_fields = ['warehouse__name', 'code', 'name']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50


@admin.register(InventoryStock)
class InventoryStockAdmin(admin.ModelAdmin):
    """库存管理"""
    list_display = [
        'product', 'warehouse', 'location', 'quantity',
        'reserved_quantity', 'available_quantity', 'cost_price',
        'last_in_date', 'last_out_date', 'is_low_stock'
    ]
    list_filter = ['warehouse', 'created_at', 'last_in_date', 'last_out_date']
    search_fields = ['product__name', 'product__code', 'warehouse__name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'available_quantity']
    list_per_page = 50

    fieldsets = (
        ('基本信息', {
            'fields': ('product', 'warehouse', 'location')
        }),
        ('库存数量', {
            'fields': ('quantity', 'reserved_quantity', 'available_quantity', 'cost_price')
        }),
        ('日期信息', {
            'fields': ('last_in_date', 'last_out_date')
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def available_quantity(self, obj):
        """显示可用库存"""
        return obj.available_quantity
    available_quantity.short_description = '可用数量'

    def is_low_stock(self, obj):
        """显示是否低库存"""
        return '是' if obj.is_low_stock else '否'
    is_low_stock.short_description = '低库存'


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(ImportExportModelAdmin):
    """库存交易管理 - 含导入导出功能"""
    resource_class = StockMovementResource
    list_display = [
        'transaction_type', 'product', 'warehouse', 'location',
        'quantity', 'unit_cost', 'total_cost', 'reference_type',
        'reference_number', 'transaction_date', 'operator'
    ]
    list_filter = ['transaction_type', 'reference_type', 'warehouse', 'transaction_date', 'created_at']
    search_fields = ['product__name', 'reference_number', 'batch_number', 'serial_number']
    readonly_fields = ['transaction_date', 'total_cost', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'transaction_date'

    fieldsets = (
        ('基本信息', {
            'fields': ('transaction_type', 'product', 'warehouse', 'location')
        }),
        ('数量与成本', {
            'fields': ('quantity', 'unit_cost', 'total_cost')
        }),
        ('关联单据', {
            'fields': ('reference_type', 'reference_id', 'reference_number')
        }),
        ('批次与序列号', {
            'fields': ('batch_number', 'serial_number', 'expiry_date'),
            'classes': ('collapse',)
        }),
        ('其他信息', {
            'fields': ('operator', 'notes')
        }),
        ('系统信息', {
            'fields': ('transaction_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(ImportExportModelAdmin):
    """库存调整管理 - 含导入导出功能"""
    resource_class = StockAdjustmentResource
    list_display = [
        'adjustment_number', 'adjustment_type', 'reason', 'product',
        'warehouse', 'original_quantity', 'adjusted_quantity',
        'difference', 'is_approved', 'approved_by', 'created_at'
    ]
    list_filter = ['adjustment_type', 'reason', 'is_approved', 'warehouse', 'created_at']
    search_fields = ['adjustment_number', 'product__name', 'notes']
    readonly_fields = ['difference', 'created_at', 'updated_at', 'created_by', 'updated_by']
    list_per_page = 50

    fieldsets = (
        ('基本信息', {
            'fields': ('adjustment_number', 'adjustment_type', 'reason', 'product', 'warehouse', 'location')
        }),
        ('数量调整', {
            'fields': ('original_quantity', 'adjusted_quantity', 'difference')
        }),
        ('审核信息', {
            'fields': ('is_approved', 'approved_by', 'approved_at')
        }),
        ('其他信息', {
            'fields': ('notes',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


class StockTransferItemInline(admin.TabularInline):
    """库存调拨明细内联编辑"""
    model = StockTransferItem
    extra = 1
    fields = ['product', 'requested_quantity', 'shipped_quantity', 'received_quantity', 'unit_cost']


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    """库存调拨管理"""
    list_display = [
        'transfer_number', 'from_warehouse', 'to_warehouse', 'status',
        'transfer_date', 'expected_arrival_date', 'actual_arrival_date',
        'approved_by', 'created_at'
    ]
    list_filter = ['status', 'from_warehouse', 'to_warehouse', 'transfer_date', 'created_at']
    search_fields = ['transfer_number', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    list_per_page = 50
    inlines = [StockTransferItemInline]
    date_hierarchy = 'transfer_date'

    fieldsets = (
        ('基本信息', {
            'fields': ('transfer_number', 'from_warehouse', 'to_warehouse', 'status')
        }),
        ('日期信息', {
            'fields': ('transfer_date', 'expected_arrival_date', 'actual_arrival_date')
        }),
        ('审核信息', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('其他信息', {
            'fields': ('notes',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StockTransferItem)
class StockTransferItemAdmin(admin.ModelAdmin):
    """调拨明细管理"""
    list_display = [
        'transfer', 'product', 'requested_quantity',
        'shipped_quantity', 'received_quantity', 'unit_cost'
    ]
    list_filter = ['transfer__status', 'created_at']
    search_fields = ['transfer__transfer_number', 'product__name', 'batch_number']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50


class StockCountItemInline(admin.TabularInline):
    """盘点明细内联编辑"""
    model = StockCountItem
    extra = 0
    fields = ['product', 'location', 'system_quantity', 'counted_quantity', 'difference']
    readonly_fields = ['difference']


@admin.register(StockCount)
class StockCountAdmin(admin.ModelAdmin):
    """库存盘点管理"""
    list_display = [
        'count_number', 'count_type', 'warehouse', 'status',
        'planned_date', 'start_date', 'end_date', 'supervisor', 'created_at'
    ]
    list_filter = ['count_type', 'status', 'warehouse', 'planned_date', 'created_at']
    search_fields = ['count_number', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    list_per_page = 50
    inlines = [StockCountItemInline]
    filter_horizontal = ['counters']
    date_hierarchy = 'planned_date'

    fieldsets = (
        ('基本信息', {
            'fields': ('count_number', 'count_type', 'warehouse', 'status')
        }),
        ('日期信息', {
            'fields': ('planned_date', 'start_date', 'end_date')
        }),
        ('人员信息', {
            'fields': ('supervisor', 'counters')
        }),
        ('其他信息', {
            'fields': ('notes',)
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StockCountItem)
class StockCountItemAdmin(admin.ModelAdmin):
    """盘点明细管理"""
    list_display = [
        'count', 'product', 'location', 'system_quantity',
        'counted_quantity', 'difference', 'counter', 'count_time'
    ]
    list_filter = ['count__status', 'created_at']
    search_fields = ['count__count_number', 'product__name', 'batch_number']
    readonly_fields = ['difference', 'created_at', 'updated_at']
    list_per_page = 50
