# 修复AIToolExecutionLog缺失字段

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ai_assistant", "0004_add_missing_fields"),
    ]

    operations = [
        # AIToolExecutionLog 添加缺失字段
        migrations.AddField(
            model_name="aitoolexecutionlog",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="aitoolexecutionlog_updated",
                to=settings.AUTH_USER_MODEL,
                verbose_name="更新人",
            ),
        ),
        migrations.AddField(
            model_name="aitoolexecutionlog",
            name="deleted_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="aitoolexecutionlog_deleted",
                to=settings.AUTH_USER_MODEL,
                verbose_name="删除人",
            ),
        ),
    ]
