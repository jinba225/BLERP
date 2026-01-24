"""
Inventory views for the ERP system.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F
from django.utils import timezone
from decimal import Decimal

from .models import (
    Warehouse,
    Location,
    InventoryStock,
    InventoryTransaction,
    StockAdjustment,
    StockTransfer,
    StockTransferItem,
    StockCount,
    StockCountItem,
    InboundOrder,
    InboundOrderItem,
    OutboundOrder,
    OutboundOrderItem,
)


@login_required
def stock_list(request):
    """List all inventory stocks with search and filter."""
    stocks = InventoryStock.objects.filter(
        is_deleted=False
    ).select_related(
        'product',
        'product__category',
        'product__unit',
        'warehouse',
        'location'
    ).order_by('-created_at')

    # Search by product name or code
    search = request.GET.get('search', '')
    if search:
        stocks = stocks.filter(
            Q(product__name__icontains=search) |
            Q(product__code__icontains=search) |
            Q(product__barcode__icontains=search)
        )

    # Filter by warehouse
    warehouse_id = request.GET.get('warehouse', '')
    if warehouse_id:
        stocks = stocks.filter(warehouse_id=warehouse_id)

    # Filter by product category
    category_id = request.GET.get('category', '')
    if category_id:
        stocks = stocks.filter(product__category_id=category_id)

    # Filter by stock status
    stock_status = request.GET.get('stock_status', '')
    if stock_status == 'low':
        # Low stock: quantity <= min_stock
        stocks = [s for s in stocks if s.is_low_stock]
    elif stock_status == 'out':
        # Out of stock: quantity = 0
        stocks = stocks.filter(quantity=0)
    elif stock_status == 'normal':
        # Normal stock: quantity > min_stock
        stocks = [s for s in stocks if not s.is_low_stock and s.quantity > 0]

    # Calculate total stock value
    if isinstance(stocks, list):
        total_value = sum(s.quantity * s.cost_price for s in stocks)
        paginator = Paginator(stocks, 20)
    else:
        total_value = sum(
            stock.quantity * stock.cost_price
            for stock in stocks
        )
        paginator = Paginator(stocks, 20)

    page_obj = paginator.get_page(request.GET.get('page'))

    # Get warehouses and categories for filter dropdowns
    from apps.products.models import ProductCategory
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    categories = ProductCategory.objects.filter(is_deleted=False)

    context = {
        'page_obj': page_obj,
        'search': search,
        'warehouse_id': warehouse_id,
        'category_id': category_id,
        'stock_status': stock_status,
        'warehouses': warehouses,
        'categories': categories,
        'total_count': paginator.count,
        'total_value': total_value,
    }
    return render(request, 'inventory/stock_list.html', context)


@login_required
def stock_detail(request, pk):
    """Display detailed stock information and transaction history."""
    stock = get_object_or_404(
        InventoryStock.objects.select_related(
            'product',
            'product__category',
            'product__unit',
            'warehouse',
            'location'
        ),
        pk=pk,
        is_deleted=False
    )

    # Get recent transactions for this product and warehouse
    transactions = InventoryTransaction.objects.filter(
        product=stock.product,
        warehouse=stock.warehouse,
        is_deleted=False
    ).select_related('operator').order_by('-transaction_date')[:20]

    context = {
        'stock': stock,
        'transactions': transactions,
    }
    return render(request, 'inventory/stock_detail.html', context)


@login_required
def transaction_list(request):
    """List all inventory transactions."""
    transactions = InventoryTransaction.objects.filter(
        is_deleted=False
    ).select_related(
        'product',
        'warehouse',
        'location',
        'operator'
    ).order_by('-created_at')

    # Search by product or reference number
    search = request.GET.get('search', '')
    if search:
        transactions = transactions.filter(
            Q(product__name__icontains=search) |
            Q(product__code__icontains=search) |
            Q(reference_number__icontains=search) |
            Q(batch_number__icontains=search)
        )

    # Filter by transaction type
    transaction_type = request.GET.get('transaction_type', '')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    # Filter by warehouse
    warehouse_id = request.GET.get('warehouse', '')
    if warehouse_id:
        transactions = transactions.filter(warehouse_id=warehouse_id)

    # Filter by date range
    date_from = request.GET.get('date_from', '')
    if date_from:
        transactions = transactions.filter(transaction_date__gte=date_from)

    date_to = request.GET.get('date_to', '')
    if date_to:
        transactions = transactions.filter(transaction_date__lte=date_to)

    # Pagination
    paginator = Paginator(transactions, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Get warehouses for filter dropdown
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)

    context = {
        'page_obj': page_obj,
        'search': search,
        'transaction_type': transaction_type,
        'warehouse_id': warehouse_id,
        'date_from': date_from,
        'date_to': date_to,
        'warehouses': warehouses,
        'transaction_types': InventoryTransaction.TRANSACTION_TYPES,
        'total_count': paginator.count,
    }
    return render(request, 'inventory/transaction_list.html', context)


@login_required
def warehouse_list(request):
    """List all warehouses."""
    warehouses = Warehouse.objects.filter(is_deleted=False).select_related('manager')

    # Search by name or code
    search = request.GET.get('search', '')
    if search:
        warehouses = warehouses.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )

    # Filter by type
    warehouse_type = request.GET.get('warehouse_type', '')
    if warehouse_type:
        warehouses = warehouses.filter(warehouse_type=warehouse_type)

    # Filter by active status
    is_active = request.GET.get('is_active', '')
    if is_active:
        warehouses = warehouses.filter(is_active=is_active == 'true')

    # 按创建时间降序（最新的在最上面）
    warehouses = warehouses.order_by('-created_at')

    # Pagination
    paginator = Paginator(warehouses, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'warehouse_type': warehouse_type,
        'is_active': is_active,
        'warehouse_types': Warehouse.WAREHOUSE_TYPES,
        'total_count': paginator.count,
    }
    return render(request, 'inventory/warehouse_list.html', context)


@login_required
def warehouse_detail(request, pk):
    """Display warehouse details and stock summary."""
    warehouse = get_object_or_404(
        Warehouse.objects.select_related('manager'),
        pk=pk,
        is_deleted=False
    )

    # Get stock summary for this warehouse
    stocks = InventoryStock.objects.filter(
        warehouse=warehouse,
        is_deleted=False
    ).select_related('product', 'product__unit').order_by('product__code')

    # Get locations for this warehouse
    locations = Location.objects.filter(
        warehouse=warehouse,
        is_deleted=False
    ).order_by('code')

    # Calculate statistics
    total_items = stocks.count()
    total_value = sum(stock.quantity * stock.cost_price for stock in stocks)
    low_stock_count = sum(1 for stock in stocks if stock.is_low_stock)

    # Pagination for stocks
    paginator = Paginator(stocks, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'warehouse': warehouse,
        'page_obj': page_obj,
        'total_items': total_items,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'locations': locations,
    }
    return render(request, 'inventory/warehouse_detail.html', context)


@login_required
@transaction.atomic
def warehouse_create(request):
    """Create a new warehouse."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    if request.method == 'POST':
        try:
            warehouse = Warehouse(
                name=request.POST.get('name'),
                code=request.POST.get('code'),
                warehouse_type=request.POST.get('warehouse_type', 'main'),
                address=request.POST.get('address', ''),
                phone=request.POST.get('phone', ''),
                capacity=Decimal(request.POST.get('capacity') or '0'),
                manager_id=request.POST.get('manager'),
                is_active=request.POST.get('is_active') == 'on',
                created_by=request.user,
            )
            warehouse.save()

            messages.success(request, f'仓库 {warehouse.name} 创建成功！')
            return redirect('inventory:warehouse_detail', pk=warehouse.pk)

        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

    # GET请求
    managers = User.objects.filter(is_active=True).order_by('username')

    context = {
        'warehouse_types': Warehouse.WAREHOUSE_TYPES,
        'managers': managers,
    }
    return render(request, 'inventory/warehouse_form.html', context)


@login_required
@transaction.atomic
def warehouse_update(request, pk):
    """Update an existing warehouse."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    warehouse = get_object_or_404(Warehouse, pk=pk, is_deleted=False)

    if request.method == 'POST':
        try:
            warehouse.name = request.POST.get('name')
            warehouse.code = request.POST.get('code')
            warehouse.warehouse_type = request.POST.get('warehouse_type', 'main')
            warehouse.address = request.POST.get('address', '')
            warehouse.phone = request.POST.get('phone', '')
            warehouse.capacity = Decimal(request.POST.get('capacity') or '0')
            warehouse.manager_id = request.POST.get('manager')
            warehouse.is_active = request.POST.get('is_active') == 'on'
            warehouse.updated_by = request.user
            warehouse.save()

            messages.success(request, f'仓库 {warehouse.name} 更新成功！')
            return redirect('inventory:warehouse_detail', pk=warehouse.pk)

        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

    # GET请求
    managers = User.objects.filter(is_active=True).order_by('username')

    context = {
        'warehouse': warehouse,
        'warehouse_types': Warehouse.WAREHOUSE_TYPES,
        'managers': managers,
        'action': 'update',
    }
    return render(request, 'inventory/warehouse_form.html', context)


@login_required
@transaction.atomic
def location_create(request, warehouse_pk):
    """Create a new location in a warehouse."""
    warehouse = get_object_or_404(Warehouse, pk=warehouse_pk, is_deleted=False)

    if request.method == 'POST':
        try:
            location = Location(
                warehouse=warehouse,
                code=request.POST.get('code'),
                name=request.POST.get('name'),
                aisle=request.POST.get('aisle', ''),
                shelf=request.POST.get('shelf', ''),
                level=request.POST.get('level', ''),
                position=request.POST.get('position', ''),
                capacity=Decimal(request.POST.get('capacity') or '0') if request.POST.get('capacity') else None,
                is_active=request.POST.get('is_active') == 'on',
                created_by=request.user,
            )
            location.save()

            messages.success(request, f'库位 {location.name} 创建成功！')
            return redirect('inventory:warehouse_detail', pk=warehouse.pk)

        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

    # GET请求
    context = {
        'warehouse': warehouse,
    }
    return render(request, 'inventory/location_form.html', context)


# ============================
# Stock Adjustment Views (库存调整管理)
# ============================

@login_required
def adjustment_list(request):
    """List all stock adjustments with search and filter."""
    adjustments = StockAdjustment.objects.filter(
        is_deleted=False
    ).select_related(
        'product',
        'warehouse',
        'location',
        'approved_by',
        'created_by'
    ).order_by('-created_at')

    # Search by adjustment number or product
    search = request.GET.get('search', '')
    if search:
        adjustments = adjustments.filter(
            Q(adjustment_number__icontains=search) |
            Q(product__name__icontains=search) |
            Q(product__code__icontains=search)
        )

    # Filter by adjustment type
    adjustment_type = request.GET.get('adjustment_type', '')
    if adjustment_type:
        adjustments = adjustments.filter(adjustment_type=adjustment_type)

    # Filter by reason
    reason = request.GET.get('reason', '')
    if reason:
        adjustments = adjustments.filter(reason=reason)

    # Filter by warehouse
    warehouse_id = request.GET.get('warehouse', '')
    if warehouse_id:
        adjustments = adjustments.filter(warehouse_id=warehouse_id)

    # Filter by approval status
    approval_status = request.GET.get('approval_status', '')
    if approval_status == 'approved':
        adjustments = adjustments.filter(is_approved=True)
    elif approval_status == 'pending':
        adjustments = adjustments.filter(is_approved=False)

    # Filter by date range
    date_from = request.GET.get('date_from', '')
    if date_from:
        adjustments = adjustments.filter(created_at__gte=date_from)

    date_to = request.GET.get('date_to', '')
    if date_to:
        adjustments = adjustments.filter(created_at__lte=date_to)

    # Pagination
    paginator = Paginator(adjustments, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Get warehouses for filter dropdown
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)

    context = {
        'page_obj': page_obj,
        'search': search,
        'adjustment_type': adjustment_type,
        'reason': reason,
        'warehouse_id': warehouse_id,
        'approval_status': approval_status,
        'date_from': date_from,
        'date_to': date_to,
        'warehouses': warehouses,
        'adjustment_types': StockAdjustment.ADJUSTMENT_TYPES,
        'adjustment_reasons': StockAdjustment.ADJUSTMENT_REASONS,
        'total_count': paginator.count,
    }
    return render(request, 'inventory/adjustment_list.html', context)


@login_required
def adjustment_detail(request, pk):
    """Display stock adjustment details."""
    adjustment = get_object_or_404(
        StockAdjustment.objects.filter(is_deleted=False).select_related(
            'product',
            'warehouse',
            'location',
            'approved_by',
            'created_by',
            'updated_by'
        ),
        pk=pk
    )

    # Get current stock information
    try:
        current_stock = InventoryStock.objects.get(
            product=adjustment.product,
            warehouse=adjustment.warehouse,
            location=adjustment.location,
            is_deleted=False
        )
    except InventoryStock.DoesNotExist:
        current_stock = None

    context = {
        'adjustment': adjustment,
        'current_stock': current_stock,
        'can_edit': not adjustment.is_approved,
        'can_approve': not adjustment.is_approved,
    }
    return render(request, 'inventory/adjustment_detail.html', context)


@login_required
@transaction.atomic
def adjustment_create(request):
    """Create a new stock adjustment."""
    if request.method == 'POST':
        from decimal import Decimal
        from .services import StockAdjustmentService

        try:
            from apps.products.models import Product
            product_id = request.POST.get('product')
            warehouse_id = request.POST.get('warehouse')
            location_id = request.POST.get('location') or None
            
            # Get current stock
            try:
                stock = InventoryStock.objects.get(
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    location_id=location_id,
                    is_deleted=False
                )
                original_quantity = stock.quantity
            except InventoryStock.DoesNotExist:
                original_quantity = Decimal('0')

            adjusted_quantity = Decimal(request.POST.get('adjusted_quantity', '0'))
            difference = adjusted_quantity - original_quantity

            data = {
                'adjustment_type': request.POST.get('adjustment_type'),
                'reason': request.POST.get('reason'),
                'product_id': product_id,
                'warehouse_id': warehouse_id,
                'location_id': location_id,
                'original_quantity': original_quantity,
                'adjusted_quantity': adjusted_quantity,
                'difference': difference,
                'notes': request.POST.get('notes', ''),
            }

            adjustment = StockAdjustmentService.create_adjustment(request.user, data)

            messages.success(request, f'库存调整单 {adjustment.adjustment_number} 创建成功！')
            return redirect('inventory:adjustment_detail', pk=adjustment.pk)

        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

    # GET request - show form
    from apps.products.models import Product

    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    products = Product.objects.filter(
        is_deleted=False,
        status='active'
    ).select_related('unit')

    context = {
        'warehouses': warehouses,
        'products': products,
        'adjustment_types': StockAdjustment.ADJUSTMENT_TYPES,
        'adjustment_reasons': StockAdjustment.ADJUSTMENT_REASONS,
        'action': 'create',
    }
    return render(request, 'inventory/adjustment_form.html', context)


@login_required
@transaction.atomic
def adjustment_update(request, pk):
    """Update an existing stock adjustment."""
    adjustment = get_object_or_404(StockAdjustment, pk=pk, is_deleted=False)

    if adjustment.is_approved:
        messages.error(request, '已审核的调整单不能编辑')
        return redirect('inventory:adjustment_detail', pk=pk)

    if request.method == 'POST':
        from decimal import Decimal
        from .services import StockAdjustmentService

        try:
            # Get updated quantities
            adjusted_quantity = Decimal(request.POST.get('adjusted_quantity', '0'))
            difference = adjusted_quantity - adjustment.original_quantity

            data = {
                'adjustment_type': request.POST.get('adjustment_type'),
                'reason': request.POST.get('reason'),
                'adjusted_quantity': adjusted_quantity,
                'difference': difference,
                'notes': request.POST.get('notes', ''),
            }

            StockAdjustmentService.update_adjustment(adjustment, request.user, data)

            messages.success(request, f'库存调整单 {adjustment.adjustment_number} 更新成功！')
            return redirect('inventory:adjustment_detail', pk=adjustment.pk)

        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

    # GET request - show form with existing data
    from apps.products.models import Product

    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    products = Product.objects.filter(
        is_deleted=False,
        status='active'
    ).select_related('unit')

    # Get current stock
    try:
        current_stock = InventoryStock.objects.get(
            product=adjustment.product,
            warehouse=adjustment.warehouse,
            location=adjustment.location,
            is_deleted=False
        )
    except InventoryStock.DoesNotExist:
        current_stock = None

    context = {
        'adjustment': adjustment,
        'current_stock': current_stock,
        'warehouses': warehouses,
        'products': products,
        'adjustment_types': StockAdjustment.ADJUSTMENT_TYPES,
        'adjustment_reasons': StockAdjustment.ADJUSTMENT_REASONS,
        'action': 'update',
    }
    return render(request, 'inventory/adjustment_form.html', context)


@login_required
@transaction.atomic
def adjustment_delete(request, pk):
    """Delete (soft delete) a stock adjustment."""
    adjustment = get_object_or_404(StockAdjustment, pk=pk, is_deleted=False)

    if adjustment.is_approved:
        messages.error(request, '已审核的调整单不能删除')
        return redirect('inventory:adjustment_detail', pk=pk)

    if request.method == 'POST':
        adjustment.is_deleted = True
        adjustment.updated_by = request.user
        adjustment.save()

        messages.success(request, f'库存调整单 {adjustment.adjustment_number} 已删除')
        return redirect('inventory:adjustment_list')

    context = {
        'adjustment': adjustment,
    }
    return render(request, 'inventory/adjustment_confirm_delete.html', context)


@login_required
@transaction.atomic
def adjustment_approve(request, pk):
    """Approve a stock adjustment and update inventory."""
    adjustment = get_object_or_404(StockAdjustment, pk=pk, is_deleted=False)

    if adjustment.is_approved:
        messages.warning(request, '该调整单已经审核过了')
        return redirect('inventory:adjustment_detail', pk=pk)

    if request.method == 'POST':
        from .services import StockAdjustmentService
        try:
            StockAdjustmentService.approve_adjustment(adjustment, request.user)

            messages.success(
                request,
                f'库存调整单 {adjustment.adjustment_number} 审核成功！'
                f'库存已更新：{adjustment.original_quantity} → {adjustment.adjusted_quantity}'
            )
            return redirect('inventory:adjustment_detail', pk=adjustment.pk)

        except Exception as e:
            messages.error(request, f'审核失败：{str(e)}')
            return redirect('inventory:adjustment_detail', pk=pk)

    context = {
        'adjustment': adjustment,
    }
    return render(request, 'inventory/adjustment_confirm_approve.html', context)


# ============================
# Stock Transfer Views (库存调拨管理)
# ============================

@login_required
def transfer_list(request):
    """List all stock transfers with search and filter."""
    transfers = StockTransfer.objects.filter(
        is_deleted=False
    ).select_related(
        'from_warehouse',
        'to_warehouse',
        'approved_by',
        'created_by'
    ).prefetch_related('items__product').order_by('-created_at')

    # Search by transfer number
    search = request.GET.get('search', '')
    if search:
        transfers = transfers.filter(
            Q(transfer_number__icontains=search)
        )

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        transfers = transfers.filter(status=status)

    # Filter by from_warehouse
    from_warehouse_id = request.GET.get('from_warehouse', '')
    if from_warehouse_id:
        transfers = transfers.filter(from_warehouse_id=from_warehouse_id)

    # Filter by to_warehouse
    to_warehouse_id = request.GET.get('to_warehouse', '')
    if to_warehouse_id:
        transfers = transfers.filter(to_warehouse_id=to_warehouse_id)

    # Filter by date range
    date_from = request.GET.get('date_from', '')
    if date_from:
        transfers = transfers.filter(transfer_date__gte=date_from)

    date_to = request.GET.get('date_to', '')
    if date_to:
        transfers = transfers.filter(transfer_date__lte=date_to)

    # Pagination
    paginator = Paginator(transfers, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Get warehouses for filter dropdown
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)

    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'from_warehouse_id': from_warehouse_id,
        'to_warehouse_id': to_warehouse_id,
        'date_from': date_from,
        'date_to': date_to,
        'warehouses': warehouses,
        'transfer_statuses': StockTransfer.TRANSFER_STATUS,
        'total_count': paginator.count,
    }
    return render(request, 'inventory/transfer_list.html', context)


@login_required
def transfer_detail(request, pk):
    """Display stock transfer details."""
    transfer = get_object_or_404(
        StockTransfer.objects.filter(is_deleted=False).select_related(
            'from_warehouse',
            'to_warehouse',
            'approved_by',
            'created_by',
            'updated_by'
        ).prefetch_related('items__product__unit'),
        pk=pk
    )

    # 系统自动生成的调拨单不允许任何操作
    if transfer.is_auto_generated:
        context = {
            'transfer': transfer,
            'items': transfer.items.filter(is_deleted=False),
            'can_edit': False,
            'can_submit': False,
            'can_approve': False,
            'can_ship': False,
            'can_receive': False,
            'can_cancel': False,
            'is_auto_generated': True,  # 用于前端显示提示
        }
    else:
        context = {
            'transfer': transfer,
            'items': transfer.items.filter(is_deleted=False),
            'can_edit': transfer.status in ['draft'],
            'can_submit': transfer.status == 'draft',
            'can_approve': transfer.status == 'pending',
            'can_ship': transfer.status == 'approved',
            'can_receive': transfer.status == 'in_transit',
            'can_cancel': transfer.status in ['draft', 'pending', 'approved'],
            'is_auto_generated': False,
        }
    return render(request, 'inventory/transfer_detail.html', context)


@login_required
@transaction.atomic
def transfer_create(request):
    """Create a new stock transfer."""
    if request.method == 'POST':
        import json
        from decimal import Decimal
        from .services import StockTransferService

        try:
            data = {
                'from_warehouse_id': request.POST.get('from_warehouse'),
                'to_warehouse_id': request.POST.get('to_warehouse'),
                'transfer_date': request.POST.get('transfer_date'),
                'expected_arrival_date': request.POST.get('expected_arrival_date') or None,
                'notes': request.POST.get('notes', ''),
            }

            # Process transfer items
            items_json = request.POST.get('items_json', '[]')
            items_raw_data = json.loads(items_json)
            items_data = []

            for item_data in items_raw_data:
                if item_data.get('product_id'):
                    items_data.append({
                        'product_id': item_data['product_id'],
                        'requested_quantity': Decimal(item_data.get('requested_quantity', 0)),
                        'unit_cost': Decimal(item_data.get('unit_cost', 0)),
                        'batch_number': item_data.get('batch_number', ''),
                        'notes': item_data.get('notes', ''),
                    })

            transfer = StockTransferService.create_transfer(request.user, data, items_data)

            messages.success(request, f'调拨单 {transfer.transfer_number} 创建成功！')
            return redirect('inventory:transfer_detail', pk=transfer.pk)

        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

    # GET request - show form
    from apps.products.models import Product

    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    products = Product.objects.filter(
        is_deleted=False,
        status='active'
    ).select_related('unit')

    context = {
        'warehouses': warehouses,
        'products': products,
        'action': 'create',
    }
    return render(request, 'inventory/transfer_form.html', context)


@login_required
@transaction.atomic
def transfer_update(request, pk):
    """Update an existing stock transfer."""
    transfer = get_object_or_404(StockTransfer, pk=pk, is_deleted=False)

    # 禁止编辑系统自动生成的调拨单
    if transfer.is_auto_generated:
        messages.error(request, '系统自动生成的调拨单不允许编辑')
        return redirect('inventory:transfer_detail', pk=pk)

    if transfer.status != 'draft':
        messages.error(request, '只有草稿状态的调拨单可以编辑')
        return redirect('inventory:transfer_detail', pk=pk)

    if request.method == 'POST':
        import json
        from decimal import Decimal
        from .services import StockTransferService

        try:
            data = {
                'from_warehouse_id': request.POST.get('from_warehouse'),
                'to_warehouse_id': request.POST.get('to_warehouse'),
                'transfer_date': request.POST.get('transfer_date'),
                'expected_arrival_date': request.POST.get('expected_arrival_date') or None,
                'notes': request.POST.get('notes', ''),
            }

            # Process transfer items
            items_json = request.POST.get('items_json', '[]')
            items_raw_data = json.loads(items_json)
            items_data = []

            for item_data in items_raw_data:
                if item_data.get('product_id'):
                    items_data.append({
                        'product_id': item_data['product_id'],
                        'requested_quantity': Decimal(item_data.get('requested_quantity', 0)),
                        'unit_cost': Decimal(item_data.get('unit_cost', 0)),
                        'batch_number': item_data.get('batch_number', ''),
                        'notes': item_data.get('notes', ''),
                    })

            StockTransferService.update_transfer(transfer, request.user, data, items_data)

            messages.success(request, f'调拨单 {transfer.transfer_number} 更新成功！')
            return redirect('inventory:transfer_detail', pk=transfer.pk)

        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

    # GET request - show form with existing data
    from apps.products.models import Product

    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    products = Product.objects.filter(
        is_deleted=False,
        status='active'
    ).select_related('unit')

    context = {
        'transfer': transfer,
        'items': transfer.items.filter(is_deleted=False),
        'warehouses': warehouses,
        'products': products,
        'action': 'update',
    }
    return render(request, 'inventory/transfer_form.html', context)


@login_required
@transaction.atomic
def transfer_delete(request, pk):
    """Delete (soft delete) a stock transfer."""
    transfer = get_object_or_404(StockTransfer, pk=pk, is_deleted=False)

    if transfer.status not in ['draft']:
        messages.error(request, '只有草稿状态的调拨单可以删除')
        return redirect('inventory:transfer_detail', pk=pk)

    if request.method == 'POST':
        transfer.is_deleted = True
        transfer.updated_by = request.user
        transfer.save()

        messages.success(request, f'调拨单 {transfer.transfer_number} 已删除')
        return redirect('inventory:transfer_list')

    context = {
        'transfer': transfer,
        'items': transfer.items.filter(is_deleted=False),
    }
    return render(request, 'inventory/transfer_confirm_delete.html', context)


@login_required
@transaction.atomic
def transfer_submit(request, pk):
    """Submit transfer for approval."""
    transfer = get_object_or_404(StockTransfer, pk=pk, is_deleted=False)

    if transfer.status != 'draft':
        messages.warning(request, '只有草稿状态的调拨单可以提交审核')
        return redirect('inventory:transfer_detail', pk=pk)

    # Check if has items
    if not transfer.items.filter(is_deleted=False).exists():
        messages.error(request, '调拨单没有明细，无法提交')
        return redirect('inventory:transfer_detail', pk=pk)

    transfer.status = 'pending'
    transfer.updated_by = request.user
    transfer.save()

    messages.success(request, f'调拨单 {transfer.transfer_number} 已提交审核')
    return redirect('inventory:transfer_detail', pk=transfer.pk)


@login_required
@transaction.atomic
def transfer_approve(request, pk):
    """Approve a stock transfer."""
    transfer = get_object_or_404(StockTransfer, pk=pk, is_deleted=False)

    if transfer.status != 'pending':
        messages.warning(request, '只有待审核状态的调拨单可以审核')
        return redirect('inventory:transfer_detail', pk=pk)

    if request.method == 'POST':
        transfer.status = 'approved'
        transfer.approved_by = request.user
        transfer.approved_at = timezone.now()
        transfer.updated_by = request.user
        transfer.save()

        messages.success(request, f'调拨单 {transfer.transfer_number} 审核通过！')
        return redirect('inventory:transfer_detail', pk=transfer.pk)

    context = {
        'transfer': transfer,
        'items': transfer.items.filter(is_deleted=False),
    }
    return render(request, 'inventory/transfer_confirm_approve.html', context)


@login_required
@transaction.atomic
def transfer_ship(request, pk):
    """Ship transfer and deduct inventory from source warehouse."""
    transfer = get_object_or_404(StockTransfer, pk=pk, is_deleted=False)

    if transfer.status != 'approved':
        messages.warning(request, '只有已审核状态的调拨单可以发货')
        return redirect('inventory:transfer_detail', pk=pk)

    if request.method == 'POST':
        from decimal import Decimal
        from .services import StockTransferService

        try:
            # Collect shipped quantities
            shipped_quantities = {}
            for item in transfer.items.filter(is_deleted=False):
                qty = Decimal(request.POST.get(f'shipped_qty_{item.id}', item.requested_quantity))
                shipped_quantities[item.id] = qty

            StockTransferService.ship_transfer(transfer, request.user, shipped_quantities)

            messages.success(request, f'调拨单 {transfer.transfer_number} 已发货！源仓库库存已扣减')
            return redirect('inventory:transfer_detail', pk=transfer.pk)

        except Exception as e:
            messages.error(request, f'发货失败：{str(e)}')
            return redirect('inventory:transfer_detail', pk=pk)

    context = {
        'transfer': transfer,
        'items': transfer.items.filter(is_deleted=False),
    }
    return render(request, 'inventory/transfer_confirm_ship.html', context)


@login_required
@transaction.atomic
def transfer_receive(request, pk):
    """Receive transfer and add inventory to destination warehouse."""
    transfer = get_object_or_404(StockTransfer, pk=pk, is_deleted=False)

    if transfer.status != 'in_transit':
        messages.warning(request, '只有在途状态的调拨单可以收货')
        return redirect('inventory:transfer_detail', pk=pk)

    if request.method == 'POST':
        from decimal import Decimal
        from .services import StockTransferService

        try:
            # Collect received quantities
            received_quantities = {}
            for item in transfer.items.filter(is_deleted=False):
                qty = Decimal(request.POST.get(f'received_qty_{item.id}', item.shipped_quantity))
                received_quantities[item.id] = qty

            StockTransferService.receive_transfer(transfer, request.user, received_quantities)

            messages.success(request, f'调拨单 {transfer.transfer_number} 已完成收货！目标仓库库存已增加')
            return redirect('inventory:transfer_detail', pk=transfer.pk)

        except Exception as e:
            messages.error(request, f'收货失败：{str(e)}')
            return redirect('inventory:transfer_detail', pk=pk)

    context = {
        'transfer': transfer,
        'items': transfer.items.filter(is_deleted=False),
    }
    return render(request, 'inventory/transfer_confirm_receive.html', context)


@login_required
@transaction.atomic
def transfer_cancel(request, pk):
    """Cancel a stock transfer."""
    transfer = get_object_or_404(StockTransfer, pk=pk, is_deleted=False)

    # 禁止取消系统自动生成的调拨单
    if transfer.is_auto_generated:
        messages.error(request, '系统自动生成的调拨单不允许取消')
        return redirect('inventory:transfer_detail', pk=pk)

    if transfer.status not in ['draft', 'pending', 'approved']:
        messages.error(request, '只有草稿、待审核或已审核状态的调拨单可以取消')
        return redirect('inventory:transfer_detail', pk=pk)

    if request.method == 'POST':
        transfer.status = 'cancelled'
        transfer.updated_by = request.user
        transfer.save()

        messages.success(request, f'调拨单 {transfer.transfer_number} 已取消')
        return redirect('inventory:transfer_detail', pk=transfer.pk)

    context = {
        'transfer': transfer,
        'items': transfer.items.filter(is_deleted=False),
    }
    return render(request, 'inventory/transfer_confirm_cancel.html', context)


# ============================
# Stock Count Views (库存盘点管理)
# ============================

@login_required
def count_list(request):
    """List all stock counts with search and filter."""
    counts = StockCount.objects.filter(
        is_deleted=False
    ).select_related(
        'warehouse',
        'supervisor',
        'created_by'
    ).prefetch_related('counters').order_by('-created_at')

    # Search by count number or warehouse
    search = request.GET.get('search', '')
    if search:
        counts = counts.filter(
            Q(count_number__icontains=search) |
            Q(warehouse__name__icontains=search)
        )

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        counts = counts.filter(status=status)

    # Filter by count type
    count_type = request.GET.get('count_type', '')
    if count_type:
        counts = counts.filter(count_type=count_type)

    # Filter by warehouse
    warehouse_id = request.GET.get('warehouse', '')
    if warehouse_id:
        counts = counts.filter(warehouse_id=warehouse_id)

    # Filter by date range
    date_from = request.GET.get('date_from', '')
    if date_from:
        counts = counts.filter(planned_date__gte=date_from)

    date_to = request.GET.get('date_to', '')
    if date_to:
        counts = counts.filter(planned_date__lte=date_to)

    # Pagination
    paginator = Paginator(counts, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Get warehouses for filter dropdown
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)

    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'count_type': count_type,
        'warehouse_id': warehouse_id,
        'date_from': date_from,
        'date_to': date_to,
        'warehouses': warehouses,
        'count_types': StockCount.COUNT_TYPES,
        'count_statuses': StockCount.COUNT_STATUS,
        'total_count': paginator.count,
    }
    return render(request, 'inventory/count_list.html', context)


@login_required
def count_detail(request, pk):
    """Display stock count details with items."""
    count = get_object_or_404(
        StockCount.objects.filter(is_deleted=False).select_related(
            'warehouse',
            'supervisor',
            'created_by',
            'updated_by'
        ).prefetch_related('counters', 'items__product', 'items__location', 'items__counter'),
        pk=pk
    )

    # Calculate statistics
    total_items = count.items.count()
    counted_items = count.items.filter(counted_quantity__isnull=False).count()
    items_with_diff = count.items.exclude(difference=0).count()

    context = {
        'count': count,
        'total_items': total_items,
        'counted_items': counted_items,
        'items_with_diff': items_with_diff,
        'can_edit': count.status == 'planned',
        'can_start': count.status == 'planned',
        'can_complete': count.status == 'in_progress',
        'can_cancel': count.status in ['planned', 'in_progress'],
    }
    return render(request, 'inventory/count_detail.html', context)


@login_required
@transaction.atomic
def count_create(request):
    """Create a new stock count."""
    if request.method == 'POST':
        import json
        from .services import StockCountService

        try:
            # Parse items data from POST
            items_json = request.POST.get('items_json', '[]')
            items_data = json.loads(items_json)

            if not items_data:
                messages.error(request, '盘点单至少需要一个产品明细')
                return redirect('inventory:count_create')

            data = {
                'count_type': request.POST.get('count_type'),
                'warehouse_id': request.POST.get('warehouse'),
                'planned_date': request.POST.get('planned_date'),
                'supervisor_id': request.POST.get('supervisor') or None,
                'notes': request.POST.get('notes', ''),
            }
            
            counter_ids = request.POST.getlist('counters')

            count = StockCountService.create_count(request.user, data, items_data, counter_ids)

            messages.success(request, f'盘点单 {count.count_number} 创建成功！')
            return redirect('inventory:count_detail', pk=count.pk)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'创建盘点单失败: {str(e)}')
            messages.error(request, f'创建失败：{str(e)}')

    # GET request - show form
    from apps.products.models import Product
    from django.contrib.auth import get_user_model
    User = get_user_model()

    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    products = Product.objects.filter(is_deleted=False, status='active')
    users = User.objects.filter(is_active=True)
    locations = Location.objects.filter(is_deleted=False, is_active=True)

    context = {
        'warehouses': warehouses,
        'products': products,
        'users': users,
        'locations': locations,
        'count_types': StockCount.COUNT_TYPES,
        'action': 'create',
    }
    return render(request, 'inventory/count_form.html', context)


@login_required
@transaction.atomic
def count_update(request, pk):
    """Update an existing stock count."""
    count = get_object_or_404(StockCount, pk=pk, is_deleted=False)

    if count.status != 'planned':
        messages.error(request, '只有计划中状态的盘点单可以编辑')
        return redirect('inventory:count_detail', pk=pk)

    if request.method == 'POST':
        import json
        from .services import StockCountService

        try:
            # Parse items data
            items_json = request.POST.get('items_json', '[]')
            items_data = json.loads(items_json)

            if not items_data:
                messages.error(request, '盘点单至少需要一个产品明细')
                return redirect('inventory:count_update', pk=pk)

            data = {
                'count_type': request.POST.get('count_type'),
                'warehouse_id': request.POST.get('warehouse'),
                'planned_date': request.POST.get('planned_date'),
                'supervisor_id': request.POST.get('supervisor') or None,
                'notes': request.POST.get('notes', ''),
            }
            
            counter_ids = request.POST.getlist('counters')

            StockCountService.update_count(count, request.user, data, items_data, counter_ids)

            messages.success(request, f'盘点单 {count.count_number} 更新成功！')
            return redirect('inventory:count_detail', pk=count.pk)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'更新盘点单失败: {str(e)}')
            messages.error(request, f'更新失败：{str(e)}')

    # GET request - show form
    from apps.products.models import Product
    from django.contrib.auth import get_user_model
    User = get_user_model()

    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    products = Product.objects.filter(is_deleted=False, status='active')
    users = User.objects.filter(is_active=True)
    locations = Location.objects.filter(is_deleted=False, is_active=True)

    context = {
        'count': count,
        'warehouses': warehouses,
        'products': products,
        'users': users,
        'locations': locations,
        'count_types': StockCount.COUNT_TYPES,
        'action': 'update',
    }
    return render(request, 'inventory/count_form.html', context)


@login_required
@transaction.atomic
def count_delete(request, pk):
    """Delete (soft delete) a stock count."""
    count = get_object_or_404(StockCount, pk=pk, is_deleted=False)

    if count.status not in ['planned']:
        messages.error(request, '只有计划中状态的盘点单可以删除')
        return redirect('inventory:count_detail', pk=pk)

    if request.method == 'POST':
        count.is_deleted = True
        count.updated_by = request.user
        count.save()

        messages.success(request, f'盘点单 {count.count_number} 已删除')
        return redirect('inventory:count_list')

    context = {
        'count': count,
        'items': count.items.select_related('product').all(),
    }
    return render(request, 'inventory/count_confirm_delete.html', context)


@login_required
@transaction.atomic
def count_start(request, pk):
    """Start a stock count."""
    count = get_object_or_404(StockCount, pk=pk, is_deleted=False)

    if count.status != 'planned':
        messages.error(request, '只有计划中状态的盘点单可以开始')
        return redirect('inventory:count_detail', pk=pk)

    if request.method == 'POST':
        count.status = 'in_progress'
        count.start_date = timezone.now()
        count.updated_by = request.user
        count.save()

        messages.success(request, f'盘点单 {count.count_number} 已开始！')
        return redirect('inventory:count_detail', pk=count.pk)

    context = {
        'count': count,
        'items': count.items.select_related('product').all(),
    }
    return render(request, 'inventory/count_confirm_start.html', context)


@login_required
@transaction.atomic
def count_complete(request, pk):
    """Complete a stock count and create adjustments."""
    count = get_object_or_404(StockCount, pk=pk, is_deleted=False)

    if count.status != 'in_progress':
        messages.error(request, '只有进行中状态的盘点单可以完成')
        return redirect('inventory:count_detail', pk=pk)

    if request.method == 'POST':
        # Update count status
        count.status = 'completed'
        count.end_date = timezone.now()
        count.updated_by = request.user
        count.save()

        # TODO: Optionally create stock adjustments based on differences
        # For now, just complete the count without creating adjustments

        messages.success(request, f'盘点单 {count.count_number} 已完成！')
        return redirect('inventory:count_detail', pk=count.pk)

    context = {
        'count': count,
        'items': count.items.select_related('product').all(),
        'items_with_diff': count.items.exclude(difference=0).select_related('product'),
    }
    return render(request, 'inventory/count_confirm_complete.html', context)


@login_required
@transaction.atomic
def count_cancel(request, pk):
    """Cancel a stock count."""
    count = get_object_or_404(StockCount, pk=pk, is_deleted=False)

    if count.status not in ['planned', 'in_progress']:
        messages.error(request, '只有计划中或进行中状态的盘点单可以取消')
        return redirect('inventory:count_detail', pk=pk)

    if request.method == 'POST':
        count.status = 'cancelled'
        count.updated_by = request.user
        count.save()

        messages.success(request, f'盘点单 {count.count_number} 已取消')
        return redirect('inventory:count_detail', pk=count.pk)

    context = {
        'count': count,
        'items': count.items.select_related('product').all(),
    }
    return render(request, 'inventory/count_confirm_cancel.html', context)


# ============================================================
# Inbound Order Views (入库单管理)
# ============================================================

@login_required
def inbound_list(request):
    """List all inbound orders with search and filter."""
    inbounds = InboundOrder.objects.filter(is_deleted=False).select_related(
        'warehouse', 'supplier', 'created_by', 'approved_by'
    ).order_by('-created_at')

    # Search by order number, supplier name, reference number
    search_query = request.GET.get('search', '').strip()
    if search_query:
        inbounds = inbounds.filter(
            Q(order_number__icontains=search_query) |
            Q(supplier__name__icontains=search_query) |
            Q(reference_number__icontains=search_query)
        )

    # Filter by status
    status = request.GET.get('status', '').strip()
    if status:
        inbounds = inbounds.filter(status=status)

    # Filter by order type
    order_type = request.GET.get('order_type', '').strip()
    if order_type:
        inbounds = inbounds.filter(order_type=order_type)

    # Filter by warehouse
    warehouse_id = request.GET.get('warehouse', '').strip()
    if warehouse_id:
        inbounds = inbounds.filter(warehouse_id=warehouse_id)

    # Filter by date range
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    if date_from:
        inbounds = inbounds.filter(order_date__gte=date_from)
    if date_to:
        inbounds = inbounds.filter(order_date__lte=date_to)

    # Pagination
    paginator = Paginator(inbounds, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Context
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status': status,
        'order_type': order_type,
        'warehouse_id': warehouse_id,
        'date_from': date_from,
        'date_to': date_to,
        'warehouses': warehouses,
        'order_types': InboundOrder.ORDER_TYPES,
        'order_statuses': InboundOrder.ORDER_STATUS,
    }

    return render(request, 'inventory/inbound_list.html', context)


@login_required
def inbound_detail(request, pk):
    """View details of an inbound order."""
    inbound = get_object_or_404(InboundOrder, pk=pk, is_deleted=False)

    items = inbound.items.filter(is_deleted=False).select_related('product', 'location')

    # Calculate total quantity
    total_quantity = items.aggregate(total=Sum('quantity'))['total'] or Decimal('0')

    context = {
        'inbound': inbound,
        'items': items,
        'total_quantity': total_quantity,
    }

    return render(request, 'inventory/inbound_detail.html', context)


@login_required
@transaction.atomic
def inbound_create(request):
    """Create a new inbound order."""
    if request.method == 'POST':
        import json
        from decimal import Decimal
        from .services import InboundOrderService

        try:
            # Parse items JSON
            items_json = request.POST.get('items_json', '[]')
            items_raw_data = json.loads(items_json)
            items_data = []

            if not items_raw_data:
                messages.error(request, '请至少添加一个产品明细')
                return redirect('inventory:inbound_create')

            data = {
                'warehouse_id': request.POST.get('warehouse'),
                'order_type': request.POST.get('order_type'),
                'order_date': request.POST.get('order_date'),
                'supplier_id': request.POST.get('supplier') or None,
                'reference_number': request.POST.get('reference_number', ''),
                'reference_type': request.POST.get('reference_type', ''),
                'notes': request.POST.get('notes', ''),
            }

            for item_data in items_raw_data:
                items_data.append({
                    'product_id': item_data['product_id'],
                    'location_id': item_data.get('location_id') or None,
                    'quantity': Decimal(item_data['quantity']),
                    'batch_number': item_data.get('batch_number', ''),
                    'expiry_date': item_data.get('expiry_date') or None,
                    'notes': item_data.get('notes', ''),
                })

            inbound = InboundOrderService.create_inbound(request.user, data, items_data)

            messages.success(request, f'入库单 {inbound.order_number} 创建成功！')
            return redirect('inventory:inbound_detail', pk=inbound.pk)

        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

    # GET request - show form
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    suppliers = Supplier.objects.filter(is_deleted=False, is_active=True)
    products = Product.objects.filter(is_deleted=False, status='active').values('id', 'name', 'code', 'unit')
    locations = Location.objects.filter(is_deleted=False).values('id', 'name', 'warehouse_id')

    context = {
        'action': 'create',
        'warehouses': warehouses,
        'suppliers': suppliers,
        'products': json.dumps(list(products), cls=DjangoJSONEncoder),
        'locations': json.dumps(list(locations), cls=DjangoJSONEncoder),
        'order_types': InboundOrder.ORDER_TYPES,
    }

    return render(request, 'inventory/inbound_form.html', context)


@login_required
@transaction.atomic
def inbound_update(request, pk):
    """Update an existing inbound order."""
    inbound = get_object_or_404(InboundOrder, pk=pk, is_deleted=False)

    # Only draft status can be edited
    if inbound.status != 'draft':
        messages.error(request, '只有草稿状态的入库单可以编辑')
        return redirect('inventory:inbound_detail', pk=pk)

    if request.method == 'POST':
        # Parse items JSON
        items_json = request.POST.get('items_json', '[]')
        items_data = json.loads(items_json)

        if not items_data:
            messages.error(request, '请至少添加一个产品明细')
            return redirect('inventory:inbound_update', pk=pk)

        # Update inbound order
        inbound.warehouse_id = request.POST.get('warehouse')
        inbound.order_type = request.POST.get('order_type')
        inbound.order_date = request.POST.get('order_date')
        inbound.supplier_id = request.POST.get('supplier') or None
        inbound.reference_number = request.POST.get('reference_number', '')
        inbound.reference_type = request.POST.get('reference_type', '')
        inbound.notes = request.POST.get('notes', '')
        inbound.updated_by = request.user
        inbound.save()

        # Delete existing items and create new ones
        inbound.items.all().delete()

        for item_data in items_data:
            InboundOrderItem.objects.create(
                inbound_order=inbound,
                product_id=item_data['product_id'],
                location_id=item_data.get('location_id') or None,
                quantity=Decimal(item_data['quantity']),
                batch_number=item_data.get('batch_number', ''),
                expiry_date=item_data.get('expiry_date') or None,
                notes=item_data.get('notes', ''),
                created_by=request.user,
                updated_by=request.user,
            )

        messages.success(request, f'入库单 {inbound.order_number} 更新成功！')
        return redirect('inventory:inbound_detail', pk=inbound.pk)

    # GET request - show form
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    suppliers = Supplier.objects.filter(is_deleted=False, is_active=True)
    products = Product.objects.filter(is_deleted=False, status='active').values('id', 'name', 'code', 'unit')
    locations = Location.objects.filter(is_deleted=False).values('id', 'name', 'warehouse_id')

    context = {
        'action': 'update',
        'inbound': inbound,
        'warehouses': warehouses,
        'suppliers': suppliers,
        'products': json.dumps(list(products), cls=DjangoJSONEncoder),
        'locations': json.dumps(list(locations), cls=DjangoJSONEncoder),
        'order_types': InboundOrder.ORDER_TYPES,
    }

    return render(request, 'inventory/inbound_form.html', context)


@login_required
@transaction.atomic
def inbound_delete(request, pk):
    """Delete an inbound order (soft delete)."""
    inbound = get_object_or_404(InboundOrder, pk=pk, is_deleted=False)

    # Only draft status can be deleted
    if inbound.status != 'draft':
        messages.error(request, '只有草稿状态的入库单可以删除')
        return redirect('inventory:inbound_detail', pk=pk)

    if request.method == 'POST':
        inbound.is_deleted = True
        inbound.deleted_at = timezone.now()
        inbound.deleted_by = request.user
        inbound.save()

        # Soft delete all items
        for item in inbound.items.all():
            item.is_deleted = True
            item.deleted_at = timezone.now()
            item.deleted_by = request.user
            item.save()

        messages.success(request, f'入库单 {inbound.order_number} 已删除')
        return redirect('inventory:inbound_list')

    context = {
        'inbound': inbound,
        'items': inbound.items.filter(is_deleted=False).select_related('product'),
    }

    return render(request, 'inventory/inbound_confirm_delete.html', context)


@login_required
@transaction.atomic
def inbound_approve(request, pk):
    """Approve an inbound order."""
    inbound = get_object_or_404(InboundOrder, pk=pk, is_deleted=False)

    # Only pending status can be approved
    if inbound.status != 'pending':
        messages.error(request, '只有待审核状态的入库单可以审核')
        return redirect('inventory:inbound_detail', pk=pk)

    if request.method == 'POST':
        inbound.status = 'approved'
        inbound.approved_by = request.user
        inbound.approved_at = timezone.now()
        inbound.updated_by = request.user
        inbound.save()

        messages.success(request, f'入库单 {inbound.order_number} 已审核通过')
        return redirect('inventory:inbound_detail', pk=inbound.pk)

    context = {
        'inbound': inbound,
        'items': inbound.items.filter(is_deleted=False).select_related('product'),
    }

    return render(request, 'inventory/inbound_confirm_approve.html', context)


@login_required
@transaction.atomic
def inbound_complete(request, pk):
    """Complete an inbound order and update inventory."""
    inbound = get_object_or_404(InboundOrder, pk=pk, is_deleted=False)

    # Only approved status can be completed
    if inbound.status != 'approved':
        messages.error(request, '只有已审核状态的入库单可以完成')
        return redirect('inventory:inbound_detail', pk=pk)

    if request.method == 'POST':
        # Update inventory stock for each item
        for item in inbound.items.filter(is_deleted=False).select_related('product'):
            # Get or create inventory stock
            stock, created = InventoryStock.objects.get_or_create(
                product=item.product,
                warehouse=inbound.warehouse,
                location=item.location,
                batch_number=item.batch_number,
                defaults={
                    'quantity': Decimal('0'),
                    'created_by': request.user,
                    'updated_by': request.user,
                }
            )

            # Increase quantity
            stock.quantity += item.quantity
            stock.updated_by = request.user
            stock.save()

            # Create stock transaction record
            StockTransaction.objects.create(
                product=item.product,
                warehouse=inbound.warehouse,
                location=item.location,
                transaction_type='inbound',
                quantity=item.quantity,
                batch_number=item.batch_number,
                reference_type='inbound_order',
                reference_id=inbound.id,
                reference_number=inbound.order_number,
                notes=f'入库单完成: {inbound.order_number}',
                created_by=request.user,
                updated_by=request.user,
            )

        # Update inbound order status
        inbound.status = 'completed'
        inbound.updated_by = request.user
        inbound.save()

        messages.success(request, f'入库单 {inbound.order_number} 已完成，库存已更新')
        return redirect('inventory:inbound_detail', pk=inbound.pk)

    context = {
        'inbound': inbound,
        'items': inbound.items.filter(is_deleted=False).select_related('product', 'location'),
    }

    return render(request, 'inventory/inbound_confirm_complete.html', context)


@login_required
@transaction.atomic
def inbound_cancel(request, pk):
    """Cancel an inbound order."""
    inbound = get_object_or_404(InboundOrder, pk=pk, is_deleted=False)

    # Only draft, pending, approved status can be cancelled
    if inbound.status not in ['draft', 'pending', 'approved']:
        messages.error(request, '只有草稿、待审核或已审核状态的入库单可以取消')
        return redirect('inventory:inbound_detail', pk=pk)

    if request.method == 'POST':
        inbound.status = 'cancelled'
        inbound.updated_by = request.user
        inbound.save()

        messages.success(request, f'入库单 {inbound.order_number} 已取消')
        return redirect('inventory:inbound_detail', pk=inbound.pk)

    context = {
        'inbound': inbound,
        'items': inbound.items.filter(is_deleted=False).select_related('product'),
    }

    return render(request, 'inventory/inbound_confirm_cancel.html', context)


# ============================================================
# Outbound Order Views (出库单管理)
# ============================================================

@login_required
def outbound_list(request):
    """List all outbound orders with search and filter."""
    outbounds = OutboundOrder.objects.filter(is_deleted=False).select_related(
        'warehouse', 'customer', 'created_by', 'approved_by'
    ).order_by('-created_at')

    # Search by order number, customer name, reference number
    search_query = request.GET.get('search', '').strip()
    if search_query:
        outbounds = outbounds.filter(
            Q(order_number__icontains=search_query) |
            Q(customer__name__icontains=search_query) |
            Q(reference_number__icontains=search_query)
        )

    # Filter by status
    status = request.GET.get('status', '').strip()
    if status:
        outbounds = outbounds.filter(status=status)

    # Filter by order type
    order_type = request.GET.get('order_type', '').strip()
    if order_type:
        outbounds = outbounds.filter(order_type=order_type)

    # Filter by warehouse
    warehouse_id = request.GET.get('warehouse', '').strip()
    if warehouse_id:
        outbounds = outbounds.filter(warehouse_id=warehouse_id)

    # Filter by date range
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    if date_from:
        outbounds = outbounds.filter(order_date__gte=date_from)
    if date_to:
        outbounds = outbounds.filter(order_date__lte=date_to)

    # Pagination
    paginator = Paginator(outbounds, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Context
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status': status,
        'order_type': order_type,
        'warehouse_id': warehouse_id,
        'date_from': date_from,
        'date_to': date_to,
        'warehouses': warehouses,
        'order_types': OutboundOrder.ORDER_TYPES,
        'order_statuses': OutboundOrder.ORDER_STATUS,
    }

    return render(request, 'inventory/outbound_list.html', context)


@login_required
def outbound_detail(request, pk):
    """View details of an outbound order."""
    outbound = get_object_or_404(OutboundOrder, pk=pk, is_deleted=False)

    items = outbound.items.filter(is_deleted=False).select_related('product', 'location')

    # Calculate total quantity
    total_quantity = items.aggregate(total=Sum('quantity'))['total'] or Decimal('0')

    context = {
        'outbound': outbound,
        'items': items,
        'total_quantity': total_quantity,
    }

    return render(request, 'inventory/outbound_detail.html', context)


@login_required
@transaction.atomic
def outbound_create(request):
    """Create a new outbound order."""
    if request.method == 'POST':
        from apps.core.utils import DocumentNumberGenerator

        # Generate order number
        order_number = DocumentNumberGenerator.generate('OBO')

        # Parse items JSON
        items_json = request.POST.get('items_json', '[]')
        items_data = json.loads(items_json)

        if not items_data:
            messages.error(request, '请至少添加一个产品明细')
            return redirect('inventory:outbound_create')

        # Create outbound order
        outbound = OutboundOrder.objects.create(
            order_number=order_number,
            warehouse_id=request.POST.get('warehouse'),
            order_type=request.POST.get('order_type'),
            status='draft',
            order_date=request.POST.get('order_date'),
            customer_id=request.POST.get('customer') or None,
            reference_number=request.POST.get('reference_number', ''),
            reference_type=request.POST.get('reference_type', ''),
            notes=request.POST.get('notes', ''),
            created_by=request.user,
            updated_by=request.user,
        )

        # Create outbound order items
        for item_data in items_data:
            OutboundOrderItem.objects.create(
                outbound_order=outbound,
                product_id=item_data['product_id'],
                location_id=item_data.get('location_id') or None,
                quantity=Decimal(item_data['quantity']),
                batch_number=item_data.get('batch_number', ''),
                notes=item_data.get('notes', ''),
                created_by=request.user,
                updated_by=request.user,
            )

        messages.success(request, f'出库单 {order_number} 创建成功！')
        return redirect('inventory:outbound_detail', pk=outbound.pk)

    # GET request - show form
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    customers = Customer.objects.filter(is_deleted=False, status='active')
    products = Product.objects.filter(is_deleted=False, status='active').values('id', 'name', 'code', 'unit')
    locations = Location.objects.filter(is_deleted=False).values('id', 'name', 'warehouse_id')

    context = {
        'action': 'create',
        'warehouses': warehouses,
        'customers': customers,
        'products': json.dumps(list(products), cls=DjangoJSONEncoder),
        'locations': json.dumps(list(locations), cls=DjangoJSONEncoder),
        'order_types': OutboundOrder.ORDER_TYPES,
    }

    return render(request, 'inventory/outbound_form.html', context)


@login_required
@transaction.atomic
def outbound_update(request, pk):
    """Update an existing outbound order."""
    outbound = get_object_or_404(OutboundOrder, pk=pk, is_deleted=False)

    # Only draft status can be edited
    if outbound.status != 'draft':
        messages.error(request, '只有草稿状态的出库单可以编辑')
        return redirect('inventory:outbound_detail', pk=pk)

    if request.method == 'POST':
        # Parse items JSON
        items_json = request.POST.get('items_json', '[]')
        items_data = json.loads(items_json)

        if not items_data:
            messages.error(request, '请至少添加一个产品明细')
            return redirect('inventory:outbound_update', pk=pk)

        # Update outbound order
        outbound.warehouse_id = request.POST.get('warehouse')
        outbound.order_type = request.POST.get('order_type')
        outbound.order_date = request.POST.get('order_date')
        outbound.customer_id = request.POST.get('customer') or None
        outbound.reference_number = request.POST.get('reference_number', '')
        outbound.reference_type = request.POST.get('reference_type', '')
        outbound.notes = request.POST.get('notes', '')
        outbound.updated_by = request.user
        outbound.save()

        # Delete existing items and create new ones
        outbound.items.all().delete()

        for item_data in items_data:
            OutboundOrderItem.objects.create(
                outbound_order=outbound,
                product_id=item_data['product_id'],
                location_id=item_data.get('location_id') or None,
                quantity=Decimal(item_data['quantity']),
                batch_number=item_data.get('batch_number', ''),
                notes=item_data.get('notes', ''),
                created_by=request.user,
                updated_by=request.user,
            )

        messages.success(request, f'出库单 {outbound.order_number} 更新成功！')
        return redirect('inventory:outbound_detail', pk=outbound.pk)

    # GET request - show form
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    customers = Customer.objects.filter(is_deleted=False, status='active')
    products = Product.objects.filter(is_deleted=False, status='active').values('id', 'name', 'code', 'unit')
    locations = Location.objects.filter(is_deleted=False).values('id', 'name', 'warehouse_id')

    context = {
        'action': 'update',
        'outbound': outbound,
        'warehouses': warehouses,
        'customers': customers,
        'products': json.dumps(list(products), cls=DjangoJSONEncoder),
        'locations': json.dumps(list(locations), cls=DjangoJSONEncoder),
        'order_types': OutboundOrder.ORDER_TYPES,
    }

    return render(request, 'inventory/outbound_form.html', context)


@login_required
@transaction.atomic
def outbound_delete(request, pk):
    """Delete an outbound order (soft delete)."""
    outbound = get_object_or_404(OutboundOrder, pk=pk, is_deleted=False)

    # Only draft status can be deleted
    if outbound.status != 'draft':
        messages.error(request, '只有草稿状态的出库单可以删除')
        return redirect('inventory:outbound_detail', pk=pk)

    if request.method == 'POST':
        outbound.is_deleted = True
        outbound.deleted_at = timezone.now()
        outbound.deleted_by = request.user
        outbound.save()

        # Soft delete all items
        for item in outbound.items.all():
            item.is_deleted = True
            item.deleted_at = timezone.now()
            item.deleted_by = request.user
            item.save()

        messages.success(request, f'出库单 {outbound.order_number} 已删除')
        return redirect('inventory:outbound_list')

    context = {
        'outbound': outbound,
        'items': outbound.items.filter(is_deleted=False).select_related('product'),
    }

    return render(request, 'inventory/outbound_confirm_delete.html', context)


@login_required
@transaction.atomic
def outbound_approve(request, pk):
    """Approve an outbound order."""
    outbound = get_object_or_404(OutboundOrder, pk=pk, is_deleted=False)

    # Only pending status can be approved
    if outbound.status != 'pending':
        messages.error(request, '只有待审核状态的出库单可以审核')
        return redirect('inventory:outbound_detail', pk=pk)

    if request.method == 'POST':
        outbound.status = 'approved'
        outbound.approved_by = request.user
        outbound.approved_at = timezone.now()
        outbound.updated_by = request.user
        outbound.save()

        messages.success(request, f'出库单 {outbound.order_number} 已审核通过')
        return redirect('inventory:outbound_detail', pk=outbound.pk)

    context = {
        'outbound': outbound,
        'items': outbound.items.filter(is_deleted=False).select_related('product'),
    }

    return render(request, 'inventory/outbound_confirm_approve.html', context)


@login_required
@transaction.atomic
def outbound_complete(request, pk):
    """Complete an outbound order and update inventory."""
    outbound = get_object_or_404(OutboundOrder, pk=pk, is_deleted=False)

    # Only approved status can be completed
    if outbound.status != 'approved':
        messages.error(request, '只有已审核状态的出库单可以完成')
        return redirect('inventory:outbound_detail', pk=pk)

    if request.method == 'POST':
        # Check inventory availability and update stock for each item
        for item in outbound.items.filter(is_deleted=False).select_related('product'):
            # Find matching inventory stock
            stock = InventoryStock.objects.filter(
                product=item.product,
                warehouse=outbound.warehouse,
                location=item.location,
                batch_number=item.batch_number,
                is_deleted=False,
            ).first()

            if not stock:
                messages.error(request, f'产品 {item.product.name} 在指定库位/批次下无库存')
                return redirect('inventory:outbound_detail', pk=pk)

            if stock.quantity < item.quantity:
                messages.error(request, f'产品 {item.product.name} 库存不足（当前: {stock.quantity}，需要: {item.quantity}）')
                return redirect('inventory:outbound_detail', pk=pk)

            # Decrease quantity
            stock.quantity -= item.quantity
            stock.updated_by = request.user
            stock.save()

            # Create stock transaction record
            StockTransaction.objects.create(
                product=item.product,
                warehouse=outbound.warehouse,
                location=item.location,
                transaction_type='outbound',
                quantity=-item.quantity,  # Negative for outbound
                batch_number=item.batch_number,
                reference_type='outbound_order',
                reference_id=outbound.id,
                reference_number=outbound.order_number,
                notes=f'出库单完成: {outbound.order_number}',
                created_by=request.user,
                updated_by=request.user,
            )

        # Update outbound order status
        outbound.status = 'completed'
        outbound.updated_by = request.user
        outbound.save()

        messages.success(request, f'出库单 {outbound.order_number} 已完成，库存已更新')
        return redirect('inventory:outbound_detail', pk=outbound.pk)

    # GET request - show confirmation page with inventory check
    items_with_stock = []
    has_insufficient_stock = False

    for item in outbound.items.filter(is_deleted=False).select_related('product', 'location'):
        stock = InventoryStock.objects.filter(
            product=item.product,
            warehouse=outbound.warehouse,
            location=item.location,
            batch_number=item.batch_number,
            is_deleted=False,
        ).first()

        current_stock = stock.quantity if stock else Decimal('0')
        is_sufficient = current_stock >= item.quantity

        if not is_sufficient:
            has_insufficient_stock = True

        items_with_stock.append({
            'item': item,
            'current_stock': current_stock,
            'is_sufficient': is_sufficient,
        })

    context = {
        'outbound': outbound,
        'items_with_stock': items_with_stock,
        'has_insufficient_stock': has_insufficient_stock,
    }

    return render(request, 'inventory/outbound_confirm_complete.html', context)


@login_required
@transaction.atomic
def outbound_cancel(request, pk):
    """Cancel an outbound order."""
    outbound = get_object_or_404(OutboundOrder, pk=pk, is_deleted=False)

    # Only draft, pending, approved status can be cancelled
    if outbound.status not in ['draft', 'pending', 'approved']:
        messages.error(request, '只有草稿、待审核或已审核状态的出库单可以取消')
        return redirect('inventory:outbound_detail', pk=pk)

    if request.method == 'POST':
        outbound.status = 'cancelled'
        outbound.updated_by = request.user
        outbound.save()

        messages.success(request, f'出库单 {outbound.order_number} 已取消')
        return redirect('inventory:outbound_detail', pk=outbound.pk)

    context = {
        'outbound': outbound,
        'items': outbound.items.filter(is_deleted=False).select_related('product'),
    }

    return render(request, 'inventory/outbound_confirm_cancel.html', context)


# ============================================================
# Inventory Report Views (库存报表)
# ============================================================

@login_required
def stock_summary_report(request):
    """Stock summary report - current inventory status."""
    stocks = InventoryStock.objects.filter(is_deleted=False).select_related(
        'product', 'warehouse', 'location'
    ).order_by('warehouse', 'product__name')

    # Search by product name or code
    search_query = request.GET.get('search', '').strip()
    if search_query:
        stocks = stocks.filter(
            Q(product__name__icontains=search_query) |
            Q(product__code__icontains=search_query)
        )

    # Filter by warehouse
    warehouse_id = request.GET.get('warehouse', '').strip()
    if warehouse_id:
        stocks = stocks.filter(warehouse_id=warehouse_id)

    # Filter by product category
    category_id = request.GET.get('category', '').strip()
    if category_id:
        stocks = stocks.filter(product__category_id=category_id)

    # Filter by low stock (quantity < safety_stock)
    show_low_stock = request.GET.get('low_stock', '').strip()
    if show_low_stock == '1':
        from django.db.models import F
        stocks = stocks.filter(quantity__lt=F('product__safety_stock'))

    # Calculate statistics
    total_products = stocks.values('product').distinct().count()
    total_quantity = stocks.aggregate(total=Sum('quantity'))['total'] or Decimal('0')
    total_value = sum(
        (stock.quantity * stock.product.cost_price) 
        for stock in stocks 
        if stock.product.cost_price
    )

    # Pagination
    paginator = Paginator(stocks, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Context
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    from apps.products.models import Category
    categories = Category.objects.filter(is_deleted=False)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'warehouse_id': warehouse_id,
        'category_id': category_id,
        'show_low_stock': show_low_stock,
        'warehouses': warehouses,
        'categories': categories,
        'total_products': total_products,
        'total_quantity': total_quantity,
        'total_value': total_value,
    }

    return render(request, 'inventory/report_stock_summary.html', context)


@login_required
def stock_transaction_report(request):
    """Stock transaction report - all inventory movements."""
    from .models import InventoryTransaction
    transactions = InventoryTransaction.objects.filter(is_deleted=False).select_related(
        'product', 'warehouse', 'location', 'created_by'
    ).order_by('-transaction_date')

    # Search by product name, code, or reference number
    search_query = request.GET.get('search', '').strip()
    if search_query:
        transactions = transactions.filter(
            Q(product__name__icontains=search_query) |
            Q(product__code__icontains=search_query) |
            Q(reference_number__icontains=search_query)
        )

    # Filter by warehouse
    warehouse_id = request.GET.get('warehouse', '').strip()
    if warehouse_id:
        transactions = transactions.filter(warehouse_id=warehouse_id)

    # Filter by transaction type
    transaction_type = request.GET.get('transaction_type', '').strip()
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    # Filter by date range
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    if date_from:
        transactions = transactions.filter(transaction_date__date__gte=date_from)
    if date_to:
        transactions = transactions.filter(transaction_date__date__lte=date_to)

    # Calculate statistics
    inbound_quantity = transactions.filter(
        transaction_type='in'
    ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
    
    outbound_quantity = transactions.filter(
        transaction_type='out'
    ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')

    # Pagination
    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Context
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'warehouse_id': warehouse_id,
        'transaction_type': transaction_type,
        'date_from': date_from,
        'date_to': date_to,
        'warehouses': warehouses,
        'transaction_types': InventoryTransaction.TRANSACTION_TYPES,
        'inbound_quantity': inbound_quantity,
        'outbound_quantity': outbound_quantity,
    }

    return render(request, 'inventory/report_stock_transaction.html', context)


@login_required
def stock_alert_report(request):
    """Stock alert report - products with low inventory."""
    from django.db.models import F
    
    # Get all products with stock below safety level
    low_stocks = InventoryStock.objects.filter(
        is_deleted=False,
        quantity__lt=F('product__safety_stock')
    ).select_related(
        'product', 'warehouse', 'location'
    ).order_by('quantity')

    # Search by product name or code
    search_query = request.GET.get('search', '').strip()
    if search_query:
        low_stocks = low_stocks.filter(
            Q(product__name__icontains=search_query) |
            Q(product__code__icontains=search_query)
        )

    # Filter by warehouse
    warehouse_id = request.GET.get('warehouse', '').strip()
    if warehouse_id:
        low_stocks = low_stocks.filter(warehouse_id=warehouse_id)

    # Calculate shortage for each stock
    stock_alerts = []
    for stock in low_stocks:
        shortage = stock.product.safety_stock - stock.quantity
        stock_alerts.append({
            'stock': stock,
            'shortage': shortage,
            'shortage_rate': (shortage / stock.product.safety_stock * 100) if stock.product.safety_stock > 0 else 0,
        })

    # Statistics
    total_alerts = len(stock_alerts)
    total_shortage_value = sum(
        (alert['shortage'] * alert['stock'].product.cost_price) 
        for alert in stock_alerts 
        if alert['stock'].product.cost_price
    )

    # Context
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)

    context = {
        'stock_alerts': stock_alerts,
        'search_query': search_query,
        'warehouse_id': warehouse_id,
        'warehouses': warehouses,
        'total_alerts': total_alerts,
        'total_shortage_value': total_shortage_value,
    }

    return render(request, 'inventory/report_stock_alert.html', context)


@login_required
def inbound_outbound_statistics(request):
    """Inbound/Outbound statistics report."""
    from django.db.models.functions import TruncDate
    from datetime import datetime, timedelta
    
    # Default date range: last 30 days
    today = datetime.now().date()
    default_date_from = today - timedelta(days=30)
    
    date_from = request.GET.get('date_from', '').strip() or str(default_date_from)
    date_to = request.GET.get('date_to', '').strip() or str(today)

    # Filter by warehouse
    warehouse_id = request.GET.get('warehouse', '').strip()

    # Get inbound orders
    inbound_orders = InboundOrder.objects.filter(
        is_deleted=False,
        status='completed',
        order_date__gte=date_from,
        order_date__lte=date_to,
    )
    if warehouse_id:
        inbound_orders = inbound_orders.filter(warehouse_id=warehouse_id)

    # Get outbound orders
    outbound_orders = OutboundOrder.objects.filter(
        is_deleted=False,
        status='completed',
        order_date__gte=date_from,
        order_date__lte=date_to,
    )
    if warehouse_id:
        outbound_orders = outbound_orders.filter(warehouse_id=warehouse_id)

    # Statistics by order type
    inbound_by_type = inbound_orders.values('order_type').annotate(
        count=Count('id'),
        total_items=Count('items')
    ).order_by('order_type')

    outbound_by_type = outbound_orders.values('order_type').annotate(
        count=Count('id'),
        total_items=Count('items')
    ).order_by('order_type')

    # Daily statistics
    daily_inbound = inbound_orders.annotate(
        date=TruncDate('order_date')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    daily_outbound = outbound_orders.annotate(
        date=TruncDate('order_date')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    # Overall statistics
    total_inbound_orders = inbound_orders.count()
    total_outbound_orders = outbound_orders.count()
    
    total_inbound_items = InboundOrderItem.objects.filter(
        inbound_order__in=inbound_orders,
        is_deleted=False
    ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
    
    total_outbound_items = OutboundOrderItem.objects.filter(
        outbound_order__in=outbound_orders,
        is_deleted=False
    ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')

    # Context
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'warehouse_id': warehouse_id,
        'warehouses': warehouses,
        'inbound_by_type': inbound_by_type,
        'outbound_by_type': outbound_by_type,
        'daily_inbound': list(daily_inbound),
        'daily_outbound': list(daily_outbound),
        'total_inbound_orders': total_inbound_orders,
        'total_outbound_orders': total_outbound_orders,
        'total_inbound_items': total_inbound_items,
        'total_outbound_items': total_outbound_items,
        'inbound_order_types': InboundOrder.ORDER_TYPES,
        'outbound_order_types': OutboundOrder.ORDER_TYPES,
    }

    return render(request, 'inventory/report_inbound_outbound_statistics.html', context)


# ============================================
# Stock Import / Initialization (库存导入及初始化)
# ============================================

@login_required
def stock_import(request):
    """
    Stock import and initialization page.
    Allows users to batch import initial stock data or manually add stocks.
    """
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    from apps.products.models import Product
    products = Product.objects.filter(is_deleted=False, status='active')[:100]  # 限制显示前100个产品

    context = {
        'warehouses': warehouses,
        'products': products,
    }
    return render(request, 'inventory/stock_import.html', context)


# ============================================================
# Unified Inventory Order Report (统一库存单据报表)
# ============================================================

@login_required
def inventory_order_report(request):
    """
    Unified inventory order report - all document types in one view.
    Filters by document type, warehouse, status, and date range.
    """
    from django.db.models import Count, Sum
    from datetime import datetime, timedelta

    # Get filter parameters
    document_type = request.GET.get('document_type', 'inbound')  # Default: inbound
    warehouse_id = request.GET.get('warehouse', '').strip()
    status = request.GET.get('status', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    search_query = request.GET.get('search', '').strip()

    # Initialize context
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)

    # Get orders based on document type
    if document_type == 'inbound':
        # 入库单
        orders = InboundOrder.objects.filter(is_deleted=False).select_related(
            'warehouse', 'supplier', 'created_by', 'approved_by'
        ).order_by('-created_at')

        # Apply filters
        if warehouse_id:
            orders = orders.filter(warehouse_id=warehouse_id)
        if status:
            orders = orders.filter(status=status)
        if date_from:
            orders = orders.filter(order_date__gte=date_from)
        if date_to:
            orders = orders.filter(order_date__lte=date_to)
        if search_query:
            orders = orders.filter(
                Q(order_number__icontains=search_query) |
                Q(supplier__name__icontains=search_query) |
                Q(reference_number__icontains=search_query)
            )

        # Statistics
        total_orders = orders.count()
        total_items = InboundOrderItem.objects.filter(
            inbound_order__in=orders,
            is_deleted=False
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')

        status_choices = InboundOrder.ORDER_STATUS
        order_type_field = 'order_type'
        order_type_choices = InboundOrder.ORDER_TYPES

    elif document_type == 'outbound':
        # 出库单
        orders = OutboundOrder.objects.filter(is_deleted=False).select_related(
            'warehouse', 'customer', 'created_by', 'approved_by'
        ).order_by('-created_at')

        # Apply filters
        if warehouse_id:
            orders = orders.filter(warehouse_id=warehouse_id)
        if status:
            orders = orders.filter(status=status)
        if date_from:
            orders = orders.filter(order_date__gte=date_from)
        if date_to:
            orders = orders.filter(order_date__lte=date_to)
        if search_query:
            orders = orders.filter(
                Q(order_number__icontains=search_query) |
                Q(customer__name__icontains=search_query) |
                Q(reference_number__icontains=search_query)
            )

        # Statistics
        total_orders = orders.count()
        total_items = OutboundOrderItem.objects.filter(
            outbound_order__in=orders,
            is_deleted=False
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')

        status_choices = OutboundOrder.ORDER_STATUS
        order_type_field = 'order_type'
        order_type_choices = OutboundOrder.ORDER_TYPES

    elif document_type == 'transfer':
        # 调拨单
        orders = StockTransfer.objects.filter(is_deleted=False).select_related(
            'from_warehouse', 'to_warehouse', 'approved_by', 'created_by'
        ).prefetch_related('items__product').order_by('-created_at')

        # Apply filters
        if warehouse_id:
            orders = orders.filter(
                Q(from_warehouse_id=warehouse_id) | Q(to_warehouse_id=warehouse_id)
            )
        if status:
            orders = orders.filter(status=status)
        if date_from:
            orders = orders.filter(transfer_date__gte=date_from)
        if date_to:
            orders = orders.filter(transfer_date__lte=date_to)
        if search_query:
            orders = orders.filter(transfer_number__icontains=search_query)

        # Statistics
        total_orders = orders.count()
        total_items = StockTransferItem.objects.filter(
            transfer__in=orders,
            is_deleted=False
        ).aggregate(total=Sum('requested_quantity'))['total'] or Decimal('0')

        status_choices = StockTransfer.TRANSFER_STATUS
        order_type_field = None
        order_type_choices = []

    elif document_type == 'count':
        # 盘点单
        orders = StockCount.objects.filter(is_deleted=False).select_related(
            'warehouse', 'supervisor', 'created_by'
        ).prefetch_related('counters').order_by('-created_at')

        # Apply filters
        if warehouse_id:
            orders = orders.filter(warehouse_id=warehouse_id)
        if status:
            orders = orders.filter(status=status)
        if date_from:
            orders = orders.filter(planned_date__gte=date_from)
        if date_to:
            orders = orders.filter(planned_date__lte=date_to)
        if search_query:
            orders = orders.filter(
                Q(count_number__icontains=search_query) |
                Q(warehouse__name__icontains=search_query)
            )

        # Statistics
        total_orders = orders.count()
        total_items = StockCountItem.objects.filter(
            count__in=orders,
            is_deleted=False
        ).count()

        status_choices = StockCount.COUNT_STATUS
        order_type_field = 'count_type'
        order_type_choices = StockCount.COUNT_TYPES

    elif document_type == 'adjustment':
        # 调整单
        orders = StockAdjustment.objects.filter(is_deleted=False).select_related(
            'product', 'warehouse', 'location', 'approved_by', 'created_by'
        ).order_by('-created_at')

        # Apply filters
        if warehouse_id:
            orders = orders.filter(warehouse_id=warehouse_id)
        if date_from:
            orders = orders.filter(created_at__gte=date_from)
        if date_to:
            orders = orders.filter(created_at__lte=date_to)
        if search_query:
            orders = orders.filter(
                Q(adjustment_number__icontains=search_query) |
                Q(product__name__icontains=search_query) |
                Q(product__code__icontains=search_query)
            )

        # For adjustments, use approval status instead
        if status:
            if status == 'approved':
                orders = orders.filter(is_approved=True)
            elif status == 'pending':
                orders = orders.filter(is_approved=False)

        # Statistics
        total_orders = orders.count()
        total_items = orders.aggregate(total=Sum('difference'))['total'] or Decimal('0')

        status_choices = [('approved', '已审核'), ('pending', '待审核')]
        order_type_field = 'adjustment_type'
        order_type_choices = StockAdjustment.ADJUSTMENT_TYPES

    else:
        # Default to empty queryset
        orders = InboundOrder.objects.none()
        total_orders = 0
        total_items = Decimal('0')
        status_choices = []
        order_type_field = None
        order_type_choices = []

    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Document types for dropdown
    document_types = [
        ('inbound', '入库单'),
        ('outbound', '出库单'),
        ('transfer', '调拨单'),
        ('count', '盘点单'),
        ('adjustment', '调整单'),
    ]

    context = {
        'page_obj': page_obj,
        'document_type': document_type,
        'document_types': document_types,
        'warehouse_id': warehouse_id,
        'warehouses': warehouses,
        'status': status,
        'status_choices': status_choices,
        'order_type_field': order_type_field,
        'order_type_choices': order_type_choices,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
        'total_orders': total_orders,
        'total_items': total_items,
    }

    return render(request, 'inventory/inventory_order_report.html', context)


@login_required
@transaction.atomic
def stock_import_submit(request):
    """
    Process stock import submission.
    Handles both file upload and manual input.
    """
    if request.method != 'POST':
        return redirect('inventory:stock_import')

    import_type = request.POST.get('import_type', 'manual')

    if import_type == 'manual':
        # Manual input processing
        warehouse_id = request.POST.get('warehouse')
        product_id = request.POST.get('product')
        quantity = request.POST.get('quantity', 0)

        try:
            warehouse = get_object_or_404(Warehouse, pk=warehouse_id, is_deleted=False)
            from apps.products.models import Product
            product = get_object_or_404(Product, pk=product_id, is_deleted=False)
            quantity = Decimal(str(quantity))

            if quantity <= 0:
                messages.error(request, '数量必须大于0')
                return redirect('inventory:stock_import')

            # Check if stock record exists
            from .models import InventoryStock, InventoryTransaction
            stock, created = InventoryStock.objects.get_or_create(
                product=product,
                warehouse=warehouse,
                location=None,
                defaults={
                    'quantity': quantity,
                    'reserved_quantity': Decimal('0'),
                    'cost_price': Decimal('0'),
                    'created_by': request.user,
                }
            )

            if not created:
                # Update existing stock
                stock.quantity += quantity
                stock.updated_by = request.user
                stock.save()

            # Create inventory transaction record
            InventoryTransaction.objects.create(
                product=product,
                warehouse=warehouse,
                location=None,
                transaction_type='in',
                quantity=quantity,
                reference_type='manual',
                reference_id=str(product.pk),
                reference_number='INIT-' + timezone.now().strftime('%Y%m%d%H%M%S'),
                notes='初始库存导入',
                operator=request.user,
                created_by=request.user,
            )

            messages.success(request, f'库存导入成功：{product.name} 数量 {quantity} 已添加到 {warehouse.name}')
            return redirect('inventory:stock_import')

        except Exception as e:
            messages.error(request, f'导入失败：{str(e)}')
            return redirect('inventory:stock_import')

    elif import_type == 'file':
        # File upload processing (to be implemented)
        messages.info(request, '文件上传功能正在开发中，请使用手动导入')
        return redirect('inventory:stock_import')

    else:
        messages.error(request, '无效的导入类型')
        return redirect('inventory:stock_import')


# ============================================================
# Data Import / Export (数据导入导出)
# ============================================================

@login_required
def data_export(request):
    """
    Export data to Excel file.
    Supports: products, locations, units, tax_rates, customers, suppliers
    """
    data_type = request.GET.get('type', 'products')

    try:
        import pandas as pd
        from django.http import HttpResponse
        from datetime import datetime
        import io

        # 根据数据类型导出不同的数据
        if data_type == 'products':
            # 导出产品数据
            from apps.products.models import Product
            queryset = Product.objects.filter(is_deleted=False).select_related(
                'category', 'brand', 'unit'
            )

            data = []
            for obj in queryset:
                data.append({
                    '产品编码': obj.code,
                    '产品名称': obj.name,
                    '条形码': obj.barcode or '',
                    '产品分类': obj.category.name if obj.category else '',
                    '品牌': obj.brand.name if obj.brand else '',
                    '产品类型': obj.get_product_type_display(),
                    '状态': obj.get_status_display(),
                    '规格': obj.specifications or '',
                    '型号': obj.model or '',
                    '单位': obj.unit.symbol if obj.unit else '',
                    '重量(kg)': obj.weight or '',
                    '长度(cm)': obj.length or '',
                    '宽度(cm)': obj.width or '',
                    '高度(cm)': obj.height or '',
                    '成本价': obj.cost_price,
                    '销售价': obj.selling_price,
                    '最小库存': obj.min_stock,
                    '最大库存': obj.max_stock,
                    '再订货点': obj.reorder_point,
                    '库存管理': '是' if obj.track_inventory else '否',
                    '保修期(月)': obj.warranty_period or '',
                    '保质期(天)': obj.shelf_life or '',
                    '备注': obj.notes or '',
                })
            filename = f'产品数据_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'

        elif data_type == 'locations':
            # 导出库位数据
            queryset = Location.objects.filter(is_deleted=False).select_related('warehouse')

            data = []
            for obj in queryset:
                data.append({
                    '仓库编码': obj.warehouse.code,
                    '仓库名称': obj.warehouse.name,
                    '库位编码': obj.code,
                    '库位名称': obj.name,
                    '通道': obj.aisle or '',
                    '货架': obj.shelf or '',
                    '层级': obj.level or '',
                    '位置': obj.position or '',
                    '容量': obj.capacity or '',
                    '是否启用': '是' if obj.is_active else '否',
                })
            filename = f'库位数据_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'

        elif data_type == 'units':
            # 导出计量单位数据
            from apps.products.models import Unit
            queryset = Unit.objects.filter(is_deleted=False)

            data = []
            for obj in queryset:
                data.append({
                    '单位名称': obj.name,
                    '单位符号': obj.symbol,
                    '单位类型': obj.get_unit_type_display(),
                    '描述': obj.description or '',
                    '是否启用': '是' if obj.is_active else '否',
                })
            filename = f'计量单位数据_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'

        elif data_type == 'tax_rates':
            # 导出税率数据
            from apps.finance.models import TaxRate
            queryset = TaxRate.objects.filter(is_deleted=False)

            data = []
            for obj in queryset:
                data.append({
                    '税率名称': obj.name,
                    '税率代码': obj.code,
                    '税种': obj.get_tax_type_display(),
                    '税率': obj.rate,
                    '是否默认': '是' if obj.is_default else '否',
                    '是否启用': '是' if obj.is_active else '否',
                    '适用说明': obj.description or '',
                    '生效日期': obj.effective_date or '',
                    '失效日期': obj.expiry_date or '',
                })
            filename = f'税率数据_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'

        elif data_type == 'customers':
            # 导出客户数据
            from apps.customers.models import Customer
            queryset = Customer.objects.filter(is_deleted=False).select_related('category', 'sales_rep')

            data = []
            for obj in queryset:
                data.append({
                    '客户编码': obj.code,
                    '客户名称': obj.name,
                    '客户等级': obj.get_customer_level_display(),
                    '状态': obj.get_status_display(),
                    '客户分类': obj.category.name if obj.category else '',
                    '网站': obj.website or '',
                    '地址': obj.address or '',
                    '城市': obj.city or '',
                    '省份': obj.province or '',
                    '国家': obj.country,
                    '邮政编码': obj.postal_code or '',
                    '行业': obj.industry or '',
                    '营业执照号': obj.business_license or '',
                    '税号': obj.tax_number or '',
                    '开户银行': obj.bank_name or '',
                    '银行账号': obj.bank_account or '',
                    '销售代表': obj.sales_rep.username if obj.sales_rep else '',
                    '信用额度': obj.credit_limit,
                    '付款方式': obj.payment_terms or '',
                    '折扣率': obj.discount_rate,
                    '客户来源': obj.source or '',
                    '备注': obj.notes or '',
                    '标签': obj.tags or '',
                })
            filename = f'客户数据_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'

        elif data_type == 'suppliers':
            # 导出供应商数据
            from apps.suppliers.models import Supplier
            queryset = Supplier.objects.filter(is_deleted=False).select_related('category', 'buyer')

            data = []
            for obj in queryset:
                data.append({
                    '供应商编码': obj.code,
                    '供应商名称': obj.name,
                    '供应商等级': obj.get_level_display(),
                    '供应商分类': obj.category.name if obj.category else '',
                    '网站': obj.website or '',
                    '地址': obj.address or '',
                    '城市': obj.city or '',
                    '省份': obj.province or '',
                    '国家': obj.country,
                    '邮政编码': obj.postal_code or '',
                    '税号': obj.tax_number or '',
                    '注册号': obj.registration_number or '',
                    '法定代表人': obj.legal_representative or '',
                    '付款方式': obj.payment_terms or '',
                    '币种': obj.currency,
                    '开户银行': obj.bank_name or '',
                    '银行账号': obj.bank_account or '',
                    '采购员': obj.buyer.username if obj.buyer else '',
                    '交货周期(天)': obj.lead_time or '',
                    '最小订单金额': obj.min_order_amount,
                    '质量评级': obj.quality_rating,
                    '交货评级': obj.delivery_rating,
                    '服务评级': obj.service_rating,
                    '认证资质': obj.certifications or '',
                    '是否启用': '是' if obj.is_active else '否',
                    '是否已审核': '是' if obj.is_approved else '否',
                    '备注': obj.notes or '',
                })
            filename = f'供应商数据_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'

        else:
            messages.error(request, '不支持的数据类型')
            return redirect('inventory:stock_import')

        # 创建Excel文件
        df = pd.DataFrame(data)

        # 使用BytesIO创建内存中的文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='数据')

        output.seek(0)

        # 返回Excel文件
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except ImportError as e:
        messages.error(request, f'缺少必要的库：{str(e)}。请安装 pandas 和 openpyxl：pip install pandas openpyxl')
        return redirect('inventory:stock_import')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'导出数据失败: {str(e)}', exc_info=True)
        messages.error(request, f'导出失败：{str(e)}')
        return redirect('inventory:stock_import')


@login_required
@transaction.atomic
def data_import(request):
    """
    Import data from Excel or CSV file.
    Supports: products, locations, units, tax_rates, customers, suppliers
    """
    if request.method != 'POST':
        messages.error(request, '仅支持POST请求')
        return redirect('inventory:stock_import')

    data_type = request.POST.get('data_type', 'products')
    skip_first_row = request.POST.get('skip_first_row') == '1'

    # 检查文件
    if 'file' not in request.FILES:
        messages.error(request, '请选择要导入的文件')
        return redirect('inventory:stock_import')

    uploaded_file = request.FILES['file']

    # 验证文件格式
    if not (uploaded_file.name.endswith('.xlsx') or
            uploaded_file.name.endswith('.xls') or
            uploaded_file.name.endswith('.csv')):
        messages.error(request, '不支持的文件格式。请上传Excel (.xlsx, .xls) 或 CSV 文件')
        return redirect('inventory:stock_import')

    try:
        import pandas as pd
        from io import BytesIO

        # 读取文件
        if uploaded_file.name.endswith('.csv'):
            # CSV文件
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        else:
            # Excel文件
            df = pd.read_excel(uploaded_file)

        # 跳过第一行（如果是表头）
        if skip_first_row and len(df) > 0:
            # pandas已经自动将第一行作为列名，所以这里不需要做额外处理
            pass

        # 检查是否有数据
        if len(df) == 0:
            messages.error(request, '文件中没有数据')
            return redirect('inventory:stock_import')

        # 根据数据类型处理导入
        success_count = 0
        error_messages = []

        if data_type == 'products':
            # 导入产品
            from apps.products.models import Product, ProductCategory, Brand, Unit

            for idx, row in df.iterrows():
                try:
                    # 查找关联对象
                    category_code = str(row.get('产品分类', '')).strip()
                    category = None
                    if category_code:
                        category = ProductCategory.objects.filter(
                            name=category_code, is_deleted=False
                        ).first()

                    brand_name = str(row.get('品牌', '')).strip()
                    brand = None
                    if brand_name:
                        brand, _ = Brand.objects.get_or_create(
                            name=brand_name,
                            defaults={'code': brand_name[:50], 'created_by': request.user}
                        )

                    unit_symbol = str(row.get('单位', '')).strip()
                    unit = None
                    if unit_symbol:
                        unit = Unit.objects.filter(symbol=unit_symbol, is_deleted=False).first()

                    # 创建产品
                    product = Product.objects.create(
                        code=str(row.get('产品编码', '')).strip() or f'AUTO_{idx}',
                        name=str(row.get('产品名称', '')).strip(),
                        barcode=str(row.get('条形码', '')).strip() or None,
                        category=category,
                        brand=brand,
                        unit=unit,
                        product_type=str(row.get('产品类型', 'finished')).strip() or 'finished',
                        status=str(row.get('状态', 'active')).strip() or 'active',
                        specifications=str(row.get('规格', '')).strip(),
                        model=str(row.get('型号', '')).strip(),
                        cost_price=Decimal(str(row.get('成本价', 0))) if pd.notna(row.get('成本价')) else Decimal('0'),
                        selling_price=Decimal(str(row.get('销售价', 0))) if pd.notna(row.get('销售价')) else Decimal('0'),
                        min_stock=int(row.get('最小库存', 0)) if pd.notna(row.get('最小库存')) else 0,
                        max_stock=int(row.get('最大库存', 0)) if pd.notna(row.get('最大库存')) else 0,
                        reorder_point=int(row.get('再订货点', 0)) if pd.notna(row.get('再订货点')) else 0,
                        track_inventory=str(row.get('库存管理', '是')).strip() == '是',
                        warranty_period=int(row.get('保修期(月)', 0)) if pd.notna(row.get('保修期(月)')) else 0,
                        shelf_life=int(row.get('保质期(天)', 0)) if pd.notna(row.get('保质期(天)')) else None,
                        notes=str(row.get('备注', '')).strip(),
                        created_by=request.user,
                        updated_by=request.user,
                    )
                    success_count += 1
                except Exception as e:
                    error_messages.append(f'第{idx+2}行：{str(e)}')

        elif data_type == 'locations':
            # 导入库位
            for idx, row in df.iterrows():
                try:
                    # 查找仓库
                    warehouse_code = str(row.get('仓库编码', '')).strip()
                    warehouse = Warehouse.objects.filter(code=warehouse_code, is_deleted=False).first()

                    if not warehouse:
                        error_messages.append(f'第{idx+2}行：找不到仓库 {warehouse_code}')
                        continue

                    # 创建库位
                    Location.objects.create(
                        warehouse=warehouse,
                        code=str(row.get('库位编码', '')).strip(),
                        name=str(row.get('库位名称', '')).strip(),
                        aisle=str(row.get('通道', '')).strip(),
                        shelf=str(row.get('货架', '')).strip(),
                        level=str(row.get('层级', '')).strip(),
                        position=str(row.get('位置', '')).strip(),
                        capacity=Decimal(str(row.get('容量', 0))) if pd.notna(row.get('容量')) else None,
                        is_active=str(row.get('是否启用', '是')).strip() == '是',
                        created_by=request.user,
                        updated_by=request.user,
                    )
                    success_count += 1
                except Exception as e:
                    error_messages.append(f'第{idx+2}行：{str(e)}')

        elif data_type == 'units':
            # 导入计量单位
            from apps.products.models import Unit

            for idx, row in df.iterrows():
                try:
                    Unit.objects.get_or_create(
                        symbol=str(row.get('单位符号', '')).strip(),
                        defaults={
                            'name': str(row.get('单位名称', '')).strip(),
                            'unit_type': str(row.get('单位类型', 'basic')).strip() or 'basic',
                            'description': str(row.get('描述', '')).strip(),
                            'is_active': str(row.get('是否启用', '是')).strip() == '是',
                            'created_by': request.user,
                            'updated_by': request.user,
                        }
                    )
                    success_count += 1
                except Exception as e:
                    error_messages.append(f'第{idx+2}行：{str(e)}')

        elif data_type == 'tax_rates':
            # 导入税率
            from apps.finance.models import TaxRate

            for idx, row in df.iterrows():
                try:
                    TaxRate.objects.get_or_create(
                        code=str(row.get('税率代码', '')).strip(),
                        defaults={
                            'name': str(row.get('税率名称', '')).strip(),
                            'tax_type': str(row.get('税种', 'vat')).strip() or 'vat',
                            'rate': Decimal(str(row.get('税率', 0))) if pd.notna(row.get('税率')) else Decimal('0'),
                            'is_default': str(row.get('是否默认', '否')).strip() == '是',
                            'is_active': str(row.get('是否启用', '是')).strip() == '是',
                            'description': str(row.get('适用说明', '')).strip(),
                            'effective_date': pd.to_datetime(row.get('生效日期')).date() if pd.notna(row.get('生效日期')) else None,
                            'expiry_date': pd.to_datetime(row.get('失效日期')).date() if pd.notna(row.get('失效日期')) else None,
                            'sort_order': int(row.get('排序', 0)) if pd.notna(row.get('排序')) else 0,
                            'created_by': request.user,
                            'updated_by': request.user,
                        }
                    )
                    success_count += 1
                except Exception as e:
                    error_messages.append(f'第{idx+2}行：{str(e)}')

        elif data_type == 'customers':
            # 导入客户
            from apps.customers.models import Customer, CustomerCategory
            from django.contrib.auth import get_user_model
            User = get_user_model()

            for idx, row in df.iterrows():
                try:
                    # 查找客户分类
                    category_name = str(row.get('客户分类', '')).strip()
                    category = None
                    if category_name:
                        category, _ = CustomerCategory.objects.get_or_create(
                            name=category_name,
                            defaults={'code': category_name[:50], 'created_by': request.user}
                        )

                    # 查找销售代表
                    sales_rep_username = str(row.get('销售代表', '')).strip()
                    sales_rep = None
                    if sales_rep_username:
                        sales_rep = User.objects.filter(username=sales_rep_username).first()

                    # 创建客户
                    Customer.objects.get_or_create(
                        code=str(row.get('客户编码', '')).strip(),
                        defaults={
                            'name': str(row.get('客户名称', '')).strip(),
                            'customer_level': str(row.get('客户等级', 'C')).strip() or 'C',
                            'status': str(row.get('状态', 'active')).strip() or 'active',
                            'category': category,
                            'website': str(row.get('网站', '')).strip(),
                            'address': str(row.get('地址', '')).strip(),
                            'city': str(row.get('城市', '')).strip(),
                            'province': str(row.get('省份', '')).strip(),
                            'country': str(row.get('国家', '中国')).strip(),
                            'postal_code': str(row.get('邮政编码', '')).strip(),
                            'industry': str(row.get('行业', '')).strip(),
                            'business_license': str(row.get('营业执照号', '')).strip(),
                            'tax_number': str(row.get('税号', '')).strip(),
                            'bank_name': str(row.get('开户银行', '')).strip(),
                            'bank_account': str(row.get('银行账号', '')).strip(),
                            'sales_rep': sales_rep,
                            'credit_limit': Decimal(str(row.get('信用额度', 0))) if pd.notna(row.get('信用额度')) else Decimal('0'),
                            'payment_terms': str(row.get('付款方式', '')).strip(),
                            'discount_rate': Decimal(str(row.get('折扣率', 0))) if pd.notna(row.get('折扣率')) else Decimal('0'),
                            'source': str(row.get('客户来源', '')).strip(),
                            'notes': str(row.get('备注', '')).strip(),
                            'tags': str(row.get('标签', '')).strip(),
                            'created_by': request.user,
                            'updated_by': request.user,
                        }
                    )
                    success_count += 1
                except Exception as e:
                    error_messages.append(f'第{idx+2}行：{str(e)}')

        elif data_type == 'suppliers':
            # 导入供应商
            from apps.suppliers.models import Supplier, SupplierCategory
            from django.contrib.auth import get_user_model
            User = get_user_model()

            for idx, row in df.iterrows():
                try:
                    # 查找供应商分类
                    category_name = str(row.get('供应商分类', '')).strip()
                    category = None
                    if category_name:
                        category, _ = SupplierCategory.objects.get_or_create(
                            name=category_name,
                            defaults={'code': category_name[:50], 'created_by': request.user}
                        )

                    # 查找采购员
                    buyer_username = str(row.get('采购员', '')).strip()
                    buyer = None
                    if buyer_username:
                        buyer = User.objects.filter(username=buyer_username).first()

                    # 创建供应商
                    Supplier.objects.get_or_create(
                        code=str(row.get('供应商编码', '')).strip(),
                        defaults={
                            'name': str(row.get('供应商名称', '')).strip(),
                            'level': str(row.get('供应商等级', 'C')).strip() or 'C',
                            'category': category,
                            'website': str(row.get('网站', '')).strip(),
                            'address': str(row.get('地址', '')).strip(),
                            'city': str(row.get('城市', '')).strip(),
                            'province': str(row.get('省份', '')).strip(),
                            'country': str(row.get('国家', '中国')).strip(),
                            'postal_code': str(row.get('邮政编码', '')).strip(),
                            'tax_number': str(row.get('税号', '')).strip(),
                            'registration_number': str(row.get('注册号', '')).strip(),
                            'legal_representative': str(row.get('法定代表人', '')).strip(),
                            'payment_terms': str(row.get('付款方式', '')).strip(),
                            'currency': str(row.get('币种', 'CNY')).strip(),
                            'bank_name': str(row.get('开户银行', '')).strip(),
                            'bank_account': str(row.get('银行账号', '')).strip(),
                            'buyer': buyer,
                            'lead_time': int(row.get('交货周期(天)', 0)) if pd.notna(row.get('交货周期(天)')) else 0,
                            'min_order_amount': Decimal(str(row.get('最小订单金额', 0))) if pd.notna(row.get('最小订单金额')) else Decimal('0'),
                            'quality_rating': Decimal(str(row.get('质量评级', 0))) if pd.notna(row.get('质量评级')) else Decimal('0'),
                            'delivery_rating': Decimal(str(row.get('交货评级', 0))) if pd.notna(row.get('交货评级')) else Decimal('0'),
                            'service_rating': Decimal(str(row.get('服务评级', 0))) if pd.notna(row.get('服务评级')) else Decimal('0'),
                            'certifications': str(row.get('认证资质', '')).strip(),
                            'is_active': str(row.get('是否启用', '是')).strip() == '是',
                            'is_approved': str(row.get('是否已审核', '否')).strip() == '是',
                            'notes': str(row.get('备注', '')).strip(),
                            'created_by': request.user,
                            'updated_by': request.user,
                        }
                    )
                    success_count += 1
                except Exception as e:
                    error_messages.append(f'第{idx+2}行：{str(e)}')

        # 显示导入结果
        if success_count > 0:
            messages.success(request, f'成功导入 {success_count} 条记录')
        if error_messages:
            messages.warning(request, f'有 {len(error_messages)} 条记录导入失败：' + '; '.join(error_messages[:5]))
            if len(error_messages) > 5:
                messages.warning(request, f'...还有 {len(error_messages) - 5} 条错误')

        return redirect('inventory:stock_import')

    except ImportError:
        messages.error(request, '缺少必要的库。请安装 pandas 和 openpyxl：pip install pandas openpyxl')
        return redirect('inventory:stock_import')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'导入数据失败: {str(e)}', exc_info=True)
        messages.error(request, f'导入失败：{str(e)}')
        return redirect('inventory:stock_import')
