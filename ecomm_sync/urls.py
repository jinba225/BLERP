"""电商同步URL配置"""
from django.urls import path, include


app_name = 'ecomm_sync'

urlpatterns = [
    # 应用命名空间
    path('ecomm_sync/', include(('ecomm_sync.urls', 'ecomm_sync')),
]
