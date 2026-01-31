"""
URL configuration for better_laser_erp project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication routes
    path('login/', core_views.login_view, name='login'),
    path('logout/', core_views.logout_view, name='logout'),

    # Frontend routes (Django template views)
    path('', core_views.dashboard_view, name='dashboard'),
    path('test-icons/', TemplateView.as_view(template_name='test_icons.html'), name='test_icons'),
    path('test-sidebar-icons/', TemplateView.as_view(template_name='test_sidebar_icons.html'), name='test_sidebar_icons'),
    path('test-sidebar-standalone/', TemplateView.as_view(template_name='test_sidebar_standalone.html'), name='test_sidebar_standalone'),
    path('simple-test/', TemplateView.as_view(template_name='simple_test.html'), name='simple_test'),

    # App frontend routes
    path('sales/', include('sales.urls')),
    path('purchase/', include('purchase.urls')),
    path('inventory/', include('inventory.urls')),
    path('products/', include('products.urls')),
    path('customers/', include('customers.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('finance/', include('finance.urls')),
    path('departments/', include('departments.urls')),
    path('users/', include('users.urls')),

    # Ecomm Sync frontend routes
    path('ecomm/', include('ecomm_sync.urls')),
    
    # Collect frontend routes
    path('collect/', include('collect.urls')),

    # Settings routes (基础设置)
    path('settings/', include('core.urls')),

    # Theme switcher routes (主题切换)
    path('theme/', TemplateView.as_view(template_name='theme_switcher/index.html'), name='theme_switch'),

    # AI Assistant routes
    path('ai/', include('ai_assistant.urls')),

    # API URLs
    path('api/auth/', include('authentication.urls')),
    path('api/core/', include('core.api_urls')),
    path('api/ecomm/', include('ecomm_sync.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "BetterLaser ERP 管理后台"
admin.site.site_title = "BetterLaser ERP"
admin.site.index_title = "欢迎使用 BetterLaser ERP 管理后台"

# Cancel registration of LogEntry to avoid showing it in sidebar
try:
    from django.contrib.admin.models import LogEntry
    admin.site.unregister(LogEntry)
except Exception:
    pass  # If LogEntry is not registered, ignore error
