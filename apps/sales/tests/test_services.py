"""
Sales模块 - 服务层测试
测试QuoteService, OrderService和订单审核业务逻辑
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from sales.services.business import OrderService, QuoteService

from apps.core.models import SystemConfig
from apps.customers.models import Customer, CustomerCategory, CustomerContact
from apps.departments.models import Department
from apps.finance.models import CustomerAccount
from apps.inventory.models import Warehouse
from apps.products.models import Brand, Product, ProductCategory, Unit
from apps.sales.models import Delivery, DeliveryItem, Quote, QuoteItem, SalesOrder, SalesOrderItem

User = get_user_model()


class SalesServiceTestCaseBase(TestCase):
    """Sales服务测试基类 - 准备测试数据"""

    def setUp(self):
        """测试前准备 - 创建测试数据"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            employee_id="EMP001",
        )

        # 创建部门
        self.department = Department.objects.create(name="销售部", code="SALES", created_by=self.user)
        self.user.department = self.department
        self.user.save()

        # 创建客户分类
        self.customer_category = CustomerCategory.objects.create(
            name="优质客户", code="VIP", created_by=self.user
        )

        # 创建测试客户
        self.customer = Customer.objects.create(
            name="测试客户A公司",
            code="CUS001",
            customer_level="A",
            status="active",
            category=self.customer_category,
            address="北京市朝阳区测试路123号",
            city="北京",
            province="北京市",
            credit_limit=Decimal("1000000.00"),
            created_by=self.user,
        )

        # 创建客户联系人
        self.contact = CustomerContact.objects.create(
            customer=self.customer,
            name="张三",
            position="采购经理",
            mobile="13800138000",
            email="zhang@customer.com",
            is_primary=True,
            created_by=self.user,
        )

        # 创建产品分类
        self.product_category = ProductCategory.objects.create(
            name="激光设备", code="LASER", created_by=self.user
        )

        # 创建品牌
        self.brand = Brand.objects.create(name="测试品牌", code="BRAND001", created_by=self.user)

        # 创建单位
        self.unit = Unit.objects.create(name="台", symbol="台", created_by=self.user)

        # 创建测试产品
        self.product1 = Product.objects.create(
            name="激光切割机A型",
            code="PRD001",
            specifications="3000W 光纤激光切割机",
            category=self.product_category,
            brand=self.brand,
            unit=self.unit,
            cost_price=Decimal("80000.00"),
            selling_price=Decimal("100000.00"),
            status="active",
            created_by=self.user,
        )

        self.product2 = Product.objects.create(
            name="激光打标机B型",
            code="PRD002",
            specifications="20W 光纤激光打标机",
            category=self.product_category,
            brand=self.brand,
            unit=self.unit,
            cost_price=Decimal("8000.00"),
            selling_price=Decimal("10000.00"),
            status="active",
            created_by=self.user,
        )

        # 创建仓库
        self.warehouse = Warehouse.objects.create(name="主仓库", code="WH001", created_by=self.user)

        # 创建系统配置（自动创建发货单）- 使用get_or_create避免唯一性冲突
        SystemConfig.objects.get_or_create(
            key="sales_auto_create_delivery_on_approve",
            defaults={
                "value": "true",
                "config_type": "business",
                "description": "审核订单时自动创建发货单",
                "is_active": True,
            },
        )

        # 创建发货单前缀配置 - 使用get_or_create避免唯一性冲突
        SystemConfig.objects.get_or_create(
            key="document_prefix_delivery",
            defaults={
                "value": "OUT",
                "config_type": "business",
                "description": "发货单前缀",
                "is_active": True,
            },
        )


class QuoteServiceTestCase(SalesServiceTestCaseBase):
    """QuoteService服务测试"""

    def test_create_quote_basic(self):
        """测试创建基础报价单"""
        quote_data = {
            "customer": self.customer,
            "quote_date": date.today(),
            "valid_until": date.today() + timedelta(days=30),
            "status": "draft",
            "tax_rate": Decimal("0.13"),
        }

        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("2"),
                "unit_price": Decimal("100000.00"),
                "tax_rate": Decimal("0.13"),
                "line_total": Decimal("200000.00"),  # quantity * unit_price
            },
            {
                "product": self.product2,
                "quantity": Decimal("5"),
                "unit_price": Decimal("10000.00"),
                "tax_rate": Decimal("0.13"),
                "line_total": Decimal("50000.00"),  # quantity * unit_price
            },
        ]

        quote = QuoteService.create_quote(self.user, quote_data, items_data)

        # 验证报价单创建成功
        self.assertIsNotNone(quote.id)
        self.assertEqual(quote.customer, self.customer)
        self.assertEqual(quote.status, "draft")
        self.assertEqual(quote.created_by, self.user)

        # 验证单据号自动生成
        self.assertIsNotNone(quote.quote_number)
        self.assertTrue(quote.quote_number.startswith("QT"))

        # 验证报价明细
        self.assertEqual(quote.items.count(), 2)
        item1 = quote.items.get(product=self.product1)
        self.assertEqual(item1.quantity, Decimal("2"))
        self.assertEqual(item1.unit_price, Decimal("100000.00"))

        # 验证总额自动计算
        self.assertGreater(quote.total_amount, Decimal("0"))

    def test_create_quote_with_custom_number(self):
        """测试创建报价单时指定单据号"""
        quote_data = {
            "customer": self.customer,
            "quote_number": "QT_CUSTOM_001",  # 指定单据号
            "quote_date": date.today(),
            "valid_until": date.today() + timedelta(days=30),
            "status": "draft",
            "tax_rate": Decimal("0.13"),
        }

        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("1"),
                "unit_price": Decimal("100000.00"),
                "tax_rate": Decimal("0.13"),
            },
        ]

        quote = QuoteService.create_quote(self.user, quote_data, items_data)

        # 验证使用了指定的单据号
        self.assertEqual(quote.quote_number, "QT_CUSTOM_001")

    def test_create_quote_empty_items(self):
        """测试创建没有明细的报价单"""
        quote_data = {
            "customer": self.customer,
            "quote_date": date.today(),
            "valid_until": date.today() + timedelta(days=30),
            "status": "draft",
            "tax_rate": Decimal("0.13"),
        }

        items_data = []  # 空明细

        quote = QuoteService.create_quote(self.user, quote_data, items_data)

        # 报价单应该创建成功，但没有明细
        self.assertIsNotNone(quote.id)
        self.assertEqual(quote.items.count(), 0)
        self.assertEqual(quote.total_amount, Decimal("0"))

    def test_update_quote_basic(self):
        """测试更新报价单"""
        # 先创建一个报价单
        quote_data = {
            "customer": self.customer,
            "quote_date": date.today(),
            "valid_until": date.today() + timedelta(days=30),
            "status": "draft",
            "tax_rate": Decimal("0.13"),
        }
        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("1"),
                "unit_price": Decimal("100000.00"),
                "tax_rate": Decimal("0.13"),
                "line_total": Decimal("100000.00"),
            },
        ]
        quote = QuoteService.create_quote(self.user, quote_data, items_data)
        original_number = quote.quote_number
        original_item_count = quote.items.count()

        # 更新报价单
        update_data = {
            "status": "sent",
            "notes": "已发送给客户",
        }
        new_items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("2"),
                "unit_price": Decimal("95000.00"),
                "tax_rate": Decimal("0.13"),
                "line_total": Decimal("190000.00"),  # 修改数量和价格
            },
            {
                "product": self.product2,
                "quantity": Decimal("3"),
                "unit_price": Decimal("10000.00"),
                "tax_rate": Decimal("0.13"),
                "line_total": Decimal("30000.00"),  # 新增产品
            },
        ]

        updated_quote = QuoteService.update_quote(quote, self.user, update_data, new_items_data)

        # 验证报价单更新成功
        self.assertEqual(updated_quote.id, quote.id)  # 同一个报价单
        self.assertEqual(updated_quote.quote_number, original_number)  # 单据号不变
        self.assertEqual(updated_quote.status, "sent")
        self.assertEqual(updated_quote.notes, "已发送给客户")
        self.assertEqual(updated_quote.updated_by, self.user)

        # 验证明细已更新
        self.assertEqual(updated_quote.items.count(), 2)
        item1 = updated_quote.items.get(product=self.product1)
        self.assertEqual(item1.quantity, Decimal("2"))
        self.assertEqual(item1.unit_price, Decimal("95000.00"))

    def test_update_quote_keep_items_when_none(self):
        """测试更新报价单但不修改明细"""
        # 创建报价单
        quote_data = {
            "customer": self.customer,
            "quote_date": date.today(),
            "valid_until": date.today() + timedelta(days=30),
            "status": "draft",
            "tax_rate": Decimal("0.13"),
        }
        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("1"),
                "unit_price": Decimal("100000.00"),
                "tax_rate": Decimal("0.13"),
                "line_total": Decimal("100000.00"),
            },
        ]
        quote = QuoteService.create_quote(self.user, quote_data, items_data)
        original_item_count = quote.items.count()

        # 更新报价单，但items_data=None（不修改明细）
        update_data = {"status": "sent"}
        updated_quote = QuoteService.update_quote(quote, self.user, update_data, items_data=None)

        # 验证明细未被删除
        self.assertEqual(updated_quote.items.count(), original_item_count)
        self.assertEqual(updated_quote.status, "sent")

    def test_create_quote_transaction_rollback(self):
        """测试创建报价单时事务回滚（如果发生错误）"""
        quote_data = {
            "customer": self.customer,
            "quote_date": date.today(),
            "valid_until": date.today() + timedelta(days=30),
            "status": "draft",
            "tax_rate": Decimal("0.13"),
        }

        # 故意传入错误的items_data（缺少必要字段）
        items_data = [
            {"product": self.product1},  # 缺少quantity和unit_price
        ]

        initial_quote_count = Quote.objects.count()

        # 应该抛出异常
        with self.assertRaises(Exception):
            QuoteService.create_quote(self.user, quote_data, items_data)

        # 验证事务回滚（没有创建报价单）
        self.assertEqual(Quote.objects.count(), initial_quote_count)


class OrderServiceTestCase(SalesServiceTestCaseBase):
    """OrderService服务测试"""

    def test_create_order_basic(self):
        """测试创建基础销售订单"""
        order_data = {
            "customer": self.customer,
            "order_date": date.today(),
            "status": "draft",
            "payment_status": "unpaid",
        }

        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("2"),
                "unit_price": Decimal("100000.00"),
            },
            {"product": self.product2, "quantity": Decimal("5"), "unit_price": Decimal("10000.00")},
        ]

        order = OrderService.create_order(self.user, order_data, items_data)

        # 验证订单创建成功
        self.assertIsNotNone(order.id)
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.status, "draft")
        self.assertEqual(order.created_by, self.user)

        # 验证单据号自动生成
        self.assertIsNotNone(order.order_number)
        self.assertTrue(order.order_number.startswith("SO"))

        # 验证订单明细
        self.assertEqual(order.items.count(), 2)

        # 验证sort_order
        items = list(order.items.order_by("sort_order"))
        self.assertEqual(items[0].sort_order, 0)
        self.assertEqual(items[1].sort_order, 1)

        # 验证总额自动计算
        self.assertGreater(order.total_amount, Decimal("0"))

    def test_create_order_filter_empty_items(self):
        """测试创建订单时过滤空明细"""
        order_data = {
            "customer": self.customer,
            "order_date": date.today(),
            "status": "draft",
        }

        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("1"),
                "unit_price": Decimal("100000.00"),
            },
            {},  # 空明细（没有product）
            {"product_id": None},  # 空product_id
            {"product": self.product2, "quantity": Decimal("2"), "unit_price": Decimal("10000.00")},
        ]

        order = OrderService.create_order(self.user, order_data, items_data)

        # 验证只创建了有效明细
        self.assertEqual(order.items.count(), 2)

    def test_update_order_basic(self):
        """测试更新销售订单"""
        # 创建订单
        order_data = {"customer": self.customer, "order_date": date.today(), "status": "draft"}
        items_data = [
            {"product": self.product1, "quantity": Decimal("1"), "unit_price": Decimal("100000.00")}
        ]
        order = OrderService.create_order(self.user, order_data, items_data)
        original_number = order.order_number

        # 更新订单
        update_data = {"status": "confirmed", "notes": "客户确认订单"}
        new_items_data = [
            {"product": self.product1, "quantity": Decimal("2"), "unit_price": Decimal("95000.00")},
            {"product": self.product2, "quantity": Decimal("3"), "unit_price": Decimal("10000.00")},
        ]

        updated_order = OrderService.update_order(order, self.user, update_data, new_items_data)

        # 验证更新成功
        self.assertEqual(updated_order.id, order.id)
        self.assertEqual(updated_order.order_number, original_number)
        self.assertEqual(updated_order.status, "confirmed")
        self.assertEqual(updated_order.updated_by, self.user)

        # 验证明细已更新
        self.assertEqual(updated_order.items.count(), 2)

    def test_convert_quote_to_order_basic(self):
        """测试报价单转销售订单"""
        # 创建报价单
        quote_data = {
            "customer": self.customer,
            "quote_date": date.today(),
            "valid_until": date.today() + timedelta(days=30),
            "status": "accepted",
            "payment_terms": "net_30",
            "tax_rate": Decimal("0.13"),
        }
        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("2"),
                "unit_price": Decimal("100000.00"),
                "tax_rate": Decimal("0.13"),
                "line_total": Decimal("200000.00"),
            },
            {
                "product": self.product2,
                "quantity": Decimal("5"),
                "unit_price": Decimal("10000.00"),
                "tax_rate": Decimal("0.13"),
                "line_total": Decimal("50000.00"),
            },
        ]
        quote = QuoteService.create_quote(self.user, quote_data, items_data)

        # 转换为订单
        order = OrderService.convert_quote_to_order(quote, self.user)

        # 验证订单创建成功
        self.assertIsNotNone(order.id)
        self.assertEqual(order.customer, quote.customer)
        self.assertEqual(order.created_by, self.user)
        self.assertEqual(order.status, "draft")  # 新订单状态为draft

        # 验证订单明细数量与报价单一致
        self.assertEqual(order.items.count(), quote.items.count())

        # 验证订单号自动生成
        self.assertTrue(order.order_number.startswith("SO"))
        self.assertNotEqual(order.order_number, quote.quote_number)

        # 验证金额一致
        self.assertEqual(order.total_amount, quote.total_amount)

    def test_convert_quote_to_order_with_extra_data(self):
        """测试报价单转订单时添加额外数据"""
        # 创建报价单
        quote_data = {
            "customer": self.customer,
            "quote_date": date.today(),
            "valid_until": date.today() + timedelta(days=30),
            "status": "accepted",
            "tax_rate": Decimal("0.13"),
        }
        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("1"),
                "unit_price": Decimal("100000.00"),
                "tax_rate": Decimal("0.13"),
                "line_total": Decimal("100000.00"),
            },
        ]
        quote = QuoteService.create_quote(self.user, quote_data, items_data)

        # 转换为订单，并添加额外数据
        extra_data = {
            "required_date": date.today() + timedelta(days=15),
            "shipping_method": "express",
            "notes": "客户要求加急",
        }
        order = OrderService.convert_quote_to_order(quote, self.user, extra_data)

        # 验证额外数据已设置
        self.assertEqual(order.required_date, extra_data["required_date"])
        self.assertEqual(order.shipping_method, extra_data["shipping_method"])
        self.assertEqual(order.notes, extra_data["notes"])


class SalesOrderApprovalTestCase(SalesServiceTestCaseBase):
    """SalesOrder审核业务逻辑测试"""

    def test_approve_order_basic(self):
        """测试基础订单审核流程"""
        # 创建订单
        order_data = {"customer": self.customer, "order_date": date.today(), "status": "draft"}
        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("1"),
                "unit_price": Decimal("100000.00"),
            },
        ]
        order = OrderService.create_order(self.user, order_data, items_data)
        order.calculate_totals()
        order.save()

        # 审核订单
        delivery, account = order.approve_order(self.user, self.warehouse)

        # 验证订单状态已更新
        order.refresh_from_db()
        self.assertEqual(order.status, "confirmed")
        self.assertEqual(order.approved_by, self.user)
        self.assertIsNotNone(order.approved_at)

        # 验证发货单已创建
        self.assertIsNotNone(delivery)
        self.assertEqual(delivery.sales_order, order)
        self.assertEqual(delivery.warehouse, self.warehouse)
        self.assertEqual(delivery.status, "preparing")
        self.assertTrue(delivery.delivery_number.startswith("OUT"))

        # 验证发货明细已创建
        self.assertEqual(delivery.items.count(), order.items.count())
        delivery_item = delivery.items.first()
        order_item = order.items.first()
        self.assertEqual(delivery_item.quantity, order_item.quantity)

        # 验证应收账款已创建
        self.assertIsNotNone(account)
        self.assertEqual(account.customer, order.customer)
        self.assertEqual(account.sales_order, order)
        self.assertEqual(account.invoice_amount, order.total_amount)
        self.assertEqual(account.balance, order.total_amount)

    def test_approve_order_already_approved(self):
        """测试重复审核订单"""
        # 创建并审核订单
        order_data = {"customer": self.customer, "order_date": date.today(), "status": "draft"}
        items_data = [
            {"product": self.product1, "quantity": Decimal("1"), "unit_price": Decimal("100000.00")}
        ]
        order = OrderService.create_order(self.user, order_data, items_data)
        order.calculate_totals()
        order.save()
        order.approve_order(self.user, self.warehouse)

        # 尝试再次审核
        with self.assertRaisesMessage(ValueError, "订单已经审核过了"):
            order.approve_order(self.user, self.warehouse)

    def test_approve_order_without_items(self):
        """测试审核没有明细的订单"""
        # 创建空订单
        order = SalesOrder.objects.create(
            order_number="SO_EMPTY_001",
            customer=self.customer,
            order_date=date.today(),
            status="draft",
            created_by=self.user,
        )

        # 尝试审核
        with self.assertRaisesMessage(ValueError, "订单没有明细，无法审核"):
            order.approve_order(self.user, self.warehouse)

    def test_approve_order_without_warehouse(self):
        """测试在没有仓库的情况下审核订单"""
        # 删除所有仓库
        Warehouse.objects.all().delete()

        # 创建订单
        order_data = {"customer": self.customer, "order_date": date.today(), "status": "draft"}
        items_data = [
            {"product": self.product1, "quantity": Decimal("1"), "unit_price": Decimal("100000.00")}
        ]
        order = OrderService.create_order(self.user, order_data, items_data)
        order.calculate_totals()
        order.save()

        # 尝试审核（没有指定仓库，且系统中也没有仓库）
        with self.assertRaisesMessage(ValueError, "没有可用的仓库，请先创建仓库"):
            order.approve_order(self.user)

    def test_approve_order_with_auto_create_delivery_disabled(self):
        """测试禁用自动创建发货单时的审核"""
        # 修改系统配置：禁用自动创建发货单
        config = SystemConfig.objects.get(key="sales_auto_create_delivery_on_approve")
        config.value = "false"
        config.save()

        # 创建订单
        order_data = {"customer": self.customer, "order_date": date.today(), "status": "draft"}
        items_data = [
            {"product": self.product1, "quantity": Decimal("1"), "unit_price": Decimal("100000.00")}
        ]
        order = OrderService.create_order(self.user, order_data, items_data)
        order.calculate_totals()
        order.save()

        # 审核订单
        delivery, account = order.approve_order(self.user, self.warehouse)

        # 验证订单已审核
        order.refresh_from_db()
        self.assertEqual(order.status, "confirmed")

        # 验证发货单未创建
        self.assertIsNone(delivery)

        # 验证应收账款仍然创建
        self.assertIsNotNone(account)
        self.assertEqual(account.invoice_amount, order.total_amount)

    def test_approve_order_payment_terms_net_30(self):
        """测试审核订单时的付款条件计算（net_30）"""
        # 创建订单
        order_data = {
            "customer": self.customer,
            "order_date": date.today(),
            "status": "draft",
            "payment_terms": "net_30",
        }
        items_data = [
            {"product": self.product1, "quantity": Decimal("1"), "unit_price": Decimal("100000.00")}
        ]
        order = OrderService.create_order(self.user, order_data, items_data)
        order.calculate_totals()
        order.save()

        # 审核订单
        delivery, account = order.approve_order(self.user, self.warehouse)

        # 验证应收账款的到期日期（30天后）
        expected_due_date = date.today() + timedelta(days=30)
        self.assertEqual(account.due_date, expected_due_date)

    def test_approve_order_payment_terms_net_60(self):
        """测试审核订单时的付款条件计算（net_60）"""
        # 创建订单
        order_data = {
            "customer": self.customer,
            "order_date": date.today(),
            "status": "draft",
            "payment_terms": "net_60",
        }
        items_data = [
            {"product": self.product1, "quantity": Decimal("1"), "unit_price": Decimal("100000.00")}
        ]
        order = OrderService.create_order(self.user, order_data, items_data)
        order.calculate_totals()
        order.save()

        # 审核订单
        delivery, account = order.approve_order(self.user, self.warehouse)

        # 验证应收账款的到期日期（60天后）
        expected_due_date = date.today() + timedelta(days=60)
        self.assertEqual(account.due_date, expected_due_date)

    def test_approve_order_with_customer_contact_info(self):
        """测试审核订单时使用客户联系人信息"""
        # 创建订单（不指定收货人）
        order_data = {"customer": self.customer, "order_date": date.today(), "status": "draft"}
        items_data = [
            {"product": self.product1, "quantity": Decimal("1"), "unit_price": Decimal("100000.00")}
        ]
        order = OrderService.create_order(self.user, order_data, items_data)
        order.calculate_totals()
        order.save()

        # 审核订单
        delivery, account = order.approve_order(self.user, self.warehouse)

        # 验证发货单使用了客户的主联系人信息
        self.assertEqual(delivery.shipping_contact, self.contact.name)
        self.assertEqual(delivery.shipping_phone, self.contact.mobile)


class SalesOrderUnapprovalTestCase(SalesServiceTestCaseBase):
    """SalesOrder撤销审核业务逻辑测试"""

    def test_unapprove_order_basic(self):
        """测试基础撤销审核流程"""
        # 创建并审核订单
        order_data = {"customer": self.customer, "order_date": date.today(), "status": "draft"}
        items_data = [
            {"product": self.product1, "quantity": Decimal("1"), "unit_price": Decimal("100000.00")}
        ]
        order = OrderService.create_order(self.user, order_data, items_data)
        order.calculate_totals()
        order.save()
        delivery, account = order.approve_order(self.user, self.warehouse)

        delivery_id = delivery.id
        account_id = account.id

        # 撤销审核
        order.unapprove_order()

        # 验证订单状态已重置
        order.refresh_from_db()
        self.assertEqual(order.status, "draft")
        self.assertIsNone(order.approved_by)
        self.assertIsNone(order.approved_at)

        # 验证发货单已删除（软删除）
        delivery = Delivery.objects.get(id=delivery_id)
        self.assertTrue(delivery.is_deleted)

        # 验证应收账款已删除（硬删除 - QuerySet.delete()）
        self.assertFalse(CustomerAccount.objects.filter(id=account_id).exists())

    def test_unapprove_order_with_shipped_delivery(self):
        """测试撤销审核时发货单已发货（应该失败）"""
        # 创建并审核订单
        order_data = {"customer": self.customer, "order_date": date.today(), "status": "draft"}
        items_data = [
            {"product": self.product1, "quantity": Decimal("1"), "unit_price": Decimal("100000.00")}
        ]
        order = OrderService.create_order(self.user, order_data, items_data)
        order.calculate_totals()
        order.save()
        delivery, account = order.approve_order(self.user, self.warehouse)

        # 标记发货单为已发货
        delivery.status = "shipped"
        delivery.actual_date = date.today()
        delivery.save()

        # 尝试撤销审核（应该失败）
        with self.assertRaises(ValueError):
            order.unapprove_order()

    def test_unapprove_order_with_paid_account(self):
        """测试撤销审核时应收账款已收款（应该失败）"""
        # 创建并审核订单
        order_data = {"customer": self.customer, "order_date": date.today(), "status": "draft"}
        items_data = [
            {"product": self.product1, "quantity": Decimal("1"), "unit_price": Decimal("100000.00")}
        ]
        order = OrderService.create_order(self.user, order_data, items_data)
        order.calculate_totals()
        order.save()
        delivery, account = order.approve_order(self.user, self.warehouse)

        # 标记应收账款已收款
        account.paid_amount = account.invoice_amount
        account.balance = Decimal("0")
        account.save()

        # 尝试撤销审核（应该失败）
        with self.assertRaises(ValueError):
            order.unapprove_order()
