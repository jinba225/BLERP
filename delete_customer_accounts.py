#!/usr/bin/env python
"""
Script to delete all customer account receivable documents.
This script handles the deletion of customer account receivables and related data.
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/janjung/Code_Projects/django_erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')

django.setup()

from apps.finance.models import CustomerAccount, Payment

def delete_customer_accounts():
    """
    Delete all customer account receivables and related payments.
    """
    print("开始删除应收账款模块所有单据...")
    
    # 先删除相关付款记录（如果付款记录与客户账款关联）
    print("1. 删除与客户账款相关的付款记录...")
    # 这里只删除与客户账户相关的收款，而不删除所有付款
    customer_receipts_deleted = Payment.objects.filter(customer__isnull=False).delete()
    print(f"   已删除 {customer_receipts_deleted[0]} 条客户收付款记录")
    
    # 删除客户应收账款
    print("2. 删除客户应收账款...")
    customer_accounts_deleted = CustomerAccount.objects.all().delete()
    print(f"   已删除 {customer_accounts_deleted[0]} 条客户应收账款记录")
    
    print("\n所有应收账款模块单据已删除完成！")

if __name__ == '__main__':
    delete_customer_accounts()