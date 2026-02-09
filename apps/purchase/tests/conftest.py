"""
Purchase tests conftest.py

导入全局pytest fixtures
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture(scope="function")
def test_users(db):
    """
    标准测试用户集合

    Returns:
        dict: 包含5种角色的测试用户
    """
    return {
        "admin": User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            is_superuser=True,
            first_name="管理员",
            last_name="系统",
        ),
        "approver": User.objects.create_user(
            username="approver",
            email="approver@test.com",
            password="testpass123",
            first_name="审核",
            last_name="人员",
        ),
        "warehouse_admin": User.objects.create_user(
            username="warehouse_admin",
            email="warehouse@test.com",
            password="testpass123",
            first_name="仓库",
            last_name="管理员",
        ),
        "salesperson": User.objects.create_user(
            username="salesperson",
            email="sales@test.com",
            password="testpass123",
            first_name="销售",
            last_name="人员",
        ),
        "accountant": User.objects.create_user(
            username="accountant",
            email="accountant@test.com",
            password="testpass123",
            first_name="会计",
            last_name="人员",
        ),
    }


@pytest.fixture(scope="function")
def test_warehouse(db):
    """
    标准测试仓库

    Returns:
        tuple: (主仓库, 借用仓)
    """
    from inventory.models import Warehouse

    warehouse = Warehouse.objects.create(
        name="测试主仓库", code="WH001", warehouse_type="main", is_active=True
    )

    borrow_wh = Warehouse.objects.create(
        name="借用仓", code="WH_BORROW", warehouse_type="borrow", is_active=True
    )

    return warehouse, borrow_wh


@pytest.fixture(scope="function")
def test_supplier(db):
    """
    标准测试供应商

    Returns:
        Supplier: 测试供应商实例
    """
    from suppliers.models import Supplier

    return Supplier.objects.create(
        name="测试供应商", code="SUP001", address="测试地址", city="测试城市", payment_terms="bank_transfer"
    )


@pytest.fixture(scope="function")
def test_customer(db):
    """
    标准测试客户

    Returns:
        Customer: 测试客户实例
    """
    from customers.models import Customer

    return Customer.objects.create(name="测试客户", code="CUS001", address="客户地址", city="客户城市")


@pytest.fixture(scope="function")
def test_product(db):
    """
    标准测试产品

    Returns:
        Product: 测试产品实例
    """
    from products.models import Product, ProductCategory, Unit

    # 创建单位
    unit = Unit.objects.create(name="件", symbol="件", unit_type="count", is_default=True)

    # 创建分类
    category = ProductCategory.objects.create(name="测试分类", code="CAT001")

    # 创建产品
    product = Product.objects.create(
        code="PROD001",
        name="测试产品",
        specifications="测试规格",
        unit=unit,
        category=category,
        cost_price=Decimal("100.00"),
        selling_price=Decimal("150.00"),
        status="active",
    )

    return product


@pytest.fixture(scope="function")
def test_products(db):
    """
    标准测试产品集合（多个产品）

    Returns:
        list: 包含3个测试产品的列表
    """
    from products.models import Product, ProductCategory, Unit

    # 创建单位
    unit = Unit.objects.create(name="件", symbol="件", unit_type="count", is_default=True)

    # 创建分类
    category = ProductCategory.objects.create(name="测试分类", code="CAT001")

    # 创建产品
    products = []
    for i in range(1, 4):
        product = Product.objects.create(
            code=f"PROD{i:03d}",
            name=f"测试产品{i}",
            specifications=f"规格{i}",
            unit=unit,
            category=category,
            cost_price=Decimal(f"{100 * i}.00"),
            selling_price=Decimal(f"{150 * i}.00"),
            status="active",
        )
        products.append(product)

    return products
