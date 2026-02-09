# Generated manually to restore conversion approval fields
# 这些字段在 0008 迁移中被错误移除，但代码和模板仍在使用

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("purchase", "0011_alter_purchaseorder_status"),
    ]

    operations = [
        # 恢复转采购审核人字段
        migrations.AddField(
            model_name="borrow",
            name="conversion_approved_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="approved_borrow_conversions",
                to=settings.AUTH_USER_MODEL,
                verbose_name="转采购审核人",
            ),
        ),
        # 恢复转采购审核时间字段
        migrations.AddField(
            model_name="borrow",
            name="conversion_approved_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="转采购审核时间"),
        ),
        # 恢复转采购备注字段
        migrations.AddField(
            model_name="borrow",
            name="conversion_notes",
            field=models.TextField(blank=True, verbose_name="转采购备注"),
        ),
    ]
