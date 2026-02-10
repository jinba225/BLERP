"""
Sales app URLs.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "sales"

router = DefaultRouter()

urlpatterns = [
    path("api/", include(router.urls)),
    path(
        "api/customers/<int:customer_id>/info/", views.get_customer_info, name="api_customer_info"
    ),
    path("api/products/<int:product_id>/info/", views.get_product_info, name="api_product_info"),
    path(
        "api/templates/available/",
        views.api_get_available_templates,
        name="api_get_available_templates",
    ),
    path(
        "api/templates/set-default/",
        views.api_set_default_template,
        name="api_set_default_template",
    ),
    path("", views.quote_list, name="quote_root"),
    path("quotes/", views.quote_list, name="quote_list"),
    path("quotes/create/", views.quote_create, name="quote_create"),
    path("quotes/<int:pk>/", views.quote_detail, name="quote_detail"),
    path("quotes/<int:pk>/edit/", views.quote_update, name="quote_update"),
    path("quotes/<int:pk>/delete/", views.quote_delete, name="quote_delete"),
    path("quotes/<int:pk>/convert/", views.quote_convert_to_order, name="quote_convert"),
    path("quotes/<int:pk>/status/", views.quote_change_status, name="quote_change_status"),
    path("quotes/<int:pk>/print/", views.quote_print, name="quote_print"),
    path("quotes/<int:pk>/duplicate/", views.quote_duplicate, name="quote_duplicate"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/create/", views.order_create, name="order_create"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/edit/", views.order_update, name="order_update"),
    path("orders/<int:pk>/delete/", views.order_delete, name="order_delete"),
    path("orders/<int:pk>/approve/", views.order_approve, name="order_approve"),
    path("orders/<int:pk>/unapprove/", views.order_unapprove, name="order_unapprove"),
    path("orders/<int:pk>/mark-invoiced/", views.order_mark_invoiced, name="order_mark_invoiced"),
    path("deliveries/", views.delivery_list, name="delivery_list"),
    path("deliveries/<int:pk>/", views.delivery_detail, name="delivery_detail"),
    path("deliveries/<int:pk>/edit/", views.delivery_update, name="delivery_update"),
    path("deliveries/<int:pk>/delete/", views.delivery_delete, name="delivery_delete"),
    path("orders/<int:order_pk>/delivery/create/", views.delivery_create, name="delivery_create"),
    path("deliveries/<int:pk>/ship/", views.delivery_ship, name="delivery_ship"),
    path("returns/", views.return_list, name="return_list"),
    path("returns/statistics/", views.return_statistics, name="return_statistics"),
    path("returns/<int:pk>/", views.return_detail, name="return_detail"),
    path("orders/<int:order_pk>/return/create/", views.return_create, name="return_create"),
    path("returns/<int:pk>/edit/", views.return_update, name="return_update"),
    path("returns/<int:pk>/delete/", views.return_delete, name="return_delete"),
    path("orders/<int:order_pk>/return/create/", views.return_create, name="return_create"),
    path("returns/<int:pk>/approve/", views.return_approve, name="return_approve"),
    path("returns/<int:pk>/receive/", views.return_receive, name="return_receive"),
    path("returns/<int:pk>/process/", views.return_process, name="return_process"),
    path("returns/<int:pk>/reject/", views.return_reject, name="return_reject"),
    path("loans/", views.loan_list, name="loan_list"),
    path("loans/create/", views.loan_create, name="loan_create"),
    path("loans/<int:pk>/", views.loan_detail, name="loan_detail"),
    path("loans/<int:pk>/edit/", views.loan_update, name="loan_update"),
    path("loans/<int:pk>/delete/", views.loan_delete, name="loan_delete"),
    path("loans/<int:pk>/return/", views.loan_return, name="loan_return"),
    path(
        "loans/<int:pk>/request-conversion/",
        views.loan_request_conversion,
        name="loan_request_conversion",
    ),
    path(
        "loans/<int:pk>/approve-conversion/",
        views.loan_approve_conversion,
        name="loan_approve_conversion",
    ),
    path("reports/", views.sales_order_report, name="order_report"),
    # API路由
    path(
        "api/customers/<int:customer_id>/contacts/",
        views.customer_contacts_api,
        name="customer_contacts_api",
    ),
]
