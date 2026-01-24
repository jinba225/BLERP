"""
Customers app URLs.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'customers'

router = DefaultRouter()

urlpatterns = [
    # API routes
    path('api/', include(router.urls)),
    path('api/customers/<int:customer_id>/contacts/', views.api_get_customer_contacts, name='api_customer_contacts'),

    # Customer URLs
    path('', views.customer_list, name='customer_list'),
    path('create/', views.customer_create, name='customer_create'),
    path('<int:pk>/', views.customer_detail, name='customer_detail'),
    path('<int:pk>/edit/', views.customer_update, name='customer_update'),
    path('<int:pk>/delete/', views.customer_delete, name='customer_delete'),

    # Contact URLs
    path('contacts/', views.contact_list, name='contact_list'),
    path('contacts/create/', views.contact_create, name='contact_create'),
    path('contacts/<int:pk>/edit/', views.contact_update, name='contact_update'),
    path('contacts/<int:pk>/delete/', views.contact_delete, name='contact_delete'),
]

