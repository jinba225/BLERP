"""
AI助手 Admin 后台管理
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AIConversation,
    AIMessage,
    AIModelConfig,
    AITool,
    AIToolExecutionLog,
    ChannelUserMapping,
    DingTalkConfig,
    TelegramConfig,
    WeChatConfig,
)


@admin.register(AIModelConfig)
class AIModelConfigAdmin(admin.ModelAdmin):
    """AI模型配置管理"""

    list_display = [
        "name",
        "provider",
        "model_name",
        "is_active",
        "is_default",
        "priority",
        "total_requests",
        "last_used_at",
    ]
    list_filter = ["provider", "is_active", "is_default"]
    search_fields = ["name", "model_name"]
    readonly_fields = [
        "total_requests",
        "total_tokens",
        "last_used_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("基本信息", {"fields": ("name", "provider", "model_name")}),
        ("API配置", {"fields": ("api_key", "api_base")}),
        ("参数配置", {"fields": ("temperature", "max_tokens", "timeout")}),
        ("状态管理", {"fields": ("is_active", "is_default", "priority")}),
        (
            "使用统计",
            {
                "fields": ("total_requests", "total_tokens", "last_used_at"),
                "classes": ("collapse",),
            },
        ),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at", "created_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # 新建时设置创建人
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    """AI对话会话管理"""

    list_display = [
        "conversation_id",
        "user",
        "channel",
        "status",
        "message_count",
        "last_message_at",
    ]
    list_filter = ["channel", "status", "created_at"]
    search_fields = ["conversation_id", "user__username", "title"]
    readonly_fields = [
        "conversation_id",
        "message_count",
        "last_message_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "会话信息",
            {"fields": ("conversation_id", "user", "channel", "channel_user_id")},
        ),
        ("会话状态", {"fields": ("status", "title", "context_summary")}),
        (
            "统计信息",
            {"fields": ("message_count", "last_message_at"), "classes": ("collapse",)},
        ),
        (
            "系统信息",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    """AI对话消息管理"""

    list_display = [
        "id",
        "conversation_link",
        "role",
        "content_preview",
        "model_config",
        "tokens_used",
        "created_at",
    ]
    list_filter = ["role", "content_type", "created_at"]
    search_fields = ["content", "conversation__conversation_id"]
    readonly_fields = ["conversation", "created_at", "updated_at"]

    fieldsets = (
        ("消息信息", {"fields": ("conversation", "role", "content", "content_type")}),
        (
            "工具调用",
            {"fields": ("tool_calls", "tool_results"), "classes": ("collapse",)},
        ),
        (
            "模型信息",
            {
                "fields": ("model_config", "tokens_used", "response_time"),
                "classes": ("collapse",),
            },
        ),
        (
            "系统信息",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def conversation_link(self, obj):
        """会话链接"""
        return format_html(
            '<a href="/admin/ai_assistant/aiconversation/{}/change/">{}</a>',
            obj.conversation.id,
            obj.conversation.conversation_id,
        )

    conversation_link.short_description = "会话"

    def content_preview(self, obj):
        """内容预览"""
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "消息内容"


@admin.register(AITool)
class AIToolAdmin(admin.ModelAdmin):
    """AI工具定义管理"""

    list_display = [
        "display_name",
        "tool_name",
        "category",
        "is_active",
        "requires_approval",
        "call_count",
        "success_count",
    ]
    list_filter = ["category", "is_active", "requires_approval"]
    search_fields = ["tool_name", "display_name", "description"]
    readonly_fields = [
        "call_count",
        "success_count",
        "last_called_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("基本信息", {"fields": ("tool_name", "display_name", "category")}),
        ("工具描述", {"fields": ("description",)}),
        ("参数定义", {"fields": ("parameters",)}),
        ("执行配置", {"fields": ("handler_path", "requires_approval")}),
        ("权限控制", {"fields": ("required_permissions",)}),
        ("状态管理", {"fields": ("is_active",)}),
        (
            "使用统计",
            {
                "fields": ("call_count", "success_count", "last_called_at"),
                "classes": ("collapse",),
            },
        ),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at", "created_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(WeChatConfig)
class WeChatConfigAdmin(admin.ModelAdmin):
    """微信配置管理"""

    list_display = ["corp_id", "agent_id", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["corp_id", "agent_id"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("基本信息", {"fields": ("corp_id", "corp_secret", "agent_id")}),
        ("安全配置", {"fields": ("token", "encoding_aes_key")}),
        ("状态管理", {"fields": ("is_active",)}),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at", "created_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DingTalkConfig)
class DingTalkConfigAdmin(admin.ModelAdmin):
    """钉钉配置管理"""

    list_display = ["app_key", "agent_id", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["app_key", "agent_id"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("基本信息", {"fields": ("app_key", "app_secret", "agent_id")}),
        ("状态管理", {"fields": ("is_active",)}),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at", "created_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TelegramConfig)
class TelegramConfigAdmin(admin.ModelAdmin):
    """Telegram配置管理"""

    list_display = ["bot_username", "allow_groups", "is_active", "created_at"]
    list_filter = ["is_active", "allow_groups"]
    search_fields = ["bot_username"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("基本信息", {"fields": ("bot_token", "bot_username", "webhook_url")}),
        ("功能设置", {"fields": ("allow_groups", "command_prefix")}),
        ("状态管理", {"fields": ("is_active",)}),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at", "created_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ChannelUserMapping)
class ChannelUserMappingAdmin(admin.ModelAdmin):
    """渠道用户映射管理"""

    list_display = ["channel", "external_username", "user", "is_active", "created_at"]
    list_filter = ["channel", "is_active", "created_at"]
    search_fields = ["external_user_id", "external_username", "user__username"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["user"]

    fieldsets = (
        ("渠道信息", {"fields": ("channel", "external_user_id", "external_username")}),
        ("系统用户", {"fields": ("user",)}),
        ("状态管理", {"fields": ("is_active",)}),
        ("元数据", {"fields": ("metadata",), "classes": ("collapse",)}),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at", "created_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AIToolExecutionLog)
class AIToolExecutionLogAdmin(admin.ModelAdmin):
    """AI工具执行日志管理"""

    list_display = ["tool_name", "user", "success", "executed_at", "execution_time"]
    list_filter = ["success", "tool_name", "executed_at"]
    search_fields = ["tool_name", "user__username"]
    readonly_fields = [
        "tool_name",
        "user",
        "parameters",
        "result",
        "success",
        "error_message",
        "executed_at",
        "execution_time",
        "conversation",
        "created_at",
    ]
    date_hierarchy = "executed_at"

    fieldsets = (
        ("工具信息", {"fields": ("tool_name", "user", "conversation")}),
        ("执行信息", {"fields": ("parameters", "result", "success", "error_message")}),
        ("时间统计", {"fields": ("executed_at", "execution_time")}),
    )

    def has_add_permission(self, request):
        # 不允许手动添加日志
        return False

    def has_change_permission(self, request, obj=None):
        # 不允许修改日志
        return False
