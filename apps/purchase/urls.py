"""
Purchase app URLs.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "purchase"

router = DefaultRouter()

urlpatterns = [
    path("api/", include(router.urls)),
    path("", views.request_list, name="request_root"),
    path("requests/", views.request_list, name="request_list"),
    path("requests/create/", views.request_create, name="request_create"),
    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("requests/<int:pk>/edit/", views.request_update, name="request_update"),
    path("requests/<int:pk>/delete/", views.request_delete, name="request_delete"),
    path(
        "requests/<int:pk>/convert/",
        views.request_convert_to_order,
        name="request_convert_to_order",
    ),
    path("requests/<int:pk>/submit/", views.request_submit, name="request_submit"),
    path("requests/<int:pk>/approve/", views.request_approve, name="request_approve"),
    path("requests/<int:pk>/unapprove/", views.request_unapprove, name="request_unapprove"),
    path(
        "requests/<int:pk>/unapprove/confirm/",
        views.request_unapprove_confirm,
        name="request_unapprove_confirm",
    ),
    path("requests/<int:pk>/reject/", views.request_reject, name="request_reject"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/create/", views.order_create, name="order_create"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/edit/", views.order_update, name="order_update"),
    path("orders/<int:pk>/delete/", views.order_delete, name="order_delete"),
    path("orders/<int:pk>/approve/", views.order_approve, name="order_approve"),
    path("orders/<int:pk>/unapprove/", views.order_unapprove, name="order_unapprove"),
    path("orders/<int:pk>/invoice/", views.order_invoice, name="order_invoice"),
    path(
        "orders/<int:pk>/request-payment/",
        views.order_request_payment,
        name="order_request_payment",
    ),
    path("receipts/", views.receipt_list, name="receipt_list"),
    path("receipts/<int:pk>/", views.receipt_detail, name="receipt_detail"),
    path("orders/<int:order_pk>/receipt/create/", views.receipt_create, name="receipt_create"),
    path("receipts/<int:pk>/receive/", views.receipt_receive, name="receipt_receive"),
    path("receipts/<int:pk>/unapprove/", views.receipt_unapprove, name="receipt_unapprove"),
    path(
        "receipts/<int:pk>/unapprove/confirm/",
        views.receipt_unapprove_confirm,
        name="receipt_unapprove_confirm",
    ),
    path("returns/", views.return_list, name="return_list"),
    path("returns/<int:pk>/", views.return_detail, name="return_detail"),
    path("orders/<int:order_pk>/return/create/", views.return_create, name="return_create"),
    path("returns/<int:pk>/approve/", views.return_approve, name="return_approve"),
    path("returns/<int:pk>/unapprove/", views.return_unapprove, name="return_unapprove"),
    path(
        "returns/<int:pk>/unapprove/confirm/",
        views.return_unapprove_confirm,
        name="return_unapprove_confirm",
    ),
    path("returns/statistics/", views.return_statistics, name="return_statistics"),
    path("borrows/", views.borrow_list, name="borrow_list"),
    path("borrows/create/", views.borrow_create, name="borrow_create"),
    path("borrows/<int:pk>/", views.borrow_detail, name="borrow_detail"),
    path("borrows/<int:pk>/edit/", views.borrow_update, name="borrow_update"),
    path(
        "borrows/<int:pk>/confirm-receipt/",
        views.borrow_confirm_receipt,
        name="borrow_confirm_receipt",
    ),
    path(
        "borrows/<int:pk>/confirm-all-receipt/",
        views.borrow_confirm_all_receipt,
        name="borrow_confirm_all_receipt",
    ),
    path("borrows/<int:pk>/return/", views.borrow_return, name="borrow_return"),
    path(
        "borrows/<int:pk>/request-conversion/",
        views.borrow_request_conversion,
        name="borrow_request_conversion",
    ),
    path(
        "borrows/<int:pk>/cancel-conversion/",
        views.borrow_cancel_conversion,
        name="borrow_cancel_conversion",
    ),
    path(
        "borrows/<int:pk>/cancel-conversion/confirm/",
        views.borrow_cancel_conversion_confirm,
        name="borrow_cancel_conversion_confirm",
    ),
    path("inquiries/", views.inquiry_list, name="inquiry_list"),
    path("inquiries/create/", views.inquiry_create, name="inquiry_create"),
    path("inquiries/<int:pk>/", views.inquiry_detail, name="inquiry_detail"),
    path("inquiries/<int:pk>/edit/", views.inquiry_update, name="inquiry_update"),
    path("inquiries/<int:pk>/delete/", views.inquiry_delete, name="inquiry_delete"),
    path("inquiries/<int:pk>/cancel/", views.inquiry_cancel, name="inquiry_cancel"),
    path(
        "inquiries/<int:pk>/cancel/confirm/",
        views.inquiry_cancel_confirm,
        name="inquiry_cancel_confirm",
    ),
    path("inquiries/<int:pk>/send/", views.inquiry_send, name="inquiry_send"),
    path(
        "inquiries/<int:inquiry_pk>/quotations/compare/",
        views.quotation_compare,
        name="quotation_compare",
    ),
    path("quotations/", views.quotation_list, name="quotation_list"),
    path("quotations/<int:pk>/", views.quotation_detail, name="quotation_detail"),
    path("quotations/<int:pk>/edit/", views.quotation_update, name="quotation_update"),
    path("quotations/<int:pk>/select/", views.quotation_select, name="quotation_select"),
    path("reports/", views.purchase_order_report, name="order_report"),
    # API路由
    path(
        "api/suppliers/<int:supplier_id>/contacts/",
        views.supplier_contacts_api,
        name="supplier_contacts_api",
    ),
]
