"""
URL configuration for better_laser_erp project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from apps.core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication routes
    path('login/', core_views.login_view, name='login'),
    path('logout/', core_views.logout_view, name='logout'),

    # Frontend routes (Django template views)
    path('', core_views.dashboard_view, name='dashboard'),
    path('test-icons/', TemplateView.as_view(template_name='test_icons.html'), name='test_icons'),

    # App frontend routes
    path('sales/', include('apps.sales.urls')),
    path('purchase/', include('apps.purchase.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('products/', include('apps.products.urls')),
    path('customers/', include('apps.customers.urls')),
    path('suppliers/', include('apps.suppliers.urls')),
    path('finance/', include('apps.finance.urls')),
    path('departments/', include('apps.departments.urls')),
    path('users/', include('apps.users.urls')),

    # ✨ Settings routes (基础设置)
    path('settings/', include('apps.core.urls')),

    # 🤖 AI Assistant routes
    path('ai/', include('apps.ai_assistant.urls')),

    # API URLs
    path('api/auth/', include('apps.authentication.urls')),
    path('api/core/', include('apps.core.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "BetterLaser ERP 管理后台"
admin.site.site_title = "BetterLaser ERP"
admin.site.index_title = "欢迎使用 BetterLaser ERP 管理后台"