"""
BetterLaser ERP - 测试数据工厂 (Factory Boy)
用于快速生成测试数据

使用示例:
    from sales.factories import SalesOrderFactory

    # 创建单个订单
    order = SalesOrderFactory()

    # 创建多个订单
    orders = SalesOrderFactory.create_batch(10)

    # 自定义字段
    order = SalesOrderFactory(
        status='confirmed',
        customer__name='特定客户名称'
    )
"""

import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyDecimal, FuzzyInteger, FuzzyDate
from datetime import date, timedelta
from decimal import Decimal


# ============================================================
# Core模块工厂
# ============================================================


class CompanyFactory(DjangoModelFactory):
    """公司工厂"""

    class Meta:
        model = "core.Company"

    name = factory.Sequence(lambda n: f"公司{n:03d}")
    short_name = factory.LazyAttribute(lambda obj: obj.name[:4])
    legal_representative = factory.Faker("name", locale="zh_CN")
    unified_social_credit_code = factory.Sequence(lambda n: f"91110000{n:010d}")
    registration_capital = FuzzyDecimal(1000000, 100000000, 2)
    address = factory.Faker("address", locale="zh_CN")
    phone = factory.Faker("phone_number", locale="zh_CN")
    email = factory.Faker("email")
    website = factory.Faker("url")


# ============================================================
# Users模块工厂
# ============================================================


class UserFactory(DjangoModelFactory):
    """用户工厂"""

    class Meta:
        model = "users.User"

    username = factory.Sequence(lambda n: f"user{n:04d}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name", locale="zh_CN")
    last_name = factory.Faker("last_name", locale="zh_CN")
    employee_id = factory.Sequence(lambda n: f"EMP{n:06d}")
    phone = factory.Faker("phone_number", locale="zh_CN")
    is_active = True
    is_staff = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """设置密码"""
        if not create:
            return
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password("testpass123")


# ============================================================
# Customers模块工厂
# ============================================================


class CustomerFactory(DjangoModelFactory):
    """客户工厂"""

    class Meta:
        model = "customers.Customer"

    code = factory.Sequence(lambda n: f"CUS{n:06d}")
    name = factory.Sequence(lambda n: f"客户{n:03d}")
    short_name = factory.LazyAttribute(lambda obj: obj.name[:4])
    customer_type = FuzzyChoice(["enterprise", "individual"])
    grade = FuzzyChoice(["A", "B", "C", "D"])
    status = "active"
    phone = factory.Faker("phone_number", locale="zh_CN")
    email = factory.Faker("email")
    address = factory.Faker("address", locale="zh_CN")
    credit_limit = FuzzyDecimal(100000, 10000000, 2)
    payment_terms = FuzzyInteger(15, 90)


class CustomerContactFactory(DjangoModelFactory):
    """客户联系人工厂"""

    class Meta:
        model = "customers.CustomerContact"

    customer = factory.SubFactory(CustomerFactory)
    name = factory.Faker("name", locale="zh_CN")
    position = FuzzyChoice(["总经理", "采购经理", "财务经理", "技术总监"])
    phone = factory.Faker("phone_number", locale="zh_CN")
    mobile = factory.Faker("phone_number", locale="zh_CN")
    email = factory.Faker("email")
    is_primary = False


# ============================================================
# Suppliers模块工厂
# ============================================================


class SupplierFactory(DjangoModelFactory):
    """供应商工厂"""

    class Meta:
        model = "suppliers.Supplier"

    code = factory.Sequence(lambda n: f"SUP{n:06d}")
    name = factory.Sequence(lambda n: f"供应商{n:03d}")
    short_name = factory.LazyAttribute(lambda obj: obj.name[:4])
    supplier_type = FuzzyChoice(["manufacturer", "distributor", "agent"])
    credit_rating = FuzzyChoice(["AAA", "AA", "A", "B", "C"])
    status = "active"
    phone = factory.Faker("phone_number", locale="zh_CN")
    email = factory.Faker("email")
    address = factory.Faker("address", locale="zh_CN")
    payment_terms = FuzzyInteger(30, 90)


# ============================================================
# Products模块工厂
# ============================================================


class BrandFactory(DjangoModelFactory):
    """品牌工厂"""

    class Meta:
        model = "products.Brand"

    name = factory.Sequence(lambda n: f"品牌{n:03d}")
    english_name = factory.Sequence(lambda n: f"Brand{n:03d}")
    description = factory.Faker("text", max_nb_chars=200, locale="zh_CN")


class UnitFactory(DjangoModelFactory):
    """单位工厂"""

    class Meta:
        model = "products.Unit"

    name = FuzzyChoice(["台", "套", "件", "个", "箱", "米", "千克"])
    symbol = factory.LazyAttribute(lambda obj: obj.name)


class ProductFactory(DjangoModelFactory):
    """产品工厂"""

    class Meta:
        model = "products.Product"

    code = factory.Sequence(lambda n: f"PRD{n:06d}")
    name = factory.Sequence(lambda n: f"激光设备{n:03d}")
    specification = factory.Faker("text", max_nb_chars=100, locale="zh_CN")
    model = factory.Sequence(lambda n: f"MODEL-{n:04d}")
    brand = factory.SubFactory(BrandFactory)
    unit = factory.SubFactory(UnitFactory)
    product_type = FuzzyChoice(["finished", "semi_finished", "raw_material", "consumable"])
    status = "active"
    cost_price = FuzzyDecimal(5000, 50000, 2)
    sale_price = factory.LazyAttribute(lambda obj: obj.cost_price * Decimal("1.3"))  # 30%加价
    min_stock_level = FuzzyInteger(5, 20)
    max_stock_level = FuzzyInteger(50, 200)


# ============================================================
# Sales模块工厂
# ============================================================


class QuoteFactory(DjangoModelFactory):
    """报价单工厂"""

    class Meta:
        model = "sales.Quote"

    quote_number = factory.Sequence(lambda n: f"QT2026010{n:04d}")
    customer = factory.SubFactory(CustomerFactory)
    quote_date = FuzzyDate(date.today() - timedelta(days=30), date.today())
    valid_until = factory.LazyAttribute(lambda obj: obj.quote_date + timedelta(days=30))
    status = "draft"
    total_amount = FuzzyDecimal(50000, 500000, 2)
    discount_amount = Decimal("0.00")
    tax_rate = Decimal("0.13")


class QuoteItemFactory(DjangoModelFactory):
    """报价明细工厂"""

    class Meta:
        model = "sales.QuoteItem"

    quote = factory.SubFactory(QuoteFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = FuzzyInteger(1, 10)
    unit_price = factory.LazyAttribute(lambda obj: obj.product.sale_price)
    line_total = factory.LazyAttribute(lambda obj: obj.quantity * obj.unit_price)
    discount_amount = Decimal("0.00")


class SalesOrderFactory(DjangoModelFactory):
    """销售订单工厂"""

    class Meta:
        model = "sales.SalesOrder"

    order_number = factory.Sequence(lambda n: f"SO2026010{n:04d}")
    customer = factory.SubFactory(CustomerFactory)
    order_date = FuzzyDate(date.today() - timedelta(days=60), date.today())
    delivery_date = factory.LazyAttribute(lambda obj: obj.order_date + timedelta(days=30))
    status = "draft"
    total_amount = FuzzyDecimal(100000, 1000000, 2)
    paid_amount = Decimal("0.00")
    discount_amount = Decimal("0.00")
    tax_rate = Decimal("0.13")


class SalesOrderItemFactory(DjangoModelFactory):
    """销售订单明细工厂"""

    class Meta:
        model = "sales.SalesOrderItem"

    order = factory.SubFactory(SalesOrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = FuzzyInteger(1, 10)
    unit_price = factory.LazyAttribute(lambda obj: obj.product.sale_price)
    line_total = factory.LazyAttribute(lambda obj: obj.quantity * obj.unit_price)
    delivered_quantity = Decimal("0")


# ============================================================
# Inventory模块工厂
# ============================================================


class WarehouseFactory(DjangoModelFactory):
    """仓库工厂"""

    class Meta:
        model = "inventory.Warehouse"

    code = factory.Sequence(lambda n: f"WH{n:03d}")
    name = factory.Sequence(lambda n: f"仓库{n:02d}")
    warehouse_type = FuzzyChoice(["main", "branch", "transit"])
    address = factory.Faker("address", locale="zh_CN")
    manager = factory.Faker("name", locale="zh_CN")
    phone = factory.Faker("phone_number", locale="zh_CN")
    status = "active"


class InventoryStockFactory(DjangoModelFactory):
    """库存工厂"""

    class Meta:
        model = "inventory.InventoryStock"

    warehouse = factory.SubFactory(WarehouseFactory)
    product = factory.SubFactory(ProductFactory)
    available_quantity = FuzzyInteger(10, 100)
    reserved_quantity = FuzzyInteger(0, 20)
    on_order_quantity = FuzzyInteger(0, 50)


# ============================================================
# Purchase模块工厂
# ============================================================


class PurchaseOrderFactory(DjangoModelFactory):
    """采购订单工厂"""

    class Meta:
        model = "purchase.PurchaseOrder"

    order_number = factory.Sequence(lambda n: f"PO2026010{n:04d}")
    supplier = factory.SubFactory(SupplierFactory)
    order_date = FuzzyDate(date.today() - timedelta(days=60), date.today())
    expected_delivery_date = factory.LazyAttribute(lambda obj: obj.order_date + timedelta(days=30))
    status = "draft"
    total_amount = FuzzyDecimal(50000, 500000, 2)
    paid_amount = Decimal("0.00")
    tax_rate = Decimal("0.13")


# ============================================================
# 辅助函数
# ============================================================


def create_complete_sales_order():
    """创建一个包含明细的完整销售订单"""
    order = SalesOrderFactory()
    items = SalesOrderItemFactory.create_batch(3, order=order)

    # 重新计算订单总金额
    order.total_amount = sum(item.line_total for item in items)
    order.save()

    return order


def create_complete_inventory_stock():
    """创建完整的库存记录（包含仓库和产品）"""
    warehouse = WarehouseFactory()
    products = ProductFactory.create_batch(10)

    stocks = []
    for product in products:
        stock = InventoryStockFactory(warehouse=warehouse, product=product)
        stocks.append(stock)

    return warehouse, stocks


def create_test_environment():
    """创建完整的测试环境"""
    # 创建用户
    users = UserFactory.create_batch(5)

    # 创建客户
    customers = CustomerFactory.create_batch(10)
    for customer in customers:
        CustomerContactFactory.create_batch(2, customer=customer)

    # 创建供应商
    suppliers = SupplierFactory.create_batch(10)

    # 创建产品
    products = ProductFactory.create_batch(20)

    # 创建仓库和库存
    warehouse = WarehouseFactory()
    for product in products:
        InventoryStockFactory(warehouse=warehouse, product=product)

    # 创建销售订单
    orders = []
    for _ in range(5):
        order = create_complete_sales_order()
        orders.append(order)

    return {
        "users": users,
        "customers": customers,
        "suppliers": suppliers,
        "products": products,
        "warehouse": warehouse,
        "orders": orders,
    }
