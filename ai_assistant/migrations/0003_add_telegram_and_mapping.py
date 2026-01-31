# Generated manually for ai_assistant

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ai_assistant', '0002_add_tool_execution_log'),
    ]

    operations = [
        # 创建Telegram配置模型
        migrations.CreateModel(
            name='TelegramConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='是否删除')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='删除时间')),
                ('bot_token', models.CharField(help_text='从 @BotFather 获取的Token，将被加密存储', max_length=500, verbose_name='Bot Token')),
                ('bot_username', models.CharField(blank=True, help_text='机器人的@username', max_length=100, verbose_name='Bot用户名')),
                ('webhook_url', models.CharField(blank=True, help_text='Telegram回调地址', max_length=500, verbose_name='Webhook URL')),
                ('allow_groups', models.BooleanField(default=False, help_text='是否允许在群组中使用', verbose_name='允许群组')),
                ('command_prefix', models.CharField(default='/', help_text='命令前缀，默认为/', max_length=10, verbose_name='命令前缀')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ai_assistant_telegramconfig_created', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
            ],
            options={
                'verbose_name': 'Telegram配置',
                'verbose_name_plural': 'Telegram配置',
                'db_table': 'telegram_config',
            },
        ),
        # 创建渠道用户映射模型
        migrations.CreateModel(
            name='ChannelUserMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='是否删除')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='删除时间')),
                ('channel', models.CharField(choices=[('wechat', '微信'), ('dingtalk', '钉钉'), ('telegram', 'Telegram')], max_length=20, verbose_name='渠道')),
                ('external_user_id', models.CharField(help_text='微信OpenID、钉钉UserID或Telegram ChatID', max_length=200, verbose_name='外部用户ID')),
                ('external_username', models.CharField(blank=True, help_text='外部平台的用户名或昵称', max_length=200, verbose_name='外部用户名')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='存储额外的用户信息', verbose_name='元数据')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ai_assistant_channelusermapping_created', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='channel_mappings', to=settings.AUTH_USER_MODEL, verbose_name='系统用户')),
            ],
            options={
                'verbose_name': '渠道用户映射',
                'verbose_name_plural': '渠道用户映射',
                'db_table': 'channel_user_mapping',
                'ordering': ['-created_at'],
            },
        ),
        # 添加唯一约束
        migrations.AlterUniqueTogether(
            name='channelusermapping',
            unique_together={('channel', 'external_user_id')},
        ),
        # 添加索引
        migrations.AddIndex(
            model_name='channelusermapping',
            index=models.Index(fields=['channel', 'external_user_id'], name='channel_use_channel_1a2b3c_idx'),
        ),
        migrations.AddIndex(
            model_name='channelusermapping',
            index=models.Index(fields=['user', 'channel'], name='channel_use_user_id_4d5e6f_idx'),
        ),
    ]
