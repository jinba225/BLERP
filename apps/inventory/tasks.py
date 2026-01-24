"""
Inventory tasks for the ERP system.
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import F
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_inventory_status():
    """Update inventory status and alerts."""
    try:
        from .models import InventoryStock
        from apps.products.models import Product
        from apps.core.models import Notification
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Find low stock items
        low_stock_products = Product.objects.filter(
            stocks__quantity__lte=F('min_stock'),
            is_active=True
        ).distinct()
        
        low_stock_count = 0
        
        for product in low_stock_products:
            # Get total stock quantity
            total_quantity = sum(stock.quantity for stock in product.stocks.all())
            
            if total_quantity <= product.min_stock:
                low_stock_count += 1
                
                # Create notification for admins (or specific role)
                # In a real app, we might target warehouse managers
                recipients = User.objects.filter(is_superuser=True, is_active=True)
                
                for recipient in recipients:
                    Notification.create_notification(
                        recipient=recipient,
                        title=f"库存预警: {product.name}",
                        message=f"产品 {product.name} ({product.code}) 库存不足。\n当前库存: {total_quantity}\n最小库存: {product.min_stock}",
                        notification_type='warning',
                        category='inventory',
                        reference_type='product',
                        reference_id=str(product.id)
                    )
        
        logger.info(f"Updated inventory status, found {low_stock_count} low stock items")
        return f"Updated inventory status, found {low_stock_count} low stock items"
        
    except Exception as e:
        logger.error(f"Failed to update inventory status: {str(e)}")
        raise


@shared_task
def check_expiring_products():
    """Check for products nearing expiration."""
    try:
        from .models import InventoryTransaction
        from apps.core.models import Notification
        from django.contrib.auth import get_user_model
        from datetime import timedelta
        
        User = get_user_model()
        
        # Check for products expiring in next 30 days
        expiry_threshold = timezone.now().date() + timedelta(days=30)
        
        expiring_items = InventoryTransaction.objects.filter(
            expiry_date__lte=expiry_threshold,
            expiry_date__gte=timezone.now().date(),
            quantity__gt=0,
            transaction_type='in'  # Only check inbound transactions that are still in stock (simplified logic)
        ).select_related('product', 'warehouse')
        
        expiring_count = expiring_items.count()
        
        if expiring_count > 0:
            recipients = User.objects.filter(is_superuser=True, is_active=True)
            
            for item in expiring_items:
                for recipient in recipients:
                    Notification.create_notification(
                        recipient=recipient,
                        title=f"产品过期预警: {item.product.name}",
                        message=f"产品 {item.product.name} (批次: {item.batch_number}) 即将过期。\n过期日期: {item.expiry_date}\n仓库: {item.warehouse.name}",
                        notification_type='warning',
                        category='inventory',
                        reference_type='inventory_transaction',
                        reference_id=str(item.id)
                    )
        
        logger.info(f"Found {expiring_count} items expiring soon")
        return f"Checked expiring products, found {expiring_count} items"
        
    except Exception as e:
        logger.error(f"Failed to check expiring products: {str(e)}")
        raise


@shared_task
def auto_reorder_products():
    """Automatically create reorder suggestions."""
    try:
        from apps.products.models import Product
        from apps.purchase.models import PurchaseRequest, PurchaseRequestItem
        from apps.core.utils import DocumentNumberGenerator
        from apps.departments.models import Department
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        system_user = User.objects.filter(is_superuser=True).first() # Use a system user or admin
        
        # Find products below reorder point
        reorder_products = Product.objects.filter(
            stocks__quantity__lte=F('reorder_point'),
            is_active=True
        ).distinct()
        
        suggestions_created = 0
        
        for product in reorder_products:
            total_quantity = sum(stock.quantity for stock in product.stocks.all())
            
            if total_quantity <= product.reorder_point:
                # Check if there is already a pending request for this product
                pending_request = PurchaseRequestItem.objects.filter(
                    product=product,
                    request__status__in=['draft', 'submitted', 'approved']
                ).exists()
                
                if not pending_request:
                    # Create Purchase Request
                    # Assuming a default department for auto-reorder or system department
                    department = Department.objects.first() # specific logic needed here in real app
                    
                    if department and system_user:
                        request = PurchaseRequest.objects.create(
                            request_number=DocumentNumberGenerator.generate('purchase_request'),
                            department=department,
                            requester=system_user,
                            status='draft',
                            priority='normal',
                            request_date=timezone.now().date(),
                            required_date=timezone.now().date() + timezone.timedelta(days=7),
                            purpose='系统自动补货',
                            justification=f'库存({total_quantity})低于再订货点({product.reorder_point})'
                        )
                        
                        # Calculate reorder quantity (e.g., up to max_stock or fixed amount)
                        reorder_qty = product.max_stock - total_quantity if product.max_stock > total_quantity else product.reorder_point
                        if reorder_qty <= 0:
                            reorder_qty = 10 # Default fallback
                            
                        PurchaseRequestItem.objects.create(
                            request=request,
                            product=product,
                            quantity=reorder_qty,
                            estimated_price=product.cost_price,
                            estimated_total=reorder_qty * product.cost_price
                        )
                        
                        suggestions_created += 1
        
        logger.info(f"Created {suggestions_created} reorder suggestions")
        return f"Created {suggestions_created} reorder suggestions"
        
    except Exception as e:
        logger.error(f"Failed to create reorder suggestions: {str(e)}")
        raise


@shared_task
def reconcile_inventory():
    """Reconcile inventory discrepancies."""
    try:
        from .models import InventoryStock, InventoryTransaction
        from django.db.models import Sum
        
        reconciled_count = 0
        
        # Check each stock record
        for stock in InventoryStock.objects.all():
            # Calculate quantity from transactions
            calculated_qty = InventoryTransaction.objects.filter(
                product=stock.product,
                warehouse=stock.warehouse,
                location=stock.location
            ).aggregate(
                total=Sum('quantity')
            )['total'] or 0
            
            # Update if there's a discrepancy
            if stock.quantity != calculated_qty:
                stock.quantity = calculated_qty
                stock.save()
                reconciled_count += 1
        
        logger.info(f"Reconciled {reconciled_count} inventory records")
        return f"Reconciled {reconciled_count} inventory records"
        
    except Exception as e:
        logger.error(f"Failed to reconcile inventory: {str(e)}")
        raise