"""
Finance 模块的导入导出资源配置
"""
from customers.models import Customer
from departments.models import Department
from django.contrib.auth import get_user_model
from import_export import fields, resources
from import_export.widgets import DateWidget, DecimalWidget, ForeignKeyWidget
from products.models import Product
from suppliers.models import Supplier

from .models import Account, Expense, Invoice, Journal, JournalEntry, Payment

User = get_user_model()


class ExpenseResource(resources.ModelResource):
    """费用报销单导入导出资源"""

    # 使用外键Widget来处理关联字段
    applicant = fields.Field(
        column_name="申请人", attribute="applicant", widget=ForeignKeyWidget(User, "username")
    )

    department = fields.Field(
        column_name="申请部门", attribute="department", widget=ForeignKeyWidget(Department, "name")
    )

    approved_by = fields.Field(
        column_name="审批人", attribute="approved_by", widget=ForeignKeyWidget(User, "username")
    )

    paid_by = fields.Field(
        column_name="支付人", attribute="paid_by", widget=ForeignKeyWidget(User, "username")
    )

    payment_account = fields.Field(
        column_name="支付科目", attribute="payment_account", widget=ForeignKeyWidget(Account, "code")
    )

    # 日期字段
    expense_date = fields.Field(
        column_name="费用日期", attribute="expense_date", widget=DateWidget(format="%Y-%m-%d")
    )

    # 金额字段
    amount = fields.Field(column_name="费用金额", attribute="amount", widget=DecimalWidget())

    class Meta:
        model = Expense
        fields = (
            "id",
            "expense_number",
            "expense_date",
            "applicant",
            "department",
            "category",
            "amount",
            "payment_method",
            "description",
            "status",
            "approved_by",
            "approved_at",
            "approval_note",
            "paid_by",
            "paid_at",
            "payment_account",
            "project",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["expense_number"]  # 使用费用单号作为唯一标识
        skip_unchanged = True  # 跳过未更改的记录
        report_skipped = True  # 报告跳过的记录

    def before_import_row(self, row, **kwargs):
        """导入前的数据预处理"""
        # 可以在这里添加自定义的数据验证和转换逻辑
        pass

    def after_import_row(self, row, row_result, **kwargs):
        """导入后的处理"""
        # 可以在这里添加导入后的逻辑，比如发送通知等
        pass


class InvoiceResource(resources.ModelResource):
    """发票导入导出资源"""

    customer = fields.Field(
        column_name="客户", attribute="customer", widget=ForeignKeyWidget(Customer, "name")
    )

    supplier = fields.Field(
        column_name="供应商", attribute="supplier", widget=ForeignKeyWidget(Supplier, "name")
    )

    invoice_date = fields.Field(
        column_name="开票日期", attribute="invoice_date", widget=DateWidget(format="%Y-%m-%d")
    )

    total_amount = fields.Field(
        column_name="含税总金额", attribute="total_amount", widget=DecimalWidget()
    )

    tax_amount = fields.Field(column_name="税额", attribute="tax_amount", widget=DecimalWidget())

    paid_amount = fields.Field(column_name="已付金额", attribute="paid_amount", widget=DecimalWidget())

    class Meta:
        model = Invoice
        fields = (
            "id",
            "invoice_number",
            "invoice_type",
            "invoice_date",
            "customer",
            "supplier",
            "total_amount",
            "tax_amount",
            "tax_rate",
            "paid_amount",
            "status",
            "notes",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["invoice_number"]
        skip_unchanged = True
        report_skipped = True


class PaymentResource(resources.ModelResource):
    """收付款记录导入导出资源"""

    customer = fields.Field(
        column_name="客户", attribute="customer", widget=ForeignKeyWidget(Customer, "name")
    )

    supplier = fields.Field(
        column_name="供应商", attribute="supplier", widget=ForeignKeyWidget(Supplier, "name")
    )

    payment_date = fields.Field(
        column_name="付款日期", attribute="payment_date", widget=DateWidget(format="%Y-%m-%d")
    )

    amount = fields.Field(column_name="金额", attribute="amount", widget=DecimalWidget())

    class Meta:
        model = Payment
        fields = (
            "id",
            "payment_number",
            "payment_type",
            "payment_date",
            "customer",
            "supplier",
            "amount",
            "currency",
            "payment_method",
            "status",
            "bank_account",
            "bank_name",
            "transaction_reference",
            "notes",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["payment_number"]
        skip_unchanged = True
        report_skipped = True


class AccountResource(resources.ModelResource):
    """会计科目导入导出资源"""

    parent = fields.Field(
        column_name="上级科目", attribute="parent", widget=ForeignKeyWidget(Account, "code")
    )

    class Meta:
        model = Account
        fields = (
            "id",
            "code",
            "name",
            "account_type",
            "parent",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["code"]
        skip_unchanged = True
        report_skipped = True


class JournalResource(resources.ModelResource):
    """会计凭证导入导出资源"""

    journal_date = fields.Field(
        column_name="凭证日期", attribute="journal_date", widget=DateWidget(format="%Y-%m-%d")
    )

    total_debit = fields.Field(column_name="借方合计", attribute="total_debit", widget=DecimalWidget())

    total_credit = fields.Field(
        column_name="贷方合计", attribute="total_credit", widget=DecimalWidget()
    )

    class Meta:
        model = Journal
        fields = (
            "id",
            "journal_number",
            "journal_type",
            "journal_date",
            "total_debit",
            "total_credit",
            "status",
            "notes",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["journal_number"]
        skip_unchanged = True
        report_skipped = True


class JournalEntryResource(resources.ModelResource):
    """会计分录导入导出资源"""

    journal = fields.Field(
        column_name="关联凭证", attribute="journal", widget=ForeignKeyWidget(Journal, "journal_number")
    )

    account = fields.Field(
        column_name="会计科目", attribute="account", widget=ForeignKeyWidget(Account, "code")
    )

    debit_amount = fields.Field(
        column_name="借方金额", attribute="debit_amount", widget=DecimalWidget()
    )

    credit_amount = fields.Field(
        column_name="贷方金额", attribute="credit_amount", widget=DecimalWidget()
    )

    class Meta:
        model = JournalEntry
        fields = (
            "id",
            "journal",
            "account",
            "debit_amount",
            "credit_amount",
            "description",
            "sort_order",
            "created_at",
            "updated_at",
        )
        export_order = fields
        import_id_fields = ["id"]
        skip_unchanged = True
        report_skipped = True
