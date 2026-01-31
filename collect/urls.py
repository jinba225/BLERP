"""
URL路由配置
"""
from django.urls import path
from . import views

app_name = 'collect'

urlpatterns = [
    # 采集任务管理
    path('manage/', views.collect_manage, name='collect_manage'),
    path('task/create/', views.collect_task_create_ajax, name='collect_task_create_ajax'),
    path('task/status/', views.collect_task_status_ajax, name='collect_task_status_ajax'),
    path('item/list/', views.collect_item_list_ajax, name='collect_item_list_ajax'),
    
    # 平台和店铺管理
    path('platforms/', views.platform_list, name='platform_list'),
    path('shops/', views.shop_list, name='shop_list'),
    
    # Listing管理
    path('listings/', views.listing_list, name='listing_list'),
    path('listing/create/', views.create_listing_ajax, name='create_listing_ajax'),
]
