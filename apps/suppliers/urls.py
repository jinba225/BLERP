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
]
