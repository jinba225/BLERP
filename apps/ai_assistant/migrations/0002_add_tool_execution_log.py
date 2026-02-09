# Generated manually for ai_assistant

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ai_assistant", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIToolExecutionLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("is_deleted", models.BooleanField(default=False, verbose_name="是否删除")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="删除时间")),
                ("tool_name", models.CharField(max_length=100, verbose_name="工具名称")),
                (
                    "parameters",
                    models.JSONField(default=dict, help_text="工具调用时传入的参数", verbose_name="执行参数"),
                ),
                (
                    "result",
                    models.JSONField(default=dict, help_text="工具返回的结果", verbose_name="执行结果"),
                ),
                ("success", models.BooleanField(default=True, verbose_name="是否成功")),
                ("error_message", models.TextField(blank=True, verbose_name="错误信息")),
                ("executed_at", models.DateTimeField(auto_now_add=True, verbose_name="执行时间")),
                (
                    "execution_time",
                    models.FloatField(blank=True, null=True, verbose_name="执行耗时(秒)"),
                ),
                (
                    "conversation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tool_executions",
                        to="ai_assistant.aiconversation",
                        verbose_name="关联会话",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ai_assistant_aitoolexecutionlog_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="创建人",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_tool_executions",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="执行用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "AI工具执行日志",
                "verbose_name_plural": "AI工具执行日志",
                "db_table": "ai_tool_execution_log",
                "ordering": ["-executed_at"],
            },
        ),
        migrations.AddIndex(
            model_name="aitoolexecutionlog",
            index=models.Index(
                fields=["tool_name", "-executed_at"], name="ai_tool_exe_tool_na_7c9b0e_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="aitoolexecutionlog",
            index=models.Index(
                fields=["user", "-executed_at"], name="ai_tool_exe_user_id_4a5e2f_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="aitoolexecutionlog",
            index=models.Index(
                fields=["success", "-executed_at"], name="ai_tool_exe_success_3d6b8c_idx"
            ),
        ),
    ]
