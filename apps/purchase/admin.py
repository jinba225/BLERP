from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import (
    Borrow,
    BorrowItem,
    PurchaseInquiry,
    PurchaseInquiryItem,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseReceipt,
    PurchaseReceiptItem,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseReturn,
    PurchaseReturnItem,
    SupplierQuotation,
    SupplierQuotationItem,
)
from .resources import (
    PurchaseOrderResource,
    PurchaseReceiptResource,
    PurchaseReturnResource,
    SupplierQuotationResource,
)


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ("product", "quantity", "unit_price", "line_total")
    readonly_fields = ("line_total",)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(ImportExportModelAdmin):
    resource_class = PurchaseOrderResource
    list_display = (
        "order_number",
        "supplier",
        "order_date",
        "status",
        "payment_status",
        "total_amount",
        "approved_by",
    )
    list_filter = ("status", "payment_status", "order_date", "supplier")
    search_fields = ("order_number", "supplier__name", "reference_number")
    readonly_fields = (
        "order_number",
        "subtotal",
        "tax_amount",
        "discount_amount",
        "total_amount",
        "created_at",
        "updated_at",
        "approved_at",
    )
    fieldsets = (
        ("基本信息", {"fields": ("order_number", "supplier", "status", "payment_status")}),
        ("日期信息", {"fields": ("order_date", "required_date", "promised_date", "received_date")}),
        ("人员信息", {"fields": ("buyer", "approved_by", "approved_at")}),
        (
            "金额信息",
            {
                "fields": (
                    "subtotal",
                    "tax_rate",
                    "tax_amount",
                    "discount_rate",
                    "discount_amount",
                    "shipping_cost",
                    "total_amount",
                    "currency",
                )
            },
        ),
        (
            "收货信息",
            {"fields": ("warehouse", "delivery_address", "delivery_contact", "delivery_phone")},
        ),
        ("其他信息", {"fields": ("payment_terms", "reference_number", "notes", "internal_notes")}),
        ("系统信息", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    inlines = [PurchaseOrderItemInline]
    date_hierarchy = "order_date"


class PurchaseRequestItemInline(admin.TabularInline):
    model = PurchaseRequestItem
    extra = 1
    fields = ("product", "quantity", "estimated_price", "specifications")
    readonly_fields = ()


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ("request_number", "department", "requester", "request_date", "status")
    list_filter = ("status", "request_date", "department")
    search_fields = ("request_number", "department__name", "purpose")
    readonly_fields = ("request_number", "approved_at", "created_at", "updated_at")
    fieldsets = (
        ("基本信息", {"fields": ("request_number", "department", "requester", "status")}),
        ("日期信息", {"fields": ("request_date", "required_date")}),
        ("申请信息", {"fields": ("purpose",)}),
        ("审核信息", {"fields": ("approved_by", "approved_at")}),
        ("转换信息", {"fields": ("converted_order",)}),
        ("其他信息", {"fields": ("notes",)}),
        ("系统信息", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    inlines = [PurchaseRequestItemInline]
    date_hierarchy = "request_date"


class PurchaseReceiptItemInline(admin.TabularInline):
    model = PurchaseReceiptItem
    extra = 1
    fields = ("order_item", "received_quantity", "batch_number", "location")


@admin.register(PurchaseReceipt)
class PurchaseReceiptAdmin(ImportExportModelAdmin):
    resource_class = PurchaseReceiptResource
    list_display = (
        "receipt_number",
        "purchase_order",
        "receipt_date",
        "warehouse",
        "status",
        "received_by",
    )
    list_filter = ("status", "receipt_date", "warehouse")
    search_fields = ("receipt_number", "purchase_order__order_number")
    readonly_fields = ("receipt_number", "created_at", "updated_at")
    fieldsets = (
        ("基本信息", {"fields": ("receipt_number", "purchase_order", "status", "warehouse")}),
        ("日期信息", {"fields": ("receipt_date",)}),
        ("人员信息", {"fields": ("received_by",)}),
        ("其他信息", {"fields": ("notes",)}),
        ("系统信息", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    inlines = [PurchaseReceiptItemInline]
    date_hierarchy = "receipt_date"


class PurchaseReturnItemInline(admin.TabularInline):
    model = PurchaseReturnItem
    extra = 1
    fields = ("order_item", "quantity", "unit_price", "line_total")
    readonly_fields = ("line_total",)


@admin.register(PurchaseReturn)
class PurchaseReturnAdmin(ImportExportModelAdmin):
    resource_class = PurchaseReturnResource
    list_display = (
        "return_number",
        "purchase_order",
        "return_date",
        "status",
        "reason",
        "refund_amount",
    )
    list_filter = ("status", "reason", "return_date")
    search_fields = ("return_number", "purchase_order__order_number")
    readonly_fields = ("return_number", "refund_amount", "approved_at", "created_at", "updated_at")
    fieldsets = (
        ("基本信息", {"fields": ("return_number", "purchase_order", "receipt", "status", "reason")}),
        ("日期信息", {"fields": ("return_date", "shipped_date")}),
        ("金额信息", {"fields": ("refund_amount",)}),
        ("审核信息", {"fields": ("approved_by", "approved_at")}),
        ("其他信息", {"fields": ("notes",)}),
        ("系统信息", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    inlines = [PurchaseReturnItemInline]
    date_hierarchy = "return_date"


# Register inquiry and quotation models
@admin.register(PurchaseInquiry)
class PurchaseInquiryAdmin(admin.ModelAdmin):
    list_display = ("inquiry_number", "inquiry_date", "required_date", "status", "buyer")
    list_filter = ("status", "inquiry_date", "buyer")
    search_fields = ("inquiry_number",)


@admin.register(SupplierQuotation)
class SupplierQuotationAdmin(ImportExportModelAdmin):
    resource_class = SupplierQuotationResource
    list_display = (
        "quotation_number",
        "inquiry",
        "supplier",
        "quotation_date",
        "status",
        "total_amount",
    )
    list_filter = ("status", "quotation_date", "supplier")
    search_fields = ("quotation_number", "supplier__name")


# ==================== Borrow Admin ====================


class BorrowItemInline(admin.TabularInline):
    model = BorrowItem
    extra = 1
    fields = (
        "product",
        "quantity",
        "returned_quantity",
        "conversion_quantity",
        "conversion_unit_price",
        "batch_number",
        "specifications",
    )
    readonly_fields = ()


@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = (
        "borrow_number",
        "supplier",
        "buyer",
        "borrow_date",
        "expected_return_date",
        "status",
    )
    list_filter = ("status", "borrow_date", "supplier")
    search_fields = ("borrow_number", "supplier__name", "purpose")
    readonly_fields = ("borrow_number", "created_at", "updated_at")
    fieldsets = (
        ("基本信息", {"fields": ("borrow_number", "supplier", "buyer", "status")}),
        ("日期信息", {"fields": ("borrow_date", "expected_return_date")}),
        ("转采购信息", {"fields": ("converted_order",)}),
        ("其他信息", {"fields": ("purpose", "notes")}),
        ("系统信息", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    inlines = [BorrowItemInline]
    date_hierarchy = "borrow_date"


@admin.register(BorrowItem)
class BorrowItemAdmin(admin.ModelAdmin):
    list_display = (
        "borrow",
        "product",
        "quantity",
        "returned_quantity",
        "conversion_quantity",
        "batch_number",
    )
    list_filter = ("borrow__status", "product")
    search_fields = ("borrow__borrow_number", "product__name", "batch_number")
    readonly_fields = ("created_at", "updated_at")
