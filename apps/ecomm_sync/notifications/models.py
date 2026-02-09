"""通知模型"""
from core.models import BaseModel
from django.db import models


class NotificationChannel(BaseModel):
    """通知渠道"""

    CHANNEL_CHOICES = [
        ("email", "邮件"),
        ("dingtalk", "钉钉"),
        ("wechat", "企业微信"),
        ("webhook", "Webhook"),
    ]

    name = models.CharField("渠道名称", max_length=100)
    channel_type = models.CharField("渠道类型", max_length=20, choices=CHANNEL_CHOICES)
    config = models.JSONField("配置参数", default=dict, blank=True)
    is_active = models.BooleanField("是否启用", default=True)
    webhook_url = models.URLField("Webhook URL", max_length=500, blank=True)
    webhook_secret = models.CharField("密钥", max_length=200, blank=True)
    recipient = models.CharField("接收人（邮件）", max_length=500, blank=True)
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        related_name="created_by",
        verbose_name="创建人",
    )
    updated_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_by",
        verbose_name="更新人",
    )

    class Meta:
        verbose_name = "通知渠道"
        verbose_name_plural = "通知渠道"
        db_table = "ecomm_notification_channel"
        indexes = [
            models.Index(fields=["channel_type"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class NotificationTemplate(BaseModel):
    """通知模板"""

    TEMPLATE_TYPES = [
        ("sync_success", "同步成功"),
        ("sync_failed", "同步失败"),
        ("price_change", "价格变更"),
        ("system_error", "系统错误"),
    ]

    name = models.CharField("模板名称", max_length=100)
    template_type = models.CharField("模板类型", max_length=20, choices=TEMPLATE_TYPES)
    subject = models.CharField("主题", max_length=200)
    body = models.TextField("邮件/消息正文", blank=True)
    html_template = models.TextField("HTML模板", blank=True)
    variables = models.JSONField("可用变量", default=list, blank=True)
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        related_name="created_by",
        verbose_name="创建人",
    )

    class Meta:
        verbose_name = "通知模板"
        verbose_name_plural = "通知模板"
        db_table = "ecomm_notification_template"
        indexes = [
            models.Index(fields=["template_type"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class NotificationLog(BaseModel):
    """通知日志"""

    NOTIFICATION_TYPES = [
        ("sync", "同步通知"),
        ("price", "价格通知"),
        ("error", "错误通知"),
        ("system", "系统通知"),
    ]

    log_type = models.CharField("日志类型", max_length=20, choices=NOTIFICATION_TYPES)
    channel = models.ForeignKey(
        NotificationChannel, on_delete=models.CASCADE, related_name="logs", verbose_name="通知渠道"
    )
    template = models.ForeignKey(
        NotificationTemplate, on_delete=models.SET_NULL, related_name="logs", verbose_name="通知模板"
    )
    recipient = models.CharField("接收人", max_length=500, blank=True)
    subject = models.CharField("主题", max_length=500, blank=True)
    body = models.TextField("消息正文", blank=True)
    status = models.CharField("状态", max_length=20, default="pending")
    error_message = models.TextField("错误信息", blank=True)
    sent_at = models.DateTimeField("发送时间", null=True, blank=True)
    sent_at = models.DateTimeField("发送时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        related_name="created_by",
        verbose_name="创建人",
    )

    class Meta:
        verbose_name = "通知日志"
        verbose_name_plural = "通知日志"
        db_table = "ecomm_notification_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["log_type"]),
            models.Index(fields=["channel"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.log_type} - {self.recipient}"
