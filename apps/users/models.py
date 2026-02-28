"""
用户模型扩展

添加密码过期和登录尝试限制功能
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    """
    自定义用户模型
    """

    # 密码过期相关字段
    password_last_updated = models.DateTimeField(default=timezone.now, verbose_name="密码最后更新时间")

    # 登录尝试相关字段
    failed_login_attempts = models.IntegerField(default=0, verbose_name="失败登录尝试次数")
    account_locked_until = models.DateTimeField(null=True, blank=True, verbose_name="账户锁定时间")

    # 密码过期天数设置
    PASSWORD_EXPIRY_DAYS = 90

    def is_password_expired(self):
        """
        检查密码是否过期
        """
        expiry_date = self.password_last_updated + timezone.timedelta(
            days=self.PASSWORD_EXPIRY_DAYS
        )
        return timezone.now() > expiry_date

    def is_account_locked(self):
        """
        检查账户是否被锁定
        """
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False

    def reset_failed_login_attempts(self):
        """
        重置失败登录尝试次数
        """
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save()

    def increment_failed_login_attempts(self):
        """
        增加失败登录尝试次数
        """
        self.failed_login_attempts += 1

        # 连续5次失败尝试后锁定账户30分钟
        if self.failed_login_attempts >= 5:
            self.account_locked_until = timezone.now() + timezone.timedelta(minutes=30)

        self.save()

    def update_password(self, raw_password):
        """
        更新密码并重置相关字段
        """
        self.set_password(raw_password)
        self.password_last_updated = timezone.now()
        self.reset_failed_login_attempts()
        self.save()

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"
