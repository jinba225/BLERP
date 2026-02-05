"""
财务模块工具

提供财务业务的查询和操作工具，包括科目、凭证、账务、收付款、费用、发票等功能
"""

from typing import Dict, Any
from django.db.models import Q, Sum, F
from finance.models import (
    Account, Journal, JournalEntry,
    CustomerAccount, SupplierAccount,
    Payment, CustomerPrepayment, SupplierPrepayment,
    Expense, Invoice
)
from .base_tool import BaseTool, ToolResult


class QueryAccountsTool(BaseTool):
    """查询会计科目工具"""

    name = "query_accounts"
    display_name = "查询会计科目"
    description = "查询会计科目列表，支持按类型、级别、关键词筛选"
    category = "finance"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "account_type": {
                    "type": "string",
                    "description": "科目类型（asset/liability/equity/revenue/expense）",
                    "enum": ["asset", "liability", "equity", "revenue", "expense"]
                },
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词（科目名称或代码）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认50）",
                    "default": 50
                }
            }
        }

    def execute(self, account_type: str = None, keyword: str = None,
                limit: int = 50, **kwargs) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            accounts = Account.objects.filter(is_deleted=False)

            if account_type:
                accounts = accounts.filter(account_type=account_type)

            if keyword:
                accounts = accounts.filter(
                    Q(name__icontains=keyword) |
                    Q(code__icontains=keyword)
                )

            accounts = accounts.order_by('code')[:limit]

            # 格式化结果
            results = []
            for acc in accounts:
                results.append({
                    "id": acc.id,
                    "code": acc.code,
                    "name": acc.name,
                    "account_type": acc.account_type,
                    "account_type_display": acc.get_account_type_display(),
                    "parent_id": acc.parent_id,
                    "is_leaf": acc.is_leaf,
                })

            return ToolResult(
                success=True,
                data=results,
                message=f"找到 {len(results)} 个会计科目"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"查询会计科目失败: {str(e)}"
            )


class QueryJournalsTool(BaseTool):
    """查询会计凭证工具"""

    name = "query_journals"
    display_name = "查询会计凭证"
    description = "查询会计凭证列表，支持按类型、状态、日期范围筛选"
    category = "finance"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "journal_type": {
                    "type": "string",
                    "description": "凭证类型（receipt/payment/transfer/adjustment）",
                    "enum": ["receipt", "payment", "transfer", "adjustment"]
                },
                "status": {
                    "type": "string",
                    "description": "凭证状态（draft/posted/cancelled）",
                    "enum": ["draft", "posted", "cancelled"]
                },
                "date_from": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）"
                },
                "date_to": {
                    "type": "string",
                    "description": "结束日期（YYYY-MM-DD）"
                },
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词（凭证号）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认20）",
                    "default": 20
                }
            }
        }

    def execute(self, journal_type: str = None, status: str = None,
                date_from: str = None, date_to: str = None,
                keyword: str = None, limit: int = 20, **kwargs) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            journals = Journal.objects.filter(is_deleted=False)

            if journal_type:
                journals = journals.filter(journal_type=journal_type)

            if status:
                journals = journals.filter(status=status)

            if date_from:
                journals = journals.filter(journal_date__gte=date_from)

            if date_to:
                journals = journals.filter(journal_date__lte=date_to)

            if keyword:
                journals = journals.filter(journal_number__icontains=keyword)

            journals = journals.order_by('-journal_date')[:limit]

            # 格式化结果
            results = []
            for journal in journals:
                results.append({
                    "id": journal.id,
                    "journal_number": journal.journal_number,
                    "journal_type": journal.journal_type,
                    "journal_type_display": journal.get_journal_type_display(),
                    "journal_date": journal.journal_date.strftime("%Y-%m-%d") if journal.journal_date else None,
                    "total_debit": float(journal.total_debit) if journal.total_debit else 0,
                    "total_credit": float(journal.total_credit) if journal.total_credit else 0,
                    "status": journal.status,
                    "status_display": journal.get_status_display(),
                    "entries_count": journal.entries.count() if hasattr(journal, 'entries') else 0,
                })

            return ToolResult(
                success=True,
                data=results,
                message=f"找到 {len(results)} 个会计凭证"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"查询会计凭证失败: {str(e)}"
            )


class QueryCustomerAccountsTool(BaseTool):
    """查询客户账工具"""

    name = "query_customer_accounts"
    display_name = "查询客户账"
    description = "查询客户应收账款列表，支持按客户、日期范围筛选"
    category = "finance"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "客户ID"
                },
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词（客户名称）"
                },
                "has_balance": {
                    "type": "boolean",
                    "description": "是否仅显示有余额的客户"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认50）",
                    "default": 50
                }
            }
        }

    def execute(self, customer_id: int = None, keyword: str = None,
                has_balance: bool = None, limit: int = 50, **kwargs) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            accounts = CustomerAccount.objects.filter(is_deleted=False)

            if customer_id:
                accounts = accounts.filter(customer_id=customer_id)

            if keyword:
                accounts = accounts.filter(customer__name__icontains=keyword)

            if has_balance:
                accounts = accounts.filter(balance__gt=0)

            accounts = accounts.select_related('customer').order_by('-balance')[:limit]

            # 格式化结果
            results = []
            for acc in accounts:
                results.append({
                    "id": acc.id,
                    "customer_id": acc.customer_id,
                    "customer_name": acc.customer.name if acc.customer else "",
                    "debit_amount": float(acc.debit_amount) if acc.debit_amount else 0,
                    "credit_amount": float(acc.credit_amount) if acc.credit_amount else 0,
                    "balance": float(acc.balance) if acc.balance else 0,
                })

            return ToolResult(
                success=True,
                data=results,
                message=f"找到 {len(results)} 个客户账"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"查询客户账失败: {str(e)}"
            )


class QuerySupplierAccountsTool(BaseTool):
    """查询供应商账工具"""

    name = "query_supplier_accounts"
    display_name = "查询供应商账"
    description = "查询供应商应付账款列表，支持按供应商、日期范围筛选"
    category = "finance"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "supplier_id": {
                    "type": "integer",
                    "description": "供应商ID"
                },
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词（供应商名称）"
                },
                "has_balance": {
                    "type": "boolean",
                    "description": "是否仅显示有余额的供应商"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认50）",
                    "default": 50
                }
            }
        }

    def execute(self, supplier_id: int = None, keyword: str = None,
                has_balance: bool = None, limit: int = 50, **kwargs) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            accounts = SupplierAccount.objects.filter(is_deleted=False)

            if supplier_id:
                accounts = accounts.filter(supplier_id=supplier_id)

            if keyword:
                accounts = accounts.filter(supplier__name__icontains=keyword)

            if has_balance:
                accounts = accounts.filter(balance__gt=0)

            accounts = accounts.select_related('supplier').order_by('-balance')[:limit]

            # 格式化结果
            results = []
            for acc in accounts:
                results.append({
                    "id": acc.id,
                    "supplier_id": acc.supplier_id,
                    "supplier_name": acc.supplier.name if acc.supplier else "",
                    "debit_amount": float(acc.debit_amount) if acc.debit_amount else 0,
                    "credit_amount": float(acc.credit_amount) if acc.credit_amount else 0,
                    "balance": float(acc.balance) if acc.balance else 0,
                })

            return ToolResult(
                success=True,
                data=results,
                message=f"找到 {len(results)} 个供应商账"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"查询供应商账失败: {str(e)}"
            )


class QueryPaymentsTool(BaseTool):
    """查询收付款记录工具"""

    name = "query_payments"
    display_name = "查询收付款记录"
    description = "查询收付款记录列表，支持按类型、状态、日期范围筛选"
    category = "finance"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "payment_type": {
                    "type": "string",
                    "description": "收付款类型（receipt/payment）",
                    "enum": ["receipt", "payment"]
                },
                "status": {
                    "type": "string",
                    "description": "状态（draft/partial/completed/cancelled）",
                    "enum": ["draft", "partial", "completed", "cancelled"]
                },
                "date_from": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）"
                },
                "date_to": {
                    "type": "string",
                    "description": "结束日期（YYYY-MM-DD）"
                },
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词（单据号）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认20）",
                    "default": 20
                }
            }
        }

    def execute(self, payment_type: str = None, status: str = None,
                date_from: str = None, date_to: str = None,
                keyword: str = None, limit: int = 20, **kwargs) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            payments = Payment.objects.filter(is_deleted=False)

            if payment_type:
                payments = payments.filter(payment_type=payment_type)

            if status:
                payments = payments.filter(status=status)

            if date_from:
                payments = payments.filter(payment_date__gte=date_from)

            if date_to:
                payments = payments.filter(payment_date__lte=date_to)

            if keyword:
                payments = payments.filter(
                    Q(payment_number__icontains=keyword) |
                    Q(reference_number__icontains=keyword)
                )

            payments = payments.order_by('-payment_date')[:limit]

            # 格式化结果
            results = []
            for payment in payments:
                results.append({
                    "id": payment.id,
                    "payment_number": payment.payment_number,
                    "payment_type": payment.payment_type,
                    "payment_type_display": payment.get_payment_type_display(),
                    "payment_date": payment.payment_date.strftime("%Y-%m-%d") if payment.payment_date else None,
                    "amount": float(payment.amount) if payment.amount else 0,
                    "paid_amount": float(payment.paid_amount) if payment.paid_amount else 0,
                    "status": payment.status,
                    "status_display": payment.get_status_display(),
                    "payment_method": payment.payment_method,
                    "payment_method_display": payment.get_payment_method_display(),
                })

            return ToolResult(
                success=True,
                data=results,
                message=f"找到 {len(results)} 个收付款记录"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"查询收付款记录失败: {str(e)}"
            )


class QueryPrepaymentsTool(BaseTool):
    """查询预付款工具"""

    name = "query_prepayments"
    display_name = "查询预付款"
    description = "查询预付款记录列表，支持按类型、状态、日期范围筛选"
    category = "finance"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prepayment_type": {
                    "type": "string",
                    "description": "预付款类型（customer/supplier）",
                    "enum": ["customer", "supplier"]
                },
                "customer_id": {
                    "type": "integer",
                    "description": "客户ID"
                },
                "supplier_id": {
                    "type": "integer",
                    "description": "供应商ID"
                },
                "status": {
                    "type": "string",
                    "description": "状态（active/partial_used/fully_used/cancelled）",
                    "enum": ["active", "partial_used", "fully_used", "cancelled"]
                },
                "date_from": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）"
                },
                "date_to": {
                    "type": "string",
                    "description": "结束日期（YYYY-MM-DD）"
                },
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词（单据号）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认20）",
                    "default": 20
                }
            }
        }

    def execute(self, prepayment_type: str = None, customer_id: int = None,
                supplier_id: int = None, status: str = None,
                date_from: str = None, date_to: str = None,
                keyword: str = None, limit: int = 20, **kwargs) -> ToolResult:
        """执行查询"""
        try:
            results = []

            # 查询客户预付款
            if not prepayment_type or prepayment_type == "customer":
                customer_prepayments = CustomerPrepayment.objects.filter(is_deleted=False)

                if customer_id:
                    customer_prepayments = customer_prepayments.filter(customer_id=customer_id)

                if status:
                    customer_prepayments = customer_prepayments.filter(status=status)

                if date_from:
                    customer_prepayments = customer_prepayments.filter(prepayment_date__gte=date_from)

                if date_to:
                    customer_prepayments = customer_prepayments.filter(prepayment_date__lte=date_to)

                if keyword:
                    customer_prepayments = customer_prepayments.filter(prepayment_number__icontains=keyword)

                customer_prepayments = customer_prepayments.select_related('customer').order_by('-prepayment_date')[:limit]

                for prep in customer_prepayments:
                    results.append({
                        "id": prep.id,
                        "prepayment_number": prep.prepayment_number,
                        "prepayment_type": "customer",
                        "entity_name": prep.customer.name if prep.customer else "",
                        "prepayment_date": prep.prepayment_date.strftime("%Y-%m-%d") if prep.prepayment_date else None,
                        "amount": float(prep.amount) if prep.amount else 0,
                        "used_amount": float(prep.used_amount) if prep.used_amount else 0,
                        "balance": float(prep.balance) if prep.balance else 0,
                        "status": prep.status,
                        "status_display": prep.get_status_display(),
                    })

            # 查询供应商预付款
            if not prepayment_type or prepayment_type == "supplier":
                supplier_prepayments = SupplierPrepayment.objects.filter(is_deleted=False)

                if supplier_id:
                    supplier_prepayments = supplier_prepayments.filter(supplier_id=supplier_id)

                if status:
                    supplier_prepayments = supplier_prepayments.filter(status=status)

                if date_from:
                    supplier_prepayments = supplier_prepayments.filter(prepayment_date__gte=date_from)

                if date_to:
                    supplier_prepayments = supplier_prepayments.filter(prepayment_date__lte=date_to)

                if keyword:
                    supplier_prepayments = supplier_prepayments.filter(prepayment_number__icontains=keyword)

                supplier_prepayments = supplier_prepayments.select_related('supplier').order_by('-prepayment_date')[:limit]

                for prep in supplier_prepayments:
                    results.append({
                        "id": prep.id,
                        "prepayment_number": prep.prepayment_number,
                        "prepayment_type": "supplier",
                        "entity_name": prep.supplier.name if prep.supplier else "",
                        "prepayment_date": prep.prepayment_date.strftime("%Y-%m-%d") if prep.prepayment_date else None,
                        "amount": float(prep.amount) if prep.amount else 0,
                        "used_amount": float(prep.used_amount) if prep.used_amount else 0,
                        "balance": float(prep.balance) if prep.balance else 0,
                        "status": prep.status,
                        "status_display": prep.get_status_display(),
                    })

            # 按日期排序
            results.sort(key=lambda x: x['prepayment_date'], reverse=True)
            results = results[:limit]

            return ToolResult(
                success=True,
                data=results,
                message=f"找到 {len(results)} 个预付款记录"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"查询预付款失败: {str(e)}"
            )


class QueryExpensesTool(BaseTool):
    """查询费用报销工具"""

    name = "query_expenses"
    display_name = "查询费用报销"
    description = "查询费用报销记录列表，支持按类别、状态、日期范围筛选"
    category = "finance"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "费用类别（travel/transportation/meal/office等）",
                    "enum": ["travel", "transportation", "meal", "office", "communication",
                            "utilities", "entertainment", "training", "maintenance", "advertising", "other"]
                },
                "status": {
                    "type": "string",
                    "description": "状态（draft/submitted/approved/rejected/paid/cancelled）",
                    "enum": ["draft", "submitted", "approved", "rejected", "paid", "cancelled"]
                },
                "department_id": {
                    "type": "integer",
                    "description": "部门ID"
                },
                "date_from": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）"
                },
                "date_to": {
                    "type": "string",
                    "description": "结束日期（YYYY-MM-DD）"
                },
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词（费用单号）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认20）",
                    "default": 20
                }
            }
        }

    def execute(self, category: str = None, status: str = None,
                department_id: int = None, date_from: str = None, date_to: str = None,
                keyword: str = None, limit: int = 20, **kwargs) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            expenses = Expense.objects.filter(is_deleted=False)

            if category:
                expenses = expenses.filter(category=category)

            if status:
                expenses = expenses.filter(status=status)

            if department_id:
                expenses = expenses.filter(department_id=department_id)

            if date_from:
                expenses = expenses.filter(expense_date__gte=date_from)

            if date_to:
                expenses = expenses.filter(expense_date__lte=date_to)

            if keyword:
                expenses = expenses.filter(expense_number__icontains=keyword)

            expenses = expenses.select_related('applicant', 'department').order_by('-expense_date')[:limit]

            # 格式化结果
            results = []
            for exp in expenses:
                results.append({
                    "id": exp.id,
                    "expense_number": exp.expense_number,
                    "expense_date": exp.expense_date.strftime("%Y-%m-%d") if exp.expense_date else None,
                    "category": exp.category,
                    "category_display": exp.get_category_display(),
                    "amount": float(exp.amount) if exp.amount else 0,
                    "status": exp.status,
                    "status_display": exp.get_status_display(),
                    "applicant": exp.applicant.username if exp.applicant else "",
                    "department": exp.department.name if exp.department else "",
                })

            return ToolResult(
                success=True,
                data=results,
                message=f"找到 {len(results)} 个费用报销记录"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"查询费用报销失败: {str(e)}"
            )


class QueryInvoicesTool(BaseTool):
    """查询发票工具"""

    name = "query_invoices"
    display_name = "查询发票"
    description = "查询发票记录列表，支持按类型、状态、日期范围筛选"
    category = "finance"
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "invoice_type": {
                    "type": "string",
                    "description": "发票类型（sales_vat/sales_common/purchase_vat/purchase_common）",
                    "enum": ["sales_vat", "sales_common", "purchase_vat", "purchase_common"]
                },
                "status": {
                    "type": "string",
                    "description": "状态（draft/partial_paid/fully_paid/cancelled）",
                    "enum": ["draft", "partial_paid", "fully_paid", "cancelled"]
                },
                "date_from": {
                    "type": "string",
                    "description": "开始日期（YYYY-MM-DD）"
                },
                "date_to": {
                    "type": "string",
                    "description": "结束日期（YYYY-MM-DD）"
                },
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词（发票号）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制（默认20）",
                    "default": 20
                }
            }
        }

    def execute(self, invoice_type: str = None, status: str = None,
                date_from: str = None, date_to: str = None,
                keyword: str = None, limit: int = 20, **kwargs) -> ToolResult:
        """执行查询"""
        try:
            # 构建查询
            invoices = Invoice.objects.filter(is_deleted=False)

            if invoice_type:
                invoices = invoices.filter(invoice_type=invoice_type)

            if status:
                invoices = invoices.filter(status=status)

            if date_from:
                invoices = invoices.filter(invoice_date__gte=date_from)

            if date_to:
                invoices = invoices.filter(invoice_date__lte=date_to)

            if keyword:
                invoices = invoices.filter(invoice_number__icontains=keyword)

            invoices = invoices.order_by('-invoice_date')[:limit]

            # 格式化结果
            results = []
            for inv in invoices:
                results.append({
                    "id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "invoice_type": inv.invoice_type,
                    "invoice_type_display": inv.get_invoice_type_display(),
                    "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if inv.invoice_date else None,
                    "total_amount": float(inv.total_amount) if inv.total_amount else 0,
                    "tax_amount": float(inv.tax_amount) if inv.tax_amount else 0,
                    "paid_amount": float(inv.paid_amount) if inv.paid_amount else 0,
                    "status": inv.status,
                    "status_display": inv.get_status_display(),
                })

            return ToolResult(
                success=True,
                data=results,
                message=f"找到 {len(results)} 个发票记录"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"查询发票失败: {str(e)}"
            )
