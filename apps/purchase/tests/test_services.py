"""
Purchase模块 - 服务层测试
测试PurchaseOrderService, PurchaseRequestService业务逻辑
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from purchase.services import PurchaseOrderService, PurchaseRequestService

from apps.departments.models import Department
from apps.inventory.models import Warehouse
from apps.products.models import Brand, Product, ProductCategory, Unit
from apps.suppliers.models import Supplier, SupplierCategory

User = get_user_model()


class PurchaseServiceTestCaseBase(TestCase):
    """Purchase服务测试基类 - 准备测试数据"""

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
        self.department = Department.objects.create(
            name="采购部", code="PURCHASE", created_by=self.user
        )
        self.user.department = self.department
        self.user.save()

        # 创建供应商分类
        self.supplier_category = SupplierCategory.objects.create(
            name="原材料供应商", code="RAW", created_by=self.user
        )

        # 创建测试供应商
        self.supplier = Supplier.objects.create(
            name="测试供应商A公司",
            code="SUP001",
            level="A",
            category=self.supplier_category,
            address="上海市浦东新区测试路456号",
            city="上海",
            province="上海市",
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
            name="激光镜片",
            code="PRD001",
            specifications="高精度激光镜片",
            category=self.product_category,
            brand=self.brand,
            unit=self.unit,
            cost_price=Decimal("5000.00"),
            selling_price=Decimal("8000.00"),
            status="active",
            created_by=self.user,
        )

        self.product2 = Product.objects.create(
            name="激光管",
            code="PRD002",
            specifications="CO2激光管",
            category=self.product_category,
            brand=self.brand,
            unit=self.unit,
            cost_price=Decimal("3000.00"),
            selling_price=Decimal("5000.00"),
            status="active",
            created_by=self.user,
        )

        # 创建仓库
        self.warehouse = Warehouse.objects.create(name="原料仓库", code="WH001", created_by=self.user)


class PurchaseOrderServiceTestCase(PurchaseServiceTestCaseBase):
    """PurchaseOrderService服务测试"""

    def test_create_order_basic(self):
        """测试创建基础采购订单"""
        order_data = {
            "supplier": self.supplier,
            "order_date": date.today(),
            "status": "draft",
            "warehouse": self.warehouse,
        }

        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("10"),
                "unit_price": Decimal("5000.00"),
            },
            {
                "product": self.product2,
                "quantity": Decimal("5"),
                "unit_price": Decimal("3000.00"),
            },
        ]

        order = PurchaseOrderService.create_order(self.user, order_data, items_data)

        # 验证订单创建成功
        self.assertIsNotNone(order.id)
        self.assertEqual(order.supplier, self.supplier)
        self.assertEqual(order.status, "draft")
        self.assertEqual(order.created_by, self.user)

        # 验证单据号自动生成
        self.assertIsNotNone(order.order_number)
        self.assertTrue(order.order_number.startswith("PO"))

        # 验证订单明细
        self.assertEqual(order.items.count(), 2)

        # 验证sort_order
        items = list(order.items.order_by("sort_order"))
        self.assertEqual(items[0].sort_order, 0)
        self.assertEqual(items[1].sort_order, 1)

        # 验证总额自动计算
        self.assertGreater(order.total_amount, Decimal("0"))

    def test_create_order_with_custom_number(self):
        """测试创建采购订单时指定单据号"""
        order_data = {
            "supplier": self.supplier,
            "order_number": "PO_CUSTOM_001",  # 指定单据号
            "order_date": date.today(),
            "status": "draft",
            "warehouse": self.warehouse,
        }

        items_data = [
            {"product": self.product1, "quantity": Decimal("1"), "unit_price": Decimal("5000.00")},
        ]

        order = PurchaseOrderService.create_order(self.user, order_data, items_data)

        # 验证使用了指定的单据号
        self.assertEqual(order.order_number, "PO_CUSTOM_001")

    def test_create_order_filter_empty_items(self):
        """测试创建订单时过滤空明细"""
        order_data = {
            "supplier": self.supplier,
            "order_date": date.today(),
            "status": "draft",
            "warehouse": self.warehouse,
        }

        items_data = [
            {"product": self.product1, "quantity": Decimal("1"), "unit_price": Decimal("5000.00")},
            {},  # 空明细
            {"product_id": None},  # 空product_id
            {"product": self.product2, "quantity": Decimal("2"), "unit_price": Decimal("3000.00")},
        ]

        order = PurchaseOrderService.create_order(self.user, order_data, items_data)

        # 验证只创建了有效明细
        self.assertEqual(order.items.count(), 2)

    def test_update_order_basic(self):
        """测试更新采购订单"""
        # 创建订单
        order_data = {
            "supplier": self.supplier,
            "order_date": date.today(),
            "status": "draft",
            "warehouse": self.warehouse,
        }
        items_data = [
            {"product": self.product1, "quantity": Decimal("1"), "unit_price": Decimal("5000.00")}
        ]
        order = PurchaseOrderService.create_order(self.user, order_data, items_data)
        original_number = order.order_number

        # 更新订单
        update_data = {"status": "approved", "notes": "已审核订单"}
        new_items_data = [
            {"product": self.product1, "quantity": Decimal("2"), "unit_price": Decimal("4800.00")},
            {"product": self.product2, "quantity": Decimal("3"), "unit_price": Decimal("3000.00")},
        ]

        updated_order = PurchaseOrderService.update_order(
            order, self.user, update_data, new_items_data
        )

        # 验证更新成功
        self.assertEqual(updated_order.id, order.id)
        self.assertEqual(updated_order.order_number, original_number)
        self.assertEqual(updated_order.status, "approved")
        self.assertEqual(updated_order.updated_by, self.user)

        # 验证明细已更新
        self.assertEqual(updated_order.items.count(), 2)

    def test_update_order_keep_items_when_none(self):
        """测试更新订单但不修改明细"""
        # 创建订单
        order_data = {
            "supplier": self.supplier,
            "order_date": date.today(),
            "status": "draft",
            "warehouse": self.warehouse,
        }
        items_data = [
            {"product": self.product1, "quantity": Decimal("1"), "unit_price": Decimal("5000.00")}
        ]
        order = PurchaseOrderService.create_order(self.user, order_data, items_data)
        original_item_count = order.items.count()

        # 更新订单，但items_data=None（不修改明细）
        update_data = {"status": "approved"}
        updated_order = PurchaseOrderService.update_order(
            order, self.user, update_data, items_data=None
        )

        # 验证明细未被删除
        self.assertEqual(updated_order.items.count(), original_item_count)
        self.assertEqual(updated_order.status, "approved")


class PurchaseRequestServiceTestCase(PurchaseServiceTestCaseBase):
    """PurchaseRequestService服务测试"""

    def test_create_request_basic(self):
        """测试创建基础采购申请"""
        request_data = {
            "requester": self.user,
            "department": self.department,
            "request_date": date.today(),
            "required_date": date.today() + timedelta(days=15),
            "purpose": "生产需要",
            "status": "draft",
        }

        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("10"),
                "estimated_price": Decimal("5000.00"),
            },
            {
                "product": self.product2,
                "quantity": Decimal("5"),
                "estimated_price": Decimal("3000.00"),
            },
        ]

        request = PurchaseRequestService.create_request(self.user, request_data, items_data)

        # 验证申请创建成功
        self.assertIsNotNone(request.id)
        self.assertEqual(request.requester, self.user)
        self.assertEqual(request.department, self.department)
        self.assertEqual(request.status, "draft")
        self.assertEqual(request.created_by, self.user)

        # 验证单据号自动生成
        self.assertIsNotNone(request.request_number)

        # 验证申请明细
        self.assertEqual(request.items.count(), 2)

        # 验证预估总额自动计算
        self.assertGreater(request.estimated_total, Decimal("0"))

    def test_update_request_basic(self):
        """测试更新采购申请"""
        # 创建申请
        request_data = {
            "requester": self.user,
            "department": self.department,
            "request_date": date.today(),
            "required_date": date.today() + timedelta(days=15),
            "purpose": "生产需要",
            "status": "draft",
        }
        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("1"),
                "estimated_price": Decimal("5000.00"),
            }
        ]
        request = PurchaseRequestService.create_request(self.user, request_data, items_data)
        original_number = request.request_number

        # 更新申请
        update_data = {"status": "submitted", "notes": "已提交审批"}
        new_items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("2"),
                "estimated_price": Decimal("5000.00"),
            },
            {
                "product": self.product2,
                "quantity": Decimal("3"),
                "estimated_price": Decimal("3000.00"),
            },
        ]

        updated_request = PurchaseRequestService.update_request(
            request, self.user, update_data, new_items_data
        )

        # 验证更新成功
        self.assertEqual(updated_request.id, request.id)
        self.assertEqual(updated_request.request_number, original_number)
        self.assertEqual(updated_request.status, "submitted")
        self.assertEqual(updated_request.updated_by, self.user)

        # 验证明细已更新
        self.assertEqual(updated_request.items.count(), 2)

        # 验证预估总额已更新
        expected_total = Decimal("2") * Decimal("5000.00") + Decimal("3") * Decimal("3000.00")
        self.assertEqual(updated_request.estimated_total, expected_total)

    def test_convert_request_to_order_basic(self):
        """测试采购申请转采购订单"""
        # 创建采购申请
        request_data = {
            "requester": self.user,
            "department": self.department,
            "request_date": date.today(),
            "required_date": date.today() + timedelta(days=15),
            "purpose": "生产需要",
            "status": "approved",
        }
        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("10"),
                "estimated_price": Decimal("5000.00"),
            },
            {
                "product": self.product2,
                "quantity": Decimal("5"),
                "estimated_price": Decimal("3000.00"),
            },
        ]
        request = PurchaseRequestService.create_request(self.user, request_data, items_data)

        # 转换为采购订单
        order = PurchaseRequestService.convert_request_to_order(
            request, self.user, self.supplier.id, self.warehouse.id
        )

        # 验证订单创建成功
        self.assertIsNotNone(order.id)
        self.assertEqual(order.supplier, self.supplier)
        self.assertEqual(order.warehouse, self.warehouse)
        self.assertEqual(order.buyer, self.user)
        self.assertEqual(order.status, "draft")

        # 验证订单明细数量与申请一致
        self.assertEqual(order.items.count(), request.items.count())

        # 验证订单号自动生成
        self.assertTrue(order.order_number.startswith("PO"))
        self.assertNotEqual(order.order_number, request.request_number)

        # 验证申请状态已更新
        request.refresh_from_db()
        self.assertEqual(request.status, "ordered")
        self.assertEqual(request.converted_order, order)

        # 验证订单关联了申请单号
        self.assertEqual(order.reference_number, request.request_number)

    def test_convert_request_to_order_with_notes(self):
        """测试采购申请转订单时生成详细备注"""
        # 创建采购申请
        request_data = {
            "requester": self.user,
            "department": self.department,
            "request_date": date.today(),
            "required_date": date.today() + timedelta(days=15),
            "purpose": "紧急生产需要",
            "status": "approved",
        }
        items_data = [
            {
                "product": self.product1,
                "quantity": Decimal("1"),
                "estimated_price": Decimal("5000.00"),
            }
        ]
        request = PurchaseRequestService.create_request(self.user, request_data, items_data)

        # 转换为订单
        order = PurchaseRequestService.convert_request_to_order(
            request, self.user, self.supplier.id, self.warehouse.id
        )

        # 验证订单备注包含申请信息
        self.assertIn(request.request_number, order.notes)
        self.assertIn(request.department.name, order.internal_notes)
        self.assertIn(request.purpose, order.internal_notes)
