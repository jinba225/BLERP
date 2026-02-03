"""
Inventory 模块的导入导出资源配置
"""
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateWidget, DecimalWidget
from .models import Warehouse, InventoryTransaction, StockAdjustment
from products.models import Product


class WarehouseResource(resources.ModelResource):
    """仓库导入导出资源"""

    class Meta:
        model = Warehouse
        fields = (
            'id', 'name', 'code', 'warehouse_type', 'location',
            'manager', 'phone', 'address',
            'is_active', 'created_at', 'updated_at'
        )
        export_order = fields
        import_id_fields = ['code']
        skip_unchanged = True
        report_skipped = True


class StockMovementResource(resources.ModelResource):
    """库存变动记录导入导出资源"""

    product = fields.Field(
        column_name='产品',
        attribute='product',
        widget=ForeignKeyWidget(Product, 'code')
    )

    warehouse = fields.Field(
        column_name='仓库',
        attribute='warehouse',
        widget=ForeignKeyWidget(Warehouse, 'code')
    )

    movement_date = fields.Field(
        column_name='变动日期',
        attribute='movement_date',
        widget=DateWidget(format='%Y-%m-%d')
    )

    quantity = fields.Field(
        column_name='变动数量',
        attribute='quantity',
        widget=DecimalWidget()
    )

    class Meta:
        model = InventoryTransaction
        fields = (
            'id', 'transaction_type', 'product', 'warehouse',
            'quantity', 'reference_type', 'reference_id',
            'movement_date', 'created_at', 'updated_at'
        )
        export_order = fields
        import_id_fields = ['id']
        skip_unchanged = True
        report_skipped = True


class StockAdjustmentResource(resources.ModelResource):
    """库存调整单导入导出资源"""

    warehouse = fields.Field(
        column_name='仓库',
        attribute='warehouse',
        widget=ForeignKeyWidget(Warehouse, 'code')
    )

    adjustment_date = fields.Field(
        column_name='调整日期',
        attribute='adjustment_date',
        widget=DateWidget(format='%Y-%m-%d')
    )

    class Meta:
        model = StockAdjustment
        fields = (
            'id', 'adjustment_number', 'adjustment_date', 'adjustment_type',
            'warehouse', 'reason', 'status',
            'created_at', 'updated_at'
        )
        export_order = fields
        import_id_fields = ['adjustment_number']
        skip_unchanged = True
        report_skipped = True
