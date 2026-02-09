"""
采集模块数据模型
实现采集任务、采集子项、字段映射规则等核心模型
注意：
1. Platform和Shop模型已移至core/models.py，统一管理
2. ProductListing模型已存在于ecomm_sync/models.py，这里不再重复定义
"""
from django.db import models
from core.models import BaseModel, Platform, Shop
from products.models import Product
from django.core.exceptions import ValidationError
import math


class CollectTask(BaseModel):
    """采集任务模型：记录每一次采集的全流程"""

    COLLECT_PLATFORM_CHOICES = (
        ("taobao", "淘宝"),
        ("1688", "1688阿里巴巴"),
    )

    COLLECT_STATUS_CHOICES = (
        ("pending", "待采集"),
        ("running", "采集中"),
        ("success", "采集成功"),
        ("failed", "采集失败"),
        ("partial", "部分采集成功"),
    )

    LAND_STATUS_CHOICES = (
        ("unland", "未落地"),
        ("running", "落地中"),
        ("success", "落地成功"),
        ("failed", "落地失败"),
    )

    # 采集基础信息
    task_name = models.CharField("采集任务名称", max_length=64)
    collect_platform = models.CharField(
        "采集平台", max_length=16, choices=COLLECT_PLATFORM_CHOICES, db_index=True
    )
    platform = models.ForeignKey(
        "core.Platform",
        on_delete=models.PROTECT,
        related_name="collect_tasks",
        verbose_name="关联平台配置",
        db_index=True,
    )
    collect_urls = models.TextField("采集商品链接", help_text="商品链接，每行一个")
    collect_num = models.IntegerField("计划采集数", default=0)
    success_num = models.IntegerField("成功采集数", default=0)
    fail_num = models.IntegerField("失败采集数", default=0)

    # 任务状态
    collect_status = models.CharField(
        "采集状态", max_length=16, choices=COLLECT_STATUS_CHOICES, default="pending", db_index=True
    )
    land_status = models.CharField(
        "落地状态", max_length=16, choices=LAND_STATUS_CHOICES, default="unland", db_index=True
    )
    celery_task_id = models.CharField("Celery任务ID", max_length=64, blank=True)

    # 跨境同步选项
    sync_cross = models.BooleanField("自动同步到跨境平台", default=False)
    cross_platform = models.ForeignKey(
        "core.Platform",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sync_tasks",
        verbose_name="目标跨境平台",
    )
    cross_shop = models.ForeignKey(
        "core.Shop",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sync_tasks",
        verbose_name="目标跨境店铺",
    )
    sync_status = models.CharField("跨境同步状态", max_length=16, blank=True)

    # 采集结果
    error_msg = models.TextField("任务失败原因", blank=True)
    collect_data = models.JSONField("采集原始数据", default=dict, blank=True)

    # 时间记录
    started_at = models.DateTimeField("开始时间", null=True, blank=True)
    completed_at = models.DateTimeField("完成时间", null=True, blank=True)

    class Meta:
        verbose_name = "采集任务"
        verbose_name_plural = "采集任务"
        db_table = "collect_task"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["collect_platform", "collect_status", "land_status"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-created_at", "collect_status"]),
        ]

    def __str__(self):
        return f"{self.get_collect_platform_display()}-{self.task_name}-{self.collect_status}"

    @property
    def success_rate(self):
        """采集成功率"""
        if self.collect_num == 0:
            return 0
        return round((self.success_num / self.collect_num) * 100, 2)

    @property
    def duration(self):
        """采集耗时"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class CollectItem(BaseModel):
    """采集子项模型：记录每个商品的采集详情"""

    COLLECT_STATUS_CHOICES = (
        ("pending", "待采集"),
        ("success", "采集成功"),
        ("failed", "采集失败"),
    )

    LAND_STATUS_CHOICES = (
        ("unland", "未落地"),
        ("success", "落地成功"),
        ("failed", "落地失败"),
    )

    collect_task = models.ForeignKey(
        CollectTask, on_delete=models.CASCADE, related_name="collect_items", verbose_name="关联采集任务"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collect_items",
        verbose_name="关联产品库产品",
        db_index=True,
    )
    collect_url = models.CharField("商品采集链接", max_length=512)
    item_name = models.CharField("商品名称", max_length=200, blank=True)
    item_sku = models.CharField("平台商品SKU", max_length=64, blank=True)

    # 状态
    collect_status = models.CharField(
        "子项采集状态", max_length=16, choices=COLLECT_STATUS_CHOICES, default="pending"
    )
    land_status = models.CharField(
        "子项落地状态", max_length=16, choices=LAND_STATUS_CHOICES, default="unland"
    )

    # 数据
    collect_data = models.JSONField("采集原始数据", default=dict)
    land_error = models.TextField("落地失败原因", blank=True)

    # 图片相关
    images = models.JSONField("图片列表", default=list, blank=True)
    main_image = models.URLField("主图链接", max_length=512, blank=True)

    # 时间记录
    collected_at = models.DateTimeField("采集时间", null=True, blank=True)
    landed_at = models.DateTimeField("落地时间", null=True, blank=True)

    class Meta:
        verbose_name = "采集商品子项"
        verbose_name_plural = "采集商品子项"
        db_table = "collect_item"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["collect_task", "collect_status"]),
            models.Index(fields=["collect_status", "land_status"]),
            models.Index(fields=["product", "is_deleted"]),
        ]

    def __str__(self):
        return f"{self.item_name or self.collect_url[:50]}-{self.get_collect_status_display()}"


class FieldMapRule(BaseModel):
    """字段映射规则模型：运营可配置的映射规则"""

    COLLECT_PLATFORM_CHOICES = (
        ("taobao", "淘宝"),
        ("1688", "1688阿里巴巴"),
    )

    TARGET_TYPE_CHOICES = (
        ("product", "产品库"),
        ("listing", "Listing"),
    )

    MAP_RULE_TYPES = (
        ("direct", "直接映射"),
        ("calc", "计算规则"),
        ("fixed", "固定值"),
        ("function", "自定义函数"),
    )

    collect_platform = models.CharField(
        "采集平台", max_length=16, choices=COLLECT_PLATFORM_CHOICES, db_index=True
    )
    target_type = models.CharField(
        "映射目标", max_length=16, choices=TARGET_TYPE_CHOICES, db_index=True
    )
    source_field = models.CharField("源字段", max_length=64, help_text="如淘宝的title, pic_url等")
    target_field = models.CharField("目标字段", max_length=64, help_text="如产品库的name, main_image等")
    rule_type = models.CharField("规则类型", max_length=16, choices=MAP_RULE_TYPES, default="direct")
    map_rule = models.CharField(
        "映射规则", max_length=256, blank=True, help_text="如: 拼接-精品, price*1.5, length*height*width"
    )
    sort_order = models.IntegerField("排序权重", default=0)
    is_active = models.BooleanField("是否启用", default=True)
    description = models.TextField("描述", blank=True)

    class Meta:
        verbose_name = "字段映射规则"
        verbose_name_plural = "字段映射规则"
        db_table = "collect_field_map"
        ordering = ["collect_platform", "target_type", "sort_order"]
        indexes = [
            models.Index(fields=["collect_platform", "target_type"]),
            models.Index(fields=["is_active"]),
        ]
        unique_together = [["collect_platform", "target_type", "source_field", "is_deleted"]]

    def __str__(self):
        return f"{self.get_collect_platform_display()}→{self.get_target_type_display()}: {self.source_field}→{self.target_field}"


# 注意：ProductListing模型已存在于ecomm_sync/models.py，这里使用ecomm_sync.models.ProductListing
# 避免与ecomm_sync的ProductListing模型冲突
from ecomm_sync.models import ProductListing as EcommProductListing


class PricingRule(BaseModel):
    """定价规则模型：自动定价规则"""

    RULE_TYPES = (
        ("markup", "加成定价"),
        ("fixed", "固定定价"),
        ("formula", "公式定价"),
    )

    name = models.CharField("规则名称", max_length=100)
    rule_type = models.CharField("规则类型", max_length=20, choices=RULE_TYPES)
    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="pricing_rules", verbose_name="适用平台"
    )

    # 定价规则配置
    markup_percent = models.DecimalField(
        "加成百分比", max_digits=5, decimal_places=2, blank=True, null=True, help_text="如: 50 表示加价50%"
    )
    fixed_price = models.DecimalField(
        "固定价格", max_digits=10, decimal_places=2, blank=True, null=True
    )
    formula = models.CharField(
        "定价公式", max_length=500, blank=True, help_text="如: cost * 1.5 + shipping_cost"
    )

    # 其他配置
    round_method = models.CharField(
        "取整方式",
        max_length=20,
        blank=True,
        choices=(
            ("none", "不取整"),
            ("up", "向上取整"),
            ("down", "向下取整"),
            ("nearest", "四舍五入"),
        ),
    )
    min_price = models.DecimalField("最低价格", max_digits=10, decimal_places=2, blank=True, null=True)
    max_price = models.DecimalField("最高价格", max_digits=10, decimal_places=2, blank=True, null=True)

    is_active = models.BooleanField("是否启用", default=True)
    description = models.TextField("描述", blank=True)

    class Meta:
        verbose_name = "定价规则"
        verbose_name_plural = "定价规则"
        db_table = "collect_pricing_rule"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"

    def calculate_price(self, cost_price):
        """根据成本价格计算销售价格"""
        if self.rule_type == "markup":
            price = (
                cost_price * (1 + self.markup_percent / 100) if self.markup_percent else cost_price
            )
        elif self.rule_type == "fixed":
            price = self.fixed_price or cost_price
        elif self.rule_type == "formula":
            try:
                # 简单的公式解析，实际应用中可以使用更安全的表达式解析库
                price = eval(self.formula, {"__builtins__": None}, {"cost": cost_price})
            except:
                price = cost_price
        else:
            price = cost_price

        # 取整处理
        if self.round_method == "up":
            price = math.ceil(price)
        elif self.round_method == "down":
            price = math.floor(price)
        elif self.round_method == "nearest":
            price = round(price)

        # 价格范围限制
        if self.min_price and price < self.min_price:
            price = self.min_price
        if self.max_price and price > self.max_price:
            price = self.max_price

        return price
