"""
Customer admin configuration.
"""
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import (
    Customer,
    CustomerAddress,
    CustomerCategory,
    CustomerContact,
    CustomerCreditHistory,
    CustomerVisit,
)
from .resources import CustomerContactResource, CustomerResource


@admin.register(CustomerCategory)
class CustomerCategoryAdmin(admin.ModelAdmin):
    """客户分类管理"""

    list_display = ["name", "code", "discount_rate", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "code", "description"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]
    list_per_page = 50

    fieldsets = (
        ("基本信息", {"fields": ("name", "code", "description", "discount_rate")}),
        ("状态", {"fields": ("is_active",)}),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


class CustomerContactInline(admin.TabularInline):
    """客户联系人内联编辑"""

    model = CustomerContact
    extra = 1
    fields = ["name", "position", "phone", "mobile", "email", "is_primary"]


class CustomerAddressInline(admin.TabularInline):
    """客户地址内联编辑"""

    model = CustomerAddress
    extra = 0
    fields = ["address_type", "address", "city", "province", "is_default"]


@admin.register(Customer)
class CustomerAdmin(ImportExportModelAdmin):
    """客户管理 - 含导入导出功能"""

    resource_class = CustomerResource
    list_display = [
        "code",
        "name",
        "customer_level",
        "status",
        "sales_rep",
        "credit_limit",
        "created_at",
    ]
    list_filter = ["customer_level", "status", "category", "created_at"]
    search_fields = ["name", "code"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]
    list_per_page = 50
    inlines = [CustomerContactInline, CustomerAddressInline]

    fieldsets = (
        ("基本信息", {"fields": ("name", "code", "customer_level", "status", "category")}),
        ("联系信息", {"fields": ("website",)}),
        (
            "地址信息",
            {
                "fields": ("address", "city", "province", "country", "postal_code"),
                "classes": ("collapse",),
            },
        ),
        (
            "业务信息",
            {
                "fields": (
                    "industry",
                    "business_license",
                    "tax_number",
                    "bank_name",
                    "bank_account",
                ),
                "classes": ("collapse",),
            },
        ),
        ("销售信息", {"fields": ("sales_rep", "credit_limit", "payment_terms", "discount_rate")}),
        ("附加信息", {"fields": ("source", "tags", "notes"), "classes": ("collapse",)}),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(CustomerContact)
class CustomerContactAdmin(ImportExportModelAdmin):
    """客户联系人管理 - 含导入导出功能"""

    resource_class = CustomerContactResource
    list_display = [
        "customer",
        "name",
        "position",
        "department",
        "phone",
        "mobile",
        "email",
        "is_primary",
    ]
    list_filter = ["is_primary", "created_at"]
    search_fields = ["customer__name", "name", "phone", "email"]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 50


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    """客户地址管理"""

    list_display = ["customer", "address_type", "city", "province", "country", "is_default"]
    list_filter = ["address_type", "country", "province", "is_default", "created_at"]
    search_fields = ["customer__name", "address", "city"]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 50


@admin.register(CustomerCreditHistory)
class CustomerCreditHistoryAdmin(admin.ModelAdmin):
    """客户信用历史管理"""

    list_display = [
        "customer",
        "credit_type",
        "old_limit",
        "new_limit",
        "approved_by",
        "created_at",
    ]
    list_filter = ["credit_type", "created_at"]
    search_fields = ["customer__name", "reason"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]
    list_per_page = 50

    fieldsets = (
        ("基本信息", {"fields": ("customer", "credit_type")}),
        ("额度变更", {"fields": ("old_limit", "new_limit", "reason")}),
        ("审批信息", {"fields": ("approved_by",)}),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(CustomerVisit)
class CustomerVisitAdmin(admin.ModelAdmin):
    """客户拜访记录管理"""

    list_display = [
        "customer",
        "visit_type",
        "visit_purpose",
        "visit_date",
        "visitor",
        "contact_person",
        "next_visit_date",
    ]
    list_filter = ["visit_type", "visit_purpose", "visit_date", "created_at"]
    search_fields = ["customer__name", "visitor__username", "contact_person", "content"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]
    list_per_page = 50
    date_hierarchy = "visit_date"

    fieldsets = (
        (
            "基本信息",
            {
                "fields": (
                    "customer",
                    "visit_type",
                    "visit_purpose",
                    "visit_date",
                    "visitor",
                    "contact_person",
                )
            },
        ),
        ("拜访内容", {"fields": ("content", "result", "next_action", "next_visit_date")}),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )
