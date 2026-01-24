"""
Finance models tests.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from apps.finance.models import (
    Account, Journal, JournalEntry,
    CustomerAccount, SupplierAccount, Payment,
    Budget, BudgetLine,
    Invoice, InvoiceItem,
    FinancialReport
)
from apps.customers.models import Customer
from apps.suppliers.models import Supplier
from apps.products.models import Product, ProductCategory, Unit
from apps.departments.models import Department
from apps.sales.models import SalesOrder
from apps.purchase.models import PurchaseOrder

User = get_user_model()


class AccountModelTest(TestCase):
    """Test Account model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

    def test_account_creation(self):
        """Test account creation."""
        account = Account.objects.create(
            code='1001',
            name='库存现金',
            account_type='asset',
            category='current_asset',
            created_by=self.user
        )

        self.assertEqual(account.code, '1001')
        self.assertEqual(account.name, '库存现金')
        self.assertEqual(account.account_type, 'asset')
        self.assertTrue(account.is_active)
        self.assertTrue(account.is_leaf)

    def test_account_hierarchy(self):
        """Test account hierarchy."""
        parent = Account.objects.create(
            code='1000',
            name='资产',
            account_type='asset',
            level=1,
            is_leaf=False,
            created_by=self.user
        )

        child = Account.objects.create(
            code='1001',
            name='库存现金',
            account_type='asset',
            parent=parent,
            level=2,
            created_by=self.user
        )

        self.assertEqual(child.parent, parent)
        self.assertEqual(child.level, 2)
        self.assertIn(child, parent.children.all())

    def test_account_full_name(self):
        """Test account full name property."""
        parent = Account.objects.create(
            code='1000',
            name='资产',
            account_type='asset',
            created_by=self.user
        )

        child = Account.objects.create(
            code='1001',
            name='库存现金',
            account_type='asset',
            parent=parent,
            created_by=self.user
        )

        expected = '资产 > 库存现金'
        self.assertEqual(child.full_name, expected)

    def test_account_str_representation(self):
        """Test account string representation."""
        account = Account.objects.create(
            code='1001',
            name='库存现金',
            account_type='asset',
            created_by=self.user
        )

        expected = '1001 - 库存现金'
        self.assertEqual(str(account), expected)


class JournalModelTest(TestCase):
    """Test Journal model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

    def test_journal_creation(self):
        """Test journal creation."""
        journal = Journal.objects.create(
            journal_number='JV202511001',
            journal_type='general',
            journal_date=timezone.now().date(),
            period='2025-11',
            prepared_by=self.user,
            created_by=self.user
        )

        self.assertEqual(journal.journal_number, 'JV202511001')
        self.assertEqual(journal.status, 'draft')
        self.assertEqual(journal.total_debit, Decimal('0'))
        self.assertEqual(journal.total_credit, Decimal('0'))

    def test_journal_is_balanced(self):
        """Test journal balance check."""
        journal = Journal.objects.create(
            journal_number='JV202511001',
            journal_type='general',
            journal_date=timezone.now().date(),
            period='2025-11',
            total_debit=Decimal('1000.00'),
            total_credit=Decimal('1000.00'),
            created_by=self.user
        )

        self.assertTrue(journal.is_balanced)

        journal.total_credit = Decimal('900.00')
        self.assertFalse(journal.is_balanced)


class JournalEntryModelTest(TestCase):
    """Test JournalEntry model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.journal = Journal.objects.create(
            journal_number='JV202511001',
            journal_type='general',
            journal_date=timezone.now().date(),
            period='2025-11',
            created_by=self.user
        )

        self.account = Account.objects.create(
            code='1001',
            name='库存现金',
            account_type='asset',
            created_by=self.user
        )

    def test_journal_entry_creation(self):
        """Test journal entry creation."""
        entry = JournalEntry.objects.create(
            journal=self.journal,
            account=self.account,
            debit_amount=Decimal('1000.00'),
            credit_amount=Decimal('0.00'),
            description='测试分录',
            created_by=self.user
        )

        self.assertEqual(entry.journal, self.journal)
        self.assertEqual(entry.account, self.account)
        self.assertEqual(entry.debit_amount, Decimal('1000.00'))


class CustomerAccountModelTest(TestCase):
    """Test CustomerAccount model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.customer = Customer.objects.create(
            name='测试客户',
            code='CUS001',
            created_by=self.user
        )

    def test_customer_account_creation(self):
        """Test customer account creation."""
        account = CustomerAccount.objects.create(
            customer=self.customer,
            invoice_number='INV001',
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            invoice_amount=Decimal('10000.00'),
            balance=Decimal('10000.00'),
            created_by=self.user
        )

        self.assertEqual(account.customer, self.customer)
        self.assertEqual(account.balance, Decimal('10000.00'))
        self.assertEqual(account.paid_amount, Decimal('0.00'))

    def test_customer_account_is_overdue(self):
        """Test customer account overdue check."""
        # Not overdue
        account = CustomerAccount.objects.create(
            customer=self.customer,
            invoice_amount=Decimal('10000.00'),
            balance=Decimal('10000.00'),
            due_date=timezone.now().date() + timedelta(days=30),
            created_by=self.user
        )
        self.assertFalse(account.is_overdue)

        # Overdue
        account.due_date = timezone.now().date() - timedelta(days=1)
        self.assertTrue(account.is_overdue)

        # Paid, not overdue
        account.balance = Decimal('0.00')
        self.assertFalse(account.is_overdue)


class SupplierAccountModelTest(TestCase):
    """Test SupplierAccount model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.supplier = Supplier.objects.create(
            name='测试供应商',
            code='SUP001',
            created_by=self.user
        )

    def test_supplier_account_creation(self):
        """Test supplier account creation."""
        account = SupplierAccount.objects.create(
            supplier=self.supplier,
            invoice_number='INV001',
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
            invoice_amount=Decimal('50000.00'),
            balance=Decimal('50000.00'),
            created_by=self.user
        )

        self.assertEqual(account.supplier, self.supplier)
        self.assertEqual(account.balance, Decimal('50000.00'))
        self.assertEqual(account.status, 'pending')

    def test_supplier_account_payment_ratio(self):
        """Test supplier account payment ratio calculation."""
        account = SupplierAccount.objects.create(
            supplier=self.supplier,
            invoice_amount=Decimal('10000.00'),
            paid_amount=Decimal('3000.00'),
            balance=Decimal('7000.00'),
            created_by=self.user
        )

        self.assertEqual(account.payment_ratio, 30.0)

    def test_supplier_account_update_status(self):
        """Test supplier account status update."""
        account = SupplierAccount.objects.create(
            supplier=self.supplier,
            invoice_amount=Decimal('10000.00'),
            balance=Decimal('10000.00'),
            created_by=self.user
        )

        # Initial status
        account.update_status()
        self.assertEqual(account.status, 'pending')

        # Partially paid
        account.paid_amount = Decimal('5000.00')
        account.balance = Decimal('5000.00')
        account.update_status()
        self.assertEqual(account.status, 'partially_paid')

        # Fully paid
        account.paid_amount = Decimal('10000.00')
        account.balance = Decimal('0.00')
        account.update_status()
        self.assertEqual(account.status, 'paid')

    def test_supplier_account_record_payment(self):
        """Test supplier account record payment."""
        account = SupplierAccount.objects.create(
            supplier=self.supplier,
            invoice_amount=Decimal('10000.00'),
            paid_amount=Decimal('0.00'),
            balance=Decimal('10000.00'),
            created_by=self.user
        )

        # Successful payment
        result = account.record_payment(Decimal('3000.00'))
        self.assertTrue(result)
        self.assertEqual(account.paid_amount, Decimal('3000.00'))
        self.assertEqual(account.balance, Decimal('7000.00'))
        self.assertEqual(account.status, 'partially_paid')

        # Invalid payment (negative)
        result = account.record_payment(Decimal('-100.00'))
        self.assertFalse(result)

        # Invalid payment (exceeds balance)
        result = account.record_payment(Decimal('10000.00'))
        self.assertFalse(result)


class PaymentModelTest(TestCase):
    """Test Payment model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.customer = Customer.objects.create(
            name='测试客户',
            code='CUS001',
            created_by=self.user
        )

        self.supplier = Supplier.objects.create(
            name='测试供应商',
            code='SUP001',
            created_by=self.user
        )

    def test_payment_creation_receipt(self):
        """Test payment creation for receipt."""
        payment = Payment.objects.create(
            payment_number='REC202511001',
            payment_type='receipt',
            payment_method='bank_transfer',
            customer=self.customer,
            amount=Decimal('5000.00'),
            payment_date=timezone.now().date(),
            created_by=self.user
        )

        self.assertEqual(payment.payment_type, 'receipt')
        self.assertEqual(payment.customer, self.customer)
        self.assertEqual(payment.amount, Decimal('5000.00'))
        self.assertEqual(payment.status, 'pending')

    def test_payment_creation_payment(self):
        """Test payment creation for payment."""
        payment = Payment.objects.create(
            payment_number='PAY202511001',
            payment_type='payment',
            payment_method='cash',
            supplier=self.supplier,
            amount=Decimal('3000.00'),
            payment_date=timezone.now().date(),
            created_by=self.user
        )

        self.assertEqual(payment.payment_type, 'payment')
        self.assertEqual(payment.supplier, self.supplier)
        self.assertEqual(payment.amount, Decimal('3000.00'))


class BudgetModelTest(TestCase):
    """Test Budget model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.department = Department.objects.create(
            name='销售部',
            code='SALES',
            created_by=self.user
        )

    def test_budget_creation(self):
        """Test budget creation."""
        budget = Budget.objects.create(
            budget_name='2025年销售部预算',
            budget_code='BUD2025001',
            budget_type='annual',
            fiscal_year=2025,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            department=self.department,
            created_by=self.user
        )

        self.assertEqual(budget.budget_code, 'BUD2025001')
        self.assertEqual(budget.status, 'draft')
        self.assertEqual(budget.department, self.department)


class BudgetLineModelTest(TestCase):
    """Test BudgetLine model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.department = Department.objects.create(
            name='销售部',
            code='SALES',
            created_by=self.user
        )

        self.budget = Budget.objects.create(
            budget_name='2025年销售部预算',
            budget_code='BUD2025001',
            budget_type='annual',
            fiscal_year=2025,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            department=self.department,
            created_by=self.user
        )

        self.account = Account.objects.create(
            code='6001',
            name='销售费用',
            account_type='expense',
            created_by=self.user
        )

    def test_budget_line_creation(self):
        """Test budget line creation."""
        line = BudgetLine.objects.create(
            budget=self.budget,
            account=self.account,
            budgeted_amount=Decimal('100000.00'),
            created_by=self.user
        )

        self.assertEqual(line.budget, self.budget)
        self.assertEqual(line.account, self.account)
        self.assertEqual(line.budgeted_amount, Decimal('100000.00'))

    def test_budget_line_variance(self):
        """Test budget line variance calculation."""
        line = BudgetLine.objects.create(
            budget=self.budget,
            account=self.account,
            budgeted_amount=Decimal('100000.00'),
            actual_amount=Decimal('95000.00'),
            created_by=self.user
        )

        self.assertEqual(line.variance, Decimal('-5000.00'))
        self.assertEqual(line.variance_percentage, -5.0)


class InvoiceModelTest(TestCase):
    """Test Invoice model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.supplier = Supplier.objects.create(
            name='测试供应商',
            code='SUP001',
            created_by=self.user
        )

        self.customer = Customer.objects.create(
            name='测试客户',
            code='CUS001',
            created_by=self.user
        )

    def test_purchase_invoice_creation(self):
        """Test purchase invoice creation."""
        invoice = Invoice.objects.create(
            invoice_number='INV202511001',
            invoice_type='purchase',
            invoice_code='123456',
            invoice_date=timezone.now().date(),
            supplier=self.supplier,
            amount_excluding_tax=Decimal('10000.00'),
            tax_rate=Decimal('13.00'),
            tax_amount=Decimal('1300.00'),
            total_amount=Decimal('11300.00'),
            created_by=self.user
        )

        self.assertEqual(invoice.invoice_type, 'purchase')
        self.assertEqual(invoice.supplier, self.supplier)
        self.assertEqual(invoice.total_amount, Decimal('11300.00'))
        self.assertEqual(invoice.status, 'draft')

    def test_sales_invoice_creation(self):
        """Test sales invoice creation."""
        invoice = Invoice.objects.create(
            invoice_number='INV202511002',
            invoice_type='sales',
            invoice_date=timezone.now().date(),
            customer=self.customer,
            amount_excluding_tax=Decimal('20000.00'),
            tax_rate=Decimal('13.00'),
            tax_amount=Decimal('2600.00'),
            total_amount=Decimal('22600.00'),
            created_by=self.user
        )

        self.assertEqual(invoice.invoice_type, 'sales')
        self.assertEqual(invoice.customer, self.customer)
        self.assertEqual(invoice.total_amount, Decimal('22600.00'))


class InvoiceItemModelTest(TestCase):
    """Test InvoiceItem model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

        self.supplier = Supplier.objects.create(
            name='测试供应商',
            code='SUP001',
            created_by=self.user
        )

        self.invoice = Invoice.objects.create(
            invoice_number='INV202511001',
            invoice_type='purchase',
            invoice_date=timezone.now().date(),
            supplier=self.supplier,
            created_by=self.user
        )

        self.category = ProductCategory.objects.create(
            name='测试分类',
            code='CAT001',
            created_by=self.user
        )

        self.unit = Unit.objects.create(
            name='件',
            symbol='pcs',
            created_by=self.user
        )

        self.product = Product.objects.create(
            name='测试产品',
            code='PROD001',
            category=self.category,
            unit=self.unit,
            created_by=self.user
        )

    def test_invoice_item_creation(self):
        """Test invoice item creation."""
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            description='测试产品',
            quantity=Decimal('10.00'),
            unit_price=Decimal('100.00'),
            tax_rate=Decimal('13.00'),
            created_by=self.user
        )

        # Amount should be calculated automatically
        self.assertEqual(item.amount, Decimal('1000.00'))
        self.assertEqual(item.tax_amount, Decimal('130.00'))

    def test_invoice_item_auto_calculation(self):
        """Test invoice item auto calculation on save."""
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            description='测试产品',
            quantity=Decimal('5.00'),
            unit_price=Decimal('200.00'),
            tax_rate=Decimal('13.00'),
            created_by=self.user
        )

        # Expected: 5 * 200 = 1000
        self.assertEqual(item.amount, Decimal('1000.00'))
        # Expected: 1000 * 0.13 = 130
        self.assertEqual(item.tax_amount, Decimal('130.00'))


class FinancialReportModelTest(TestCase):
    """Test FinancialReport model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )

    def test_balance_sheet_creation(self):
        """Test balance sheet creation."""
        report = FinancialReport.objects.create(
            report_type='balance_sheet',
            report_date=timezone.now().date(),
            report_data={'assets': {}, 'liabilities': {}, 'equity': {}},
            total_assets=Decimal('1000000.00'),
            total_liabilities=Decimal('600000.00'),
            total_equity=Decimal('400000.00'),
            generated_by=self.user,
            created_by=self.user
        )

        self.assertEqual(report.report_type, 'balance_sheet')
        self.assertEqual(report.total_assets, Decimal('1000000.00'))

    def test_income_statement_creation(self):
        """Test income statement creation."""
        report = FinancialReport.objects.create(
            report_type='income_statement',
            report_date=timezone.now().date(),
            start_date=timezone.now().date() - timedelta(days=30),
            end_date=timezone.now().date(),
            report_data={'revenue': {}, 'expenses': {}},
            net_profit=Decimal('50000.00'),
            generated_by=self.user,
            created_by=self.user
        )

        self.assertEqual(report.report_type, 'income_statement')
        self.assertEqual(report.net_profit, Decimal('50000.00'))
