"""
Default template mapping models.
Defines which template is the default for each document type.
"""
from django.db import models
from apps.core.models import BaseModel


class DefaultTemplateMapping(BaseModel):
    """
    单据默认模板配置表

    用于为每种单据类型设置默认打印模板。
    例如：国内报价单默认使用"标准报价单"模板。
    """

    # 单据类型选项（细粒度，区分不同场景）
    DOCUMENT_TYPE_CHOICES = [
        # 报价单（区分国内/海外）
        ('quote_domestic', '报价单-国内'),
        ('quote_overseas', '报价单-海外'),

        # 销售订单
        ('sales_order', '销售订单'),

        # 发货单
        ('delivery', '发货单'),

        # 销售退货
        ('sales_return', '销售退货'),

        # 采购订单
        ('purchase_order', '采购订单'),

        # 采购入库
        ('purchase_receipt', '采购入库'),

        # 采购退货
        ('purchase_return', '采购退货'),

        # 入库单
        ('stock_in', '入库单'),

        # 出库单
        ('stock_out', '出库单'),

        # 调拨单
        ('stock_transfer', '调拨单'),

        # 盘点单
        ('stock_check', '盘点单'),

        # 发票
        ('invoice', '发票'),

        # 付款单
        ('payment', '付款单'),

        # 收款单
        ('receipt', '收款单'),
    ]

    document_type = models.CharField(
        '单据类型',
        max_length=50,
        choices=DOCUMENT_TYPE_CHOICES,
        unique=True,  # 每种单据只能有一个默认模板
        db_index=True,
        help_text='为该单据类型设置默认打印模板'
    )

    template = models.ForeignKey(
        'PrintTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='默认模板',
        related_name='default_for_documents',
        help_text='该单据类型的默认模板，打印时自动选中'
    )

    class Meta:
        db_table = 'core_default_template_mapping'
        verbose_name = '默认模板配置'
        verbose_name_plural = verbose_name
        ordering = ['document_type']

    def __str__(self):
        template_name = self.template.name if self.template else '未设置'
        return f"{self.get_document_type_display()} → {template_name}"

    def clean(self):
        """验证模板类别是否匹配单据类型"""
        from django.core.exceptions import ValidationError

        if self.template:
            # 验证模板类别与单据类型是否匹配
            doc_category = self._get_expected_category()
            if self.template.template_category != doc_category:
                raise ValidationError(
                    f"模板类别不匹配：{self.get_document_type_display()} "
                    f"应该使用 {doc_category} 类模板，"
                    f"但当前选择的是 {self.template.get_template_category_display()} 类模板"
                )

    def _get_expected_category(self):
        """根据单据类型推断应该使用的模板类别"""
        # 提取单据类型的基础部分
        doc_type = self.document_type

        # 销售类
        if doc_type in ['quote_domestic', 'quote_overseas', 'sales_order', 'delivery', 'sales_return']:
            return 'sales'

        # 采购类
        if doc_type in ['purchase_order', 'purchase_receipt', 'purchase_return']:
            return 'purchase'

        # 库存类
        if doc_type in ['stock_in', 'stock_out', 'stock_transfer', 'stock_check']:
            return 'inventory'

        # 财务类
        if doc_type in ['invoice', 'payment', 'receipt']:
            return 'finance'

        # 其他
        return 'other'
