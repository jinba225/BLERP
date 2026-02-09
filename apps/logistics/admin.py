"""
物流模块Admin配置
"""
from django.contrib import admin
from logistics.models import (
    LogisticsCompany,
    ShippingOrder,
    TrackingInfo,
    LogisticsCost,
    WaybillTemplate,
)


@admin.register(LogisticsCompany)
class LogisticsCompanyAdmin(admin.ModelAdmin):
    """物流公司Admin"""

    list_display = ["code", "name", "tier", "is_active", "website"]
    list_filter = ["tier", "is_active"]
    search_fields = ["code", "name", "website"]
    list_editable = ["is_active"]
    ordering = ["code"]

    fieldsets = (
        ("基本信息", {"fields": ("name", "code", "tier", "is_active")}),
        (
            "API配置",
            {
                "fields": ("api_endpoint", "tracking_url_template", "api_config"),
                "classes": ("collapse",),
            },
        ),
        ("其他信息", {"fields": ("logo_url", "website"), "classes": ("collapse",)}),
    )


@admin.register(ShippingOrder)
class ShippingOrderAdmin(admin.ModelAdmin):
    """物流订单Admin"""

    list_display = [
        "tracking_number",
        "platform_order",
        "logistics_company",
        "shipping_status",
        "shipping_cost",
        "shipped_at",
    ]
    list_filter = ["shipping_status", "logistics_company", "shipped_at"]
    search_fields = ["tracking_number", "platform_order__platform_order_id"]
    ordering = ["-shipped_at"]

    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("订单信息", {"fields": ("platform_order", "logistics_company", "tracking_number")}),
        (
            "物流信息",
            {
                "fields": (
                    "shipping_status",
                    "shipping_cost",
                    "weight",
                    "volume",
                    "shipped_at",
                    "delivered_at",
                    "last_track_at",
                )
            },
        ),
        ("面单信息", {"fields": ("waybill_image", "waybill_pdf"), "classes": ("collapse",)}),
        ("其他", {"fields": ("note",), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("platform_order", "logistics_company")


@admin.register(TrackingInfo)
class TrackingInfoAdmin(admin.ModelAdmin):
    """物流轨迹Admin"""

    list_display = ["shipping_order", "track_time", "track_status", "track_location", "operator"]
    list_filter = ["track_status", "track_time"]
    search_fields = ["shipping_order__tracking_number", "track_status"]
    ordering = ["-track_time"]

    readonly_fields = ["raw_data"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("shipping_order")


@admin.register(LogisticsCost)
class LogisticsCostAdmin(admin.ModelAdmin):
    """物流成本Admin"""

    list_display = ["shipping_order", "cost_type", "cost_amount", "cost_date", "description"]
    list_filter = ["cost_type", "cost_date"]
    search_fields = ["shipping_order__tracking_number", "reference_number"]
    ordering = ["-cost_date"]

    fieldsets = (
        ("成本信息", {"fields": ("shipping_order", "cost_type", "cost_amount", "cost_date")}),
        ("详细信息", {"fields": ("description", "reference_number"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("shipping_order")


@admin.register(WaybillTemplate)
class WaybillTemplateAdmin(admin.ModelAdmin):
    """物流面单模板Admin"""

    list_display = ["logistics_company", "name", "template_type", "is_default"]
    list_filter = ["logistics_company", "template_type", "is_default"]
    search_fields = ["name"]
    ordering = ["-is_default", "name"]

    fieldsets = (
        ("基本信息", {"fields": ("logistics_company", "name", "template_type", "is_default")}),
        ("模板内容", {"fields": ("template_html", "css_style")}),
        ("其他", {"fields": ("thumbnail",), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("logistics_company")
