"""
Suppliers app URLs.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "suppliers"

router = DefaultRouter()

urlpatterns = [
    # API routes
    path("api/", include(router.urls)),
    # Supplier URLs
    path("", views.supplier_list, name="supplier_list"),
    path("create/", views.supplier_create, name="supplier_create"),
    path("<int:pk>/", views.supplier_detail, name="supplier_detail"),
    path("<int:pk>/edit/", views.supplier_update, name="supplier_update"),
    path("<int:pk>/delete/", views.supplier_delete, name="supplier_delete"),
    # Supplier Contact URLs
    path("contacts/", views.contact_list, name="contact_list"),
    path("contacts/create/", views.contact_create, name="contact_create"),
    path("contacts/<int:pk>/edit/", views.contact_update, name="contact_update"),
    path("contacts/<int:pk>/delete/", views.contact_delete, name="contact_delete"),
]
