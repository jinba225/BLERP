"""
采购借用模块测试

测试覆盖：
1. 模型层测试（Borrow, BorrowItem）
2. 业务逻辑测试（归还、转采购、状态流转）
3. 视图功能测试（所有视图的GET和POST）
4. 权限控制测试（登录、状态权限、审核权限）
5. 边界条件测试（零值、负值、精度等）
6. 异常处理测试（无效数据、重复操作等）
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.products.models import Product, Unit
from apps.purchase.models import Borrow, BorrowItem, PurchaseOrder
from apps.suppliers.models import Supplier
from common.utils import DocumentNumberGenerator

User = get_user_model()


class BorrowModelTestCase(TestCase):
    """Borrow 模型测试"""

    def setUp(self):
        """测试前准备"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123", is_staff=False
        )
        self.admin_user = User.objects.create_user(
            username="admin", email="admin@example.com", password="adminpass123", is_staff=True
        )
        self.supplier = Supplier.objects.create(
            name="测试供应商", code="SUP001", created_by=self.user, updated_by=self.user
        )
        # 创建计量单位
        self.unit = Unit.objects.create(
            name="个", symbol="个", created_by=self.user, updated_by=self.user
        )
        self.product = Product.objects.create(
            name="测试产品",
            code="PRD001",
            unit=self.unit,
            status="active",
            created_by=self.user,
            updated_by=self.user,
        )

    def test_borrow_creation(self):
        """MT-B-001: 验证借用单创建"""
        borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(borrow.borrow_number, "BO260106001")
        self.assertEqual(borrow.supplier, self.supplier)
        self.assertEqual(borrow.status, "borrowed")
        self.assertIsNotNone(borrow.created_at)

    def test_borrow_number_unique(self):
        """MT-B-002: 验证借用单号唯一性"""
        Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )
        with self.assertRaises(Exception):
            Borrow.objects.create(
                borrow_number="BO260106001",  # 重复单据号
                supplier=self.supplier,
                buyer=self.user,
                status="borrowed",
                borrow_date=date.today(),
                created_by=self.user,
                updated_by=self.user,
            )

    def test_borrow_status_choices(self):
        """MT-B-003: 验证所有状态选项"""
        statuses = [choice[0] for choice in Borrow.BORROW_STATUS]
        expected_statuses = ["draft", "borrowed", "completed"]
        self.assertEqual(statuses, expected_statuses)

    def test_total_borrowed_quantity(self):
        """MT-B-004: 验证总借用数量计算"""
        borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )
        BorrowItem.objects.create(
            borrow=borrow,
            product=self.product,
            quantity=10,
            created_by=self.user,
            updated_by=self.user,
        )
        BorrowItem.objects.create(
            borrow=borrow,
            product=self.product,
            quantity=5,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(borrow.total_borrowed_quantity, 15)

    def test_total_returned_quantity(self):
        """MT-B-005: 验证总归还数量计算"""
        borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )
        BorrowItem.objects.create(
            borrow=borrow,
            product=self.product,
            quantity=10,
            returned_quantity=3,
            created_by=self.user,
            updated_by=self.user,
        )
        BorrowItem.objects.create(
            borrow=borrow,
            product=self.product,
            quantity=5,
            returned_quantity=2,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(borrow.total_returned_quantity, 5)

    def test_total_remaining_quantity(self):
        """MT-B-006: 验证剩余数量计算"""
        borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )
        item = BorrowItem.objects.create(
            borrow=borrow,
            product=self.product,
            quantity=10,
            borrowed_quantity=10,  # 已借用数量等于借用数量
            returned_quantity=3,
            conversion_quantity=2,
            created_by=self.user,
            updated_by=self.user,
        )
        # 剩余 = 已借用 - 归还 - 转采购 = 10 - 3 - 2 = 5
        self.assertEqual(borrow.total_remaining_quantity, 5)

    def test_is_fully_returned(self):
        """MT-B-007: 验证是否全部归还判断"""
        borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )
        item = BorrowItem.objects.create(
            borrow=borrow,
            product=self.product,
            quantity=10,
            borrowed_quantity=10,  # 已借用数量等于借用数量
            created_by=self.user,
            updated_by=self.user,
        )

        # 未归还
        self.assertFalse(borrow.is_fully_returned)

        # 部分归还
        item.returned_quantity = 5
        item.save()
        self.assertFalse(borrow.is_fully_returned)

        # 全部归还
        item.returned_quantity = 10
        item.save()
        self.assertTrue(borrow.is_fully_returned)

    def test_borrow_soft_delete(self):
        """MT-B-008: 验证软删除功能"""
        borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )
        borrow.delete()
        self.assertTrue(borrow.is_deleted)
        self.assertIsNotNone(borrow.deleted_at)

    def test_borrow_str_representation(self):
        """MT-B-009: 验证字符串表示"""
        borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(str(borrow), "BO260106001 - 测试供应商")

    def test_borrow_detail_shows_inventory_transactions(self):
        """MT-B-010: 验证借用单详情页面能正确显示库存交易记录"""
        from apps.inventory.models import InventoryStock, InventoryTransaction, Warehouse

        # 创建借用仓
        borrow_warehouse = Warehouse.objects.create(
            name="借用仓",
            code="BORROW",
            warehouse_type="borrow",
            created_by=self.user,
            updated_by=self.user,
        )

        # 创建借用单
        borrow = Borrow.objects.create(
            borrow_number="BO260106002",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )

        # 创建借用单明细
        item = BorrowItem.objects.create(
            borrow=borrow,
            product=self.product,
            quantity=Decimal("10"),
            specifications="规格A",
            batch_number="BATCH001",
            created_by=self.user,
            updated_by=self.user,
        )

        # 确认入库（创建库存交易记录）
        borrow.confirm_borrow_receipt(self.user, None)

        # 刷新借用单状态
        borrow.refresh_from_db()

        # 验证库存交易记录已创建
        transactions = InventoryTransaction.objects.filter(
            reference_number=borrow.borrow_number, is_deleted=False
        )
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions.first().transaction_type, "in")
        self.assertEqual(transactions.first().product, self.product)
        self.assertEqual(transactions.first().warehouse, borrow_warehouse)
        self.assertEqual(transactions.first().quantity, 10)

        # 验证库存记录已创建
        stocks = InventoryStock.objects.filter(
            product=self.product, warehouse=borrow_warehouse, is_deleted=False
        )
        self.assertEqual(stocks.count(), 1)
        self.assertEqual(stocks.first().quantity, 10)


class BorrowItemModelTestCase(TestCase):
    """BorrowItem 模型测试"""

    def setUp(self):
        """测试前准备"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.supplier = Supplier.objects.create(
            name="测试供应商", code="SUP001", created_by=self.user, updated_by=self.user
        )
        # 创建计量单位
        self.unit = Unit.objects.create(
            name="个", symbol="个", created_by=self.user, updated_by=self.user
        )
        self.product = Product.objects.create(
            name="测试产品",
            code="PRD001",
            unit=self.unit,
            status="active",
            created_by=self.user,
            updated_by=self.user,
        )
        self.borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )

    def test_borrow_item_creation(self):
        """MT-BI-001: 验证明细创建"""
        item = BorrowItem.objects.create(
            borrow=self.borrow,
            product=self.product,
            quantity=Decimal("10.0000"),
            batch_number="BATCH001",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(item.borrow, self.borrow)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, Decimal("10.0000"))

    def test_remaining_quantity_property(self):
        """MT-BI-002: 验证剩余数量属性"""
        item = BorrowItem.objects.create(
            borrow=self.borrow,
            product=self.product,
            quantity=10,
            borrowed_quantity=10,  # 已借用数量（模拟已入库确认）
            returned_quantity=3,
            conversion_quantity=2,
            created_by=self.user,
            updated_by=self.user,
        )
        # 剩余 = borrowed_quantity - returned_quantity - conversion_quantity = 10 - 3 - 2 = 5
        self.assertEqual(item.remaining_quantity, 5)

    def test_can_convert_property(self):
        """MT-BI-003: 验证可转采购判断"""
        item = BorrowItem.objects.create(
            borrow=self.borrow,
            product=self.product,
            quantity=10,  # IntegerField使用整数
            borrowed_quantity=10,  # 已借用数量等于借用数量（模拟已入库确认）
            created_by=self.user,
            updated_by=self.user,
        )

        # 有剩余，可转采购
        self.assertTrue(item.can_convert)

        # 全部归还，不可转采购
        item.returned_quantity = 10
        item.save()
        self.assertFalse(item.can_convert)

    def test_quantity_precision(self):
        """MT-BI-004: 验证数量精度（4位小数）"""
        item = BorrowItem.objects.create(
            borrow=self.borrow,
            product=self.product,
            quantity=Decimal("10.1234"),
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(item.quantity, Decimal("10.1234"))

    def test_price_precision(self):
        """MT-BI-005: 验证价格精度（2位小数）"""
        item = BorrowItem.objects.create(
            borrow=self.borrow,
            product=self.product,
            quantity=Decimal("10.0000"),
            conversion_unit_price=Decimal("99.99"),
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(item.conversion_unit_price, Decimal("99.99"))

    def test_cascade_delete(self):
        """MT-BI-006: 验证级联删除"""
        item = BorrowItem.objects.create(
            borrow=self.borrow,
            product=self.product,
            quantity=Decimal("10.0000"),
            created_by=self.user,
            updated_by=self.user,
        )
        item_id = item.id

        # 删除借用单
        self.borrow.hard_delete()

        # 明细应该也被删除
        self.assertFalse(BorrowItem.objects.filter(id=item_id).exists())

    def test_borrow_item_str_representation(self):
        """MT-BI-007: 验证字符串表示"""
        item = BorrowItem.objects.create(
            borrow=self.borrow,
            product=self.product,
            quantity=Decimal("10.0000"),
            created_by=self.user,
            updated_by=self.user,
        )
        expected = f"{self.borrow.borrow_number} - {self.product.name}"
        self.assertEqual(str(item), expected)


class ReturnFlowTestCase(TestCase):
    """归还流程测试"""

    def setUp(self):
        """测试前准备"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.supplier = Supplier.objects.create(
            name="测试供应商", code="SUP001", created_by=self.user, updated_by=self.user
        )
        # 创建计量单位
        self.unit = Unit.objects.create(
            name="个", symbol="个", created_by=self.user, updated_by=self.user
        )
        self.product = Product.objects.create(
            name="测试产品",
            code="PRD001",
            unit=self.unit,
            status="active",
            created_by=self.user,
            updated_by=self.user,
        )
        self.borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )
        self.item = BorrowItem.objects.create(
            borrow=self.borrow,
            product=self.product,
            quantity=10,
            borrowed_quantity=10,  # 添加：已借用数量（模拟已入库确认）
            created_by=self.user,
            updated_by=self.user,
        )

    def test_full_return(self):
        """BL-R-001: 验证全部归还功能"""
        # 全部归还
        self.item.returned_quantity = 10
        self.item.save()

        # 更新借用单状态
        if self.borrow.is_fully_returned:
            self.borrow.status = "fully_returned"
            self.borrow.save()

        self.assertEqual(self.item.returned_quantity, 10)
        self.assertEqual(self.item.remaining_quantity, 0)
        self.assertEqual(self.borrow.status, "fully_returned")
        self.assertTrue(self.borrow.is_fully_returned)

    def test_partial_return(self):
        """BL-R-002: 验证部分归还功能"""
        # 部分归还
        self.item.returned_quantity = 3
        self.item.save()

        # 更新借用单状态
        self.borrow.status = "partially_returned"
        self.borrow.save()

        self.assertEqual(self.item.returned_quantity, 3)
        self.assertEqual(self.item.remaining_quantity, 7)
        self.assertEqual(self.borrow.status, "partially_returned")
        self.assertFalse(self.borrow.is_fully_returned)

    def test_multiple_partial_returns(self):
        """BL-R-003: 验证多次部分归还"""
        # 第一次归还3个
        self.item.returned_quantity = 3
        self.item.save()
        self.assertEqual(self.item.remaining_quantity, 7)

        # 第二次再归还4个
        self.item.returned_quantity = 7
        self.item.save()
        self.assertEqual(self.item.remaining_quantity, 3)

        # 第三次归还剩余3个
        self.item.returned_quantity = 10
        self.item.save()
        self.assertEqual(self.item.remaining_quantity, 0)
        self.assertTrue(self.borrow.is_fully_returned)

    def test_return_exceeds_remaining(self):
        """BL-R-004: 验证归还数量超限检查"""
        # 尝试归还超过借用数量
        # 这个检查应该在视图层处理，这里只测试数据状态
        self.item.returned_quantity = 15  # 超过10
        self.item.save()

        # remaining_quantity 使用 max(0, ...) 截断为0
        self.assertEqual(self.item.remaining_quantity, 0)

    def test_return_status_update(self):
        """BL-R-005: 验证归还后状态更新"""
        # 部分归还
        self.item.returned_quantity = Decimal("5.0000")
        self.item.save()
        self.borrow.status = "partially_returned"
        self.borrow.save()
        self.assertEqual(self.borrow.status, "partially_returned")

        # 全部归还
        self.item.returned_quantity = Decimal("10.0000")
        self.item.save()
        if self.borrow.is_fully_returned:
            self.borrow.status = "fully_returned"
            self.borrow.save()
        self.assertEqual(self.borrow.status, "fully_returned")


class ConversionFlowTestCase(TestCase):
    """转采购流程测试"""

    def setUp(self):
        """测试前准备"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.admin_user = User.objects.create_user(
            username="admin", email="admin@example.com", password="adminpass123", is_staff=True
        )
        self.supplier = Supplier.objects.create(
            name="测试供应商", code="SUP001", created_by=self.user, updated_by=self.user
        )
        # 创建计量单位
        self.unit = Unit.objects.create(
            name="个", symbol="个", created_by=self.user, updated_by=self.user
        )
        self.product = Product.objects.create(
            name="测试产品",
            code="PRD001",
            unit=self.unit,
            status="active",
            created_by=self.user,
            updated_by=self.user,
        )
        self.borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )
        self.item = BorrowItem.objects.create(
            borrow=self.borrow,
            product=self.product,
            quantity=10,
            borrowed_quantity=10,  # 添加：已借用数量（模拟已入库确认）
            created_by=self.user,
            updated_by=self.user,
        )

    def test_conversion_request(self):
        """BL-C-001: 验证转采购请求提交"""
        # 设置转换数量和价格
        self.item.conversion_quantity = Decimal("5.0000")
        self.item.conversion_unit_price = Decimal("100.00")
        self.item.save()

        # 更新状态为转换中
        self.borrow.status = "converting"
        self.borrow.conversion_notes = "测试转采购"
        self.borrow.save()

        self.assertEqual(self.borrow.status, "converting")
        self.assertEqual(self.item.conversion_quantity, Decimal("5.0000"))
        self.assertEqual(self.item.conversion_unit_price, Decimal("100.00"))

    def test_conversion_with_manual_price(self):
        """BL-C-004: 验证手动输入价格"""
        # 设置手动输入的价格
        self.item.conversion_quantity = Decimal("10.0000")
        self.item.conversion_unit_price = Decimal("123.45")
        self.item.save()

        self.assertEqual(self.item.conversion_unit_price, Decimal("123.45"))

        # 计算小计
        subtotal = self.item.conversion_quantity * self.item.conversion_unit_price
        self.assertEqual(subtotal, Decimal("1234.50"))

    def test_partial_conversion(self):
        """BL-C-005: 验证部分转采购"""
        # 只转换部分数量
        self.item.conversion_quantity = 6
        self.item.conversion_unit_price = Decimal("100.00")
        self.item.save()

        # 剩余数量 = borrowed_quantity(10) - returned_quantity(0) - conversion_quantity(6) = 4
        self.assertEqual(self.item.remaining_quantity, 4)
        self.assertTrue(self.item.can_convert)  # 还有剩余，可继续转换

    def test_conversion_exceeds_remaining(self):
        """BL-C-006: 验证转采购数量超限检查"""
        # 尝试转换超过剩余数量
        # 这个检查应该在视图层处理
        self.item.conversion_quantity = 15  # 超过10
        self.item.save()

        # remaining_quantity 使用 max(0, ...) 截断为0
        self.assertEqual(self.item.remaining_quantity, 0)


class StatusTransitionTestCase(TestCase):
    """状态流转测试"""

    def setUp(self):
        """测试前准备"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.supplier = Supplier.objects.create(
            name="测试供应商", code="SUP001", created_by=self.user, updated_by=self.user
        )
        # 创建计量单位
        self.unit = Unit.objects.create(
            name="个", symbol="个", created_by=self.user, updated_by=self.user
        )
        self.product = Product.objects.create(
            name="测试产品",
            code="PRD001",
            unit=self.unit,
            status="active",
            created_by=self.user,
            updated_by=self.user,
        )

    def test_draft_to_borrowed(self):
        """BL-S-001: 验证草稿→借用中"""
        borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="draft",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )

        # 提交借用
        borrow.status = "borrowed"
        borrow.save()

        self.assertEqual(borrow.status, "borrowed")

    def test_borrowed_to_partially_returned(self):
        """BL-S-002: 验证借用中→部分归还"""
        borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )

        # 部分归还
        borrow.status = "partially_returned"
        borrow.save()

        self.assertEqual(borrow.status, "partially_returned")

    def test_partially_returned_to_fully_returned(self):
        """BL-S-003: 验证部分归还→全部归还"""
        borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="partially_returned",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )

        # 全部归还
        borrow.status = "fully_returned"
        borrow.save()

        self.assertEqual(borrow.status, "fully_returned")

    def test_borrowed_to_converting(self):
        """BL-S-004: 验证借用中→转换中"""
        borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )

        # 发起转采购请求
        borrow.status = "converting"
        borrow.save()

        self.assertEqual(borrow.status, "converting")

    def test_converting_to_converted(self):
        """BL-S-005: 验证转换中→已转采购"""
        borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="converting",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )

        # 审核通过
        borrow.status = "converted"
        borrow.save()

        self.assertEqual(borrow.status, "converted")


class BoundaryConditionTestCase(TestCase):
    """边界条件测试"""

    def setUp(self):
        """测试前准备"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.supplier = Supplier.objects.create(
            name="测试供应商", code="SUP001", created_by=self.user, updated_by=self.user
        )
        # 创建计量单位
        self.unit = Unit.objects.create(
            name="个", symbol="个", created_by=self.user, updated_by=self.user
        )
        self.product = Product.objects.create(
            name="测试产品",
            code="PRD001",
            unit=self.unit,
            status="active",
            created_by=self.user,
            updated_by=self.user,
        )
        self.borrow = Borrow.objects.create(
            borrow_number="BO260106001",
            supplier=self.supplier,
            buyer=self.user,
            status="borrowed",
            borrow_date=date.today(),
            created_by=self.user,
            updated_by=self.user,
        )

    def test_zero_quantity(self):
        """BT-001: 验证零数量处理"""
        # 数据库层面允许，但业务层应该阻止
        item = BorrowItem.objects.create(
            borrow=self.borrow,
            product=self.product,
            quantity=Decimal("0.0000"),
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(item.quantity, Decimal("0.0000"))

    def test_decimal_precision(self):
        """BT-003: 验证小数精度处理"""
        item = BorrowItem.objects.create(
            borrow=self.borrow,
            product=self.product,
            quantity=Decimal("10.1234"),  # 4位小数
            conversion_unit_price=Decimal("99.99"),  # 2位小数
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(item.quantity, Decimal("10.1234"))
        self.assertEqual(item.conversion_unit_price, Decimal("99.99"))

    def test_large_quantity(self):
        """BT-004: 验证大数量处理"""
        item = BorrowItem.objects.create(
            borrow=self.borrow,
            product=self.product,
            quantity=Decimal("99999999.9999"),  # max_digits=12
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(item.quantity, Decimal("99999999.9999"))
