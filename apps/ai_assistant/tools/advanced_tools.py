"""
高级操作工具

提供复杂的业务操作功能，如合并预付款、处理付款等
"""

from datetime import datetime
from typing import Any, Dict, List

from django.db import transaction
from django.utils import timezone

from .base_tool import BaseTool, ToolResult


class ConsolidatePrepaymentTool(BaseTool):
    """合并预付款工具"""

    name = "consolidate_prepayment"
    display_name = "合并预付款"
    description = "将多笔小额预付款合并为一笔大额预付款，或使用预付款冲销应付款项"
    category = "finance"
    risk_level = "high"
    require_permission = "finance.consolidate_prepayment"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prepayment_type": {
                    "type": "string",
                    "description": "预付款类型",
                    "enum": ["customer", "supplier"],
                },
                "source_prepayment_ids": {
                    "type": "array",
                    "description": "源预付款ID列表（要合并的预付款）",
                    "items": {"type": "integer"},
                },
                "target_prepayment_id": {"type": "integer", "description": "目标预付款ID（合并到这笔预付款）"},
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["prepayment_type", "source_prepayment_ids", "target_prepayment_id"],
        }

    def execute(
        self,
        prepayment_type: str,
        source_prepayment_ids: List[int],
        target_prepayment_id: int,
        notes: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行合并"""
        try:
            if prepayment_type == "customer":
                from finance.models import CustomerPrepayment

                # 获取目标预付款
                try:
                    target_prepayment = CustomerPrepayment.objects.get(
                        id=target_prepayment_id, is_deleted=False
                    )
                except CustomerPrepayment.DoesNotExist:
                    return ToolResult(success=False, error=f"目标预付款ID {target_prepayment_id} 不存在")

                # 获取源预付款列表
                source_prepayments = CustomerPrepayment.objects.filter(
                    id__in=source_prepayment_ids,
                    is_deleted=False,
                    customer=target_prepayment.customer,
                )

                if source_prepayments.count() != len(source_prepayment_ids):
                    return ToolResult(success=False, error="部分源预付款不存在或不属于同一客户")

                # 执行合并
                with transaction.atomic():
                    total_amount = 0
                    for source in source_prepayments:
                        total_amount += source.balance
                        source.status = "fully_used"
                        source.used_amount += source.balance
                        source.balance = 0
                        source.save()

                    target_prepayment.amount += total_amount
                    target_prepayment.notes = f"{target_prepayment.notes or ''}\n合并记录: {notes}"
                    target_prepayment.save()

            else:  # supplier
                from finance.models import SupplierPrepayment

                # 获取目标预付款
                try:
                    target_prepayment = SupplierPrepayment.objects.get(
                        id=target_prepayment_id, is_deleted=False
                    )
                except SupplierPrepayment.DoesNotExist:
                    return ToolResult(success=False, error=f"目标预付款ID {target_prepayment_id} 不存在")

                # 获取源预付款列表
                source_prepayments = SupplierPrepayment.objects.filter(
                    id__in=source_prepayment_ids,
                    is_deleted=False,
                    supplier=target_prepayment.supplier,
                )

                if source_prepayments.count() != len(source_prepayment_ids):
                    return ToolResult(success=False, error="部分源预付款不存在或不属于同一供应商")

                # 执行合并
                with transaction.atomic():
                    total_amount = 0
                    for source in source_prepayments:
                        total_amount += source.balance
                        source.status = "fully_used"
                        source.used_amount += source.balance
                        source.balance = 0
                        source.save()

                    target_prepayment.amount += total_amount
                    target_prepayment.notes = f"{target_prepayment.notes or ''}\n合并记录: {notes}"
                    target_prepayment.save()

            return ToolResult(
                success=True,
                data={
                    "target_prepayment_id": target_prepayment.id,
                    "target_number": target_prepayment.prepayment_number,
                    "consolidated_amount": float(total_amount),
                    "source_count": len(source_prepayment_ids),
                },
                message=f"已将 {
                    len(source_prepayment_ids)} 笔预付款合并到 {
                    target_prepayment.prepayment_number}，总金额 {
                    total_amount:.2f} 元",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"合并预付款失败: {str(e)}")


class ProcessPaymentTool(BaseTool):
    """处理付款工具"""

    name = "process_payment"
    display_name = "处理付款"
    description = "处理付款申请，执行付款操作并更新应付款项"
    category = "finance"
    risk_level = "high"
    require_permission = "finance.payment"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "payment_id": {"type": "integer", "description": "付款记录ID"},
                "payment_method": {
                    "type": "string",
                    "description": "付款方式",
                    "enum": ["cash", "bank_transfer", "check", "draft", "other"],
                },
                "payment_date": {"type": "string", "description": "付款日期（YYYY-MM-DD，默认今天）"},
                "reference_number": {"type": "string", "description": "银行参考号或支票号"},
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["payment_id"],
        }

    def execute(
        self,
        payment_id: int,
        payment_method: str = "bank_transfer",
        payment_date: str = None,
        reference_number: str = "",
        notes: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行处理付款"""
        try:
            from finance.models import Payment

            payment = Payment.objects.get(id=payment_id, is_deleted=False)

            if payment.payment_type != "payment":
                return ToolResult(
                    success=False, error=f"记录类型为 {payment.get_payment_type_display()}，不是付款记录"
                )

            if payment.status == "completed":
                return ToolResult(success=False, error="付款记录已完成，无需重复处理")

            # 处理付款
            with transaction.atomic():
                payment_date_obj = (
                    datetime.strptime(payment_date, "%Y-%m-%d").date()
                    if payment_date
                    else timezone.now().date()
                )

                payment.payment_method = payment_method
                payment.payment_date = payment_date_obj
                payment.reference_number = reference_number or payment.reference_number
                payment.status = "completed"
                payment.notes = f"{payment.notes or ''}\n处理备注: {notes}"
                payment.paid_at = timezone.now()
                payment.paid_by = self.user
                payment.save()

                # TODO: 更新应付款项（供应商账）

            return ToolResult(
                success=True,
                data={
                    "payment_id": payment.id,
                    "payment_number": payment.payment_number,
                    "amount": float(payment.amount),
                    "payment_date": payment.payment_date.strftime("%Y-%m-%d"),
                    "payment_method": payment.get_payment_method_display(),
                },
                message=f"付款 {payment.payment_number} 处理成功，金额 {payment.amount:.2f} 元",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"处理付款失败: {str(e)}")


class ApproveBudgetTool(BaseTool):
    """审批预算工具"""

    name = "approve_budget"
    display_name = "审批预算"
    description = "审批预算申请或预算执行"
    category = "finance"
    risk_level = "high"
    require_permission = "finance.approve_budget"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "budget_id": {"type": "integer", "description": "预算ID"},
                "action": {
                    "type": "string",
                    "description": "操作类型",
                    "enum": ["approve", "adjust", "freeze"],
                },
                "notes": {"type": "string", "description": "审批备注或调整说明"},
                "new_amount": {"type": "number", "description": "新预算金额（仅在调整时需要）"},
            },
            "required": ["budget_id", "action"],
        }

    def execute(
        self, budget_id: int, action: str, notes: str = "", new_amount: float = None, **kwargs
    ) -> ToolResult:
        """执行审批预算"""
        try:
            from finance.models import Budget

            budget = Budget.objects.get(id=budget_id, is_deleted=False)

            if action == "approve":
                # 批准预算
                if budget.status != "draft":
                    return ToolResult(
                        success=False, error=f"预算状态为 {budget.get_status_display()}，不能批准"
                    )

                budget.status = "approved"
                budget.approved_at = timezone.now()
                budget.approved_by = self.user
                budget.notes = f"{budget.notes or ''}\n审批备注: {notes}"
                budget.save()

                return ToolResult(
                    success=True,
                    data={
                        "budget_id": budget.id,
                        "budget_name": budget.name,
                        "status": budget.status,
                    },
                    message=f"预算 {budget.name} 已批准",
                )

            elif action == "adjust":
                # 调整预算
                if new_amount is None:
                    return ToolResult(success=False, error="调整预算必须指定新金额")

                old_amount = float(budget.amount) if budget.amount else 0
                budget.amount = new_amount
                budget.notes = f"{
                    budget.notes or ''}\n调整记录: 原金额 {
                    old_amount:.2f}，新金额 {
                    new_amount:.2f}，原因: {notes}"
                budget.last_modified_at = timezone.now()
                budget.last_modified_by = self.user
                budget.save()

                return ToolResult(
                    success=True,
                    data={
                        "budget_id": budget.id,
                        "budget_name": budget.name,
                        "old_amount": old_amount,
                        "new_amount": new_amount,
                    },
                    message=f"预算 {budget.name} 已调整，从 {old_amount:.2f} 调整为 {new_amount:.2f}",
                )

            elif action == "freeze":
                # 冻结预算
                if budget.status != "approved":
                    return ToolResult(success=False, error="只有已批准的预算才能冻结")

                budget.status = "frozen"
                budget.notes = f"{budget.notes or ''}\n冻结原因: {notes}"
                budget.last_modified_at = timezone.now()
                budget.last_modified_by = self.user
                budget.save()

                return ToolResult(
                    success=True,
                    data={
                        "budget_id": budget.id,
                        "budget_name": budget.name,
                        "status": budget.status,
                    },
                    message=f"预算 {budget.name} 已冻结",
                )

        except Exception as e:
            return ToolResult(success=False, error=f"审批预算失败: {str(e)}")
