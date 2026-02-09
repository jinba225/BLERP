"""
Suppliers 模块的导入导出资源配置
"""
from import_export import resources

from .models import Supplier, SupplierContact


class SupplierResource(resources.ModelResource):
    """供应商导入导出资源"""

    class Meta:
        model = Supplier
        fields = (
            "id",
            "name",
            "code",
            "supplier_type",
            "rating",
            "contact_person",
            "phone",
            "email",
            "website",
            "address",
            "payment_terms",
            "tax_number",
            "is_active",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["code"]
        skip_unchanged = True
        report_skipped = True


class SupplierContactResource(resources.ModelResource):
    """供应商联系人导入导出资源"""

    class Meta:
        model = SupplierContact
        fields = (
            "id",
            "supplier",
            "name",
            "position",
            "department",
            "phone",
            "mobile",
            "email",
            "is_primary",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["id"]
        skip_unchanged = True
        report_skipped = True
