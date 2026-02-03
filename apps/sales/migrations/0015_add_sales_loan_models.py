# Generated manually on 2026-01-06
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
        ('products', '0003_product_track_inventory'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sales', '0014_change_tax_rate_default'),
    ]

    operations = [
        migrations.CreateModel(
            name='SalesLoan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='是否删除')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='删除时间')),
                ('loan_number', models.CharField(db_index=True, max_length=100, unique=True, verbose_name='借用单号')),
                ('status', models.CharField(choices=[('draft', '草稿'), ('loaned', '借出中'), ('partially_returned', '部分归还'), ('fully_returned', '全部归还'), ('converting', '转换中'), ('converted', '已转销售'), ('cancelled', '已取消')], default='draft', max_length=20, verbose_name='状态')),
                ('loan_date', models.DateField(verbose_name='借出日期')),
                ('expected_return_date', models.DateField(blank=True, null=True, verbose_name='预计归还日期')),
                ('purpose', models.TextField(blank=True, help_text='样品试用/展会展示/客户测试等', verbose_name='借用目的')),
                ('delivery_address', models.TextField(blank=True, verbose_name='借出地址')),
                ('contact_person', models.CharField(blank=True, max_length=100, verbose_name='联系人')),
                ('contact_phone', models.CharField(blank=True, max_length=20, verbose_name='联系电话')),
                ('conversion_approved_at', models.DateTimeField(blank=True, null=True, verbose_name='转销售审核时间')),
                ('conversion_notes', models.TextField(blank=True, verbose_name='转销售备注')),
                ('notes', models.TextField(blank=True, verbose_name='备注')),
                ('conversion_approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='loan_conversion_approved', to=settings.AUTH_USER_MODEL, verbose_name='转销售审核人')),
                ('converted_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='source_loan', to='sales.salesorder', verbose_name='转换的销售订单')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sales_loans', to='customers.customer', verbose_name='客户')),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_deleted', to=settings.AUTH_USER_MODEL, verbose_name='删除人')),
                ('salesperson', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales_loans_as_salesperson', to=settings.AUTH_USER_MODEL, verbose_name='销售员')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='更新人')),
            ],
            options={
                'verbose_name': '销售借用单',
                'verbose_name_plural': '销售借用单',
                'db_table': 'sales_loan',
                'ordering': ['-loan_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SalesLoanItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='是否删除')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='删除时间')),
                ('quantity', models.DecimalField(decimal_places=4, help_text='借给客户的数量', max_digits=12, verbose_name='借出数量')),
                ('returned_quantity', models.DecimalField(decimal_places=4, default=0, max_digits=12, verbose_name='已归还数量')),
                ('batch_number', models.CharField(blank=True, max_length=100, verbose_name='批次号')),
                ('serial_numbers', models.TextField(blank=True, help_text='多个序列号用换行分隔', verbose_name='序列号')),
                ('conversion_unit_price', models.DecimalField(blank=True, decimal_places=2, help_text='转销售时手动输入的含税单价', max_digits=10, null=True, verbose_name='转销售单价')),
                ('conversion_quantity', models.DecimalField(decimal_places=4, default=0, help_text='已转销售的数量', max_digits=12, verbose_name='转销售数量')),
                ('specifications', models.TextField(blank=True, verbose_name='规格要求')),
                ('notes', models.TextField(blank=True, verbose_name='备注')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_deleted', to=settings.AUTH_USER_MODEL, verbose_name='删除人')),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='sales.salesloan', verbose_name='借用单')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product', verbose_name='产品')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='更新人')),
            ],
            options={
                'verbose_name': '销售借用明细',
                'verbose_name_plural': '销售借用明细',
                'db_table': 'sales_loan_item',
            },
        ),
    ]
