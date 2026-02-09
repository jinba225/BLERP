"""
Finance模块pytest配置
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture(scope="function")
def test_users(db):
    """标准测试用户集合"""
    users = {
        "admin": User.objects.create_user(
            username="admin", email="admin@test.com", password="testpass123", is_superuser=True
        ),
        "accountant": User.objects.create_user(
            username="accountant", email="accountant@test.com", password="testpass123"
        ),
    }
    return users
