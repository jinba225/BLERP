"""
自定义认证后端

处理登录尝试限制和密码过期检查
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class CustomAuthBackend(ModelBackend):
    """
    自定义认证后端

    处理登录尝试限制和密码过期检查
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        认证用户

        检查账户是否被锁定，验证密码，并处理登录尝试
        """
        # 获取用户
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在，返回None
            return None

        # 检查账户是否被锁定
        if user.is_account_locked():
            raise ValidationError(_("账户已被锁定，请30分钟后再试"), code="account_locked")

        # 验证密码
        if not user.check_password(password):
            # 密码错误，增加失败尝试次数
            user.increment_failed_login_attempts()
            raise ValidationError(_("用户名或密码错误"), code="invalid_credentials")

        # 密码正确，重置失败尝试次数
        user.reset_failed_login_attempts()

        # 检查密码是否过期
        if user.is_password_expired():
            raise ValidationError(_("密码已过期，请更新密码"), code="password_expired")

        # 验证用户是否激活
        if not user.is_active:
            raise ValidationError(_("账户未激活"), code="account_inactive")

        return user

    def get_user(self, user_id):
        """
        获取用户
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
