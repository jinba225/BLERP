"""
Customers 模块的导入导出资源配置
"""
from import_export import resources, fields
from import_export.widgets import DateWidget
from .models import Customer, CustomerContact
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomerResource(resources.ModelResource):
    """客户导入导出资源"""

    established_date = fields.Field(
        column_name="成立日期", attribute="established_date", widget=DateWidget(format="%Y-%m-%d")
    )

    class Meta:
        model = Customer
        fields = (
            "id",
            "name",
            "code",
            "customer_type",
            "industry",
            "credit_level",
            "payment_terms",
            "tax_number",
            "legal_representative",
            "established_date",
            "contact_person",
            "phone",
            "email",
            "fax",
            "website",
            "address",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["code"]
        skip_unchanged = True
        report_skipped = True


class CustomerContactResource(resources.ModelResource):
    """客户联系人导入导出资源"""

    class Meta:
        model = CustomerContact
        fields = (
            "id",
            "customer",
            "name",
            "position",
            "department",
            "phone",
            "mobile",
            "email",
            "wechat",
            "is_primary",
            "notes",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["id"]
        skip_unchanged = True
        report_skipped = True
