"""
Core admin configuration.
"""
import re
import shlex
import subprocess
from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    Attachment,
    AuditLog,
    ChoiceOption,
    ChoiceOptionGroup,
    Company,
    DefaultTemplateMapping,
    Notification,
    PrintTemplate,
    SystemConfig,
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "legal_representative", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "code", "legal_representative"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("基本信息", {"fields": ("name", "code", "is_active")}),
        (
            "公司信息",
            {"fields": ("legal_representative", "registration_number", "tax_number", "address")},
        ),
        ("联系方式", {"fields": ("phone", "fax", "email", "website")}),
        ("Logo和描述", {"fields": ("logo", "description", "description_en")}),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ["key", "display_value", "config_type", "is_active", "updated_at"]
    list_filter = ["config_type", "is_active", "created_at"]
    search_fields = ["key", "value", "description"]
    readonly_fields = ["created_at", "updated_at"]
    list_editable = ["is_active"]

    fieldsets = (
        ("基本信息", {"fields": ("key", "value", "config_type", "is_active")}),
        ("说明", {"fields": ("description",)}),
        ("系统信息", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def display_value(self, obj):
        """显示配置值，单号前缀以高亮显示"""
        if obj.key.startswith("document_prefix_"):
            return f"{obj.value} (单号前缀)"
        return obj.value

    display_value.short_description = "配置值"

    def get_queryset(self, request):
        """重写查询集，按 config_type 和 key 排序"""
        qs = super().get_queryset(request)
        return qs.order_by("config_type", "key")

    class ActionForm(forms.Form):
        action = forms.ChoiceField(label=_("动作"), required=False)
        select_across = forms.CharField(required=False, initial="1", widget=forms.HiddenInput)
        timestamp = forms.CharField(required=False, label=_("备份时间戳"))

    actions = ["backup_database_action", "restore_database_action", "flush_test_data_action"]
    action_form = ActionForm

    def changelist_view(self, request, extra_context=None):
        if request.method == "POST" and request.POST.get("action"):
            if not request.POST.getlist(helpers.ACTION_CHECKBOX_NAME) and not request.POST.get(
                "select_across"
            ):
                post = request.POST.copy()
                post["select_across"] = "1"
                request.POST = post
        return super().changelist_view(request, extra_context=extra_context)

    def _run_backup_script(self):
        cmd = ["bash", "scripts/backup.sh"]
        return subprocess.run(cmd, cwd=settings.BASE_DIR, capture_output=True, text=True)

    def _backup_sqlite(self):
        ts = timezone.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        src = Path(settings.DATABASES["default"]["NAME"])
        dst = backup_dir / f"db_{ts}.sqlite3"
        result = subprocess.run(
            ["bash", "-lc", f"cp {shlex.quote(str(src))} {shlex.quote(str(dst))}"],
            capture_output=True,
            text=True,
        )
        return result, str(dst)

    def backup_database_action(self, request, queryset):
        from .tasks import backup_database

        if getattr(settings, "CELERY_BROKER_URL", None):
            backup_database.delay()
            self.message_user(request, "已触发后台数据库备份任务", level=messages.SUCCESS)
            return
        engine = settings.DATABASES["default"]["ENGINE"]
        if engine == "django.db.backends.sqlite3":
            result, dst = self._backup_sqlite()
            if result.returncode == 0:
                self.message_user(request, f"SQLite 数据库备份完成: {dst}", level=messages.SUCCESS)
            else:
                self.message_user(
                    request, f"SQLite 备份失败: {result.stderr or result.stdout}", level=messages.ERROR
                )
            return
        result = self._run_backup_script()
        if result.returncode == 0:
            self.message_user(request, "数据库备份完成", level=messages.SUCCESS)
        else:
            self.message_user(
                request, f"备份失败: {result.stderr or result.stdout}", level=messages.ERROR
            )

    backup_database_action.short_description = "立即备份数据库"

    def restore_database_action(self, request, queryset):
        ts = request.POST.get("timestamp") or ""
        if not re.match(r"^\d{8}_\d{6}$", ts):
            self.message_user(request, "请在动作表单中填写备份时间戳，如 20250101_120000", level=messages.ERROR)
            return
        db = settings.DATABASES["default"]
        engine = db["ENGINE"]
        if engine == "django.db.backends.sqlite3":
            backup_file = Path(settings.BASE_DIR) / "backups" / f"db_{ts}.sqlite3"
            if not backup_file.exists():
                self.message_user(request, f"找不到备份文件: {backup_file}", level=messages.ERROR)
                return
            dst = Path(db["NAME"])
            result = subprocess.run(
                ["bash", "-lc", f"cp {shlex.quote(str(backup_file))} {shlex.quote(str(dst))}"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                self.message_user(request, "SQLite 数据库恢复完成", level=messages.SUCCESS)
            else:
                self.message_user(
                    request, f"恢复失败: {result.stderr or result.stdout}", level=messages.ERROR
                )
            return
        host = db.get("HOST", "localhost")
        port = str(db.get("PORT", "3306"))
        user = db.get("USER", "root")
        password = db.get("PASSWORD", "")
        name = db.get("NAME")
        backup_dir = "/var/backups/better-laser-erp"
        sql_gz = f"{backup_dir}/database_{ts}.sql.gz"
cmd = (
    f"gunzip -c {shlex.quote(sql_gz)} | mysql -h{shlex.quote(host)} -P{shlex.quote(port)} -u{shlex.quote(user)} -p{shlex.quote(password)} {shlex.quote(name)}"
)
        result = subprocess.run(
            ["bash", "-lc", cmd], cwd=settings.BASE_DIR, capture_output=True, text=True
        )
        if result.returncode == 0:
            self.message_user(request, "数据库恢复完成", level=messages.SUCCESS)
        else:
            self.message_user(
                request, f"恢复失败: {result.stderr or result.stdout}", level=messages.ERROR
            )

    restore_database_action.short_description = "从时间戳恢复数据库"

    def flush_test_data_action(self, request, queryset):
        from django.apps import apps as django_apps

        try:
            app_labels = [
                "customers",
                "suppliers",
                "products",
                "inventory",
                "sales",
                "purchase",
                "finance",
                "production",
                "reports",
                "contracts",
            ]
            total_deleted = 0
            for label in app_labels:
                config = django_apps.get_app_config(label)
                for model in config.get_models():
                    deleted, _ = model.objects.all().delete()
                    total_deleted += deleted
            self.message_user(request, f"测试数据已清除，共删除 {total_deleted} 条记录", level=messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"清除失败: {e}", level=messages.ERROR)

    flush_test_data_action.short_description = "一键清除测试数据库"


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ["name", "file_type", "file_size_display", "created_at"]
    list_filter = ["file_type", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at", "file_size"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["user", "action", "model_name", "object_repr", "timestamp"]
    list_filter = ["action", "model_name", "timestamp"]
    search_fields = ["user__username", "object_repr"]
    readonly_fields = ["timestamp"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "title", "category", "notification_type", "is_read", "created_at"]
    list_filter = ["notification_type", "category", "is_read", "created_at"]
    search_fields = ["recipient__username", "title", "message"]
    readonly_fields = ["created_at", "read_at"]

    def has_add_permission(self, request):
        # Notifications should be created programmatically
        return False


# ============================================
# 打印模板管理 (移自 sales 模块)
# ============================================
@admin.register(PrintTemplate)
class PrintTemplateAdmin(admin.ModelAdmin):
    """
    Admin configuration for Print Template model.
    """

    list_display = (
        "name",
        "template_category",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("template_category", "is_active")
    search_fields = ("name", "company_name")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")

    fieldsets = (
        ("基本信息", {"fields": ("name", "template_category", "suitable_for", "is_active")}),
        (
            "公司信息",
            {
                "fields": (
                    "company_name",
                    "company_address",
                    "company_phone",
                    "company_email",
                    "company_logo",
                )
            },
        ),
        ("布局配置", {"fields": ("layout_config",)}),
        ("自定义样式", {"fields": ("custom_css",)}),
        ("备注", {"fields": ("notes",)}),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """Save the model and set the user information."""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DefaultTemplateMapping)
class DefaultTemplateMappingAdmin(admin.ModelAdmin):
    """
    Admin configuration for Default Template Mapping model.
    """

    list_display = (
        "document_type",
        "template",
        "created_at",
        "updated_at",
    )
    list_filter = ("document_type",)
    search_fields = ("template__name",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")

    fieldsets = (
        ("基本信息", {"fields": ("document_type", "template")}),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """Save the model and set the user information."""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================
# 选项配置管理 (Dynamic Choice Options)
# ============================================


@admin.register(ChoiceOption)
class ChoiceOptionAdmin(admin.ModelAdmin):
    """选项配置管理"""

    list_display = [
        "get_category_display_custom",
        "code",
        "label",
        "sort_order",
        "is_active",
        "is_system",
        "color_preview",
        "created_at",
    ]
    list_filter = ["category", "is_active", "is_system", "created_at"]
    search_fields = ["code", "label", "description"]
    ordering = ["category", "sort_order", "code"]
    list_editable = ["sort_order", "is_active"]

    fieldsets = (
        ("基本信息", {"fields": ("category", "code", "label", "description")}),
        ("显示设置", {"fields": ("sort_order", "is_active", "color", "icon")}),
        (
            "系统信息",
            {
                "fields": ("is_system", "created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def get_category_display_custom(self, obj):
        """显示分类名称"""
        return obj.get_category_display()

    get_category_display_custom.short_description = "选项分类"
    get_category_display_custom.admin_order_field = "category"

    def color_preview(self, obj):
        """颜色预览"""
        if obj.color:
            return format_html(
                '<span style="background-color: {}; padding: 2px 10px; border-radius: 3px; color: white;">{}</span>',
                obj.color,
                obj.color,
            )
        return "-"

    color_preview.short_description = "颜色"

    def get_readonly_fields(self, request, obj=None):
        """系统内置选项不允许修改分类和代码"""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_system:
            readonly.extend(["category", "code"])
        return readonly

    def has_delete_permission(self, request, obj=None):
        """系统内置选项不允许删除"""
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        """保存时设置创建人/更新人"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    # 添加批量操作
    actions = ["activate_selected", "deactivate_selected", "duplicate_selected"]

    def activate_selected(self, request, queryset):
        """批量启用"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"成功启用 {updated} 个选项", level=messages.SUCCESS)

    activate_selected.short_description = "启用选中的选项"

    def deactivate_selected(self, request, queryset):
        """批量禁用"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"成功禁用 {updated} 个选项", level=messages.SUCCESS)

    deactivate_selected.short_description = "禁用选中的选项"

    def duplicate_selected(self, request, queryset):
        """批量复制选项"""
        count = 0
        for obj in queryset:
            obj.pk = None
            obj.code = f"{obj.code}_copy"
            obj.label = f"{obj.label} (副本)"
            obj.is_system = False
            obj.created_by = request.user
            obj.updated_by = request.user
            obj.save()
            count += 1
        self.message_user(request, f"成功复制 {count} 个选项", level=messages.SUCCESS)

    duplicate_selected.short_description = "复制选中的选项"


@admin.register(ChoiceOptionGroup)
class ChoiceOptionGroupAdmin(admin.ModelAdmin):
    """选项分组管理"""

    list_display = [
        "get_category_display_custom",
        "code",
        "name",
        "sort_order",
        "is_active",
        "created_at",
    ]
    list_filter = ["category", "is_active", "created_at"]
    search_fields = ["code", "name"]
    ordering = ["category", "sort_order", "code"]
    list_editable = ["sort_order", "is_active"]

    fieldsets = (
        ("基本信息", {"fields": ("category", "code", "name")}),
        ("显示设置", {"fields": ("sort_order", "is_active")}),
        (
            "系统信息",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def get_category_display_custom(self, obj):
        """显示分类名称"""
        return obj.get_category_display()

    get_category_display_custom.short_description = "所属分类"
    get_category_display_custom.admin_order_field = "category"

    def save_model(self, request, obj, form, change):
        """保存时设置创建人/更新人"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
