"""
Finance app URLs.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, views_reports, views_expense

app_name = 'finance'

router = DefaultRouter()

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),

    # 会计科目
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/<int:pk>/', views.account_detail, name='account_detail'),

    # 凭证/分录
    path('journals/', views.journal_list, name='journal_list'),
    path('journals/<int:pk>/', views.journal_detail, name='journal_detail'),

    # 预算
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/<int:pk>/', views.budget_detail, name='budget_detail'),

    # Customer Accounts
    path('customer-accounts/', views.customer_account_list, name='customer_account_list'),
    path('customer-accounts/<int:pk>/', views.customer_account_detail, name='customer_account_detail'),
    path('customer-accounts/<int:pk>/writeoff/', views.customer_account_writeoff, name='customer_account_writeoff'),
    path('customer-accounts/<int:pk>/available-prepays/', views.api_customer_account_available_prepays, name='api_customer_account_available_prepays'),

    # Supplier Accounts
    path('supplier-accounts/', views.supplier_account_list, name='supplier_account_list'),
    path('supplier-accounts/<int:pk>/', views.supplier_account_detail, name='supplier_account_detail'),
    path('supplier-accounts/generate-from-invoice/<int:invoice_id>/', views.generate_supplier_account_from_invoice, name='generate_supplier_account_from_invoice'),
    path('supplier-accounts/<int:pk>/writeoff/', views.supplier_account_writeoff, name='supplier_account_writeoff'),
    path('supplier-accounts/<int:pk>/available-prepays/', views.api_supplier_account_available_prepays, name='api_supplier_account_available_prepays'),
    path('supplier-accounts/payment/', views.supplier_account_payment_list, name='supplier_account_payment_list'),
    path('supplier-accounts/payment/<int:pk>/allocate/', views.supplier_account_payment_allocate, name='supplier_account_payment_allocate'),

    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),

    # 收款记录
    path('payment-receipts/', views.payment_receipt_list, name='payment_receipt_list'),
    path('payment-receipts/create/', views.payment_receipt_create, name='payment_receipt_create'),
    path('payment-receipts/<int:pk>/', views.payment_receipt_detail, name='payment_receipt_detail'),
    path('payment-receipts/<int:pk>/edit/', views.payment_receipt_update, name='payment_receipt_update'),
    path('payment-receipts/<int:pk>/delete/', views.payment_receipt_delete, name='payment_receipt_delete'),
    path('payment-receipts/<int:pk>/cancel/', views.payment_receipt_cancel, name='payment_receipt_cancel'),

    # 付款记录
    path('payment-payments/', views.payment_payment_list, name='payment_payment_list'),
    path('payment-payments/create/', views.payment_payment_create, name='payment_payment_create'),
    path('payment-payments/<int:pk>/', views.payment_payment_detail, name='payment_payment_detail'),
    path('payment-payments/<int:pk>/edit/', views.payment_payment_update, name='payment_payment_update'),
    path('payment-payments/<int:pk>/delete/', views.payment_payment_delete, name='payment_payment_delete'),
    path('payment-payments/<int:pk>/cancel/', views.payment_payment_cancel, name='payment_payment_cancel'),

    # 发票
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('invoices/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('invoices/<int:pk>/verify/', views.invoice_verify, name='invoice_verify'),
    path('invoices/create-from-sales-order/<int:order_id>/', views.invoice_create_from_sales_order, name='invoice_create_from_sales_order'),

    # 税率
    path('tax-rates/', views.tax_rate_list, name='tax_rate_list'),
    path('tax-rates/create/', views.tax_rate_create, name='tax_rate_create'),
    path('tax-rates/<int:pk>/', views.tax_rate_detail, name='tax_rate_detail'),
    path('tax-rates/<int:pk>/edit/', views.tax_rate_update, name='tax_rate_update'),
    path('tax-rates/<int:pk>/delete/', views.tax_rate_delete, name='tax_rate_delete'),

    # 预收预付
    path('prepayments/customer/', views.customer_prepayment_list, name='customer_prepayment_list'),
    path('prepayments/customer/create/', views.customer_prepayment_create, name='customer_prepayment_create'),
    path('prepayments/customer/<int:pk>/edit/', views.customer_prepayment_edit, name='customer_prepayment_edit'),
    path('prepayments/customer/<int:pk>/delete/', views.customer_prepayment_delete, name='customer_prepayment_delete'),
    path('prepayments/customer/consolidate/<int:customer_id>/', views.customer_prepayment_consolidate, name='customer_prepayment_consolidate'),
    path('prepayments/supplier/', views.supplier_prepayment_list, name='supplier_prepayment_list'),
    path('prepayments/supplier/create/', views.supplier_prepayment_create, name='supplier_prepayment_create'),
    path('prepayments/supplier/manage/<int:supplier_id>/', views.supplier_prepayment_manage, name='supplier_prepayment_manage'),
    path('prepayments/supplier/<int:pk>/edit/', views.supplier_prepayment_edit, name='supplier_prepayment_edit'),
    path('prepayments/supplier/<int:pk>/delete/', views.supplier_prepayment_delete, name='supplier_prepayment_delete'),
    path('prepayments/supplier/consolidate/<int:supplier_id>/', views.supplier_prepayment_consolidate, name='supplier_prepayment_consolidate'),

    # 往来款项报表
    path('reports/accounts/', views.account_report, name='account_report'),

    # 费用管理
    path('expenses/', views_expense.expense_list, name='expense_list'),
    path('expenses/create/', views_expense.expense_create, name='expense_create'),
    path('expenses/<int:pk>/', views_expense.expense_detail, name='expense_detail'),
    path('expenses/<int:pk>/edit/', views_expense.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views_expense.expense_delete, name='expense_delete'),
    path('expenses/<int:pk>/submit/', views_expense.expense_submit, name='expense_submit'),
    path('expenses/<int:pk>/approve/', views_expense.expense_approve, name='expense_approve'),
    path('expenses/<int:pk>/reject/', views_expense.expense_reject, name='expense_reject'),
    path('expenses/<int:pk>/pay/', views_expense.expense_pay, name='expense_pay'),

    # 财务报表
    path('reports/', views_reports.financial_report_list, name='report_list'),
    path('reports/generator/', views_reports.financial_report_generator, name='report_generator'),
    path('reports/<int:pk>/', views_reports.financial_report_detail, name='report_detail'),

    # 财务报表生成器
    path('reports/generate/balance-sheet/', views_reports.generate_balance_sheet, name='generate_balance_sheet'),
    path('reports/generate/income-statement/', views_reports.generate_income_statement, name='generate_income_statement'),
    path('reports/generate/cash-flow/', views_reports.generate_cash_flow, name='generate_cash_flow'),
    path('reports/generate/trial-balance/', views_reports.generate_trial_balance, name='generate_trial_balance'),

    path('', include(router.urls)),
]