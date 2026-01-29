"""电商同步URL配置"""
from django.urls import path, include


app_name = 'ecomm_sync'

urlpatterns = [
    path('ecomm_sync/', include(('apps.ecomm_sync.urls', 'ecomm_sync')),
]
