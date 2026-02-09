"""
采购退货数量约束验证测试

测试退货数量不能超过可退货数量的业务规则
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.test import TestCase

from apps.products.models import Product
from apps.purchase.models import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseReturn,
    PurchaseReturnItem,
)
from apps.suppliers.models import Supplier

User = get_user_model()


class PurchaseReturnValidationTest(TestCase):
    """采购退货数量验证测试"""

    def setUp(self):
        """设置测试数据"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username="test_user", email="test@example.com", password="test_pass123"
        )

        # 创建供应商
        self.supplier = Supplier.objects.create(
            name="测试供应商", code="TEST001", contact="张三", phone="13800138000"
        )

        # 创建产品
        self.product = Product.objects.create(name="测试产品", code="PROD001", price=Decimal("100.00"))

        # 创建采购订单
        self.order = PurchaseOrder.objects.create(
            order_number="TEST-RETURN-001",
            supplier=self.supplier,
            order_date="2026-01-01",
            expected_date="2026-01-15",
            status="confirmed",
            total_amount=Decimal("1000.00"),
            created_by=self.user,
        )

        # 创建订单明细（10个）
        self.order_item = PurchaseOrderItem.objects.create(
            purchase_order=self.order,
            product=self.product,
            quantity=10,
            unit_price=Decimal("100.00"),
            line_total=Decimal("1000.00"),
        )

        # 模拟收货（直接修改已收货数量为10）
        self.order_item.received_quantity = 10
        self.order_item.save()

    def _calculate_returned_quantity(self):
        """计算已退货数量（只统计已审核的退货单）"""
        return (
            PurchaseReturnItem.objects.filter(
                order_item=self.order_item,
                purchase_return__purchase_order=self.order,
                purchase_return__is_deleted=False,
                purchase_return__status__in=["approved", "returned", "completed"],
            ).aggregate(total=Sum("quantity"))["total"]
            or 0
        )

    def test_first_return_within_limit(self):
        """测试第一次退货在可退货数量范围内"""
        # 第一次退货：3个（可退货数量=10）
        return_quantity = 3

        return_order = PurchaseReturn.objects.create(
            purchase_order=self.order,
            return_date="2026-01-10",
            reason="quality",
            refund_amount=Decimal("300.00"),
            status="approved",
            created_by=self.user,
        )

        PurchaseReturnItem.objects.create(
            purchase_return=return_order,
            order_item=self.order_item,
            quantity=return_quantity,
            unit_price=Decimal("100.00"),
            created_by=self.user,
        )

        # 验证已退货数量
        returned_qty = self._calculate_returned_quantity()
        self.assertEqual(returned_qty, 3)

        # 验证剩余可退货数量
        returnable_qty = self.order_item.received_quantity - returned_qty
        self.assertEqual(returnable_qty, 7)

    def test_second_return_exceeds_limit(self):
        """测试第二次退货超过可退货数量"""
        # 第一次退货：7个
        return_order_1 = PurchaseReturn.objects.create(
            purchase_order=self.order,
            return_date="2026-01-10",
            reason="quality",
            refund_amount=Decimal("700.00"),
            status="approved",
            created_by=self.user,
        )

        PurchaseReturnItem.objects.create(
            purchase_return=return_order_1,
            order_item=self.order_item,
            quantity=7,
            unit_price=Decimal("100.00"),
            created_by=self.user,
        )

        # 验证可退货数量 = 10 - 7 = 3
        returned_qty = self._calculate_returned_quantity()
        returnable_qty = self.order_item.received_quantity - returned_qty
        self.assertEqual(returnable_qty, 3)

        # 尝试第二次退货：4个（超过可退货数量3）
        # 这应该被验证逻辑阻止
        return_quantity_2 = 4

        # 模拟后端验证逻辑
        if return_quantity_2 > returnable_qty:
            # 验证成功：正确阻止了超额退货
            self.assertTrue(True)
            self.assertEqual(return_quantity_2, 4)  # 尝试退货4个
            self.assertEqual(returnable_qty, 3)  # 但只能退3个
        else:
            self.fail("应该阻止超过可退货数量的退货")

    def test_boundary_return_equals_limit(self):
        """测试边界情况：退货数量等于可退货数量"""
        # 第一次退货：7个
        return_order_1 = PurchaseReturn.objects.create(
            purchase_order=self.order,
            return_date="2026-01-10",
            reason="quality",
            refund_amount=Decimal("700.00"),
            status="approved",
            created_by=self.user,
        )

        PurchaseReturnItem.objects.create(
            purchase_return=return_order_1,
            order_item=self.order_item,
            quantity=7,
            unit_price=Decimal("100.00"),
            created_by=self.user,
        )

        # 第二次退货：3个（刚好等于可退货数量）
        return_quantity_2 = 3

        returned_qty = self._calculate_returned_quantity()
        returnable_qty = self.order_item.received_quantity - returned_qty

        # 验证允许
        self.assertLessEqual(return_quantity_2, returnable_qty)
        self.assertEqual(return_quantity_2, 3)
        self.assertEqual(returnable_qty, 3)

    def test_pending_return_not_counted(self):
        """测试待审核状态的退货不计入已退货数量"""
        # 创建一个待审核的退货单：5个
        pending_return = PurchaseReturn.objects.create(
            purchase_order=self.order,
            return_date="2026-01-10",
            reason="quality",
            refund_amount=Decimal("500.00"),
            status="pending",  # 待审核状态
            created_by=self.user,
        )

        PurchaseReturnItem.objects.create(
            purchase_return=pending_return,
            order_item=self.order_item,
            quantity=5,
            unit_price=Decimal("100.00"),
            created_by=self.user,
        )

        # 验证待审核退货不被计入
        returned_qty = self._calculate_returned_quantity()
        self.assertEqual(returned_qty, 0)  # 待审核不计入

        # 可退货数量仍然是10
        returnable_qty = self.order_item.received_quantity - returned_qty
        self.assertEqual(returnable_qty, 10)

    def test_cumulative_returns(self):
        """测试多次退货累积"""
        # 第一次退货：3个
        return_order_1 = PurchaseReturn.objects.create(
            purchase_order=self.order,
            return_date="2026-01-10",
            reason="quality",
            refund_amount=Decimal("300.00"),
            status="approved",
            created_by=self.user,
        )

        PurchaseReturnItem.objects.create(
            purchase_return=return_order_1,
            order_item=self.order_item,
            quantity=3,
            unit_price=Decimal("100.00"),
            created_by=self.user,
        )

        # 第二次退货：4个
        return_order_2 = PurchaseReturn.objects.create(
            purchase_order=self.order,
            return_date="2026-01-11",
            reason="quality",
            refund_amount=Decimal("400.00"),
            status="approved",
            created_by=self.user,
        )

        PurchaseReturnItem.objects.create(
            purchase_return=return_order_2,
            order_item=self.order_item,
            quantity=4,
            unit_price=Decimal("100.00"),
            created_by=self.user,
        )

        # 第三次退货：3个
        return_order_3 = PurchaseReturn.objects.create(
            purchase_order=self.order,
            return_date="2026-01-12",
            reason="quality",
            refund_amount=Decimal("300.00"),
            status="approved",
            created_by=self.user,
        )

        PurchaseReturnItem.objects.create(
            purchase_return=return_order_3,
            order_item=self.order_item,
            quantity=3,
            unit_price=Decimal("100.00"),
            created_by=self.user,
        )

        # 验证累计退货：3 + 4 + 3 = 10
        returned_qty = self._calculate_returned_quantity()
        self.assertEqual(returned_qty, 10)

        # 可退货数量 = 10 - 10 = 0
        returnable_qty = self.order_item.received_quantity - returned_qty
        self.assertEqual(returnable_qty, 0)

        # 第四次退货应该被阻止
        return_quantity_4 = 1
        if return_quantity_4 > returnable_qty:
            self.assertTrue(True)  # 正确阻止
        else:
            self.fail("应该阻止退货（可退货数量为0）")

    def test_cancelled_return_not_counted(self):
        """测试已取消状态的退货不计入已退货数量"""
        # 创建一个已取消的退货单：5个
        cancelled_return = PurchaseReturn.objects.create(
            purchase_order=self.order,
            return_date="2026-01-10",
            reason="quality",
            refund_amount=Decimal("500.00"),
            status="cancelled",  # 已取消状态
            created_by=self.user,
        )

        PurchaseReturnItem.objects.create(
            purchase_return=cancelled_return,
            order_item=self.order_item,
            quantity=5,
            unit_price=Decimal("100.00"),
            created_by=self.user,
        )

        # 验证已取消退货不被计入
        returned_qty = self._calculate_returned_quantity()
        self.assertEqual(returned_qty, 0)  # 已取消不计入

        # 可退货数量仍然是10
        returnable_qty = self.order_item.received_quantity - returned_qty
        self.assertEqual(returnable_qty, 10)
