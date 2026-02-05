"""
审核和状态变更工具

提供业务流程的审核和状态变更功能
"""

from typing import Dict, Any
from .base_tool import BaseTool, ToolResult
from ..services.approval_service import ApprovalService, ApprovalRequest
from ..services.workflow_manager import WorkflowManager, WorkflowAction


class ApproveDeliveryTool(BaseTool):
    """审核发货单工具"""

    name = "approve_delivery"
    display_name = "审核发货单"
    description = "审核发货单（已通过创建流程，此工具用于最终确认）"
    category = "sales"
    risk_level = "high"
    require_permission = "sales.approve_delivery"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "delivery_id": {
                    "type": "integer",
                    "description": "发货单ID"
                },
                "notes": {
                    "type": "string",
                    "description": "审核备注"
                }
            },
            "required": ["delivery_id"]
        }

    def execute(self, delivery_id: int, notes: str = "", **kwargs) -> ToolResult:
        """执行审核"""
        try:
            from sales.models import Delivery

            delivery = Delivery.objects.get(id=delivery_id, is_deleted=False)

            # 创建审批请求并批准
            request = ApprovalRequest(
                request_type="delivery_approval",
                entity_type="delivery",
                entity_id=delivery.id,
                entity_number=delivery.delivery_number,
                requester=self.user,
                description=f"审核发货单 {delivery.delivery_number}"
            )

            success, message, data = ApprovalService.approve_request(request, self.user, notes)

            if success:
                return ToolResult(success=True, data=data, message=message)
            else:
                return ToolResult(success=False, error=message)

        except Exception as e:
            return ToolResult(success=False, error=f"审核发货单失败: {str(e)}")


class ApproveSalesReturnTool(BaseTool):
    """审核退货单工具"""

    name = "approve_sales_return"
    display_name = "审核退货单"
    description = "审核销售退货单申请"
    category = "sales"
    risk_level = "high"
    require_permission = "sales.approve_return"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "return_id": {
                    "type": "integer",
                    "description": "退货单ID"
                },
                "notes": {
                    "type": "string",
                    "description": "审核备注"
                }
            },
            "required": ["return_id"]
        }

    def execute(self, return_id: int, notes: str = "", **kwargs) -> ToolResult:
        """执行审核"""
        try:
            from sales.models import SalesReturn

            sales_return = SalesReturn.objects.get(id=return_id, is_deleted=False)

            # 创建审批请求并批准
            request = ApprovalRequest(
                request_type="sales_return_approval",
                entity_type="sales_return",
                entity_id=sales_return.id,
                entity_number=sales_return.return_number,
                amount=float(sales_return.refund_amount) if sales_return.refund_amount else 0,
                requester=self.user,
                description=f"审核退货单 {sales_return.return_number}"
            )

            success, message, data = ApprovalService.approve_request(request, self.user, notes)

            if success:
                return ToolResult(success=True, data=data, message=message)
            else:
                return ToolResult(success=False, error=message)

        except Exception as e:
            return ToolResult(success=False, error=f"审核退货单失败: {str(e)}")


class ConfirmShipmentTool(BaseTool):
    """确认发货工具"""

    name = "confirm_shipment"
    display_name = "确认发货"
    description = "确认发货单发货，扣减库存"
    category = "sales"
    risk_level = "high"
    require_permission = "sales.confirm_delivery"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "delivery_id": {
                    "type": "integer",
                    "description": "发货单ID"
                },
                "tracking_number": {
                    "type": "string",
                    "description": "快递单号"
                },
                "notes": {
                    "type": "string",
                    "description": "备注"
                }
            },
            "required": ["delivery_id"]
        }

    def execute(self, delivery_id: int, tracking_number: str = "", notes: str = "", **kwargs) -> ToolResult:
        """执行确认发货"""
        try:
            from sales.models import Delivery

            delivery = Delivery.objects.get(id=delivery_id, is_deleted=False)

            # 更新快递单号
            if tracking_number:
                delivery.tracking_number = tracking_number

            # 使用工作流管理器执行发货
            context = WorkflowManager.ExecutionContext(
                user=self.user,
                action=WorkflowAction.COMPLETE,
                entity_type="delivery",
                entity_id=delivery.id,
                notes=notes
            )

            success, message, data = WorkflowManager.execute_workflow_action(context)

            if success:
                return ToolResult(success=True, data=data, message=message)
            else:
                return ToolResult(success=False, error=message)

        except Exception as e:
            return ToolResult(success=False, error=f"确认发货失败: {str(e)}")


class ApprovePurchaseReceiptTool(BaseTool):
    """审核收货单工具"""

    name = "approve_purchase_receipt"
    display_name = "审核收货单"
    description = "审核采购收货单，确认入库"
    category = "purchase"
    risk_level = "high"
    require_permission = "purchase.approve_receipt"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "receipt_id": {
                    "type": "integer",
                    "description": "收货单ID"
                },
                "notes": {
                    "type": "string",
                    "description": "审核备注"
                }
            },
            "required": ["receipt_id"]
        }

    def execute(self, receipt_id: int, notes: str = "", **kwargs) -> ToolResult:
        """执行审核"""
        try:
            from purchase.models import PurchaseReceipt

            receipt = PurchaseReceipt.objects.get(id=receipt_id, is_deleted=False)

            # 创建审批请求并批准
            request = ApprovalRequest(
                request_type="purchase_receipt_approval",
                entity_type="purchase_receipt",
                entity_id=receipt.id,
                entity_number=receipt.receipt_number,
                requester=self.user,
                description=f"审核收货单 {receipt.receipt_number}"
            )

            success, message, data = ApprovalService.approve_request(request, self.user, notes)

            if success:
                return ToolResult(success=True, data=data, message=message)
            else:
                return ToolResult(success=False, error=message)

        except Exception as e:
            return ToolResult(success=False, error=f"审核收货单失败: {str(e)}")


class ConfirmReceiptTool(BaseTool):
    """确认收货工具"""

    name = "confirm_receipt"
    display_name = "确认收货"
    description = "确认收货单收货，增加库存"
    category = "purchase"
    risk_level = "high"
    require_permission = "purchase.confirm_receipt"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "receipt_id": {
                    "type": "integer",
                    "description": "收货单ID"
                },
                "notes": {
                    "type": "string",
                    "description": "备注"
                }
            },
            "required": ["receipt_id"]
        }

    def execute(self, receipt_id: int, notes: str = "", **kwargs) -> ToolResult:
        """执行确认收货"""
        try:
            from purchase.models import PurchaseReceipt

            receipt = PurchaseReceipt.objects.get(id=receipt_id, is_deleted=False)

            # 使用工作流管理器执行收货确认
            context = WorkflowManager.ExecutionContext(
                user=self.user,
                action=WorkflowAction.COMPLETE,
                entity_type="purchase_receipt",
                entity_id=receipt.id,
                notes=notes
            )

            success, message, data = WorkflowManager.execute_workflow_action(context)

            if success:
                return ToolResult(success=True, data=data, message=message)
            else:
                return ToolResult(success=False, error=message)

        except Exception as e:
            return ToolResult(success=False, error=f"确认收货失败: {str(e)}")


class ApproveExpenseTool(BaseTool):
    """审批费用工具"""

    name = "approve_expense"
    display_name = "审批费用报销"
    description = "审批费用报销申请"
    category = "finance"
    risk_level = "high"
    require_permission = "finance.approve_expense"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expense_id": {
                    "type": "integer",
                    "description": "费用报销单ID"
                },
                "notes": {
                    "type": "string",
                    "description": "审批备注"
                }
            },
            "required": ["expense_id"]
        }

    def execute(self, expense_id: int, notes: str = "", **kwargs) -> ToolResult:
        """执行审批"""
        try:
            from finance.models import Expense

            expense = Expense.objects.get(id=expense_id, is_deleted=False)

            # 创建审批请求并批准
            request = ApprovalRequest(
                request_type="expense_approval",
                entity_type="expense",
                entity_id=expense.id,
                entity_number=expense.expense_number,
                amount=float(expense.amount) if expense.amount else 0,
                requester=self.user,
                description=f"审批费用报销 {expense.expense_number}"
            )

            success, message, data = ApprovalService.approve_request(request, self.user, notes)

            if success:
                return ToolResult(success=True, data=data, message=message)
            else:
                return ToolResult(success=False, error=message)

        except Exception as e:
            return ToolResult(success=False, error=f"审批费用报销失败: {str(e)}")


class ApproveJournalTool(BaseTool):
    """审核会计凭证工具"""

    name = "approve_journal"
    display_name = "审核会计凭证"
    description = "审核会计凭证并过账"
    category = "finance"
    risk_level = "high"
    require_permission = "finance.approve_journal"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "journal_id": {
                    "type": "integer",
                    "description": "会计凭证ID"
                },
                "notes": {
                    "type": "string",
                    "description": "审核备注"
                }
            },
            "required": ["journal_id"]
        }

    def execute(self, journal_id: int, notes: str = "", **kwargs) -> ToolResult:
        """执行审核"""
        try:
            from finance.models import Journal

            journal = Journal.objects.get(id=journal_id, is_deleted=False)

            # 创建审批请求并批准
            request = ApprovalRequest(
                request_type="journal_approval",
                entity_type="journal",
                entity_id=journal.id,
                entity_number=journal.journal_number,
                requester=self.user,
                description=f"审核会计凭证 {journal.journal_number}"
            )

            success, message, data = ApprovalService.approve_request(request, self.user, notes)

            if success:
                return ToolResult(success=True, data=data, message=message)
            else:
                return ToolResult(success=False, error=message)

        except Exception as e:
            return ToolResult(success=False, error=f"审核会计凭证失败: {str(e)}")


class ShipTransferTool(BaseTool):
    """调拨发货工具"""

    name = "ship_transfer"
    display_name = "调拨发货"
    description = "执行库存调拨发货，扣减源仓库库存"
    category = "inventory"
    risk_level = "high"
    require_permission = "inventory.ship_transfer"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "transfer_id": {
                    "type": "integer",
                    "description": "调拨单ID"
                },
                "notes": {
                    "type": "string",
                    "description": "备注"
                }
            },
            "required": ["transfer_id"]
        }

    def execute(self, transfer_id: int, notes: str = "", **kwargs) -> ToolResult:
        """执行调拨发货"""
        try:
            from inventory.models import StockTransfer

            transfer = StockTransfer.objects.get(id=transfer_id, is_deleted=False)

            if transfer.status != 'pending':
                return ToolResult(
                    success=False,
                    error=f"调拨单状态为 {transfer.get_status_display()}，不能发货"
                )

            # 使用工作流管理器执行发货
            from ..services.workflow_manager import ExecutionContext
            context = ExecutionContext(
                user=self.user,
                action=WorkflowAction.COMPLETE,
                entity_type="stock_transfer",
                entity_id=transfer.id,
                notes=notes
            )

            success, message, data = WorkflowManager.execute_workflow_action(context)

            if success:
                return ToolResult(success=True, data=data, message=message)
            else:
                return ToolResult(success=False, error=message)

        except Exception as e:
            return ToolResult(success=False, error=f"调拨发货失败: {str(e)}")


class ReceiveTransferTool(BaseTool):
    """调拨收货工具"""

    name = "receive_transfer"
    display_name = "调拨收货"
    description = "执行库存调拨收货，增加目标仓库库存"
    category = "inventory"
    risk_level = "high"
    require_permission = "inventory.receive_transfer"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "transfer_id": {
                    "type": "integer",
                    "description": "调拨单ID"
                },
                "notes": {
                    "type": "string",
                    "description": "备注"
                }
            },
            "required": ["transfer_id"]
        }

    def execute(self, transfer_id: int, notes: str = "", **kwargs) -> ToolResult:
        """执行调拨收货"""
        try:
            from inventory.models import StockTransfer

            transfer = StockTransfer.objects.get(id=transfer_id, is_deleted=False)

            if transfer.status != 'shipped':
                return ToolResult(
                    success=False,
                    error=f"调拨单状态为 {transfer.get_status_display()}，不能收货"
                )

            # 使用工作流管理器执行收货
            from ..services.workflow_manager import ExecutionContext
            context = ExecutionContext(
                user=self.user,
                action=WorkflowAction.COMPLETE,
                entity_type="stock_transfer",
                entity_id=transfer.id,
                notes=notes
            )

            success, message, data = WorkflowManager.execute_workflow_action(context)

            if success:
                return ToolResult(success=True, data=data, message=message)
            else:
                return ToolResult(success=False, error=message)

        except Exception as e:
            return ToolResult(success=False, error=f"调拨收货失败: {str(e)}")
