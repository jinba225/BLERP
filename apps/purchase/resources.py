"""
Purchase 模块的导入导出资源配置
"""
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateWidget, DecimalWidget
from .models import (
    PurchaseOrder, PurchaseOrderItem,
    PurchaseReceipt, PurchaseReceiptItem,
    PurchaseReturn, PurchaseReturnItem,
    SupplierQuotation, SupplierQuotationItem,
)
from django.contrib.auth import get_user_model
from apps.suppliers.models import Supplier
from apps.products.models import Product

User = get_user_model()


class PurchaseOrderResource(resources.ModelResource):
    """采购订单导入导出资源"""

    supplier = fields.Field(
        column_name='供应商',
        attribute='supplier',
        widget=ForeignKeyWidget(Supplier, 'name')
    )

    order_date = fields.Field(
        column_name='订单日期',
        attribute='order_date',
        widget=DateWidget(format='%Y-%m-%d')
    )

    expected_delivery_date = fields.Field(
        column_name='期望交货日期',
        attribute='expected_delivery_date',
        widget=DateWidget(format='%Y-%m-%d')
    )

    total_amount = fields.Field(
        column_name='含税总金额',
        attribute='total_amount',
        widget=DecimalWidget()
    )

    class Meta:
        model = PurchaseOrder
        fields = (
            'id', 'order_number', 'order_date', 'expected_delivery_date',
            'supplier', 'total_amount', 'tax_rate', 'tax_amount',
            'status', 'notes',
            'created_at', 'updated_at'
        )
        export_order = fields
        import_id_fields = ['order_number']
        skip_unchanged = True
        report_skipped = True


class PurchaseReceiptResource(resources.ModelResource):
    """采购收货导入导出资源"""

    purchase_order = fields.Field(
        column_name='采购订单',
        attribute='purchase_order',
        widget=ForeignKeyWidget(PurchaseOrder, 'order_number')
    )

    supplier = fields.Field(
        column_name='供应商',
        attribute='supplier',
        widget=ForeignKeyWidget(Supplier, 'name')
    )

    receipt_date = fields.Field(
        column_name='收货日期',
        attribute='receipt_date',
        widget=DateWidget(format='%Y-%m-%d')
    )

    class Meta:
        model = PurchaseReceipt
        fields = (
            'id', 'receipt_number', 'receipt_date',
            'purchase_order', 'supplier', 'status', 'notes',
            'created_at', 'updated_at'
        )
        export_order = fields
        import_id_fields = ['receipt_number']
        skip_unchanged = True
        report_skipped = True


class PurchaseReturnResource(resources.ModelResource):
    """采购退货导入导出资源"""

    purchase_order = fields.Field(
        column_name='采购订单',
        attribute='purchase_order',
        widget=ForeignKeyWidget(PurchaseOrder, 'order_number')
    )

    supplier = fields.Field(
        column_name='供应商',
        attribute='supplier',
        widget=ForeignKeyWidget(Supplier, 'name')
    )

    return_date = fields.Field(
        column_name='退货日期',
        attribute='return_date',
        widget=DateWidget(format='%Y-%m-%d')
    )

    class Meta:
        model = PurchaseReturn
        fields = (
            'id', 'return_number', 'return_date',
            'purchase_order', 'supplier', 'return_reason', 'status', 'notes',
            'created_at', 'updated_at'
        )
        export_order = fields
        import_id_fields = ['return_number']
        skip_unchanged = True
        report_skipped = True


class SupplierQuotationResource(resources.ModelResource):
    """供应商报价导入导出资源"""

    supplier = fields.Field(
        column_name='供应商',
        attribute='supplier',
        widget=ForeignKeyWidget(Supplier, 'name')
    )

    quotation_date = fields.Field(
        column_name='报价日期',
        attribute='quotation_date',
        widget=DateWidget(format='%Y-%m-%d')
    )

    valid_until = fields.Field(
        column_name='有效期至',
        attribute='valid_until',
        widget=DateWidget(format='%Y-%m-%d')
    )

    class Meta:
        model = SupplierQuotation
        fields = (
            'id', 'quotation_number', 'quotation_date', 'valid_until',
            'supplier', 'status', 'notes',
            'created_at', 'updated_at'
        )
        export_order = fields
        import_id_fields = ['quotation_number']
        skip_unchanged = True
        report_skipped = True
