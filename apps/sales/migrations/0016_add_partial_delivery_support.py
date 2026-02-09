# Generated manually for partial delivery support
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sales", "0015_add_sales_loan_models"),
    ]

    operations = [
        # 1. 添加 DeliveryItem.actual_shipped_quantity 字段
        migrations.AddField(
            model_name="deliveryitem",
            name="actual_shipped_quantity",
            field=models.DecimalField(
                decimal_places=4,
                default=0,
                help_text="实际已发货数量（支持部分发货）",
                max_digits=12,
                verbose_name="实际发货数量",
            ),
        ),
        # 2. 修改 quantity 字段的 verbose_name 和 help_text
        migrations.AlterField(
            model_name="deliveryitem",
            name="quantity",
            field=models.DecimalField(
                decimal_places=4, help_text="计划发货数量", max_digits=12, verbose_name="计划发货数量"
            ),
        ),
        # 3. 修改 Delivery.status 字段，添加 'partially_shipped' 选项
        migrations.AlterField(
            model_name="delivery",
            name="status",
            field=models.CharField(
                choices=[
                    ("preparing", "准备中"),
                    ("ready", "待发货"),
                    ("partially_shipped", "部分发货"),
                    ("shipped", "已发货"),
                    ("in_transit", "运输中"),
                    ("delivered", "已送达"),
                    ("failed", "配送失败"),
                    ("returned", "已退回"),
                ],
                default="preparing",
                max_length=20,
                verbose_name="状态",
            ),
        ),
    ]
