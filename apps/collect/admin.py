"""
Admin后台配置
"""
from django.contrib import admin

from .models import CollectItem, CollectTask, FieldMapRule, Platform, PricingRule, Shop

# ProductListing模型已在ecomm_sync/admin.py中注册，无需重复导入


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    """平台配置管理"""

    list_display = ["platform_name", "platform_code", "platform_type", "is_active", "created_at"]
    list_filter = ["platform_type", "is_active", "platform_code"]
    search_fields = ["platform_name", "platform_code"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]
    fieldsets = (
        ("基础信息", {"fields": ("platform_name", "platform_code", "platform_type", "description")}),
        ("API配置", {"fields": ("api_key", "api_secret", "api_url", "api_version", "auth_type")}),
        (
            "OAuth配置",
            {
                "fields": ("access_token", "refresh_token", "token_expires_at"),
                "classes": ("collapse",),
            },
        ),
        ("状态", {"fields": ("is_active",)}),
        (
            "审计信息",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    """店铺配置管理"""

    list_display = ["shop_name", "platform", "shop_code", "is_active", "created_at"]
    list_filter = ["platform", "is_active"]
    search_fields = ["shop_name", "shop_code", "shop_id"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]
    fieldsets = (
        ("基础信息", {"fields": ("shop_name", "shop_code", "shop_id", "description")}),
        ("所属平台", {"fields": ("platform",)}),
        ("店铺配置", {"fields": ("shop_config", "currency", "country")}),
        ("API凭证", {"fields": ("api_key", "api_secret")}),
        (
            "OAuth配置",
            {
                "fields": ("access_token", "refresh_token", "token_expires_at"),
                "classes": ("collapse",),
            },
        ),
        ("状态", {"fields": ("is_active",)}),
        (
            "审计信息",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(CollectTask)
class CollectTaskAdmin(admin.ModelAdmin):
    """采集任务管理"""

    list_display = [
        "task_name",
        "platform",
        "collect_status",
        "land_status",
        "collect_num",
        "success_num",
        "fail_num",
        "created_at",
    ]
    list_filter = ["collect_status", "land_status", "platform", "collect_platform"]
    search_fields = ["task_name"]
    readonly_fields = [
        "collect_num",
        "success_num",
        "fail_num",
        "success_rate",
        "duration",
        "celery_task_id",
        "error_msg",
        "started_at",
        "completed_at",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    ]
    date_hierarchy = "created_at"
    fieldsets = (
        ("基础信息", {"fields": ("task_name", "platform", "collect_platform")}),
        ("采集配置", {"fields": ("collect_urls",)}),
        (
            "跨境同步配置",
            {"fields": ("sync_cross", "cross_platform", "cross_shop"), "classes": ("collapse",)},
        ),
        (
            "统计信息",
            {
                "fields": ("collect_num", "success_num", "fail_num", "success_rate", "duration"),
                "classes": ("collapse",),
            },
        ),
        (
            "状态信息",
            {
                "fields": ("collect_status", "land_status", "sync_status", "error_msg"),
                "classes": ("collapse",),
            },
        ),
        (
            "任务追踪",
            {"fields": ("celery_task_id", "started_at", "completed_at"), "classes": ("collapse",)},
        ),
        (
            "审计信息",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(CollectItem)
class CollectItemAdmin(admin.ModelAdmin):
    """采集子项管理"""

    list_display = [
        "item_name",
        "collect_task",
        "collect_status",
        "land_status",
        "collected_at",
        "landed_at",
    ]
    list_filter = ["collect_status", "land_status", "collect_task"]
    search_fields = ["item_name", "item_sku", "collect_url"]
    readonly_fields = [
        "collected_at",
        "landed_at",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    ]
    fieldsets = (
        ("基础信息", {"fields": ("collect_task", "product", "collect_url")}),
        ("采集信息", {"fields": ("item_name", "item_sku", "collect_status", "collected_at")}),
        ("落地信息", {"fields": ("land_status", "land_error", "landed_at"), "classes": ("collapse",)}),
        ("数据", {"fields": ("collect_data", "main_image", "images"), "classes": ("collapse",)}),
        (
            "审计信息",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(FieldMapRule)
class FieldMapRuleAdmin(admin.ModelAdmin):
    """字段映射规则管理"""

    list_display = [
        "collect_platform",
        "target_type",
        "source_field",
        "target_field",
        "rule_type",
        "sort_order",
        "is_active",
    ]
    list_filter = ["collect_platform", "target_type", "rule_type", "is_active"]
    search_fields = ["source_field", "target_field"]
    list_editable = ["sort_order", "is_active"]
    fieldsets = (
        ("映射配置", {"fields": ("collect_platform", "target_type", "source_field", "target_field")}),
        ("映射规则", {"fields": ("rule_type", "map_rule", "sort_order")}),
        ("状态", {"fields": ("is_active", "description")}),
        (
            "审计信息",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


# ProductListing模型已在ecomm_sync/admin.py中注册，无需重复注册


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    """定价规则管理"""

    list_display = [
        "name",
        "platform",
        "rule_type",
        "markup_percent",
        "fixed_price",
        "is_active",
        "created_at",
    ]
    list_filter = ["rule_type", "platform", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]
    fieldsets = (
        ("基础信息", {"fields": ("name", "platform", "description")}),
        ("定价规则", {"fields": ("rule_type",)}),
        (
            "加成定价",
            {
                "fields": ("markup_percent",),
                "classes": ("collapse",),
                "description": "适用于rule_type=markup",
            },
        ),
        (
            "固定定价",
            {
                "fields": ("fixed_price",),
                "classes": ("collapse",),
                "description": "适用于rule_type=fixed",
            },
        ),
        (
            "公式定价",
            {
                "fields": ("formula",),
                "classes": ("collapse",),
                "description": "适用于rule_type=formula",
            },
        ),
        ("其他配置", {"fields": ("round_method", "min_price", "max_price")}),
        ("状态", {"fields": ("is_active",)}),
        (
            "审计信息",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )
