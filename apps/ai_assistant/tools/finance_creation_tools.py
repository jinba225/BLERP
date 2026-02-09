"""
财务模块创建工具

提供财务业务的创建功能，包括凭证、收付款、预付款、费用等
"""

from typing import Dict, Any
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from finance.models import (
    Journal,
    JournalEntry,
    Payment,
    CustomerPrepayment,
    SupplierPrepayment,
    Expense,
    Account,
)
from customers.models import Customer
from suppliers.models import Supplier
from common.utils import DocumentNumberGenerator
from .base_tool import BaseTool, ToolResult


class CreateJournalTool(BaseTool):
    """创建会计凭证工具"""

    name = "create_journal"
    display_name = "创建会计凭证"
    description = "创建会计凭证（含借贷分录）"
    category = "finance"
    risk_level = "high"
    require_permission = "finance.add_journal"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "journal_type": {
                    "type": "string",
                    "description": "凭证类型",
                    "enum": ["receipt", "payment", "transfer", "adjustment"],
                },
                "journal_date": {"type": "string", "description": "凭证日期（YYYY-MM-DD，默认今天）"},
                "entries": {
                    "type": "array",
                    "description": "分录列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "account_id": {"type": "integer", "description": "科目ID"},
                            "debit_amount": {"type": "number", "description": "借方金额"},
                            "credit_amount": {"type": "number", "description": "贷方金额"},
                            "description": {"type": "string", "description": "摘要"},
                        },
                        "required": ["account_id", "description"],
                    },
                },
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["journal_type", "entries"],
        }

    def execute(
        self, journal_type: str, entries: list, journal_date: str = None, notes: str = "", **kwargs
    ) -> ToolResult:
        """执行创建凭证"""
        try:
            # 计算借贷合计
            total_debit = 0.0
            total_credit = 0.0

            # 验证科目和金额
            validated_entries = []
            for entry in entries:
                try:
                    account = Account.objects.get(id=entry["account_id"], is_deleted=False)
                except Account.DoesNotExist:
                    return ToolResult(success=False, error=f"科目ID {entry['account_id']} 不存在")

                debit_amount = float(entry.get("debit_amount", 0))
                credit_amount = float(entry.get("credit_amount", 0))

                # 每个分录借方或贷方必须有且仅有一个有值
                if debit_amount > 0 and credit_amount > 0:
                    return ToolResult(success=False, error=f"科目 {account.name} 的借方和贷方不能同时有值")

                if debit_amount == 0 and credit_amount == 0:
                    return ToolResult(success=False, error=f"科目 {account.name} 的借方或贷方必须有一个有值")

                total_debit += debit_amount
                total_credit += credit_amount

                validated_entries.append(
                    {
                        "account": account,
                        "debit_amount": debit_amount,
                        "credit_amount": credit_amount,
                        "description": entry.get("description", ""),
                    }
                )

            # 验证借贷平衡
            if abs(total_debit - total_credit) > 0.01:
                return ToolResult(
                    success=False, error=f"借贷不平衡：借方合计 {total_debit}，贷方合计 {total_credit}"
                )

            # 创建凭证
            with transaction.atomic():
                journal_number = DocumentNumberGenerator.generate("journal")
                journal_date_obj = (
                    datetime.strptime(journal_date, "%Y-%m-%d").date()
                    if journal_date
                    else timezone.now().date()
                )

                journal = Journal.objects.create(
                    journal_number=journal_number,
                    journal_type=journal_type,
                    journal_date=journal_date_obj,
                    total_debit=total_debit,
                    total_credit=total_credit,
                    status="draft",
                    notes=notes,
                    created_by=self.user,
                )

                # 创建分录
                for entry_data in validated_entries:
                    JournalEntry.objects.create(
                        journal=journal,
                        account=entry_data["account"],
                        debit_amount=entry_data["debit_amount"],
                        credit_amount=entry_data["credit_amount"],
                        description=entry_data["description"],
                        created_by=self.user,
                    )

            return ToolResult(
                success=True,
                data={
                    "journal_id": journal.id,
                    "journal_number": journal.journal_number,
                    "journal_type": journal.get_journal_type_display(),
                    "journal_date": journal.journal_date.strftime("%Y-%m-%d"),
                    "total_debit": float(total_debit),
                    "total_credit": float(total_credit),
                    "entries_count": len(validated_entries),
                },
                message=f"凭证 {journal.journal_number} 创建成功，借贷各 {total_debit:.2f} 元",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"创建凭证失败: {str(e)}")


class CreatePaymentTool(BaseTool):
    """创建收付款工具"""

    name = "create_payment"
    display_name = "创建收付款"
    description = "创建收款或付款记录"
    category = "finance"
    risk_level = "high"
    require_permission = "finance.add_payment"
    require_approval = True

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "payment_type": {
                    "type": "string",
                    "description": "收付款类型",
                    "enum": ["receipt", "payment"],
                },
                "customer_id": {"type": "integer", "description": "客户ID（收款时必填）"},
                "supplier_id": {"type": "integer", "description": "供应商ID（付款时必填）"},
                "amount": {"type": "number", "description": "金额"},
                "payment_date": {"type": "string", "description": "收付款日期（YYYY-MM-DD，默认今天）"},
                "payment_method": {
                    "type": "string",
                    "description": "付款方式",
                    "enum": ["cash", "bank_transfer", "check", "draft", "other"],
                },
                "reference_number": {"type": "string", "description": "参考单号"},
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["payment_type", "amount"],
        }

    def execute(
        self,
        payment_type: str,
        amount: float,
        customer_id: int = None,
        supplier_id: int = None,
        payment_date: str = None,
        payment_method: str = "bank_transfer",
        reference_number: str = "",
        notes: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行创建收付款"""
        try:
            amount = float(amount)

            if amount <= 0:
                return ToolResult(success=False, error="金额必须大于0")

            # 验证客户或供应商
            customer = None
            supplier = None

            if payment_type == "receipt":
                if not customer_id:
                    return ToolResult(success=False, error="收款必须指定客户")
                try:
                    customer = Customer.objects.get(id=customer_id, is_deleted=False)
                except Customer.DoesNotExist:
                    return ToolResult(success=False, error=f"客户ID {customer_id} 不存在")

            elif payment_type == "payment":
                if not supplier_id:
                    return ToolResult(success=False, error="付款必须指定供应商")
                try:
                    supplier = Supplier.objects.get(id=supplier_id, is_deleted=False)
                except Supplier.DoesNotExist:
                    return ToolResult(success=False, error=f"供应商ID {supplier_id} 不存在")

            # 创建收付款记录
            with transaction.atomic():
                payment_number = DocumentNumberGenerator.generate("payment")
                payment_date_obj = (
                    datetime.strptime(payment_date, "%Y-%m-%d").date()
                    if payment_date
                    else timezone.now().date()
                )

                payment = Payment.objects.create(
                    payment_number=payment_number,
                    payment_type=payment_type,
                    customer=customer,
                    supplier=supplier,
                    amount=amount,
                    payment_date=payment_date_obj,
                    payment_method=payment_method,
                    reference_number=reference_number,
                    status="draft",
                    notes=notes,
                    created_by=self.user,
                )

            entity_name = customer.name if customer else supplier.name

            return ToolResult(
                success=True,
                data={
                    "payment_id": payment.id,
                    "payment_number": payment.payment_number,
                    "payment_type": payment.get_payment_type_display(),
                    "entity_name": entity_name,
                    "amount": float(amount),
                    "payment_date": payment.payment_date.strftime("%Y-%m-%d"),
                    "payment_method": payment.get_payment_method_display(),
                },
                message=f"{payment.get_payment_type_display()} {payment.payment_number} 创建成功，金额 {amount:.2f} 元",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"创建收付款失败: {str(e)}")


class CreatePrepaymentTool(BaseTool):
    """创建预付款工具"""

    name = "create_prepayment"
    display_name = "创建预付款"
    description = "创建客户预付款或供应商预付款"
    category = "finance"
    risk_level = "medium"
    require_permission = "finance.add_prepayment"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prepayment_type": {
                    "type": "string",
                    "description": "预付款类型",
                    "enum": ["customer", "supplier"],
                },
                "customer_id": {"type": "integer", "description": "客户ID"},
                "supplier_id": {"type": "integer", "description": "供应商ID"},
                "amount": {"type": "number", "description": "预付金额"},
                "prepayment_date": {"type": "string", "description": "预付日期（YYYY-MM-DD，默认今天）"},
                "payment_method": {
                    "type": "string",
                    "description": "付款方式",
                    "enum": ["cash", "bank_transfer", "check", "other"],
                },
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["prepayment_type", "amount"],
        }

    def execute(
        self,
        prepayment_type: str,
        amount: float,
        customer_id: int = None,
        supplier_id: int = None,
        prepayment_date: str = None,
        payment_method: str = "bank_transfer",
        notes: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行创建预付款"""
        try:
            amount = float(amount)

            if amount <= 0:
                return ToolResult(success=False, error="金额必须大于0")

            prepayment_date_obj = (
                datetime.strptime(prepayment_date, "%Y-%m-%d").date()
                if prepayment_date
                else timezone.now().date()
            )

            # 根据类型创建相应的预付款
            if prepayment_type == "customer":
                if not customer_id:
                    return ToolResult(success=False, error="客户预付款必须指定客户ID")
                try:
                    customer = Customer.objects.get(id=customer_id, is_deleted=False)
                except Customer.DoesNotExist:
                    return ToolResult(success=False, error=f"客户ID {customer_id} 不存在")

                with transaction.atomic():
                    prepayment_number = DocumentNumberGenerator.generate("customer_prepayment")
                    prepayment = CustomerPrepayment.objects.create(
                        prepayment_number=prepayment_number,
                        customer=customer,
                        amount=amount,
                        prepayment_date=prepayment_date_obj,
                        payment_method=payment_method,
                        status="active",
                        notes=notes,
                        created_by=self.user,
                    )

                entity_name = customer.name

            else:  # supplier
                if not supplier_id:
                    return ToolResult(success=False, error="供应商预付款必须指定供应商ID")
                try:
                    supplier = Supplier.objects.get(id=supplier_id, is_deleted=False)
                except Supplier.DoesNotExist:
                    return ToolResult(success=False, error=f"供应商ID {supplier_id} 不存在")

                with transaction.atomic():
                    prepayment_number = DocumentNumberGenerator.generate("supplier_prepayment")
                    prepayment = SupplierPrepayment.objects.create(
                        prepayment_number=prepayment_number,
                        supplier=supplier,
                        amount=amount,
                        prepayment_date=prepayment_date_obj,
                        payment_method=payment_method,
                        status="active",
                        notes=notes,
                        created_by=self.user,
                    )

                entity_name = supplier.name

            return ToolResult(
                success=True,
                data={
                    "prepayment_id": prepayment.id,
                    "prepayment_number": prepayment.prepayment_number,
                    "prepayment_type": prepayment_type,
                    "entity_name": entity_name,
                    "amount": float(amount),
                    "prepayment_date": prepayment.prepayment_date.strftime("%Y-%m-%d"),
                },
                message=f"预付款 {prepayment.prepayment_number} 创建成功，金额 {amount:.2f} 元",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"创建预付款失败: {str(e)}")


class CreateExpenseTool(BaseTool):
    """创建费用报销工具"""

    name = "create_expense"
    display_name = "创建费用报销"
    description = "创建费用报销单"
    category = "finance"
    risk_level = "medium"
    require_permission = "finance.add_expense"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "费用类别",
                    "enum": [
                        "travel",
                        "transportation",
                        "meal",
                        "office",
                        "communication",
                        "utilities",
                        "entertainment",
                        "training",
                        "maintenance",
                        "advertising",
                        "other",
                    ],
                },
                "amount": {"type": "number", "description": "费用金额"},
                "expense_date": {"type": "string", "description": "费用日期（YYYY-MM-DD，默认今天）"},
                "department_id": {"type": "integer", "description": "部门ID（可选）"},
                "description": {"type": "string", "description": "费用说明"},
                "notes": {"type": "string", "description": "备注"},
            },
            "required": ["category", "amount"],
        }

    def execute(
        self,
        category: str,
        amount: float,
        expense_date: str = None,
        department_id: int = None,
        description: str = "",
        notes: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行创建费用报销"""
        try:
            from departments.models import Department

            amount = float(amount)

            if amount <= 0:
                return ToolResult(success=False, error="金额必须大于0")

            # 获取部门
            department = None
            if department_id:
                try:
                    department = Department.objects.get(id=department_id, is_deleted=False)
                except Department.DoesNotExist:
                    return ToolResult(success=False, error=f"部门ID {department_id} 不存在")

            # 创建费用报销
            with transaction.atomic():
                expense_number = DocumentNumberGenerator.generate("expense")
                expense_date_obj = (
                    datetime.strptime(expense_date, "%Y-%m-%d").date()
                    if expense_date
                    else timezone.now().date()
                )

                expense = Expense.objects.create(
                    expense_number=expense_number,
                    expense_date=expense_date_obj,
                    applicant=self.user,
                    department=department,
                    category=category,
                    amount=amount,
                    description=description,
                    status="draft",
                    notes=notes,
                    created_by=self.user,
                )

            return ToolResult(
                success=True,
                data={
                    "expense_id": expense.id,
                    "expense_number": expense.expense_number,
                    "category": expense.get_category_display(),
                    "amount": float(amount),
                    "expense_date": expense.expense_date.strftime("%Y-%m-%d"),
                    "department": department.name if department else "",
                    "applicant": self.user.username,
                },
                message=f"费用报销 {expense.expense_number} 创建成功，金额 {amount:.2f} 元",
            )

        except Exception as e:
            return ToolResult(success=False, error=f"创建费用报销失败: {str(e)}")
