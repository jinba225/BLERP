"""
简单的pytest设置测试
验证pytest-django是否正常工作
"""

import pytest


@pytest.mark.django_db
def test_pytest_django_works():
    """测试pytest-django是否正常工作"""
    from django.contrib.auth import get_user_model

    User = get_user_model()

    # 创建一个测试用户
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

    # 验证用户创建成功
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_django_config_loaded():
    """测试Django配置是否正确加载"""
    from django.conf import settings

    # 验证INSTALLED_APPS包含核心应用
    assert 'purchase' in [app.split('.')[-1] for app in settings.INSTALLED_APPS]
    assert 'sales' in [app.split('.')[-1] for app in settings.INSTALLED_APPS]
    assert 'inventory' in [app.split('.')[-1] for app in settings.INSTALLED_APPS]
    assert 'finance' in [app.split('.')[-1] for app in settings.INSTALLED_APPS]
