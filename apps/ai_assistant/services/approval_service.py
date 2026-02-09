"""
审批服务

负责管理ERP系统中的审批流程，包括审批请求创建、审批执行等
"""

from typing import Any, Dict, List

from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class ApprovalLevel:
    """审批级别"""

    # 根据金额确定审批级别
    LEVELS = {
        1: {"name": "一级审批", "max_amount": 5000, "approvers": ["department_manager"]},
        2: {"name": "二级审批", "max_amount": 20000, "approvers": ["director"]},
        3: {"name": "三级审批", "max_amount": 100000, "approvers": ["vice_president"]},
        4: {"name": "四级审批", "max_amount": float("inf"), "approvers": ["president"]},
    }

    @classmethod
    def get_level_by_amount(cls, amount: float) -> int:
        """
        根据金额确定审批级别

        Args:
            amount: 金额

        Returns:
            审批级别（1-4）
        """
        for level, config in sorted(cls.LEVELS.items()):
            if amount <= config["max_amount"]:
                return level
        return max(cls.LEVELS.keys())

    @classmethod
    def get_approvers(cls, level: int) -> List[str]:
        """
        获取指定级别的审批人角色列表

        Args:
            level: 审批级别

        Returns:
            审批人角色列表
        """
        return cls.LEVELS.get(level, {}).get("approvers", [])


class ApprovalRequest:
    """审批请求（数据类）"""

    def __init__(
        self,
        request_type: str,
        entity_type: str,
        entity_id: int,
        entity_number: str,
        amount: float = 0,
        requester: User = None,
        description: str = "",
        metadata: Dict[str, Any] = None,
    ):
        self.request_type = request_type  # 请求类型（如 "expense_approval"）
        self.entity_type = entity_type  # 实体类型（如 "expense"）
        self.entity_id = entity_id  # 实体ID
        self.entity_number = entity_number  # 实体编号
        self.amount = amount  # 金额
        self.requester = requester  # 申请人
        self.description = description  # 描述
        self.metadata = metadata or {}  # 额外元数据
        self.created_at = timezone.now()

        # 根据金额确定审批级别
        self.approval_level = ApprovalLevel.get_level_by_amount(amount)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_type": self.request_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_number": self.entity_number,
            "amount": self.amount,
            "requester": self.requester.username if self.requester else "",
            "description": self.description,
            "approval_level": self.approval_level,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class ApprovalService:
    """
    审批服务

    负责处理审批请求的创建、审批、拒绝等操作
    """

    @staticmethod
    def create_approval_request(
        request_type: str,
        entity_type: str,
        entity_id: int,
        entity_number: str,
        amount: float = 0,
        requester: User = None,
        description: str = "",
        **kwargs,
    ) -> ApprovalRequest:
        """
        创建审批请求

        Args:
            request_type: 请求类型
            entity_type: 实体类型
            entity_id: 实体ID
            entity_number: 实体编号
            amount: 金额
            requester: 申请人
            description: 描述
            **kwargs: 额外参数

        Returns:
            审批请求对象
        """
        request = ApprovalRequest(
            request_type=request_type,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_number=entity_number,
            amount=amount,
            requester=requester,
            description=description,
            metadata=kwargs,
        )

        # TODO: 将审批请求保存到数据库或发送通知
        # 目前只返回请求对象，实际使用时可以根据需要实现持久化

        return request

    @staticmethod
    def approve_request(
        request: ApprovalRequest, approver: User, notes: str = ""
    ) -> tuple[bool, str, Dict[str, Any]]:
        """
        批准审批请求

        Args:
            request: 审批请求
            approver: 审批人
            notes: 审批备注

        Returns:
            (是否成功, 消息, 结果数据)
        """
        try:
            # 检查审批人权限
            # TODO: 实现权限检查逻辑

            # 根据实体类型执行相应的审批逻辑
            if request.entity_type == "expense":
                return ApprovalService._approve_expense(request, approver, notes)
            elif request.entity_type == "journal":
                return ApprovalService._approve_journal(request, approver, notes)
            elif request.entity_type == "sales_order":
                return ApprovalService._approve_sales_order(request, approver, notes)
            elif request.entity_type == "purchase_order":
                return ApprovalService._approve_purchase_order(request, approver, notes)
            elif request.entity_type == "sales_return":
                return ApprovalService._approve_sales_return(request, approver, notes)
            elif request.entity_type == "purchase_receipt":
                return ApprovalService._approve_purchase_receipt(request, approver, notes)
            else:
                return False, f"不支持的实体类型: {request.entity_type}", {}

        except Exception as e:
            return False, f"批准失败: {str(e)}", {}

    @staticmethod
    def reject_request(
        request: ApprovalRequest, approver: User, reason: str = ""
    ) -> tuple[bool, str, Dict[str, Any]]:
        """
        拒绝审批请求

        Args:
            request: 审批请求
            approver: 审批人
            reason: 拒绝原因

        Returns:
            (是否成功, 消息, 结果数据)
        """
        try:
            # 根据实体类型执行相应的拒绝逻辑
            if request.entity_type == "expense":
                return ApprovalService._reject_expense(request, approver, reason)
            elif request.entity_type == "sales_order":
                return ApprovalService._reject_sales_order(request, approver, reason)
            elif request.entity_type == "purchase_order":
                return ApprovalService._reject_purchase_order(request, approver, reason)
            else:
                # 通用的拒绝逻辑
                return False, f"拒绝实体类型 {request.entity_type} 的审批请求: {reason}", {}

        except Exception as e:
            return False, f"拒绝失败: {str(e)}", {}

    # ========== 具体实体的审批逻辑 ==========

    @staticmethod
    def _approve_expense(
        request: ApprovalRequest, approver: User, notes: str
    ) -> tuple[bool, str, Dict[str, Any]]:
        """批准费用报销"""
        from finance.models import Expense

        expense = Expense.objects.get(id=request.entity_id, is_deleted=False)

        # 检查状态
        if expense.status != "submitted":
            return False, f"费用状态为 {expense.get_status_display()}，不能审批", {}

        # 执行批准
        expense.approve(approved_by_user=approver)

        return (
            True,
            f"费用报销 {expense.expense_number} 已批准",
            {
                "expense_number": expense.expense_number,
                "status": expense.status,
                "amount": float(expense.amount),
            },
        )

    @staticmethod
    def _approve_journal(
        request: ApprovalRequest, approver: User, notes: str
    ) -> tuple[bool, str, Dict[str, Any]]:
        """批准会计凭证"""
        from finance.models import Journal

        journal = Journal.objects.get(id=request.entity_id, is_deleted=False)

        # 检查状态
        if journal.status != "draft":
            return False, f"凭证状态为 {journal.get_status_display()}，不能审批", {}

        # 批准并过账
        journal.status = "posted"
        journal.posted_at = timezone.now()
        journal.posted_by = approver
        journal.notes = f"批准备注: {notes}\n{journal.notes or ''}"
        journal.save()

        return (
            True,
            f"会计凭证 {journal.journal_number} 已审批并过账",
            {
                "journal_number": journal.journal_number,
                "status": journal.status,
            },
        )

    @staticmethod
    def _approve_sales_order(
        request: ApprovalRequest, approver: User, notes: str
    ) -> tuple[bool, str, Dict[str, Any]]:
        """批准销售订单"""
        from sales.models import SalesOrder

        order = SalesOrder.objects.get(id=request.entity_id, is_deleted=False)

        # 检查状态
        if order.status != "pending":
            return False, f"订单状态为 {order.get_status_display()}，不能审批", {}

        # 执行批准
        order.approve_order(approved_by_user=approver)

        return (
            True,
            f"订单 {order.order_number} 已批准",
            {
                "order_number": order.order_number,
                "status": order.status,
            },
        )

    @staticmethod
    def _approve_purchase_order(
        request: ApprovalRequest, approver: User, notes: str
    ) -> tuple[bool, str, Dict[str, Any]]:
        """批准采购订单"""
        from purchase.models import PurchaseOrder

        order = PurchaseOrder.objects.get(id=request.entity_id, is_deleted=False)

        # 检查状态
        if order.status != "pending":
            return False, f"订单状态为 {order.get_status_display()}，不能审批", {}

        # 执行批准
        order.status = "approved"
        order.approved_at = timezone.now()
        order.approved_by = approver
        order.save()

        return (
            True,
            f"采购订单 {order.order_number} 已批准",
            {
                "order_number": order.order_number,
                "status": order.status,
            },
        )

    @staticmethod
    def _approve_sales_return(
        request: ApprovalRequest, approver: User, notes: str
    ) -> tuple[bool, str, Dict[str, Any]]:
        """批准销售退货"""
        from sales.models import SalesReturn

        sales_return = SalesReturn.objects.get(id=request.entity_id, is_deleted=False)

        # 检查状态
        if sales_return.status != "pending":
            return False, f"退货单状态为 {sales_return.get_status_display()}，不能审批", {}

        # 执行批准
        sales_return.status = "approved"
        sales_return.approved_at = timezone.now()
        sales_return.approved_by = approver
        sales_return.save()

        return (
            True,
            f"退货单 {sales_return.return_number} 已批准",
            {
                "return_number": sales_return.return_number,
                "status": sales_return.status,
            },
        )

    @staticmethod
    def _approve_purchase_receipt(
        request: ApprovalRequest, approver: User, notes: str
    ) -> tuple[bool, str, Dict[str, Any]]:
        """批准采购收货"""
        from purchase.models import PurchaseReceipt

        receipt = PurchaseReceipt.objects.get(id=request.entity_id, is_deleted=False)

        # 检查状态
        if receipt.status not in ["pending", "received"]:
            return False, f"收货单状态为 {receipt.get_status_display()}，不能审批", {}

        # 执行批准
        receipt.status = "inspected" if receipt.status == "received" else "approved"
        receipt.approved_at = timezone.now()
        receipt.approved_by = approver
        receipt.notes = f"批准备注: {notes}\n{receipt.notes or ''}"
        receipt.save()

        return (
            True,
            f"收货单 {receipt.receipt_number} 已批准入库",
            {
                "receipt_number": receipt.receipt_number,
                "status": receipt.status,
            },
        )

    # ========== 拒绝逻辑 ==========

    @staticmethod
    def _reject_expense(
        request: ApprovalRequest, approver: User, reason: str
    ) -> tuple[bool, str, Dict[str, Any]]:
        """拒绝费用报销"""
        from finance.models import Expense

        expense = Expense.objects.get(id=request.entity_id, is_deleted=False)

        # 检查状态
        if expense.status != "submitted":
            return False, f"费用状态为 {expense.get_status_display()}，不能拒绝", {}

        # 执行拒绝
        expense.reject(rejected_by_user=approver, reason=reason)

        return (
            True,
            f"费用报销 {expense.expense_number} 已拒绝: {reason}",
            {
                "expense_number": expense.expense_number,
                "status": expense.status,
            },
        )

    @staticmethod
    def _reject_sales_order(
        request: ApprovalRequest, approver: User, reason: str
    ) -> tuple[bool, str, Dict[str, Any]]:
        """拒绝销售订单"""
        from sales.models import SalesOrder

        order = SalesOrder.objects.get(id=request.entity_id, is_deleted=False)

        # 检查状态
        if order.status != "pending":
            return False, f"订单状态为 {order.get_status_display()}，不能拒绝", {}

        # 执行拒绝
        order.status = "cancelled"
        order.cancelled_at = timezone.now()
        order.cancelled_by = approver
        order.cancellation_reason = reason
        order.save()

        return (
            True,
            f"订单 {order.order_number} 已拒绝: {reason}",
            {
                "order_number": order.order_number,
                "status": order.status,
            },
        )

    @staticmethod
    def _reject_purchase_order(
        request: ApprovalRequest, approver: User, reason: str
    ) -> tuple[bool, str, Dict[str, Any]]:
        """拒绝采购订单"""
        from purchase.models import PurchaseOrder

        order = PurchaseOrder.objects.get(id=request.entity_id, is_deleted=False)

        # 检查状态
        if order.status != "pending":
            return False, f"订单状态为 {order.get_status_display()}，不能拒绝", {}

        # 执行拒绝
        order.status = "cancelled"
        order.cancelled_at = timezone.now()
        order.cancelled_by = approver
        order.cancellation_reason = reason
        order.save()

        return (
            True,
            f"采购订单 {order.order_number} 已拒绝: {reason}",
            {
                "order_number": order.order_number,
                "status": order.status,
            },
        )
