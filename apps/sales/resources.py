"""
Sales 模块的导入导出资源配置
"""
from customers.models import Customer
from django.contrib.auth import get_user_model
from import_export import fields, resources
from import_export.widgets import DateWidget, DecimalWidget, ForeignKeyWidget
from inventory.models import Warehouse
from products.models import Product

from .models import (
    Delivery,
    DeliveryItem,
    Quote,
    QuoteItem,
    SalesLoan,
    SalesLoanItem,
    SalesOrder,
    SalesOrderItem,
    SalesReturn,
    SalesReturnItem,
)

User = get_user_model()


class QuoteResource(resources.ModelResource):
    """报价单导入导出资源"""

    customer = fields.Field(
        column_name="客户", attribute="customer", widget=ForeignKeyWidget(Customer, "name")
    )

    quote_date = fields.Field(
        column_name="报价日期", attribute="quote_date", widget=DateWidget(format="%Y-%m-%d")
    )

    valid_until = fields.Field(
        column_name="有效期至", attribute="valid_until", widget=DateWidget(format="%Y-%m-%d")
    )

    total_amount = fields.Field(
        column_name="含税总金额", attribute="total_amount", widget=DecimalWidget()
    )

    class Meta:
        model = Quote
        fields = (
            "id",
            "quote_number",
            "quote_date",
            "valid_until",
            "customer",
            "total_amount",
            "tax_rate",
            "tax_amount",
            "status",
            "notes",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["quote_number"]
        skip_unchanged = True
        report_skipped = True


class SalesOrderResource(resources.ModelResource):
    """销售订单导入导出资源"""

    customer = fields.Field(
        column_name="客户", attribute="customer", widget=ForeignKeyWidget(Customer, "name")
    )

    quote = fields.Field(
        column_name="关联报价单", attribute="quote", widget=ForeignKeyWidget(Quote, "quote_number")
    )

    order_date = fields.Field(
        column_name="订单日期", attribute="order_date", widget=DateWidget(format="%Y-%m-%d")
    )

    delivery_date = fields.Field(
        column_name="交货日期", attribute="delivery_date", widget=DateWidget(format="%Y-%m-%d")
    )

    total_amount = fields.Field(
        column_name="含税总金额", attribute="total_amount", widget=DecimalWidget()
    )

    class Meta:
        model = SalesOrder
        fields = (
            "id",
            "order_number",
            "order_date",
            "delivery_date",
            "customer",
            "quote",
            "total_amount",
            "tax_rate",
            "tax_amount",
            "status",
            "notes",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["order_number"]
        skip_unchanged = True
        report_skipped = True


class DeliveryResource(resources.ModelResource):
    """发货单导入导出资源"""

    sales_order = fields.Field(
        column_name="销售订单",
        attribute="sales_order",
        widget=ForeignKeyWidget(SalesOrder, "order_number"),
    )

    customer = fields.Field(
        column_name="客户", attribute="customer", widget=ForeignKeyWidget(Customer, "name")
    )

    warehouse = fields.Field(
        column_name="发货仓库", attribute="warehouse", widget=ForeignKeyWidget(Warehouse, "name")
    )

    delivery_date = fields.Field(
        column_name="发货日期", attribute="delivery_date", widget=DateWidget(format="%Y-%m-%d")
    )

    total_amount = fields.Field(
        column_name="含税总金额", attribute="total_amount", widget=DecimalWidget()
    )

    class Meta:
        model = Delivery
        fields = (
            "id",
            "delivery_number",
            "delivery_date",
            "sales_order",
            "customer",
            "warehouse",
            "total_amount",
            "status",
            "notes",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["delivery_number"]
        skip_unchanged = True
        report_skipped = True


class SalesReturnResource(resources.ModelResource):
    """销售退货单导入导出资源"""

    sales_order = fields.Field(
        column_name="原销售订单",
        attribute="sales_order",
        widget=ForeignKeyWidget(SalesOrder, "order_number"),
    )

    customer = fields.Field(
        column_name="客户", attribute="customer", widget=ForeignKeyWidget(Customer, "name")
    )

    return_date = fields.Field(
        column_name="退货日期", attribute="return_date", widget=DateWidget(format="%Y-%m-%d")
    )

    total_amount = fields.Field(
        column_name="退货总金额", attribute="total_amount", widget=DecimalWidget()
    )

    class Meta:
        model = SalesReturn
        fields = (
            "id",
            "return_number",
            "return_date",
            "sales_order",
            "customer",
            "total_amount",
            "return_reason",
            "status",
            "notes",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["return_number"]
        skip_unchanged = True
        report_skipped = True


class SalesLoanResource(resources.ModelResource):
    """销售借货单导入导出资源"""

    customer = fields.Field(
        column_name="客户", attribute="customer", widget=ForeignKeyWidget(Customer, "name")
    )

    loan_date = fields.Field(
        column_name="借货日期", attribute="loan_date", widget=DateWidget(format="%Y-%m-%d")
    )

    expected_return_date = fields.Field(
        column_name="预计归还日期", attribute="expected_return_date", widget=DateWidget(format="%Y-%m-%d")
    )

    actual_return_date = fields.Field(
        column_name="实际归还日期", attribute="actual_return_date", widget=DateWidget(format="%Y-%m-%d")
    )

    class Meta:
        model = SalesLoan
        fields = (
            "id",
            "loan_number",
            "loan_date",
            "expected_return_date",
            "actual_return_date",
            "customer",
            "status",
            "notes",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["loan_number"]
        skip_unchanged = True
        report_skipped = True
