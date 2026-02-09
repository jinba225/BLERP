"""
Dynamic choice options management.
统一的动态选项管理模型，替代硬编码的choices。
"""
from core.models import BaseModel
from django.core.cache import cache
from django.db import models


class ChoiceOption(BaseModel):
    """
    统一的选项管理模型。
    用于管理系统中各种下拉选项，如客户等级、付款方式等。
    支持通过Admin后台动态增删改，无需修改代码。
    """

    # 选项分类定义 - 业务配置类（可动态管理）
    CATEGORY_CHOICES = [
        # 客户相关
        ("customer_level", "客户等级"),
        ("customer_status", "客户状态"),
        ("address_type", "地址类型"),
        ("visit_type", "拜访类型"),
        ("visit_purpose", "拜访目的"),
        ("credit_type", "信用操作类型"),
        # 供应商相关
        ("supplier_level", "供应商等级"),
        ("contact_type", "联系人类型"),
        ("evaluation_period", "评估周期"),
        # 产品相关
        ("product_type", "产品类型"),
        ("product_status", "产品状态"),
        ("unit_type", "单位类型"),
        ("attribute_type", "属性类型"),
        ("price_type", "价格类型"),
        # 库存相关
        ("warehouse_type", "仓库类型"),
        ("adjustment_type", "库存调整类型"),
        ("adjustment_reason", "调整原因"),
        ("count_type", "盘点类型"),
        ("transaction_type", "库存事务类型"),
        # 财务相关
        ("payment_terms", "付款方式"),
    ]

    category = models.CharField(
        "选项分类",
        max_length=50,
        choices=CATEGORY_CHOICES,
        db_index=True,
        help_text="选项所属的分类，如客户等级、付款方式等",
    )

    code = models.CharField("选项代码", max_length=50, db_index=True, help_text="选项的唯一标识代码，用于程序内部引用")

    label = models.CharField("显示名称", max_length=100, help_text="显示给用户看的名称")

    description = models.TextField("描述", blank=True, help_text="选项的详细说明")

    sort_order = models.IntegerField("排序", default=0, help_text="排序号，数字越小越靠前")

    is_active = models.BooleanField("是否启用", default=True, help_text="禁用后该选项不会在下拉列表中显示")

    is_system = models.BooleanField("是否系统内置", default=False, help_text="系统内置选项不允许删除，但可以修改显示名称")

    # 额外的元数据字段（可选）
    color = models.CharField("颜色标识", max_length=20, blank=True, help_text="用于前端显示的颜色，如#FF0000")

    icon = models.CharField(
        "图标类名", max_length=50, blank=True, help_text="Font Awesome图标类名，如fa-star"
    )

    class Meta:
        verbose_name = "选项配置"
        verbose_name_plural = "选项配置"
        db_table = "core_choice_option"
        ordering = ["category", "sort_order", "code"]
        unique_together = [["category", "code"]]
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["category", "sort_order"]),
        ]

    def __str__(self):
        return f"{self.get_category_display()} - {self.label}"

    def save(self, *args, **kwargs):
        # 清除缓存
        self._clear_cache()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # 清除缓存
        self._clear_cache()
        super().delete(*args, **kwargs)

    def _clear_cache(self):
        """清除该分类的缓存"""
        cache_key = f"choice_options_{self.category}"
        cache.delete(cache_key)

    @classmethod
    def get_choices(cls, category, include_inactive=False):
        """
        获取指定分类的所有选项，返回适用于forms的choices格式。
        使用缓存提高性能。

        Args:
            category: 选项分类
            include_inactive: 是否包含禁用的选项

        Returns:
            [(code, label), ...] 格式的列表
        """
        # 尝试从缓存获取
        cache_key = f"choice_options_{category}"
        cached_choices = cache.get(cache_key)

        if cached_choices is None:
            # 缓存未命中，从数据库查询
            queryset = cls.objects.filter(category=category, is_deleted=False)
            if not include_inactive:
                queryset = queryset.filter(is_active=True)

            cached_choices = [(opt.code, opt.label) for opt in queryset]

            # 缓存1小时
            cache.set(cache_key, cached_choices, 3600)

        return cached_choices

    @classmethod
    def get_label(cls, category, code):
        """
        获取指定选项的显示名称。

        Args:
            category: 选项分类
            code: 选项代码

        Returns:
            显示名称，如果未找到则返回代码本身
        """
        try:
            option = cls.objects.get(category=category, code=code, is_active=True, is_deleted=False)
            return option.label
        except cls.DoesNotExist:
            return code

    @classmethod
    def get_dict(cls, category, include_inactive=False):
        """
        获取指定分类的所有选项，返回字典格式。

        Args:
            category: 选项分类
            include_inactive: 是否包含禁用的选项

        Returns:
            {code: label, ...} 格式的字典
        """
        choices = cls.get_choices(category, include_inactive)
        return dict(choices)

    @classmethod
    def get_option(cls, category, code):
        """
        获取选项对象。

        Args:
            category: 选项分类
            code: 选项代码

        Returns:
            ChoiceOption对象或None
        """
        try:
            return cls.objects.get(category=category, code=code, is_deleted=False)
        except cls.DoesNotExist:
            return None


class ChoiceOptionGroup(BaseModel):
    """
    选项分组模型（可选）。
    用于将同一分类下的选项进行分组管理。
    """

    category = models.CharField(
        "所属分类", max_length=50, choices=ChoiceOption.CATEGORY_CHOICES, db_index=True
    )

    name = models.CharField("分组名称", max_length=100)

    code = models.CharField("分组代码", max_length=50)

    sort_order = models.IntegerField("排序", default=0)

    is_active = models.BooleanField("是否启用", default=True)

    class Meta:
        verbose_name = "选项分组"
        verbose_name_plural = "选项分组"
        db_table = "core_choice_option_group"
        ordering = ["category", "sort_order"]
        unique_together = [["category", "code"]]

    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"
