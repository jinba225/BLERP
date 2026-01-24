"""
Finance views for the ERP system.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP

from .models import (
    Account, Journal, JournalEntry, CustomerAccount,
    SupplierAccount, Payment, Budget, BudgetLine,
    Invoice, InvoiceItem, FinancialReport, TaxRate,
    CustomerPrepayment, SupplierPrepayment
)
from apps.customers.models import Customer
from apps.suppliers.models import Supplier


# 配置日志
logger = logging.getLogger(__name__)


# ==================== Helper Functions ====================

def _generate_supplier_account_from_invoice(invoice):
    """
    从采购发票生成应付账款。

    Args:
        invoice: Invoice对象 (必须是采购发票)

    Returns:
        tuple: (success: bool, account: SupplierAccount or None, error_message: str or None)
    """
    from datetime import timedelta

    try:
        # 验证发票类型
        if invoice.invoice_type != 'purchase':
            return False, None, '只能为采购发票生成应付账款'

        # 检查是否已生成
        if SupplierAccount.objects.filter(invoice=invoice, is_deleted=False).exists():
            return False, None, '该发票已生成应付账款'

        # 检查供应商
        if not invoice.supplier:
            return False, None, '发票缺少供应商信息'

        # 计算到期日期（默认30天账期）
        due_date = invoice.invoice_date + timedelta(days=30)
        if hasattr(invoice.supplier, 'payment_terms_days') and invoice.supplier.payment_terms_days:
            due_date = invoice.invoice_date + timedelta(days=invoice.supplier.payment_terms_days)

        # 创建应付账款
        account = SupplierAccount.objects.create(
            supplier=invoice.supplier,
            purchase_order=invoice.reference_type == 'purchase_order' and
                          invoice.reference_id and
                          PurchaseOrder.objects.filter(id=invoice.reference_id).first() or None,
            invoice=invoice,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            due_date=due_date,
            status='pending',
            invoice_amount=invoice.total_amount,
            paid_amount=0,
            balance=invoice.total_amount,
            currency=invoice.get('currency', 'CNY') if isinstance(invoice, dict) else 'CNY',
            notes=f'由发票 {invoice.invoice_number} 自动生成',
            created_by=invoice.created_by,
            updated_by=invoice.updated_by,
        )

        logger.info(
            f'Generated supplier account {account.id} from invoice {invoice.invoice_number}, '
            f'amount: {account.invoice_amount}'
        )

        return True, account, None

    except Exception as e:
        logger.exception(f'Error generating supplier account from invoice {invoice.invoice_number}: {str(e)}')
        return False, None, f'生成应付账款失败：{str(e)}'

def _prepare_invoice_items_from_order(order):
    """
    从订单明细准备发票明细的初始数据。

    适用于采购订单和销售订单。
    """
    from decimal import Decimal

    initial_items = []
    for item in order.items.all():
        initial_items.append({
            'product_id': item.product.id if item.product else '',
            'description': item.product.name if item.product else '',
            'specification': item.product.specifications if item.product else '',
            'unit': item.product.unit if item.product else '',
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'amount': item.line_total,
            'tax_rate': 13.00,  # 默认税率
            'tax_amount': item.line_total * Decimal('0.13'),
        })
    return initial_items


def _create_invoice_from_order_post(request, order, invoice_type, party_field):
    """
    从订单创建发票的通用POST处理逻辑。

    Args:
        request: Django request对象
        order: 订单对象（PurchaseOrder或SalesOrder）
        invoice_type: 'purchase' 或 'sales'
        party_field: 关联方字段名 ('supplier' 或 'customer')

    Returns:
        tuple: (success: bool, invoice: Invoice or None, error_message: str or None)
    """
    from apps.products.models import Product
    from apps.core.utils import DocumentNumberGenerator
    from decimal import Decimal, InvalidOperation

    logger.info(
        f'User {request.user.username} attempting to create {invoice_type} invoice from order {order.order_number}'
    )

    try:
        # 数据验证
        invoice_date = request.POST.get('invoice_date')
        if not invoice_date:
            logger.warning(f'Invoice creation failed: missing invoice_date')
            return False, None, '开票日期是必填项'

        try:
            tax_rate = Decimal(request.POST.get('tax_rate', '13.00'))
            if tax_rate < 0 or tax_rate > 100:
                logger.warning(f'Invoice creation failed: invalid tax_rate {tax_rate}')
                return False, None, '税率必须在0-100之间'
        except (InvalidOperation, ValueError):
            logger.warning(f'Invoice creation failed: invalid tax_rate format')
            return False, None, '税率格式无效'

        # 验证明细
        item_count = int(request.POST.get('item_count', 0))
        if item_count == 0:
            logger.warning(f'Invoice creation failed: no items')
            return False, None, '发票至少需要一个明细项'

        # 生成发票号
        invoice_number = DocumentNumberGenerator.generate('invoice')
        logger.debug(f'Generated invoice number: {invoice_number}')

        # 准备发票数据
        invoice_data = {
            'invoice_number': invoice_number,
            'invoice_type': invoice_type,
            'invoice_date': invoice_date,
            'tax_date': request.POST.get('tax_date') or None,
            'tax_rate': tax_rate,
            'invoice_code': request.POST.get('invoice_code', ''),
            'status': request.POST.get('status', 'draft'),
            'reference_number': order.order_number,
            'reference_type': f'{invoice_type}_order',
            'reference_id': order.id,
            'remark': request.POST.get('remark', ''),
            'created_by': request.user,
            'updated_by': request.user,
        }

        # 设置关联方（supplier或customer）
        party = getattr(order, party_field)
        if not party:
            logger.error(f'Order {order.id} missing {party_field}')
            return False, None, f'订单缺少{party_field}信息'
        invoice_data[party_field] = party

        # 创建发票
        invoice = Invoice.objects.create(**invoice_data)
        logger.info(f'Created invoice {invoice.invoice_number} (ID: {invoice.id})')

        # 处理附件
        if request.FILES.get('attachment'):
            invoice.attachment = request.FILES['attachment']
            invoice.save()
            logger.debug(f'Attachment uploaded for invoice {invoice.invoice_number}')

        # 创建发票明细
        items_created = 0
        for i in range(item_count):
            description = request.POST.get(f'item_{i}_description')
            if not description:
                continue

            try:
                quantity = Decimal(request.POST.get(f'item_{i}_quantity', '0'))
                unit_price = Decimal(request.POST.get(f'item_{i}_unit_price', '0'))
                item_tax_rate = Decimal(request.POST.get(f'item_{i}_tax_rate', '13'))

                if quantity <= 0:
                    raise ValueError(f'第{i+1}行：数量必须大于0')
                if unit_price < 0:
                    raise ValueError(f'第{i+1}行：单价不能为负数')

            except (InvalidOperation, ValueError) as e:
                # 如果出错，删除已创建的发票
                logger.error(f'Invoice item validation failed: {str(e)}, rolling back invoice {invoice.invoice_number}')
                invoice.delete()
                return False, None, str(e)

            product_id = request.POST.get(f'item_{i}_product')
            product = Product.objects.get(pk=product_id) if product_id else None

            InvoiceItem.objects.create(
                invoice=invoice,
                product=product,
                description=description,
                specification=request.POST.get(f'item_{i}_specification', ''),
                unit=request.POST.get(f'item_{i}_unit', ''),
                quantity=quantity,
                unit_price=unit_price,
                tax_rate=item_tax_rate,
                created_by=request.user,
                updated_by=request.user,
            )
            items_created += 1

        logger.info(f'Created {items_created} items for invoice {invoice.invoice_number}')

        # 检查是否至少创建了一条明细
        if items_created == 0:
            logger.warning(f'No valid items created for invoice {invoice.invoice_number}, rolling back')
            invoice.delete()
            return False, None, '必须至少有一条有效的发票明细'

        # 计算发票总额
        invoice.calculate_totals()
        invoice.save()
        logger.info(
            f'Invoice {invoice.invoice_number} completed: total={invoice.total_amount}, tax={invoice.tax_amount}'
        )

        return True, invoice, None

    except Product.DoesNotExist:
        logger.error(f'Product not found during invoice creation')
        return False, None, '指定的产品不存在'
    except Exception as e:
        logger.exception(f'Unexpected error creating invoice from order {order.order_number}: {str(e)}')
        return False, None, f'创建发票时发生错误：{str(e)}'


# ==================== Views ====================


@login_required
def account_list(request):
    """
    List all chart of accounts with search and filter capabilities.
    """
    accounts = Account.objects.filter(is_deleted=False).select_related('parent')

    # Search
    search = request.GET.get('search', '')
    if search:
        accounts = accounts.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    # Filter by account type
    account_type = request.GET.get('account_type', '')
    if account_type:
        accounts = accounts.filter(account_type=account_type)

    # Filter by active status
    is_active = request.GET.get('is_active', '')
    if is_active:
        accounts = accounts.filter(is_active=is_active == 'true')

    # Sorting
    sort = request.GET.get('sort', 'code')
    accounts = accounts.order_by(sort)

    # Pagination
    paginator = Paginator(accounts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'account_type': account_type,
        'is_active': is_active,
        'total_count': paginator.count,
    }
    return render(request, 'finance/account_list.html', context)


@login_required
def account_detail(request, pk):
    """
    Display account details and transaction history.
    """
    account = get_object_or_404(
        Account.objects.filter(is_deleted=False).select_related('parent'),
        pk=pk
    )

    # Get journal entries for this account
    entries = JournalEntry.objects.filter(
        account=account
    ).select_related('journal').order_by('-journal__journal_date')[:50]

    context = {
        'account': account,
        'entries': entries,
    }
    return render(request, 'finance/account_detail.html', context)


@login_required
def journal_list(request):
    """
    List all journals/vouchers with search and filter capabilities.
    """
    journals = Journal.objects.filter(is_deleted=False).select_related(
        'prepared_by', 'reviewed_by', 'posted_by'
    ).prefetch_related('entries')

    # Search
    search = request.GET.get('search', '')
    if search:
        journals = journals.filter(
            Q(journal_number__icontains=search) |
            Q(description__icontains=search)
        )

    # Filter by journal type
    journal_type = request.GET.get('journal_type', '')
    if journal_type:
        journals = journals.filter(journal_type=journal_type)

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        journals = journals.filter(status=status)

    # Filter by period
    period = request.GET.get('period', '')
    if period:
        journals = journals.filter(period=period)

    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        journals = journals.filter(journal_date__gte=date_from)
    if date_to:
        journals = journals.filter(journal_date__lte=date_to)

    # Sorting - 按创建时间降序（最新的在最上面）
    sort = request.GET.get('sort', '-created_at')
    journals = journals.order_by(sort)

    # Pagination
    paginator = Paginator(journals, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'journal_type': journal_type,
        'status': status,
        'period': period,
        'date_from': date_from,
        'date_to': date_to,
        'total_count': paginator.count,
    }
    return render(request, 'finance/journal_list.html', context)


@login_required
def journal_detail(request, pk):
    """
    Display journal details with all entries.
    """
    journal = get_object_or_404(
        Journal.objects.filter(is_deleted=False).select_related(
            'prepared_by', 'reviewed_by', 'posted_by'
        ).prefetch_related('entries__account'),
        pk=pk
    )

    context = {
        'journal': journal,
    }
    return render(request, 'finance/journal_detail.html', context)


@login_required
def customer_account_list(request):
    """
    List all customer accounts receivable.
    """
    accounts = CustomerAccount.objects.filter(
        is_deleted=False
    ).select_related('customer', 'sales_order')

    # Search
    search = request.GET.get('search', '')
    if search:
        accounts = accounts.filter(
            Q(customer__name__icontains=search) |
            Q(invoice_number__icontains=search)
        )

    # Filter by customer
    customer_id = request.GET.get('customer', '')
    if customer_id:
        accounts = accounts.filter(customer_id=customer_id)

    # Filter by overdue
    is_overdue = request.GET.get('is_overdue', '')
    if is_overdue == 'true':
        accounts = accounts.filter(due_date__lt=timezone.now().date(), balance__gt=0)

    # Sorting - 按创建时间降序（最新的在最上面）
    sort = request.GET.get('sort', '-created_at')
    accounts = accounts.order_by(sort)

    # Pagination
    paginator = Paginator(accounts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate totals
    totals = accounts.aggregate(
        total_invoice=Sum('invoice_amount'),
        total_paid=Sum('paid_amount'),
        total_balance=Sum('balance')
    )

    # Get customers for filter dropdown
    from apps.customers.models import Customer
    customers = Customer.objects.filter(is_deleted=False, status='active')

    context = {
        'page_obj': page_obj,
        'search': search,
        'customer_id': customer_id,
        'is_overdue': is_overdue,
        'total_count': paginator.count,
        'totals': totals,
        'customers': customers,
    }
    return render(request, 'finance/customer_account_list.html', context)

@login_required
def customer_account_detail(request, pk):
    account = get_object_or_404(
        CustomerAccount.objects.filter(is_deleted=False).select_related('customer', 'sales_order'),
        pk=pk
    )

    payments = Payment.objects.filter(
        is_deleted=False,
        payment_type='receipt',
        reference_type='customer_account',
        reference_id=str(account.id)
    ).order_by('-payment_date')

    # Recalculate paid amount from payments to ensure consistency
    try:
        total_paid = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_paid = Decimal(total_paid).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
        expected_balance = (account.invoice_amount - total_paid).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

        if account.paid_amount != total_paid or account.balance != expected_balance:
            account.paid_amount = total_paid
            account.balance = expected_balance if expected_balance > Decimal('0.00') else Decimal('0.00')
            account.save(update_fields=['paid_amount', 'balance', 'updated_at'])
    except Exception:
        pass

    paid_total = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    from django.utils import timezone
    return render(request, 'finance/customer_account_detail.html', {
        'account': account,
        'payments': payments,
        'paid_total': paid_total,
        'today': timezone.now().date(),
    })


@login_required
def supplier_account_list(request):
    """
    List all supplier accounts payable.
    """
    accounts = SupplierAccount.objects.filter(
        is_deleted=False
    ).select_related('supplier', 'purchase_order', 'invoice')

    # Search
    search = request.GET.get('search', '')
    if search:
        accounts = accounts.filter(
            Q(supplier__name__icontains=search) |
            Q(invoice_number__icontains=search)
        )

    # Filter by supplier
    supplier_id = request.GET.get('supplier', '')
    if supplier_id:
        accounts = accounts.filter(supplier_id=supplier_id)

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        accounts = accounts.filter(status=status)

    # Filter by overdue
    is_overdue = request.GET.get('is_overdue', '')
    if is_overdue == 'true':
        accounts = accounts.filter(due_date__lt=timezone.now().date(), balance__gt=0)

    # Sorting - 按创建时间降序（最新创建的在最上面）
    sort = request.GET.get('sort', '-created_at')
    accounts = accounts.order_by(sort)

    # Pagination
    paginator = Paginator(accounts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate totals
    totals = accounts.aggregate(
        total_invoice=Sum('invoice_amount'),
        total_paid=Sum('paid_amount'),
        total_balance=Sum('balance')
    )

    context = {
        'page_obj': page_obj,
        'search': search,
        'supplier_id': supplier_id,
        'status': status,
        'is_overdue': is_overdue,
        'total_count': paginator.count,
        'totals': totals,
        'status_choices': SupplierAccount.ACCOUNT_STATUS,
    }
    return render(request, 'finance/supplier_account_list.html', context)


@login_required
def supplier_account_detail(request, pk):
    """
    Display supplier account payable details.
    """
    account = get_object_or_404(
        SupplierAccount.objects.filter(is_deleted=False).select_related(
            'supplier', 'purchase_order', 'invoice', 'created_by', 'updated_by'
        ),
        pk=pk
    )

    # Get related payments
    related_payments = Payment.objects.filter(
        is_deleted=False,
        payment_type='payment',
        supplier=account.supplier,
        reference_type='supplier_account',
        reference_id=str(account.id)
    ).order_by('-payment_date')

    context = {
        'account': account,
        'related_payments': related_payments,
    }
    return render(request, 'finance/supplier_account_detail.html', context)

@login_required
def customer_account_writeoff(request, pk):
    """应收核销：将预收款或现金收款核销到应收账款"""
    account = get_object_or_404(CustomerAccount, pk=pk, is_deleted=False)

    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', '0') or '0')
        prepay_id = request.POST.get('prepayment')
        payment_method = request.POST.get('payment_method')
        payment_date = request.POST.get('payment_date')
        notes = request.POST.get('notes', '')

        if amount < 0:
            messages.error(request, '收款金额无效')
            return redirect('finance:customer_account_detail', pk=pk)

        effective_prepay_amount = Decimal('0')
        if prepay_id:
            prepay = CustomerPrepayment.objects.filter(pk=prepay_id, is_deleted=False).first()
            if not prepay:
                messages.error(request, '预收款不存在或已删除')
                return redirect('finance:customer_account_detail', pk=pk)
            max_use = (account.balance - amount)
            if max_use < 0:
                max_use = Decimal('0')
            effective_prepay_amount = min(prepay.balance, max_use)
            if effective_prepay_amount > 0:
                prepay.balance -= effective_prepay_amount
                prepay.save()

        total_offset = (effective_prepay_amount + amount).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
        if total_offset <= Decimal('0.00') or total_offset > account.balance:
            messages.error(request, '核销总额无效')
            return redirect('finance:customer_account_detail', pk=pk)

        # ============ 第一步：在独立事务中生成唯一的付款单号 ============
        # 这样可以避免在主事务中发生 IntegrityError 后无法继续查询的问题
        payment_numbers = []

        def generate_unique_payment_number(prefix_key):
            """生成唯一的付款单号（带重试机制）"""
            from apps.core.utils import DocumentNumberGenerator
            from django.db import transaction, IntegrityError

            max_retries = 5
            for attempt in range(max_retries):
                # 使用独立的事务来验证单号唯一性
                try:
                    with transaction.atomic(savepoint=False):
                        payment_number = DocumentNumberGenerator.generate(prefix_key)
                        # 创建占位记录来验证单号唯一性
                        placeholder = Payment.objects.create(
                            payment_number=payment_number,
                            payment_type='receipt',
                            payment_method='other',
                            status='pending',
                            amount=Decimal('0'),
                            currency='CNY',
                            payment_date=timezone.now().date(),
                            description='PLACEHOLDER',
                            created_by=request.user
                        )
                        # 立即硬删除占位记录（只用于验证单号唯一性）
                        placeholder.hard_delete()
                    return payment_number
                except IntegrityError:
                    # 单号冲突，继续尝试下一个
                    continue
            raise Exception(f'生成付款单号失败：已尝试 {max_retries} 次')

        # 生成预收款冲抵的单号
        if prepay_id and effective_prepay_amount > 0:
            try:
                payment_numbers.append(generate_unique_payment_number('payment_receipt'))
            except Exception as e:
                messages.error(request, f'生成预收款单号失败：{str(e)}')
                return redirect('finance:customer_account_detail', pk=pk)

        # 生成现金收款的的单号
        if amount > 0:
            try:
                payment_numbers.append(generate_unique_payment_number('payment_receipt'))
            except Exception as e:
                messages.error(request, f'生成收款单号失败：{str(e)}')
                return redirect('finance:customer_account_detail', pk=pk)

        # ============ 第二步：在主事务中使用已生成的单号 ============
        try:
            with transaction.atomic():
                payment_number_index = 0

                # 创建预收款冲抵的付款记录
                if prepay_id and effective_prepay_amount > 0:
                    Payment.objects.create(
                        payment_number=payment_numbers[payment_number_index],
                        payment_type='receipt',
                        payment_method='other',
                        status='completed',
                        customer=account.customer,
                        amount=effective_prepay_amount,
                        currency=account.currency,
                        payment_date=payment_date or timezone.now().date(),
                        reference_type='customer_account',
                        reference_id=str(account.id),
                        reference_number=account.invoice_number or '',
                        description='预收款冲抵',
                        notes=notes,
                        processed_by=request.user,
                        created_by=request.user,
                    )
                    payment_number_index += 1

                # 创建现金收款的付款记录
                cash_amount = amount
                if cash_amount > 0:
                    if not payment_method:
                        messages.error(request, '请选择收款方式')
                        return redirect('finance:customer_account_detail', pk=pk)

                    Payment.objects.create(
                        payment_number=payment_numbers[payment_number_index],
                        payment_type='receipt',
                        payment_method=payment_method or 'bank_transfer',
                        status='completed',
                        customer=account.customer,
                        amount=cash_amount,
                        currency=account.currency,
                        payment_date=payment_date or timezone.now().date(),
                        reference_type='customer_account',
                        reference_id=str(account.id),
                        reference_number=account.invoice_number or '',
                        description='应收核销',
                        notes=notes,
                        processed_by=request.user,
                        created_by=request.user,
                    )

                # 更新应收账款（处理进位误差，确保结清时置零）
                paid = (account.paid_amount + total_offset).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
                remaining = (account.invoice_amount - paid).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
                if remaining <= Decimal('0.00'):
                    account.paid_amount = account.invoice_amount.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
                    account.balance = Decimal('0.00')
                else:
                    account.paid_amount = paid
                    account.balance = remaining
                account.notes = (account.notes or '')
                if notes:
                    account.notes += f"\n[{timezone.now().strftime('%Y-%m-%d')}] 核销 {amount}：{notes}"
                account.save()

                # 同步更新关联销售订单的付款状态
                if account.sales_order_id:
                    from apps.sales.models import SalesOrder
                    order = SalesOrder.objects.filter(pk=account.sales_order_id, is_deleted=False).first()
                    if order:
                        qs = CustomerAccount.objects.filter(sales_order_id=order.id, is_deleted=False)
                        agg = qs.aggregate(
                            total_invoice=Sum('invoice_amount'),
                            total_paid=Sum('paid_amount'),
                            total_balance=Sum('balance')
                        )
                        total_invoice = agg['total_invoice'] or Decimal('0.00')
                        total_paid = (agg['total_paid'] or Decimal('0.00')).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
                        total_balance = (agg['total_balance'] or Decimal('0.00')).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

                        # 逾期判定
                        any_overdue = qs.filter(due_date__lt=timezone.now().date(), balance__gt=0).exists()

                        if total_balance <= Decimal('0.00') and total_invoice > 0:
                            order.payment_status = 'paid'
                        elif any_overdue:
                            order.payment_status = 'overdue'
                        elif total_paid > Decimal('0.00'):
                            order.payment_status = 'partial'
                        else:
                            order.payment_status = 'unpaid'

                        order.save(update_fields=['payment_status'])

            messages.success(request, '应收核销完成')
            return redirect('finance:customer_account_detail', pk=pk)

        except Exception as e:
            messages.error(request, f'创建收款记录失败：{str(e)}')
            return redirect('finance:customer_account_detail', pk=pk)

    prepays = CustomerPrepayment.objects.filter(customer=account.customer, is_deleted=False, balance__gt=0)
    return render(request, 'finance/customer_account_writeoff.html', {
        'account': account,
        'prepays': prepays,
        'payment_methods': Payment.PAYMENT_METHODS,
    })

@login_required
def supplier_account_writeoff(request, pk):
    """应付核销：将预付款或现金付款核销到应付账款"""
    account = get_object_or_404(SupplierAccount, pk=pk, is_deleted=False)

    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', '0') or '0')
        prepay_id = request.POST.get('prepayment')
        payment_method = request.POST.get('payment_method')
        payment_date = request.POST.get('payment_date')
        invoice_number = request.POST.get('invoice_number', '').strip()
        notes = request.POST.get('notes', '')

        if amount < 0:
            messages.error(request, '付款金额无效')
            return redirect('finance:supplier_account_detail', pk=pk)

        effective_prepay_amount = Decimal('0')
        if prepay_id:
            prepay = SupplierPrepayment.objects.filter(pk=prepay_id, is_deleted=False).first()
            if not prepay:
                messages.error(request, '预付款不存在或已删除')
                return redirect('finance:supplier_account_detail', pk=pk)
            max_use = (account.balance - amount)
            if max_use < 0:
                max_use = Decimal('0')
            effective_prepay_amount = min(prepay.balance, max_use)
            if effective_prepay_amount > 0:
                prepay.balance -= effective_prepay_amount
                prepay.save()

        total_offset = (effective_prepay_amount + amount).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
        if total_offset <= Decimal('0.00') or total_offset > account.balance:
            messages.error(request, '核销总额无效')
            return redirect('finance:supplier_account_detail', pk=pk)

        # ============ 第一步：在独立事务中生成唯一的付款单号 ============
        payment_numbers = []

        def generate_unique_payment_number(prefix_key):
            """生成唯一的付款单号（带重试机制）"""
            from apps.core.utils import DocumentNumberGenerator
            from django.db import transaction, IntegrityError

            max_retries = 5
            for attempt in range(max_retries):
                try:
                    with transaction.atomic(savepoint=False):
                        payment_number = DocumentNumberGenerator.generate(prefix_key)
                        # 创建占位记录来验证单号唯一性
                        placeholder = Payment.objects.create(
                            payment_number=payment_number,
                            payment_type='payment',
                            payment_method='other',
                            status='pending',
                            amount=Decimal('0'),
                            currency='CNY',
                            payment_date=timezone.now().date(),
                            description='PLACEHOLDER',
                            created_by=request.user
                        )
                        # 立即硬删除占位记录（只用于验证单号唯一性）
                        placeholder.hard_delete()
                    return payment_number
                except IntegrityError:
                    continue
            raise Exception(f'生成付款单号失败：已尝试 {max_retries} 次')

        # 生成预付款冲抵的单号
        if prepay_id and effective_prepay_amount > 0:
            try:
                payment_numbers.append(generate_unique_payment_number('payment'))
            except Exception as e:
                messages.error(request, f'生成预付款单号失败：{str(e)}')
                return redirect('finance:supplier_account_detail', pk=pk)

        # 生成现金付款的单号
        if amount > 0:
            try:
                payment_numbers.append(generate_unique_payment_number('payment'))
            except Exception as e:
                messages.error(request, f'生成付款单号失败：{str(e)}')
                return redirect('finance:supplier_account_detail', pk=pk)

        # ============ 第二步：在主事务中使用已生成的单号 ============
        try:
            with transaction.atomic():
                payment_number_index = 0

                # 创建预付款冲抵的付款记录
                if prepay_id and effective_prepay_amount > 0:
                    Payment.objects.create(
                        payment_number=payment_numbers[payment_number_index],
                        payment_type='payment',
                        payment_method='other',
                        status='completed',
                        supplier=account.supplier if account.supplier else None,
                        customer=account.customer if account.customer else None,
                        amount=effective_prepay_amount,
                        currency=account.currency,
                        payment_date=payment_date or timezone.now().date(),
                        reference_type='supplier_account',
                        reference_id=str(account.id),
                        reference_number=account.invoice_number or '',
                        description='预付款冲抵',
                        notes=notes,
                        processed_by=request.user,
                        created_by=request.user,
                    )
                    payment_number_index += 1

                # 创建现金付款的付款记录
                cash_amount = amount
                if cash_amount > 0:
                    if not payment_method:
                        messages.error(request, '请选择付款方式')
                        return redirect('finance:supplier_account_detail', pk=pk)

                    Payment.objects.create(
                        payment_number=payment_numbers[payment_number_index],
                        payment_type='payment',
                        payment_method=payment_method or 'bank_transfer',
                        status='completed',
                        supplier=account.supplier if account.supplier else None,
                        customer=account.customer if account.customer else None,
                        amount=cash_amount,
                        currency=account.currency,
                        payment_date=payment_date or timezone.now().date(),
                        reference_type='supplier_account',
                        reference_id=str(account.id),
                        reference_number=account.invoice_number or '',
                        description='应付核销',
                        notes=notes,
                        processed_by=request.user,
                        created_by=request.user,
                    )

                # 更新应付账款（处理进位误差，确保结清时置零）
                paid = (account.paid_amount + total_offset).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
                remaining = (account.invoice_amount - paid).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
                if remaining <= Decimal('0.00'):
                    account.paid_amount = account.invoice_amount.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
                    account.balance = Decimal('0.00')
                else:
                    account.paid_amount = paid
                    account.balance = remaining

                # 更新发票号（如果提供）
                invoice_updated = False
                if invoice_number and invoice_number != account.invoice_number:
                    account.invoice_number = invoice_number
                    invoice_updated = True

                # 更新备注
                account.notes = (account.notes or '')
                if notes:
                    account.notes += f"\n[{timezone.now().strftime('%Y-%m-%d')}] 核销 {amount}：{notes}"

                # 更新状态
                if hasattr(account, 'update_status'):
                    account.update_status()
                account.save()

                # 同步更新采购订单的付款状态
                if account.purchase_order_id:
                    from apps.purchase.models import PurchaseOrder
                    order = PurchaseOrder.objects.filter(pk=account.purchase_order_id, is_deleted=False).first()
                    if order:
                        qs = SupplierAccount.objects.filter(purchase_order_id=order.id, is_deleted=False)
                        agg = qs.aggregate(
                            total_invoice=Sum('invoice_amount'),
                            total_paid=Sum('paid_amount')
                        )
                        total_invoice = agg.get('total_invoice') or Decimal('0')
                        total_paid = agg.get('total_paid') or Decimal('0')

                        if total_paid >= total_invoice and total_invoice > 0:
                            order.payment_status = 'paid'
                        elif total_paid > 0:
                            order.payment_status = 'partial'
                        else:
                            order.payment_status = 'unpaid'

                        # 更新发票状态（如果提供了发票号）
                        if invoice_updated and invoice_number:
                            order.status = 'invoiced'
                            order.save(update_fields=['payment_status', 'status'])
                        else:
                            order.save(update_fields=['payment_status'])

            messages.success(request, f'应付核销完成，已付款 ¥{total_offset}')
            return redirect('finance:supplier_account_detail', pk=pk)

        except Exception as e:
            messages.error(request, f'创建付款记录失败：{str(e)}')
            return redirect('finance:supplier_account_detail', pk=pk)

    # GET request - 显示核销表单
    prepays = []
    if account.supplier:
        prepays = SupplierPrepayment.objects.filter(
            supplier=account.supplier,
            is_deleted=False,
            balance__gt=0
        ).order_by('-created_at')

    context = {
        'account': account,
        'prepays': prepays,
    }
    return render(request, 'finance/supplier_account_writeoff.html', context)

@login_required
def customer_prepayment_list(request):
    prepays = CustomerPrepayment.objects.filter(is_deleted=False)
    paginator = Paginator(prepays, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'finance/customer_prepayment_list.html', {'page_obj': page_obj})

@login_required
@transaction.atomic
def customer_prepayment_create(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        amount = Decimal(request.POST.get('amount', '0'))
        date = request.POST.get('received_date')
        CustomerPrepayment.objects.create(
            customer_id=customer_id,
            amount=amount,
            balance=amount,
            received_date=date,
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        messages.success(request, '预收款创建成功')
        return redirect('finance:customer_prepayment_list')
    customers = Customer.objects.filter(is_deleted=False)
    return render(request, 'finance/customer_prepayment_form.html', {'customers': customers})

@login_required
def supplier_prepayment_list(request):
    prepays = SupplierPrepayment.objects.filter(is_deleted=False)
    paginator = Paginator(prepays, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'finance/supplier_prepayment_list.html', {'page_obj': page_obj})

@login_required
@transaction.atomic
def supplier_prepayment_create(request):
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        amount = Decimal(request.POST.get('amount', '0'))
        date = request.POST.get('paid_date')
        SupplierPrepayment.objects.create(
            supplier_id=supplier_id,
            amount=amount,
            balance=amount,
            paid_date=date,
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        messages.success(request, '预付款创建成功')
        return redirect('finance:supplier_prepayment_list')
    suppliers = Supplier.objects.filter(is_deleted=False)
    return render(request, 'finance/supplier_prepayment_form.html', {'suppliers': suppliers})


@login_required
@transaction.atomic
def generate_supplier_account_from_invoice(request, invoice_id):
    """
    手动从发票生成应付账款。
    """
    invoice = get_object_or_404(
        Invoice.objects.filter(is_deleted=False),
        pk=invoice_id
    )

    if request.method == 'POST':
        success, account, error = _generate_supplier_account_from_invoice(invoice)

        if success:
            messages.success(
                request,
                f'成功为发票 {invoice.invoice_number} 生成应付账款！'
                f'应付金额：¥{account.invoice_amount}，到期日期：{account.due_date}'
            )
            return redirect('finance:supplier_account_detail', pk=account.pk)
        else:
            messages.error(request, error)
            return redirect('finance:invoice_detail', pk=invoice_id)

    # GET request - show confirmation page
    context = {
        'invoice': invoice,
    }
    return render(request, 'finance/confirm_generate_supplier_account.html', context)


@login_required
def payment_list(request):
    """
    List all payments.
    """
    payments = Payment.objects.filter(is_deleted=False).select_related(
        'customer', 'supplier', 'processed_by'
    )

    # Search
    search = request.GET.get('search', '')
    if search:
        payments = payments.filter(
            Q(payment_number__icontains=search) |
            Q(reference_number__icontains=search)
        )

    # Filter by payment type
    payment_type = request.GET.get('payment_type', '')
    if payment_type:
        payments = payments.filter(payment_type=payment_type)

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        payments = payments.filter(status=status)

    # Filter by payment method
    payment_method = request.GET.get('payment_method', '')
    if payment_method:
        payments = payments.filter(payment_method=payment_method)

    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)

    # Sorting - 按创建时间降序（最新的在最上面）
    sort = request.GET.get('sort', '-created_at')
    payments = payments.order_by(sort)

    # Pagination
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate totals
    totals = payments.aggregate(
        total_amount=Sum('amount')
    )

    context = {
        'page_obj': page_obj,
        'search': search,
        'payment_type': payment_type,
        'status': status,
        'payment_method': payment_method,
        'date_from': date_from,
        'date_to': date_to,
        'total_count': paginator.count,
        'totals': totals,
    }
    return render(request, 'finance/payment_list.html', context)


@login_required
def payment_detail(request, pk):
    """
    Display payment details.
    """
    payment = get_object_or_404(
        Payment.objects.filter(is_deleted=False).select_related(
            'customer', 'supplier', 'processed_by'
        ),
        pk=pk
    )

    context = {
        'payment': payment,
    }
    return render(request, 'finance/payment_detail.html', context)


@login_required
def budget_list(request):
    """
    List all budgets.
    """
    budgets = Budget.objects.filter(is_deleted=False).select_related(
        'department', 'created_by'
    ).prefetch_related('lines')

    # Search
    search = request.GET.get('search', '')
    if search:
        budgets = budgets.filter(
            Q(name__icontains=search) |
            Q(budget_code__icontains=search)
        )

    # Filter by department
    department_id = request.GET.get('department', '')
    if department_id:
        budgets = budgets.filter(department_id=department_id)

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        budgets = budgets.filter(status=status)

    # Filter by fiscal year
    fiscal_year = request.GET.get('fiscal_year', '')
    if fiscal_year:
        budgets = budgets.filter(fiscal_year=fiscal_year)

    # Sorting
    sort = request.GET.get('sort', '-fiscal_year')
    budgets = budgets.order_by(sort)

    # Pagination
    paginator = Paginator(budgets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'department_id': department_id,
        'status': status,
        'fiscal_year': fiscal_year,
        'total_count': paginator.count,
    }
    return render(request, 'finance/budget_list.html', context)


@login_required
def budget_detail(request, pk):
    """
    Display budget details with all budget lines.
    """
    budget = get_object_or_404(
        Budget.objects.filter(is_deleted=False).select_related(
            'department', 'created_by'
        ).prefetch_related('lines__account'),
        pk=pk
    )

    context = {
        'budget': budget,
    }
    return render(request, 'finance/budget_detail.html', context)


@login_required
def dashboard(request):
    """
    Finance dashboard with key metrics and summary.
    """
    # Get key metrics
    total_receivables = CustomerAccount.objects.filter(
        is_deleted=False
    ).aggregate(total=Sum('balance'))['total'] or Decimal('0')

    total_payables = SupplierAccount.objects.filter(
        is_deleted=False
    ).aggregate(total=Sum('balance'))['total'] or Decimal('0')

    # Overdue accounts
    overdue_receivables = CustomerAccount.objects.filter(
        is_deleted=False,
        due_date__lt=timezone.now().date(),
        balance__gt=0
    ).count()

    overdue_payables = SupplierAccount.objects.filter(
        is_deleted=False,
        due_date__lt=timezone.now().date(),
        balance__gt=0
    ).count()

    # Recent journals
    recent_journals = Journal.objects.filter(
        is_deleted=False
    ).order_by('-journal_date')[:10]

    # Recent payments
    recent_payments = Payment.objects.filter(
        is_deleted=False
    ).order_by('-payment_date')[:10]

    context = {
        'total_receivables': total_receivables,
        'total_payables': total_payables,
        'overdue_receivables': overdue_receivables,
        'overdue_payables': overdue_payables,
        'recent_journals': recent_journals,
        'recent_payments': recent_payments,
    }
    return render(request, 'finance/dashboard.html', context)


# ==================== Invoice Management ====================

@login_required
def invoice_list(request):
    """
    List all invoices with search and filter capabilities.
    """
    invoices = Invoice.objects.filter(is_deleted=False).select_related(
        'supplier', 'customer', 'created_by'
    ).prefetch_related('items')

    # Search
    search = request.GET.get('search', '')
    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search) |
            Q(invoice_code__icontains=search) |
            Q(reference_number__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(supplier__name__icontains=search)
        )

    # Filter by invoice type
    invoice_type = request.GET.get('invoice_type', '')
    if invoice_type:
        invoices = invoices.filter(invoice_type=invoice_type)

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        invoices = invoices.filter(status=status)

    # Filter by customer
    customer_id = request.GET.get('customer', '')
    if customer_id:
        invoices = invoices.filter(customer_id=customer_id)

    # Filter by supplier
    supplier_id = request.GET.get('supplier', '')
    if supplier_id:
        invoices = invoices.filter(supplier_id=supplier_id)

    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        invoices = invoices.filter(invoice_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(invoice_date__lte=date_to)

    # Sorting - 按创建时间降序（最新的在最上面）
    sort = request.GET.get('sort', '-created_at')
    invoices = invoices.order_by(sort)

    # Pagination
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate totals
    totals = invoices.aggregate(
        total_amount=Sum('total_amount'),
        total_tax=Sum('tax_amount'),
        total_excluding_tax=Sum('amount_excluding_tax')
    )

    context = {
        'page_obj': page_obj,
        'search': search,
        'invoice_type': invoice_type,
        'status': status,
        'customer_id': customer_id,
        'supplier_id': supplier_id,
        'date_from': date_from,
        'date_to': date_to,
        'total_count': paginator.count,
        'totals': totals,
        'invoice_type_choices': Invoice.INVOICE_TYPES,
        'status_choices': Invoice.INVOICE_STATUS,
    }
    return render(request, 'finance/invoice_list.html', context)


@login_required
def invoice_detail(request, pk):
    """
    Display invoice details with all items.
    """
    invoice = get_object_or_404(
        Invoice.objects.filter(is_deleted=False).select_related(
            'supplier', 'customer', 'created_by', 'updated_by'
        ).prefetch_related('items__product'),
        pk=pk
    )

    context = {
        'invoice': invoice,
    }
    return render(request, 'finance/invoice_detail.html', context)


@login_required
@transaction.atomic
def invoice_create(request):
    """
    Create a new invoice.
    """
    if request.method == 'POST':
        try:
            # Generate invoice number
            from apps.core.utils import DocumentNumberGenerator
            invoice_number = DocumentNumberGenerator.generate('invoice')

            # Create invoice
            invoice = Invoice.objects.create(
                invoice_number=invoice_number,
                invoice_code=request.POST.get('invoice_code', ''),
                invoice_type=request.POST.get('invoice_type'),
                status=request.POST.get('status', 'draft'),
                invoice_date=request.POST.get('invoice_date'),
                tax_date=request.POST.get('tax_date') or None,
                tax_rate=Decimal(request.POST.get('tax_rate', '13')),
                reference_type=request.POST.get('reference_type', ''),
                reference_id=request.POST.get('reference_id', ''),
                reference_number=request.POST.get('reference_number', ''),
                remark=request.POST.get('remark', ''),
                created_by=request.user,
                updated_by=request.user,
            )

            # Set supplier or customer based on invoice type
            if invoice.invoice_type == 'purchase':
                supplier_id = request.POST.get('supplier')
                if supplier_id:
                    invoice.supplier_id = supplier_id
            else:  # sales
                customer_id = request.POST.get('customer')
                if customer_id:
                    invoice.customer_id = customer_id

            invoice.save()

            # Handle invoice items
            item_count = int(request.POST.get('item_count', 0))
            for i in range(item_count):
                product_id = request.POST.get(f'item_{i}_product')
                description = request.POST.get(f'item_{i}_description', '')
                quantity = request.POST.get(f'item_{i}_quantity')
                unit_price = request.POST.get(f'item_{i}_unit_price')

                if description and quantity and unit_price:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        product_id=product_id if product_id else None,
                        description=description,
                        specification=request.POST.get(f'item_{i}_specification', ''),
                        unit=request.POST.get(f'item_{i}_unit', ''),
                        quantity=Decimal(quantity),
                        unit_price=Decimal(unit_price),
                        tax_rate=Decimal(request.POST.get(f'item_{i}_tax_rate', invoice.tax_rate)),
                        created_by=request.user,
                        updated_by=request.user,
                    )

            # Calculate invoice totals
            invoice.calculate_totals()
            invoice.save()

            messages.success(request, f'发票 {invoice.invoice_number} 创建成功！')
            return redirect('finance:invoice_detail', pk=invoice.pk)

        except Exception as e:
            messages.error(request, f'创建发票失败：{str(e)}')
            return redirect('finance:invoice_list')

    # GET request - show form
    from apps.customers.models import Customer
    from apps.suppliers.models import Supplier
    from apps.products.models import Product

    context = {
        'invoice_type_choices': Invoice.INVOICE_TYPES,
        'status_choices': Invoice.INVOICE_STATUS,
        'customers': Customer.objects.filter(is_deleted=False, status='active'),
        'suppliers': Supplier.objects.filter(is_deleted=False, is_active=True),
        'products': Product.objects.filter(is_deleted=False, status='active'),
        'default_tax_rate': 13,
    }
    return render(request, 'finance/invoice_form.html', context)


@login_required
@transaction.atomic
def invoice_edit(request, pk):
    """
    Edit an existing invoice.
    """
    invoice = get_object_or_404(
        Invoice.objects.filter(is_deleted=False),
        pk=pk
    )

    # Only allow editing draft invoices
    if invoice.status != 'draft':
        messages.warning(request, '只有草稿状态的发票可以编辑！')
        return redirect('finance:invoice_detail', pk=pk)

    if request.method == 'POST':
        try:
            # Update invoice fields
            invoice.invoice_code = request.POST.get('invoice_code', '')
            invoice.invoice_type = request.POST.get('invoice_type')
            invoice.status = request.POST.get('status', 'draft')
            invoice.invoice_date = request.POST.get('invoice_date')
            invoice.tax_date = request.POST.get('tax_date') or None
            invoice.tax_rate = Decimal(request.POST.get('tax_rate', '13'))
            invoice.reference_type = request.POST.get('reference_type', '')
            invoice.reference_id = request.POST.get('reference_id', '')
            invoice.reference_number = request.POST.get('reference_number', '')
            invoice.remark = request.POST.get('remark', '')
            invoice.updated_by = request.user

            # Update supplier or customer
            if invoice.invoice_type == 'purchase':
                supplier_id = request.POST.get('supplier')
                invoice.supplier_id = supplier_id if supplier_id else None
                invoice.customer = None
            else:  # sales
                customer_id = request.POST.get('customer')
                invoice.customer_id = customer_id if customer_id else None
                invoice.supplier = None

            invoice.save()

            # Delete existing items
            invoice.items.all().delete()

            # Add new items
            item_count = int(request.POST.get('item_count', 0))
            for i in range(item_count):
                product_id = request.POST.get(f'item_{i}_product')
                description = request.POST.get(f'item_{i}_description', '')
                quantity = request.POST.get(f'item_{i}_quantity')
                unit_price = request.POST.get(f'item_{i}_unit_price')

                if description and quantity and unit_price:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        product_id=product_id if product_id else None,
                        description=description,
                        specification=request.POST.get(f'item_{i}_specification', ''),
                        unit=request.POST.get(f'item_{i}_unit', ''),
                        quantity=Decimal(quantity),
                        unit_price=Decimal(unit_price),
                        tax_rate=Decimal(request.POST.get(f'item_{i}_tax_rate', invoice.tax_rate)),
                        created_by=request.user,
                        updated_by=request.user,
                    )

            # Recalculate totals
            invoice.calculate_totals()
            invoice.save()

            messages.success(request, f'发票 {invoice.invoice_number} 更新成功！')
            return redirect('finance:invoice_detail', pk=invoice.pk)

        except Exception as e:
            messages.error(request, f'更新发票失败：{str(e)}')
            return redirect('finance:invoice_detail', pk=pk)

    # GET request - show form
    from apps.customers.models import Customer
    from apps.suppliers.models import Supplier
    from apps.products.models import Product

    context = {
        'invoice': invoice,
        'invoice_type_choices': Invoice.INVOICE_TYPES,
        'status_choices': Invoice.INVOICE_STATUS,
        'customers': Customer.objects.filter(is_deleted=False, status='active'),
        'suppliers': Supplier.objects.filter(is_deleted=False, is_active=True),
        'products': Product.objects.filter(is_deleted=False, status='active'),
    }
    return render(request, 'finance/invoice_form.html', context)


@login_required
@transaction.atomic
def invoice_delete(request, pk):
    """
    Soft delete an invoice (mark as deleted).
    """
    invoice = get_object_or_404(
        Invoice.objects.filter(is_deleted=False),
        pk=pk
    )

    # Only allow deleting draft invoices
    if invoice.status != 'draft':
        messages.warning(request, '只有草稿状态的发票可以删除！')
        return redirect('finance:invoice_detail', pk=pk)

    if request.method == 'POST':
        # Soft delete
        invoice.is_deleted = True
        invoice.deleted_at = timezone.now()
        invoice.deleted_by = request.user
        invoice.save()

        messages.success(request, f'发票 {invoice.invoice_number} 已删除。')
        return redirect('finance:invoice_list')

    context = {
        'invoice': invoice,
    }
    return render(request, 'finance/invoice_confirm_delete.html', context)


@login_required
@transaction.atomic
def invoice_verify(request, pk):
    """
    认证发票（采购发票）或确认开具（销售发票）。
    采购发票认证后自动生成应付账款。
    """
    invoice = get_object_or_404(
        Invoice.objects.filter(is_deleted=False),
        pk=pk
    )

    # 只有已开具或已收到的发票可以认证
    if invoice.status not in ['issued', 'received']:
        messages.warning(request, '只有已开具或已收到状态的发票可以认证！')
        return redirect('finance:invoice_detail', pk=pk)

    if request.method == 'POST':
        try:
            # 更新发票状态
            invoice.status = 'verified'
            invoice.updated_by = request.user
            invoice.save()

            logger.info(
                f'User {request.user.username} verified invoice {invoice.invoice_number}'
            )

            # 如果是采购发票，自动生成应付账款
            if invoice.invoice_type == 'purchase':
                success, account, error = _generate_supplier_account_from_invoice(invoice)

                if success:
                    messages.success(
                        request,
                        f'发票 {invoice.invoice_number} 已认证！'
                        f'已自动生成应付账款，应付金额：¥{account.invoice_amount}，到期日期：{account.due_date}'
                    )
                    logger.info(
                        f'Auto-generated supplier account {account.id} for verified invoice {invoice.invoice_number}'
                    )
                elif error and '已生成应付账款' in error:
                    # 如果已经存在应付账款，只提示认证成功
                    messages.success(request, f'发票 {invoice.invoice_number} 已认证！')
                    logger.warning(f'Invoice {invoice.invoice_number} already has supplier account')
                else:
                    # 生成失败，回滚发票状态
                    invoice.status = 'received'
                    invoice.save()
                    messages.error(request, f'发票认证成功，但生成应付账款失败：{error}')
                    logger.error(
                        f'Failed to generate supplier account for invoice {invoice.invoice_number}: {error}'
                    )
            else:
                # 销售发票只更新状态
                messages.success(request, f'发票 {invoice.invoice_number} 已确认开具！')

            return redirect('finance:invoice_detail', pk=pk)

        except Exception as e:
            logger.exception(f'Error verifying invoice {invoice.invoice_number}: {str(e)}')
            messages.error(request, f'认证发票失败：{str(e)}')
            return redirect('finance:invoice_detail', pk=pk)

    # GET request - show confirmation page
    context = {
        'invoice': invoice,
    }
    return render(request, 'finance/invoice_confirm_verify.html', context)


@login_required
@transaction.atomic
def invoice_create_from_sales_order(request, order_id):
    """
    从销售订单创建发票。
    """
    from apps.sales.models import Order as SalesOrder
    from apps.customers.models import Customer
    from apps.suppliers.models import Supplier
    from apps.products.models import Product

    # 获取销售订单（优化查询避免N+1问题）
    order = get_object_or_404(
        SalesOrder.objects.filter(is_deleted=False).select_related(
            'customer'
        ).prefetch_related('items__product'),
        pk=order_id
    )

    if request.method == 'POST':
        # 使用辅助函数处理POST请求
        success, invoice, error = _create_invoice_from_order_post(
            request, order, 'sales', 'customer'
        )

        if success:
            messages.success(request, f'从销售订单 {order.order_number} 创建发票成功！')
            return redirect('finance:invoice_detail', pk=invoice.pk)
        else:
            messages.error(request, f'创建发票失败：{error}')
            return redirect('sales:order_detail', pk=order_id)

    # GET请求：显示预填充的发票表单
    # 使用辅助函数准备初始发票明细数据
    initial_items = _prepare_invoice_items_from_order(order)

    context = {
        'invoice': None,  # 新建发票
        'invoice_type_choices': Invoice.INVOICE_TYPES,
        'status_choices': Invoice.INVOICE_STATUS,
        'customers': Customer.objects.filter(is_deleted=False, status='active'),
        'suppliers': Supplier.objects.filter(is_deleted=False, is_active=True),
        'products': Product.objects.filter(is_deleted=False, status='active'),
        'default_tax_rate': 13.00,
        'from_order': True,
        'order': order,
        'initial_invoice_type': 'sales',
        'initial_customer': order.customer,
        'initial_items': initial_items,
        'reference_number': order.order_number,
    }
    return render(request, 'finance/invoice_form.html', context)


# ============================
# Payment Receipt Views (收款记录管理)
# ============================

@login_required
def payment_receipt_list(request):
    """List all payment receipts with search and filter."""
    payments = Payment.objects.filter(
        is_deleted=False,
        payment_type='receipt'  # 只显示收款记录
    ).select_related(
        'customer',
        'processed_by',
        'created_by'
    ).order_by('-created_at')

    # Search by payment number or customer
    search = request.GET.get('search', '')
    if search:
        payments = payments.filter(
            Q(payment_number__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(reference_number__icontains=search)
        )

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        payments = payments.filter(status=status)

    # Filter by payment method
    payment_method = request.GET.get('payment_method', '')
    if payment_method:
        payments = payments.filter(payment_method=payment_method)

    # Filter by customer
    customer_id = request.GET.get('customer', '')
    if customer_id:
        payments = payments.filter(customer_id=customer_id)

    # Filter by date range
    date_from = request.GET.get('date_from', '')
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)

    date_to = request.GET.get('date_to', '')
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)

    # Calculate total amount
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Pagination
    paginator = Paginator(payments, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Get customers for filter dropdown
    from apps.customers.models import Customer
    customers = Customer.objects.filter(is_deleted=False, status='active')

    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'payment_method': payment_method,
        'customer_id': customer_id,
        'date_from': date_from,
        'date_to': date_to,
        'customers': customers,
        'payment_methods': Payment.PAYMENT_METHODS,
        'payment_statuses': Payment.PAYMENT_STATUS,
        'total_count': paginator.count,
        'total_amount': total_amount,
    }
    return render(request, 'finance/payment_receipt_list.html', context)


@login_required
def payment_receipt_detail(request, pk):
    """Display payment receipt details."""
    payment = get_object_or_404(
        Payment.objects.filter(is_deleted=False, payment_type='receipt').select_related(
            'customer',
            'processed_by',
            'created_by',
            'updated_by'
        ),
        pk=pk
    )

    context = {
        'payment': payment,
        'can_edit': payment.status in ['pending'],
        'can_cancel': payment.status in ['pending', 'completed'],
    }
    return render(request, 'finance/payment_receipt_detail.html', context)


@login_required
@transaction.atomic
def payment_receipt_create(request):
    """Create a new payment receipt."""
    if request.method == 'POST':
        from apps.core.utils import DocumentNumberGenerator

        # Generate payment number using the config key name
        payment_number = DocumentNumberGenerator.generate('payment_receipt')

        try:
            # Create payment receipt
            payment = Payment.objects.create(
                payment_number=payment_number,
                payment_type='receipt',
                payment_method=request.POST.get('payment_method'),
                status='completed',  # 收款默认直接完成
                customer_id=request.POST.get('customer'),
                amount=Decimal(request.POST.get('amount', 0)),
                currency=request.POST.get('currency', 'CNY'),
                payment_date=request.POST.get('payment_date'),
                bank_account=request.POST.get('bank_account', ''),
                bank_name=request.POST.get('bank_name', ''),
                transaction_reference=request.POST.get('transaction_reference', ''),
                reference_number=request.POST.get('reference_number', ''),
                description=request.POST.get('description', ''),
                notes=request.POST.get('notes', ''),
                processed_by=request.user,
                created_by=request.user,
            )

            messages.success(request, f'收款记录 {payment_number} 创建成功！')
            return redirect('finance:payment_receipt_detail', pk=payment.pk)

        except Exception as e:
            logger.error(f'创建收款记录失败: {str(e)}')
            messages.error(request, f'创建失败：{str(e)}')

    # GET request - show form
    from apps.customers.models import Customer

    customers = Customer.objects.filter(is_deleted=False, status='active')

    context = {
        'customers': customers,
        'payment_methods': Payment.PAYMENT_METHODS,
        'action': 'create',
    }
    return render(request, 'finance/payment_receipt_form.html', context)


@login_required
@transaction.atomic
def payment_receipt_update(request, pk):
    """Update an existing payment receipt."""
    payment = get_object_or_404(Payment, pk=pk, is_deleted=False, payment_type='receipt')

    if payment.status not in ['pending']:
        messages.error(request, '只有待处理状态的收款记录可以编辑')
        return redirect('finance:payment_receipt_detail', pk=pk)

    if request.method == 'POST':
        try:
            # Update payment receipt
            payment.payment_method = request.POST.get('payment_method')
            payment.customer_id = request.POST.get('customer')
            payment.amount = Decimal(request.POST.get('amount', 0))
            payment.currency = request.POST.get('currency', 'CNY')
            payment.payment_date = request.POST.get('payment_date')
            payment.bank_account = request.POST.get('bank_account', '')
            payment.bank_name = request.POST.get('bank_name', '')
            payment.transaction_reference = request.POST.get('transaction_reference', '')
            payment.reference_number = request.POST.get('reference_number', '')
            payment.description = request.POST.get('description', '')
            payment.notes = request.POST.get('notes', '')
            payment.updated_by = request.user
            payment.save()

            messages.success(request, f'收款记录 {payment.payment_number} 更新成功！')
            return redirect('finance:payment_receipt_detail', pk=payment.pk)

        except Exception as e:
            logger.error(f'更新收款记录失败: {str(e)}')
            messages.error(request, f'更新失败：{str(e)}')

    # GET request - show form with existing data
    from apps.customers.models import Customer

    customers = Customer.objects.filter(is_deleted=False, status='active')

    context = {
        'payment': payment,
        'customers': customers,
        'payment_methods': Payment.PAYMENT_METHODS,
        'action': 'update',
    }
    return render(request, 'finance/payment_receipt_form.html', context)


@login_required
@transaction.atomic
def payment_receipt_delete(request, pk):
    """Delete (soft delete) a payment receipt."""
    payment = get_object_or_404(Payment, pk=pk, is_deleted=False, payment_type='receipt')

    if payment.status not in ['pending']:
        messages.error(request, '只有待处理状态的收款记录可以删除')
        return redirect('finance:payment_receipt_detail', pk=pk)

    if request.method == 'POST':
        payment.is_deleted = True
        payment.updated_by = request.user
        payment.save()

        messages.success(request, f'收款记录 {payment.payment_number} 已删除')
        return redirect('finance:payment_receipt_list')

    context = {
        'payment': payment,
    }
    return render(request, 'finance/payment_receipt_confirm_delete.html', context)


@login_required
@transaction.atomic
def payment_receipt_cancel(request, pk):
    """Cancel a payment receipt."""
    payment = get_object_or_404(Payment, pk=pk, is_deleted=False, payment_type='receipt')

    if payment.status not in ['pending', 'completed']:
        messages.error(request, '只有待处理或已完成状态的收款记录可以取消')
        return redirect('finance:payment_receipt_detail', pk=pk)

    if request.method == 'POST':
        payment.status = 'cancelled'
        payment.updated_by = request.user
        payment.save()

        messages.success(request, f'收款记录 {payment.payment_number} 已取消')
        return redirect('finance:payment_receipt_detail', pk=payment.pk)

    context = {
        'payment': payment,
    }
    return render(request, 'finance/payment_receipt_confirm_cancel.html', context)


# ============================
# Payment Payment Views (付款记录管理)
# ============================

@login_required
def payment_payment_list(request):
    """List all payment payments with search and filter."""
    payments = Payment.objects.filter(
        is_deleted=False,
        payment_type='payment'  # 只显示付款记录
    ).select_related(
        'supplier',
        'processed_by',
        'created_by'
    ).order_by('-created_at')

    # Search by payment number or counterpart
    search = request.GET.get('search', '')
    if search:
        payments = payments.filter(
            Q(payment_number__icontains=search) |
            Q(supplier__name__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(reference_number__icontains=search)
        )

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        payments = payments.filter(status=status)

    # Filter by payment method
    payment_method = request.GET.get('payment_method', '')
    if payment_method:
        payments = payments.filter(payment_method=payment_method)

    # Filter by supplier
    supplier_id = request.GET.get('supplier', '')
    if supplier_id:
        payments = payments.filter(supplier_id=supplier_id)

    # Filter by customer
    customer_id = request.GET.get('customer', '')
    if customer_id:
        payments = payments.filter(customer_id=customer_id)

    # Filter by date range
    date_from = request.GET.get('date_from', '')
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)

    date_to = request.GET.get('date_to', '')
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)

    # Calculate total amount
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Pagination
    paginator = Paginator(payments, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Get suppliers/customers for filter dropdown
    from apps.suppliers.models import Supplier
    from apps.customers.models import Customer
    suppliers = Supplier.objects.filter(is_deleted=False, is_active=True)
    customers = Customer.objects.filter(is_deleted=False, status='active')

    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'payment_method': payment_method,
        'supplier_id': supplier_id,
        'customer_id': customer_id,
        'date_from': date_from,
        'date_to': date_to,
        'suppliers': suppliers,
        'customers': customers,
        'payment_methods': Payment.PAYMENT_METHODS,
        'payment_statuses': Payment.PAYMENT_STATUS,
        'total_count': paginator.count,
        'total_amount': total_amount,
    }
    return render(request, 'finance/payment_payment_list.html', context)


@login_required
def payment_payment_detail(request, pk):
    """Display payment payment details."""
    payment = get_object_or_404(
        Payment.objects.filter(is_deleted=False, payment_type='payment').select_related(
            'supplier',
            'processed_by',
            'created_by',
            'updated_by'
        ),
        pk=pk
    )

    context = {
        'payment': payment,
        'can_edit': payment.status in ['pending'],
        'can_cancel': payment.status in ['pending', 'completed'],
    }
    return render(request, 'finance/payment_payment_detail.html', context)


@login_required
@transaction.atomic
def payment_payment_create(request):
    """Create a new payment payment."""
    if request.method == 'POST':
        from apps.core.utils import DocumentNumberGenerator

        # Generate payment number using the config key name
        payment_number = DocumentNumberGenerator.generate('payment')

        try:
            # Create payment payment
            payment = Payment.objects.create(
                payment_number=payment_number,
                payment_type='payment',
                payment_method=request.POST.get('payment_method'),
                status=request.POST.get('status', 'pending'),  # 付款默认待处理
                supplier_id=request.POST.get('supplier'),
                amount=Decimal(request.POST.get('amount', 0)),
                currency=request.POST.get('currency', 'CNY'),
                payment_date=request.POST.get('payment_date'),
                bank_account=request.POST.get('bank_account', ''),
                bank_name=request.POST.get('bank_name', ''),
                transaction_reference=request.POST.get('transaction_reference', ''),
                reference_number=request.POST.get('reference_number', ''),
                description=request.POST.get('description', ''),
                notes=request.POST.get('notes', ''),
                processed_by=request.user,
                created_by=request.user,
            )

            messages.success(request, f'付款记录 {payment_number} 创建成功！')
            return redirect('finance:payment_payment_detail', pk=payment.pk)

        except Exception as e:
            logger.error(f'创建付款记录失败: {str(e)}')
            messages.error(request, f'创建失败：{str(e)}')

    # GET request - show form
    from apps.suppliers.models import Supplier

    suppliers = Supplier.objects.filter(is_deleted=False, is_active=True)

    context = {
        'suppliers': suppliers,
        'payment_methods': Payment.PAYMENT_METHODS,
        'payment_statuses': Payment.PAYMENT_STATUS,
        'action': 'create',
    }
    return render(request, 'finance/payment_payment_form.html', context)


@login_required
@transaction.atomic
def payment_payment_update(request, pk):
    """Update an existing payment payment."""
    payment = get_object_or_404(Payment, pk=pk, is_deleted=False, payment_type='payment')

    if payment.status not in ['pending']:
        messages.error(request, '只有待处理状态的付款记录可以编辑')
        return redirect('finance:payment_payment_detail', pk=pk)

    if request.method == 'POST':
        try:
            # Update payment payment
            payment.payment_method = request.POST.get('payment_method')
            payment.supplier_id = request.POST.get('supplier')
            payment.amount = Decimal(request.POST.get('amount', 0))
            payment.currency = request.POST.get('currency', 'CNY')
            payment.payment_date = request.POST.get('payment_date')
            payment.bank_account = request.POST.get('bank_account', '')
            payment.bank_name = request.POST.get('bank_name', '')
            payment.transaction_reference = request.POST.get('transaction_reference', '')
            payment.reference_number = request.POST.get('reference_number', '')
            payment.description = request.POST.get('description', '')
            payment.notes = request.POST.get('notes', '')
            payment.status = request.POST.get('status', 'pending')
            payment.updated_by = request.user
            payment.save()

            messages.success(request, f'付款记录 {payment.payment_number} 更新成功！')
            return redirect('finance:payment_payment_detail', pk=payment.pk)

        except Exception as e:
            logger.error(f'更新付款记录失败: {str(e)}')
            messages.error(request, f'更新失败：{str(e)}')

    # GET request - show form with existing data
    from apps.suppliers.models import Supplier

    suppliers = Supplier.objects.filter(is_deleted=False, is_active=True)

    context = {
        'payment': payment,
        'suppliers': suppliers,
        'payment_methods': Payment.PAYMENT_METHODS,
        'payment_statuses': Payment.PAYMENT_STATUS,
        'action': 'update',
    }
    return render(request, 'finance/payment_payment_form.html', context)


@login_required
@transaction.atomic
def payment_payment_delete(request, pk):
    """Delete (soft delete) a payment payment."""
    payment = get_object_or_404(Payment, pk=pk, is_deleted=False, payment_type='payment')

    if payment.status not in ['pending']:
        messages.error(request, '只有待处理状态的付款记录可以删除')
        return redirect('finance:payment_payment_detail', pk=pk)

    if request.method == 'POST':
        payment.is_deleted = True
        payment.updated_by = request.user
        payment.save()

        messages.success(request, f'付款记录 {payment.payment_number} 已删除')
        return redirect('finance:payment_payment_list')

    context = {
        'payment': payment,
    }
    return render(request, 'finance/payment_payment_confirm_delete.html', context)


@login_required
@transaction.atomic
def payment_payment_cancel(request, pk):
    """Cancel a payment payment."""
    payment = get_object_or_404(Payment, pk=pk, is_deleted=False, payment_type='payment')

    if payment.status not in ['pending', 'completed']:
        messages.error(request, '只有待处理或已完成状态的付款记录可以取消')
        return redirect('finance:payment_payment_detail', pk=pk)

    if request.method == 'POST':
        payment.status = 'cancelled'
        payment.updated_by = request.user
        payment.save()

        messages.success(request, f'付款记录 {payment.payment_number} 已取消')
        return redirect('finance:payment_payment_detail', pk=payment.pk)

    context = {
        'payment': payment,
    }
    return render(request, 'finance/payment_payment_confirm_cancel.html', context)


# ============================================
# Tax Rate Management Views (税率管理)
# ============================================

@login_required
def tax_rate_list(request):
    """
    List all tax rates with search and filter capabilities.
    """
    tax_rates = TaxRate.objects.filter(is_deleted=False)

    # Search
    search = request.GET.get('search', '')
    if search:
        tax_rates = tax_rates.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(description__icontains=search)
        )

    # Filter by tax type
    tax_type = request.GET.get('tax_type', '')
    if tax_type:
        tax_rates = tax_rates.filter(tax_type=tax_type)

    # Filter by active status
    is_active = request.GET.get('is_active', '')
    if is_active:
        tax_rates = tax_rates.filter(is_active=is_active == 'true')

    # Sorting
    sort = request.GET.get('sort', 'tax_type')
    tax_rates = tax_rates.order_by(sort)

    # Pagination
    paginator = Paginator(tax_rates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'tax_type': tax_type,
        'is_active': is_active,
        'total_count': paginator.count,
        'tax_types': TaxRate.TAX_TYPES,
    }
    return render(request, 'finance/tax_rate_list.html', context)


@login_required
def tax_rate_detail(request, pk):
    """
    Display tax rate details.
    """
    tax_rate = get_object_or_404(TaxRate, pk=pk, is_deleted=False)

    context = {
        'tax_rate': tax_rate,
    }
    return render(request, 'finance/tax_rate_detail.html', context)


@login_required
@transaction.atomic
def tax_rate_create(request):
    """
    Create a new tax rate.
    """
    if request.method == 'POST':
        data = {
            'name': request.POST.get('name'),
            'code': request.POST.get('code'),
            'tax_type': request.POST.get('tax_type', 'vat'),
            'rate': request.POST.get('rate'),
            'sort_order': request.POST.get('sort_order', 0),
            'is_default': request.POST.get('is_default') == 'on',
            'is_active': request.POST.get('is_active') == 'on',
            'description': request.POST.get('description', ''),
        }

        # Handle optional date fields
        effective_date = request.POST.get('effective_date')
        if effective_date:
            data['effective_date'] = effective_date

        expiry_date = request.POST.get('expiry_date')
        if expiry_date:
            data['expiry_date'] = expiry_date

        try:
            tax_rate = TaxRate(**data)
            tax_rate.created_by = request.user
            tax_rate.save()

            messages.success(request, f'税率 {tax_rate.name} 创建成功！')
            return redirect('finance:tax_rate_detail', pk=tax_rate.pk)
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

    context = {
        'action': 'create',
        'tax_types': TaxRate.TAX_TYPES,
    }
    return render(request, 'finance/tax_rate_form.html', context)


@login_required
@transaction.atomic
def tax_rate_update(request, pk):
    """
    Update an existing tax rate.
    """
    tax_rate = get_object_or_404(TaxRate, pk=pk, is_deleted=False)

    if request.method == 'POST':
        tax_rate.name = request.POST.get('name')
        tax_rate.code = request.POST.get('code')
        tax_rate.tax_type = request.POST.get('tax_type', 'vat')
        tax_rate.rate = request.POST.get('rate')
        tax_rate.sort_order = request.POST.get('sort_order', 0)
        tax_rate.is_default = request.POST.get('is_default') == 'on'
        tax_rate.is_active = request.POST.get('is_active') == 'on'
        tax_rate.description = request.POST.get('description', '')

        # Handle optional date fields
        effective_date = request.POST.get('effective_date')
        tax_rate.effective_date = effective_date if effective_date else None

        expiry_date = request.POST.get('expiry_date')
        tax_rate.expiry_date = expiry_date if expiry_date else None

        tax_rate.updated_by = request.user

        try:
            tax_rate.save()
            messages.success(request, f'税率 {tax_rate.name} 更新成功！')
            return redirect('finance:tax_rate_detail', pk=tax_rate.pk)
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

    context = {
        'tax_rate': tax_rate,
        'action': 'update',
        'tax_types': TaxRate.TAX_TYPES,
    }
    return render(request, 'finance/tax_rate_form.html', context)


@login_required
def tax_rate_delete(request, pk):
    """
    Delete (soft delete) a tax rate.
    """
    tax_rate = get_object_or_404(TaxRate, pk=pk, is_deleted=False)

    if request.method == 'POST':
        tax_rate.is_deleted = True
        tax_rate.deleted_at = timezone.now()
        tax_rate.deleted_by = request.user
        tax_rate.save()

        messages.success(request, f'税率 {tax_rate.name} 已删除')
        return redirect('finance:tax_rate_list')

    context = {
        'tax_rate': tax_rate,
    }
    return render(request, 'finance/tax_rate_confirm_delete.html', context)



# ============================================
# 往来账款报表
# ============================================

@login_required
def account_report(request):
    """
    往来账款报表 - 根据账款类型显示对应的单据表

    支持筛选：
    - 账款类型（应收/应付）
    - 逾期状态
    - 结清状态
    """
    from django.db.models import Count, Sum, Q, F
    from django.core.paginator import Paginator
    from apps.sales.models import SalesOrder
    from apps.purchase.models import PurchaseOrder

    # 获取账款类型
    account_type = request.GET.get('account_type', 'receivable').strip()

    # 基础查询集：查询账款记录
    if account_type == 'receivable':
        # 应收账款
        accounts = CustomerAccount.objects.filter(
            is_deleted=False,
            sales_order__isnull=False  # 确保有关联订单
        ).select_related(
            'customer', 'sales_order', 'created_by'
        ).order_by('-invoice_date', '-created_at')
    else:
        # 应付账款
        accounts = SupplierAccount.objects.filter(
            is_deleted=False,
            purchase_order__isnull=False  # 确保有关联订单
        ).select_related(
            'supplier', 'purchase_order', 'created_by'
        ).order_by('-invoice_date', '-created_at')

    # === 筛选条件 ===
    # 逾期状态
    overdue_status = request.GET.get('overdue_status', '').strip()
    if overdue_status == 'overdue':
        # 已逾期：到期日 < 今天 且 余额 > 0
        accounts = accounts.filter(
            due_date__lt=timezone.now().date(),
            balance__gt=0
        )
    elif overdue_status == 'not_overdue':
        # 未逾期：到期日 >= 今天 或 余额 = 0
        accounts = accounts.filter(
            Q(due_date__gte=timezone.now().date()) | Q(balance=0)
        )

    # 结清状态
    settlement_status = request.GET.get('settlement_status', '').strip()
    if settlement_status == 'settled':
        # 已结清
        accounts = accounts.filter(balance=0)
    elif settlement_status == 'unsettled':
        # 未结清
        accounts = accounts.filter(balance__gt=0)

    # 统计信息
    stats = accounts.aggregate(
        total_count=Count('id'),
        total_amount=Sum('invoice_amount'),
        total_paid=Sum('paid_amount'),
        total_balance=Sum('balance'),
    )

    # 计算统计数据（避免None值）
    if stats['total_count'] is None or stats['total_count'] == 0:
        stats = {
            'total_count': 0,
            'total_amount': 0,
            'total_paid': 0,
            'total_balance': 0,
        }
    else:
        for key in ['total_amount', 'total_paid', 'total_balance']:
            if stats[key] is None:
                stats[key] = 0

    # 分页
    paginator = Paginator(accounts, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'account_type': account_type,
        # 保留筛选条件（用于表单回显）
        'filter_overdue_status': overdue_status,
        'filter_settlement_status': settlement_status,
        'today': timezone.now().date(),
    }

    return render(request, 'finance/account_report.html', context)


# ==================== Supplier Account Payment Allocation (按明细核销) ====================

@login_required
def supplier_account_payment_list(request):
    """
    供应商应付账款列表（支持按明细核销）
    """
    from apps.finance.models import SupplierAccountDetail

    accounts = SupplierAccount.objects.filter(
        is_deleted=False,
        supplier__isnull=False  # 只显示供应商应付
    ).select_related(
        'supplier', 'purchase_order'
    ).prefetch_related(
        'details'  # 预加载明细
    ).order_by('-created_at')

    # 搜索
    search = request.GET.get('search', '').strip()
    if search:
        accounts = accounts.filter(
            Q(invoice_number__icontains=search) |
            Q(supplier__name__icontains=search) |
            Q(purchase_order__order_number__icontains=search)
        )

    # 状态筛选
    status = request.GET.get('status', '').strip()
    if status:
        accounts = accounts.filter(status=status)

    # 统计信息
    stats = accounts.aggregate(
        total_count=Count('id'),
        total_invoice_amount=Sum('invoice_amount'),
        total_paid_amount=Sum('paid_amount'),
        total_balance=Sum('balance'),
    )

    # 处理None值
    for key in ['total_invoice_amount', 'total_paid_amount', 'total_balance']:
        if stats[key] is None:
            stats[key] = Decimal('0')

    # 分页
    paginator = Paginator(accounts, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # 为每个账户添加明细统计
    for account in page_obj:
        details = account.details.filter(is_deleted=False)
        account.detail_count = details.count()
        account.pending_details = details.filter(status='pending').count()
        account.total_positive = details.filter(detail_type='receipt').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        account.total_negative = details.filter(detail_type='return').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'search': search,
        'status': status,
        'today': timezone.now().date(),
    }
    return render(request, 'finance/supplier_account_payment_list.html', context)


@login_required
def supplier_account_payment_allocate(request, pk):
    """
    应付账款付款核销（按明细核销）
    """
    from apps.finance.models import SupplierAccountDetail

    account = get_object_or_404(
        SupplierAccount.objects.prefetch_related('details__receipt', 'details__return_order'),
        pk=pk,
        is_deleted=False
    )

    # 获取所有待核销的明细（按余额排序，先核销余额小的）
    details = account.details.filter(
        is_deleted=False
    ).exclude(
        status='allocated'  # 排除已全额核销的
    ).annotate(
        balance_calc=Expression(
            F('amount') - F('allocated_amount'),
            output_field=DecimalField()
        )
    ).order_by('balance_calc')

    if request.method == 'POST':
        from apps.core.utils import DocumentNumberGenerator

        payment_method = request.POST.get('payment_method')
        payment_date = request.POST.get('payment_date')
        notes = request.POST.get('notes', '')

        if not payment_method:
            messages.error(request, '请选择付款方式')
            return redirect('finance:supplier_account_payment_allocate', pk=pk)

        try:
            with transaction.atomic():
                # 收集所有要核销的明细
                allocation_data = []
                total_allocation = Decimal('0')

                for detail in details:
                    alloc_key = f'allocate_{detail.id}'
                    alloc_amount = request.POST.get(alloc_key, '0')

                    if alloc_amount:
                        alloc_amount = Decimal(alloc_amount)
                        if alloc_amount > 0:
                            # 验证核销金额不能超过余额
                            balance = detail.amount - detail.allocated_amount
                            if alloc_amount > balance:
                                raise ValueError(f'明细 {detail.detail_number} 的核销金额不能超过未核销余额 {balance}')

                            allocation_data.append({
                                'detail': detail,
                                'amount': alloc_amount
                            })
                            total_allocation += alloc_amount

                if total_allocation <= 0:
                    raise ValueError('请至少选择一个明细进行核销')

                # 生成付款单号
                payment_number = DocumentNumberGenerator.generate('payment')

                # 创建付款记录
                payment = Payment.objects.create(
                    payment_number=payment_number,
                    payment_type='payment',
                    payment_method=payment_method,
                    status='completed',
                    supplier=account.supplier,
                    amount=total_allocation,
                    currency=account.currency,
                    payment_date=payment_date or timezone.now().date(),
                    reference_type='supplier_account',
                    reference_id=str(account.id),
                    reference_number=account.invoice_number or '',
                    description=f'应付账款核销（核销{len(allocation_data)}个明细）',
                    notes=notes,
                    processed_by=request.user,
                    created_by=request.user,
                )

                # 核销每个明细
                for alloc in allocation_data:
                    detail = alloc['detail']
                    amount = alloc['amount']

                    # 调用明细的核销方法
                    detail.allocate(amount)

                # 自动归集应付主单
                account.aggregate_from_details()

                messages.success(
                    request,
                    f'付款核销成功！付款单号：{payment_number}，核销金额：¥{total_allocation:.2f}，'
                    f'共核销 {len(allocation_data)} 个明细'
                )
                return redirect('finance:supplier_account_payment_allocate', pk=pk)

        except Exception as e:
            messages.error(request, f'核销失败：{str(e)}')
            return redirect('finance:supplier_account_payment_allocate', pk=pk)

    # GET 请求
    context = {
        'account': account,
        'details': details,
        'today': timezone.now().date(),
    }
    return render(request, 'finance/supplier_account_payment_allocate.html', context)
