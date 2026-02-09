"""
物流模块

支持多物流公司对接、物流追踪、成本管理等功能
"""
from core.models import BaseModel
from django.core.validators import URLValidator
from django.db import models


class LogisticsCompany(BaseModel):
    """物流公司模型"""

    TIER_CHOICES = [
        ("tier_1", "完整API支持（创建运单、查询轨迹、打印面单、取消运单）"),
        ("tier_2", "部分API支持（仅查询轨迹）"),
        ("tier_3", "仅网页查询（爬虫支持）"),
    ]

    name = models.CharField("物流公司名称", max_length=200)
    code = models.CharField("物流公司代码", max_length=50, unique=True, help_text="唯一标识，如SF、YTO、DHL等")
    api_endpoint = models.URLField("API端点", blank=True, max_length=500, help_text="官方API地址")
    tracking_url_template = models.CharField(
        "查询URL模板",
        max_length=500,
        blank=True,
        help_text="物流查询URL模板，如https://www.sf-express.com/waybill/#search/all/{tracking_number}",
    )
    tier = models.CharField(
        "支持级别", max_length=10, choices=TIER_CHOICES, default="tier_1", help_text="API支持级别"
    )
    is_active = models.BooleanField("是否启用", default=True)
    api_config = models.JSONField(
        "API配置", default=dict, blank=True, help_text="API配置信息，如app_id、app_secret等"
    )
    logo_url = models.URLField("Logo URL", blank=True, max_length=500)
    website = models.URLField("官网地址", blank=True, max_length=500)

    class Meta:
        verbose_name = "物流公司"
        verbose_name_plural = "物流公司"
        db_table = "logistics_company"
        ordering = ["code"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class ShippingOrder(BaseModel):
    """物流订单模型"""

    SHIPPING_STATUS_CHOICES = [
        ("pending", "待发货"),
        ("shipped", "已发货"),
        ("in_transit", "运输中"),
        ("out_for_delivery", "派送中"),
        ("delivered", "已签收"),
        ("failed", "配送失败"),
        ("returned", "已退货"),
        ("cancelled", "已取消"),
    ]

    platform_order = models.ForeignKey(
        "ecomm_sync.PlatformOrder",
        on_delete=models.CASCADE,
        related_name="shipping_orders",
        verbose_name="平台订单",
    )
    logistics_company = models.ForeignKey(
        LogisticsCompany,
        on_delete=models.PROTECT,
        related_name="shipping_orders",
        verbose_name="物流公司",
    )
    tracking_number = models.CharField("快递单号", max_length=200, db_index=True)
    shipping_status = models.CharField(
        "物流状态", max_length=20, choices=SHIPPING_STATUS_CHOICES, default="pending"
    )
    shipping_cost = models.DecimalField(
        "物流费用", max_digits=10, decimal_places=2, default=0, help_text="物流总费用"
    )
    weight = models.DecimalField(
        "重量(kg)", max_digits=10, decimal_places=3, null=True, blank=True, help_text="订单总重量"
    )
    volume = models.DecimalField(
        "体积(m³)", max_digits=10, decimal_places=3, null=True, blank=True, help_text="订单总体积"
    )
    shipped_at = models.DateTimeField("发货时间", null=True, blank=True)
    delivered_at = models.DateTimeField("签收时间", null=True, blank=True)
    last_track_at = models.DateTimeField("最后查询时间", null=True, blank=True)
    note = models.TextField("备注", blank=True)
    waybill_image = models.ImageField("面单图片", upload_to="waybills/%Y/%m/", null=True, blank=True)
    waybill_pdf = models.FileField("面单PDF", upload_to="waybills/pdf/%Y/%m/", null=True, blank=True)

    class Meta:
        verbose_name = "物流订单"
        verbose_name_plural = "物流订单"
        db_table = "logistics_shipping_order"
        indexes = [
            models.Index(fields=["tracking_number"]),
            models.Index(fields=["shipping_status"]),
            models.Index(fields=["-shipped_at"]),
            models.Index(fields=["platform_order", "-shipped_at"]),
            models.Index(fields=["logistics_company", "shipping_status"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tracking_number} - {self.get_shipping_status_display()}"

    @property
    def is_delivered(self):
        return self.shipping_status == "delivered"

    @property
    def days_in_transit(self):
        if self.shipped_at and self.delivered_at:
            return (self.delivered_at - self.shipped_at).days
        return None


class TrackingInfo(BaseModel):
    """物流轨迹模型"""

    shipping_order = models.ForeignKey(
        ShippingOrder, on_delete=models.CASCADE, related_name="tracking_infos", verbose_name="物流订单"
    )
    track_time = models.DateTimeField("轨迹时间", db_index=True)
    track_status = models.CharField("轨迹状态", max_length=100, db_index=True)
    track_location = models.CharField("轨迹地点", max_length=500, blank=True)
    track_description = models.TextField("轨迹描述", blank=True)
    operator = models.CharField("操作人", max_length=200, blank=True)
    raw_data = models.JSONField("原始数据", default=dict, blank=True)

    class Meta:
        verbose_name = "物流轨迹"
        verbose_name_plural = "物流轨迹"
        db_table = "logistics_tracking_info"
        indexes = [
            models.Index(fields=["shipping_order", "-track_time"]),
            models.Index(fields=["track_status", "-track_time"]),
        ]
        ordering = ["track_time"]

    def __str__(self):
        return f"{self.shipping_order.tracking_number} - {self.track_time}"


class LogisticsCost(BaseModel):
    """物流成本模型"""

    COST_TYPE_CHOICES = [
        ("freight", "运费"),
        ("fuel_surcharge", "燃油费"),
        ("remote_area_fee", "偏远费"),
        ("cod_fee", "货到付款费"),
        ("insurance", "保险费"),
        ("package_fee", "包装费"),
        ("other", "其他费用"),
    ]

    shipping_order = models.ForeignKey(
        ShippingOrder, on_delete=models.CASCADE, related_name="costs", verbose_name="物流订单"
    )
    cost_type = models.CharField("费用类型", max_length=50, choices=COST_TYPE_CHOICES)
    cost_amount = models.DecimalField("费用金额", max_digits=10, decimal_places=2)
    cost_date = models.DateField("费用日期")
    description = models.CharField("费用描述", max_length=500, blank=True)
    reference_number = models.CharField("参考号", max_length=200, blank=True, help_text="物流公司提供的费用参考号")

    class Meta:
        verbose_name = "物流成本"
        verbose_name_plural = "物流成本"
        db_table = "logistics_cost"
        indexes = [
            models.Index(fields=["shipping_order", "cost_date"]),
            models.Index(fields=["cost_type", "-cost_date"]),
        ]
        ordering = ["-cost_date"]

    def __str__(self):
        return f"{self.shipping_order.tracking_number} - {self.get_cost_type_display()} - {self.cost_amount}"


class WaybillTemplate(BaseModel):
    """物流面单模板模型"""

    TEMPLATE_TYPE_CHOICES = [
        ("thermal_100x180", "热敏纸 100x180mm"),
        ("thermal_100x100", "热敏纸 100x100mm"),
        ("a4", "A4纸"),
        ("a5", "A5纸"),
        ("custom", "自定义"),
    ]

    logistics_company = models.ForeignKey(
        LogisticsCompany,
        on_delete=models.CASCADE,
        related_name="waybill_templates",
        verbose_name="物流公司",
    )
    name = models.CharField("模板名称", max_length=200)
    template_type = models.CharField(
        "模板类型", max_length=50, choices=TEMPLATE_TYPE_CHOICES, default="thermal_100x180"
    )
    template_html = models.TextField("HTML模板")
    css_style = models.TextField("CSS样式", blank=True)
    is_default = models.BooleanField("是否默认模板", default=False)
    thumbnail = models.ImageField(
        "缩略图", upload_to="waybill_templates/thumbnails/", null=True, blank=True
    )

    class Meta:
        verbose_name = "物流面单模板"
        verbose_name_plural = "物流面单模板"
        db_table = "logistics_waybill_template"
        unique_together = [["logistics_company", "name"]]
        ordering = ["-is_default", "name"]

    def __str__(self):
        return f"{self.logistics_company.name} - {self.name}"
