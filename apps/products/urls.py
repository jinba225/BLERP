"""
Products app URLs.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "products"

router = DefaultRouter()

urlpatterns = [
    # API routes
    path("api/", include(router.urls)),
    # Product URLs
    path("", views.product_list, name="product_list"),
    path("create/", views.product_create, name="product_create"),
    path("<int:pk>/", views.product_detail, name="product_detail"),
    path("<int:pk>/edit/", views.product_update, name="product_update"),
    path("<int:pk>/delete/", views.product_delete, name="product_delete"),
    # Unit URLs (计量单位)
    path("units/", views.unit_list, name="unit_list"),
    path("units/create/", views.unit_create, name="unit_create"),
    path("units/<int:pk>/", views.unit_detail, name="unit_detail"),
    path("units/<int:pk>/edit/", views.unit_update, name="unit_update"),
    path("units/<int:pk>/delete/", views.unit_delete, name="unit_delete"),
    path("units/<int:pk>/set-default/", views.unit_set_default, name="unit_set_default"),
    # Brand URLs (品牌)
    path("brands/", views.brand_list, name="brand_list"),
    path("brands/create/", views.brand_create, name="brand_create"),
    path("brands/<int:pk>/", views.brand_detail, name="brand_detail"),
    path("brands/<int:pk>/edit/", views.brand_update, name="brand_update"),
    path("brands/<int:pk>/delete/", views.brand_delete, name="brand_delete"),
    # Category URLs (产品分类)
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.category_create, name="category_create"),
    path("categories/<int:pk>/", views.category_detail, name="category_detail"),
    path("categories/<int:pk>/edit/", views.category_update, name="category_update"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
]
