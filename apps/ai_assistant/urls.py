"""
AI Assistant URL配置
"""

from django.urls import path
from . import views
from . import webhook_views

app_name = "ai_assistant"

urlpatterns = [
    # AI模型配置管理
    path("settings/ai-models/", views.model_config_list, name="model_config_list"),
    path("settings/ai-models/create/", views.model_config_create, name="model_config_create"),
    path("settings/ai-models/<int:pk>/edit/", views.model_config_edit, name="model_config_edit"),
    path(
        "settings/ai-models/<int:pk>/delete/", views.model_config_delete, name="model_config_delete"
    ),
    path("settings/ai-models/<int:pk>/test/", views.model_config_test, name="model_config_test"),
    path(
        "settings/ai-models/<int:pk>/set-default/",
        views.model_config_set_default,
        name="model_config_set_default",
    ),
    # Webhook端点
    path("webhook/wechat/", webhook_views.wechat_webhook, name="wechat_webhook"),
    path("webhook/dingtalk/", webhook_views.dingtalk_webhook, name="dingtalk_webhook"),
    path("webhook/telegram/", webhook_views.telegram_webhook, name="telegram_webhook"),
]
