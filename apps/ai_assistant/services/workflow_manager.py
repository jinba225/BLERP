"""
工作流管理器

负责管理ERP系统中的业务流程，包括审批流程、状态流转等
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()


class WorkflowStatus(Enum):
    """工作流状态"""

    PENDING = "pending"  # 待处理
    IN_PROGRESS = "in_progress"  # 处理中
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    CANCELLED = "cancelled"  # 已取消
    COMPLETED = "completed"  # 已完成


class WorkflowAction(Enum):
    """工作流动作"""

    SUBMIT = "submit"  # 提交
    APPROVE = "approve"  # 批准
    REJECT = "reject"  # 拒绝
    CANCEL = "cancel"  # 取消
    COMPLETE = "complete"  # 完成


@dataclass
class WorkflowStep:
    """工作流步骤"""

    step_id: str
    step_name: str
    required_role: Optional[str] = None
    required_permission: Optional[str] = None
    auto_approve: bool = False  # 是否自动批准


@dataclass
class ExecutionContext:
    """执行上下文"""

    user: User
    action: Any  # WorkflowAction，使用Any避免循环依赖
    entity_type: str
    entity_id: int
    notes: str = ""
    metadata: Dict[str, Any] = None


class WorkflowManager:
    """
    工作流管理器

    负责定义和管理业务流程的审批工作流
    """

    # 定义各种业务类型的工作流
    WORKFLOWS = {
        "sales_order": [
            WorkflowStep("create", "创建订单"),
            WorkflowStep("approve", "审核订单", required_permission="sales.approve_order"),
        ],
        "delivery": [
            WorkflowStep("create", "创建发货单"),
            WorkflowStep("confirm", "确认发货", required_permission="sales.confirm_delivery"),
        ],
        "sales_return": [
            WorkflowStep("request", "申请退货"),
            WorkflowStep("approve", "审核退货", required_permission="sales.approve_return"),
            WorkflowStep("receive", "接收退货", required_permission="sales.receive_return"),
        ],
        "purchase_order": [
            WorkflowStep("create", "创建采购订单"),
            WorkflowStep("approve", "审核订单", required_permission="purchase.approve_order"),
        ],
        "purchase_receipt": [
            WorkflowStep("create", "创建收货单"),
            WorkflowStep("inspect", "质量检验"),
            WorkflowStep("approve", "审核入库", required_permission="purchase.approve_receipt"),
        ],
        "expense": [
            WorkflowStep("submit", "提交报销"),
            WorkflowStep("approve", "审批费用", required_permission="finance.approve_expense"),
            WorkflowStep("pay", "支付", required_permission="finance.payment"),
        ],
        "journal": [
            WorkflowStep("create", "创建凭证"),
            WorkflowStep("approve", "审核凭证", required_permission="finance.approve_journal"),
            WorkflowStep("post", "过账", required_permission="finance.post_journal"),
        ],
        "stock_transfer": [
            WorkflowStep("create", "创建调拨单"),
            WorkflowStep("approve", "审核调拨", required_permission="inventory.approve_transfer"),
            WorkflowStep("ship", "发货", required_permission="inventory.ship_transfer"),
            WorkflowStep("receive", "收货", required_permission="inventory.receive_transfer"),
        ],
    }

    @classmethod
    def get_workflow(cls, entity_type: str) -> List[WorkflowStep]:
        """
        获取指定业务类型的工作流

        Args:
            entity_type: 业务类型（如 "sales_order"）

        Returns:
            工作流步骤列表
        """
        return cls.WORKFLOWS.get(entity_type, [])

    @classmethod
    def get_next_step(cls, entity_type: str, current_step_id: str) -> Optional[WorkflowStep]:
        """
        获取下一步工作流步骤

        Args:
            entity_type: 业务类型
            current_step_id: 当前步骤ID

        Returns:
            下一个步骤，如果没有则返回None
        """
        steps = cls.get_workflow(entity_type)
        for i, step in enumerate(steps):
            if step.step_id == current_step_id:
                if i + 1 < len(steps):
                    return steps[i + 1]
        return None

    @classmethod
    def can_execute_action(
        cls, context: ExecutionContext, workflow_step: WorkflowStep
    ) -> tuple[bool, str]:
        """
        检查用户是否可以执行指定步骤

        Args:
            context: 执行上下文
            workflow_step: 工作流步骤

        Returns:
            (是否可以执行, 错误信息)
        """
        user = context.user

        # 超级用户可以执行任何操作
        if user.is_superuser:
            return True, ""

        # 检查权限
        if workflow_step.required_permission:
            if not user.has_perm(workflow_step.required_permission):
                # 尝试使用自定义权限检查
                try:
                    from ai_assistant.utils.permissions import has_custom_permission

                    if not has_custom_permission(user, workflow_step.required_permission):
                        return False, f"需要权限: {workflow_step.required_permission}"
                except Exception:
                    return False, f"需要权限: {workflow_step.required_permission}"

        # 检查角色
        if workflow_step.required_role:
            # 这里可以根据实际需求实现角色检查逻辑
            pass

        return True, ""

    @classmethod
    def execute_workflow_action(cls, context: ExecutionContext) -> tuple[bool, str, Dict[str, Any]]:
        """
        执行工作流动作

        Args:
            context: 执行上下文

        Returns:
            (是否成功, 消息, 结果数据)
        """
        # 根据实体类型和动作执行相应的业务逻辑
        # 这里提供一个框架，具体实现需要根据业务需求

        entity_type = context.entity_type
        action = context.action

        # 导入相应的模型和服务
        if entity_type == "delivery" and action == WorkflowAction.CONFIRM_SHIPMENT:
            return cls._execute_delivery_shipment(context)
        elif entity_type == "purchase_receipt" and action == WorkflowAction.CONFIRM_RECEIPT:
            return cls._execute_purchase_receipt_confirm(context)
        elif entity_type == "stock_transfer" and action == WorkflowAction.SHIP:
            return cls._execute_transfer_ship(context)
        elif entity_type == "stock_transfer" and action == WorkflowAction.RECEIVE:
            return cls._execute_transfer_receive(context)
        # ... 其他工作流动作

        return False, "不支持的工作流动作", {}

    @classmethod
    def _execute_delivery_shipment(
        cls, context: "ExecutionContext"
    ) -> tuple[bool, str, Dict[str, Any]]:
        """执行发货确认"""
        try:
            from sales.models import Delivery

            delivery = Delivery.objects.get(id=context.entity_id, is_deleted=False)

            # 更新状态
            delivery.status = "shipped"
            if hasattr(delivery, "shipped_at"):
                delivery.shipped_at = timezone.now()
            if hasattr(delivery, "shipped_by"):
                delivery.shipped_by = context.user
            delivery.save()

            # TODO: 扣减库存、创建库存变动记录等

            return (
                True,
                f"发货单 {delivery.delivery_number} 已确认发货",
                {"delivery_number": delivery.delivery_number, "status": delivery.status},
            )
        except Exception as e:
            return False, f"确认发货失败: {str(e)}", {}

    @classmethod
    def _execute_purchase_receipt_confirm(
        cls, context: ExecutionContext
    ) -> tuple[bool, str, Dict[str, Any]]:
        """执行收货确认"""
        try:
            from purchase.models import PurchaseReceipt

            receipt = PurchaseReceipt.objects.get(id=context.entity_id, is_deleted=False)

            # 更新状态
            receipt.status = "received"
            receipt.received_at = timezone.now()
            receipt.received_by = context.user
            receipt.save()

            # TODO: 增加库存、创建库存变动记录等

            return (
                True,
                f"收货单 {receipt.receipt_number} 已确认收货",
                {"receipt_number": receipt.receipt_number, "status": receipt.status},
            )
        except Exception as e:
            return False, f"确认收货失败: {str(e)}", {}

    @classmethod
    def _execute_transfer_ship(cls, context: ExecutionContext) -> tuple[bool, str, Dict[str, Any]]:
        """执行调拨发货"""
        try:
            from inventory.models import StockTransfer
            from inventory.services import InventoryTransaction

            transfer = StockTransfer.objects.get(id=context.entity_id, is_deleted=False)

            # 扣减源仓库库存
            for item in transfer.items.filter(is_deleted=False):
                InventoryTransaction.update_stock(
                    warehouse=transfer.source_warehouse,
                    product=item.product,
                    quantity=-item.quantity,  # 负数表示扣减
                    transaction_type="out",
                    reference_number=transfer.transfer_number,
                )

            # 更新状态
            transfer.status = "shipped"
            transfer.shipped_at = timezone.now()
            transfer.shipped_by = context.user
            transfer.save()

            return (
                True,
                f"调拨单 {transfer.transfer_number} 已发货",
                {"transfer_number": transfer.transfer_number, "status": transfer.status},
            )
        except Exception as e:
            return False, f"调拨发货失败: {str(e)}", {}

    @classmethod
    def _execute_transfer_receive(
        cls, context: ExecutionContext
    ) -> tuple[bool, str, Dict[str, Any]]:
        """执行调拨收货"""
        try:
            from inventory.models import StockTransfer
            from inventory.services import InventoryTransaction

            transfer = StockTransfer.objects.get(id=context.entity_id, is_deleted=False)

            # 增加目标仓库库存
            for item in transfer.items.filter(is_deleted=False):
                InventoryTransaction.update_stock(
                    warehouse=transfer.target_warehouse,
                    product=item.product,
                    quantity=item.quantity,  # 正数表示增加
                    transaction_type="in",
                    reference_number=transfer.transfer_number,
                )

            # 更新状态
            transfer.status = "received"
            transfer.received_at = timezone.now()
            transfer.received_by = context.user
            transfer.save()

            return (
                True,
                f"调拨单 {transfer.transfer_number} 已收货",
                {"transfer_number": transfer.transfer_number, "status": transfer.status},
            )
        except Exception as e:
            return False, f"调拨收货失败: {str(e)}", {}
