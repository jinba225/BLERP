"""
Print template models for customizable quote/order printing.
"""

from core.models import BaseModel
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class PrintTemplate(BaseModel):
    """
    Print template configuration for quotes and orders.
    Allows users to customize the layout and content of printed documents.

    设计说明：
    - template_category: 模板大类（销售/采购/库存/财务/其他）
    - suitable_for: 适用单据类型（支持多选，用于排序优先级）
    """

    # 模板大类选项
    CATEGORY_CHOICES = [
        ("sales", "📊 销售类"),
        ("purchase", "🛒 采购类"),
        ("inventory", "📦 库存类"),
        ("finance", "💰 财务类"),
        ("other", "📋 其他类"),
    ]

    # 适用单据类型选项（用于 suitable_for 字段的参考）
    DOCUMENT_TYPE_CHOICES = [
        # 销售类
        ("quote", "报价单"),
        ("sales_order", "销售订单"),
        ("delivery", "发货单"),
        ("sales_return", "销售退货"),
        # 采购类
        ("purchase_order", "采购订单"),
        ("purchase_receipt", "采购入库"),
        ("purchase_return", "采购退货"),
        # 库存类
        ("stock_in", "入库单"),
        ("stock_out", "出库单"),
        ("stock_transfer", "调拨单"),
        ("stock_check", "盘点单"),
        # 财务类
        ("invoice", "发票"),
        ("payment", "付款单"),
        ("receipt", "收款单"),
    ]

    name = models.CharField("模板名称", max_length=100)

    # 模板大类（必选）
    template_category = models.CharField(
        "模板类别",
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="sales",  # 默认为销售类
        db_index=True,
        help_text="模板所属的大类，同类别的模板可以共享使用",
    )

    # 适用单据类型（可选，用于排序优先级）
    suitable_for = models.JSONField(
        "适用单据类型",
        default=list,
        blank=True,
        help_text='JSON数组格式，例如：["quote", "sales_order"]。用于在打印时优先显示更相关的模板',
    )

    is_active = models.BooleanField("是否启用", default=True)

    # Company information
    company_name = models.CharField("公司名称", max_length=200, default="BetterLaser 激光科技有限公司")
    company_address = models.CharField("公司地址", max_length=500, blank=True)
    company_phone = models.CharField("联系电话", max_length=50, blank=True)
    company_email = models.CharField("电子邮箱", max_length=100, blank=True)
    company_logo = models.ImageField(
        "公司Logo", upload_to="print_templates/logos/", blank=True, null=True
    )

    # Layout configuration (JSON)
    # Structure: {
    #   "sections": [
    #     {"id": "header", "visible": true, "order": 1, "fields": [...]},
    #     {"id": "customer_info", "visible": true, "order": 2, "fields": [...]},
    #     ...
    #   ],
    #   "page_settings": {
    #     "size": "A4",
    #     "orientation": "portrait",
    #     "margin": {"top": "1cm", "right": "1cm", "bottom": "1cm", "left": "1cm"}
    #   },
    #   "styles": {
    #     "font_family": "Microsoft YaHei",
    #     "font_size": "12px",
    #     "primary_color": "#333",
    #     "secondary_color": "#666"
    #   }
    # }
    layout_config = models.JSONField("布局配置", default=dict)

    # Custom CSS
    custom_css = models.TextField("自定义样式", blank=True, help_text="自定义CSS样式")

    # Notes
    notes = models.TextField("备注", blank=True)

    class Meta:
        db_table = "core_print_template"
        verbose_name = "打印模板"
        verbose_name_plural = verbose_name
        ordering = ["template_category", "name"]
        indexes = [
            models.Index(fields=["template_category", "is_active"]),
        ]

    def __str__(self):
        return f"{self.get_template_category_display()} - {self.name}"

    @classmethod
    def get_default_layout_config(cls, template_category):
        """
        Get default layout configuration based on template category.
        For HiPrint, return empty config so users can design from scratch.
        """
        return {}
