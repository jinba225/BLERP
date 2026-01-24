#!/usr/bin/env python
"""
Script to delete all sales documents including quotes, sales orders, deliveries, and returns.
This script handles the deletion in the correct order to respect foreign key relationships.
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/janjung/Code_Projects/django_erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')

django.setup()

from apps.sales.models import Quote, QuoteItem, SalesOrder, SalesOrderItem, Delivery, DeliveryItem, SalesReturn, SalesReturnItem

def delete_sales_documents():
    """
    Delete all sales documents in the correct order to respect foreign key constraints.
    """
    print("开始删除销售模块所有单据...")
    
    # 首先删除明细表数据
    print("1. 删除销售退货明细...")
    sales_return_items_deleted = SalesReturnItem.objects.all().delete()
    print(f"   已删除 {sales_return_items_deleted[0]} 条销售退货明细")
    
    print("2. 删除销售发货明细...")
    delivery_items_deleted = DeliveryItem.objects.all().delete()
    print(f"   已删除 {delivery_items_deleted[0]} 条销售发货明细")
    
    print("3. 删除销售订单明细...")
    sales_order_items_deleted = SalesOrderItem.objects.all().delete()
    print(f"   已删除 {sales_order_items_deleted[0]} 条销售订单明细")
    
    print("4. 删除销售报价明细...")
    quote_items_deleted = QuoteItem.objects.all().delete()
    print(f"   已删除 {quote_items_deleted[0]} 条销售报价明细")
    
    # 然后删除主表数据
    print("5. 删除销售退货单...")
    sales_returns_deleted = SalesReturn.objects.all().delete()
    print(f"   已删除 {sales_returns_deleted[0]} 条销售退货单")
    
    print("6. 删除销售发货单...")
    deliveries_deleted = Delivery.objects.all().delete()
    print(f"   已删除 {deliveries_deleted[0]} 条销售发货单")
    
    print("7. 删除销售订单...")
    sales_orders_deleted = SalesOrder.objects.all().delete()
    print(f"   已删除 {sales_orders_deleted[0]} 条销售订单")
    
    print("8. 删除销售报价单...")
    quotes_deleted = Quote.objects.all().delete()
    print(f"   已删除 {quotes_deleted[0]} 条销售报价单")
    
    print("\n所有销售模块单据已删除完成！")

if __name__ == '__main__':
    delete_sales_documents()
