"""
Sales services for the ERP system.
Handles business logic for Quotes and Sales Orders.
"""
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from sales.models import Quote, QuoteItem, SalesOrder, SalesOrderItem
from core.utils import DocumentNumberGenerator

class QuoteService:
    @staticmethod
    @transaction.atomic
    def create_quote(user, quote_data, items_data):
        """
        Create a new quote.
        
        Args:
            user: User creating the quote
            quote_data: Dictionary of quote fields
            items_data: List of dictionaries for quote items
            
        Returns:
            Created Quote instance
        """
        # Generate quote number if not provided
        if 'quote_number' not in quote_data:
            quote_data['quote_number'] = DocumentNumberGenerator.generate('quotation')
            
        quote = Quote(**quote_data)
        quote.created_by = user
        quote.save()
        
        for item_data in items_data:
            QuoteItem.objects.create(
                quote=quote,
                created_by=user,
                **item_data
            )
            
        quote.calculate_totals()
        quote.save()
        
        return quote

    @staticmethod
    @transaction.atomic
    def update_quote(quote, user, quote_data, items_data):
        """
        Update an existing quote.
        
        Args:
            quote: Quote instance to update
            user: User updating the quote
            quote_data: Dictionary of fields to update
            items_data: List of dictionaries for items (replaces existing items)
            
        Returns:
            Updated Quote instance
        """
        # Update quote fields
        for key, value in quote_data.items():
            setattr(quote, key, value)
        
        quote.updated_by = user
        quote.save()
        
        # Update items - Strategy: Delete all and recreate (simple but effective for this scale)
        if items_data is not None:
            quote.items.all().delete()
            for item_data in items_data:
                QuoteItem.objects.create(
                    quote=quote,
                    created_by=user if not item_data.get('id') else None, # preserve creator if needed?
                    updated_by=user,
                    **item_data
                )
        
        quote.calculate_totals()
        quote.save()
        
        return quote

class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(user, order_data, items_data):
        """
        Create a new sales order.
        """
        if 'order_number' not in order_data:
            order_data['order_number'] = DocumentNumberGenerator.generate('sales_order')
            
        order = SalesOrder(**order_data)
        order.created_by = user
        order.save()
        
        for idx, item_data in enumerate(items_data):
            # Filter out empty items if any
            if not item_data.get('product_id') and not item_data.get('product'):
                continue
                
            SalesOrderItem.objects.create(
                order=order,
                created_by=user,
                sort_order=idx,
                **item_data
            )
            
        order.calculate_totals()
        order.save()
        
        return order

    @staticmethod
    @transaction.atomic
    def update_order(order, user, order_data, items_data):
        """
        Update an existing sales order.
        """
        for key, value in order_data.items():
            setattr(order, key, value)
            
        order.updated_by = user
        order.save()
        
        if items_data is not None:
            order.items.all().delete()
            for idx, item_data in enumerate(items_data):
                if not item_data.get('product_id') and not item_data.get('product'):
                    continue
                    
                SalesOrderItem.objects.create(
                    order=order,
                    created_by=user, # Re-creating items, so user is creator of new item
                    sort_order=idx,
                    **item_data
                )
                
        order.calculate_totals()
        order.save()
        
        return order

    @staticmethod
    @transaction.atomic
    def convert_quote_to_order(quote, user, extra_data=None):
        """
        Convert a quote to a sales order.
        """
        if extra_data is None:
            extra_data = {}
            
        order = quote.convert_to_order()
        order.created_by = user
        
        for key, value in extra_data.items():
            if hasattr(order, key) and value is not None:
                setattr(order, key, value)
                
        order.save()
        return order
