"""
Inventory services for the ERP system.
Handles business logic for Stock Adjustments, Transfers, Counts, and Inbound/Outbound Orders.
"""
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import (
    InventoryStock, InventoryTransaction, StockAdjustment, 
    StockTransfer, StockTransferItem, StockCount, StockCountItem,
    InboundOrder, InboundOrderItem
)
from apps.core.utils import DocumentNumberGenerator

class StockAdjustmentService:
    @staticmethod
    @transaction.atomic
    def create_adjustment(user, data):
        """Create a new stock adjustment."""
        if 'adjustment_number' not in data:
            data['adjustment_number'] = DocumentNumberGenerator.generate('ADJ')
            
        adjustment = StockAdjustment.objects.create(
            created_by=user,
            **data
        )
        return adjustment

    @staticmethod
    @transaction.atomic
    def update_adjustment(adjustment, user, data):
        """Update an existing stock adjustment."""
        for key, value in data.items():
            setattr(adjustment, key, value)
        
        adjustment.updated_by = user
        adjustment.save()
        return adjustment

    @staticmethod
    @transaction.atomic
    def approve_adjustment(adjustment, user):
        """Approve stock adjustment and update inventory."""
        # Update or create inventory stock
        stock, created = InventoryStock.objects.get_or_create(
            product=adjustment.product,
            warehouse=adjustment.warehouse,
            location=adjustment.location,
            defaults={
                'quantity': Decimal('0'),
                'cost_price': Decimal('0'),
                'created_by': user,
            }
        )

        # Record the transaction (will automatically update stock)
        InventoryTransaction.objects.create(
            product=adjustment.product,
            warehouse=adjustment.warehouse,
            location=adjustment.location,
            transaction_type='adjustment',
            quantity=adjustment.difference,
            transaction_date=timezone.now().date(),
            reference_number=adjustment.adjustment_number,
            notes=f'库存调整审核 - {adjustment.get_reason_display()}',
            operator=user,
            created_by=user,
        )

        # Mark adjustment as approved
        adjustment.is_approved = True
        adjustment.approved_by = user
        adjustment.approved_at = timezone.now()
        adjustment.updated_by = user
        adjustment.save()
        
        return adjustment

class StockTransferService:
    @staticmethod
    @transaction.atomic
    def create_transfer(user, data, items_data):
        """Create a new stock transfer."""
        if 'transfer_number' not in data:
            data['transfer_number'] = DocumentNumberGenerator.generate('TRF')
            
        transfer = StockTransfer.objects.create(
            created_by=user,
            status='draft',
            **data
        )
        
        for item_data in items_data:
            if item_data.get('product_id'):
                StockTransferItem.objects.create(
                    transfer=transfer,
                    created_by=user,
                    **item_data
                )
        return transfer

    @staticmethod
    @transaction.atomic
    def update_transfer(transfer, user, data, items_data):
        """Update an existing stock transfer."""
        for key, value in data.items():
            setattr(transfer, key, value)
            
        transfer.updated_by = user
        transfer.save()
        
        if items_data is not None:
            transfer.items.all().delete()
            for item_data in items_data:
                if item_data.get('product_id'):
                    StockTransferItem.objects.create(
                        transfer=transfer,
                        created_by=user,
                        **item_data
                    )
        return transfer

    @staticmethod
    @transaction.atomic
    def ship_transfer(transfer, user, shipped_quantities):
        """Ship transfer and deduct inventory."""
        for item in transfer.items.filter(is_deleted=False):
            shipped_qty = shipped_quantities.get(item.id, item.requested_quantity)
            
            item.shipped_quantity = shipped_qty
            item.updated_by = user
            item.save()

            # Deduct from source warehouse
            try:
                stock = InventoryStock.objects.get(
                    product=item.product,
                    warehouse=transfer.from_warehouse,
                    is_deleted=False
                )

                if stock.quantity < shipped_qty:
                    raise ValueError(f'产品 {item.product.name} 库存不足，当前库存：{stock.quantity}，发货数量：{shipped_qty}')

                # Record transaction (updates stock)
                InventoryTransaction.objects.create(
                    product=item.product,
                    warehouse=transfer.from_warehouse,
                    transaction_type='out',
                    quantity=shipped_qty,
                    transaction_date=timezone.now().date(),
                    reference_number=transfer.transfer_number,
                    notes=f'调拨出库 → {transfer.to_warehouse.name}',
                    operator=user,
                    created_by=user,
                )

            except InventoryStock.DoesNotExist:
                raise ValueError(f'产品 {item.product.name} 在源仓库 {transfer.from_warehouse.name} 中不存在库存')

        transfer.status = 'in_transit'
        transfer.updated_by = user
        transfer.save()
        return transfer

    @staticmethod
    @transaction.atomic
    def receive_transfer(transfer, user, received_quantities):
        """Receive transfer and add inventory."""
        for item in transfer.items.filter(is_deleted=False):
            received_qty = received_quantities.get(item.id, item.shipped_quantity)
            
            item.received_quantity = received_qty
            item.updated_by = user
            item.save()

            # Add to destination warehouse
            InventoryStock.objects.get_or_create(
                product=item.product,
                warehouse=transfer.to_warehouse,
                defaults={
                    'quantity': Decimal('0'),
                    'cost_price': item.unit_cost,
                    'created_by': user,
                }
            )

            # Record transaction (updates stock)
            InventoryTransaction.objects.create(
                product=item.product,
                warehouse=transfer.to_warehouse,
                transaction_type='in',
                quantity=received_qty,
                transaction_date=timezone.now().date(),
                reference_number=transfer.transfer_number,
                notes=f'调拨入库 ← {transfer.from_warehouse.name}',
                operator=user,
                created_by=user,
            )

        transfer.status = 'completed'
        transfer.actual_arrival_date = timezone.now().date()
        transfer.updated_by = user
        transfer.save()
        return transfer

class StockCountService:
    @staticmethod
    @transaction.atomic
    def create_count(user, data, items_data, counter_ids=None):
        """Create a new stock count."""
        if 'count_number' not in data:
            data['count_number'] = DocumentNumberGenerator.generate('CNT')
            
        count = StockCount.objects.create(
            created_by=user,
            updated_by=user,
            status='planned',
            **data
        )
        
        if counter_ids:
            count.counters.set(counter_ids)
            
        for item_data in items_data:
            # Get system quantity
            stock = InventoryStock.objects.filter(
                product_id=item_data['product_id'],
                warehouse=count.warehouse,
                is_deleted=False
            ).first()
            system_quantity = stock.quantity if stock else Decimal('0')
            
            StockCountItem.objects.create(
                count=count,
                system_quantity=system_quantity,
                created_by=user,
                updated_by=user,
                **item_data
            )
        return count

    @staticmethod
    @transaction.atomic
    def update_count(count, user, data, items_data, counter_ids=None):
        """Update an existing stock count."""
        for key, value in data.items():
            setattr(count, key, value)
        
        count.updated_by = user
        count.save()
        
        if counter_ids is not None:
            count.counters.set(counter_ids)
            
        if items_data is not None:
            count.items.all().delete()
            for item_data in items_data:
                # Get system quantity
                stock = InventoryStock.objects.filter(
                    product_id=item_data['product_id'],
                    warehouse=count.warehouse,
                    is_deleted=False
                ).first()
                system_quantity = stock.quantity if stock else Decimal('0')
                
                StockCountItem.objects.create(
                    count=count,
                    system_quantity=system_quantity,
                    created_by=user,
                    updated_by=user,
                    **item_data
                )
        return count

class InboundOrderService:
    @staticmethod
    @transaction.atomic
    def create_inbound(user, data, items_data):
        """Create a new inbound order."""
        if 'order_number' not in data:
            data['order_number'] = DocumentNumberGenerator.generate('IBO')
            
        inbound = InboundOrder.objects.create(
            created_by=user,
            updated_by=user,
            status='draft',
            **data
        )
        
        for item_data in items_data:
            InboundOrderItem.objects.create(
                inbound_order=inbound,
                created_by=user,
                updated_by=user,
                **item_data
            )
        return inbound
