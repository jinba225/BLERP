"""
密码验证器

提供自定义密码验证规则
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re


class SpecialCharacterValidator:
    """
    验证密码是否包含特殊字符
    """
    def validate(self, password, user=None):
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _('密码必须包含至少一个特殊字符 (!@#$%^&*(),.?":{}|<>)'),
                code='password_no_special_character',
            )

    def get_help_text(self):
        return _('密码必须包含至少一个特殊字符 (!@#$%^&*(),.?":{}|<>)')


class UppercaseValidator:
    """
    验证密码是否包含大写字母
    """
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _('密码必须包含至少一个大写字母'),
                code='password_no_uppercase',
            )

    def get_help_text(self):
        return _('密码必须包含至少一个大写字母')


class LowercaseValidator:
    """
    验证密码是否包含小写字母
    """
    def validate(self, password, user=None):
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _('密码必须包含至少一个小写字母'),
                code='password_no_lowercase',
            )

    def get_help_text(self):
        return _('密码必须包含至少一个小写字母')


class NumberValidator:
    """
    验证密码是否包含数字
    """
    def validate(self, password, user=None):
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _('密码必须包含至少一个数字'),
                code='password_no_number',
            )

    def get_help_text(self):
        return _('密码必须包含至少一个数字')