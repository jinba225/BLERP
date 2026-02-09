"""
Products 模块的导入导出资源配置
"""
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DecimalWidget
from .models import Product, ProductCategory


class ProductCategoryResource(resources.ModelResource):
    """产品分类导入导出资源"""

    class Meta:
        model = ProductCategory
        fields = ("id", "name", "code", "description", "is_active", "created_at", "updated_at")
        export_order = fields
        import_id_fields = ["code"]
        skip_unchanged = True
        report_skipped = True


class ProductResource(resources.ModelResource):
    """产品导入导出资源"""

    category = fields.Field(
        column_name="产品分类", attribute="category", widget=ForeignKeyWidget(ProductCategory, "code")
    )

    standard_price = fields.Field(
        column_name="标准价格", attribute="standard_price", widget=DecimalWidget()
    )

    cost = fields.Field(column_name="成本", attribute="cost", widget=DecimalWidget())

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "code",
            "category",
            "product_type",
            "specification",
            "unit",
            "standard_price",
            "cost",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["code"]
        skip_unchanged = True
        report_skipped = True
