#!/usr/bin/env python3
import os
import re

def unify_search_card_heights():
    """统一所有搜索卡片中输入框和选择框的高度"""
    # 要处理的文件列表
    files = [
        # 采购相关
        'templates/modules/purchase/request_list.html',
        'templates/modules/purchase/borrow_list.html',
        'templates/modules/purchase/inquiry_list.html',
        'templates/modules/purchase/quotation_list.html',
        'templates/modules/purchase/order_list.html',
        'templates/modules/purchase/receipt_list.html',
        'templates/modules/purchase/return_list.html',
        
        # 库存相关
        'templates/modules/inventory/warehouse_list.html',
        'templates/modules/inventory/stock_list.html',
        'templates/modules/inventory/transaction_list.html',
        'templates/modules/inventory/outbound_list.html',
        'templates/modules/inventory/count_list.html',
        'templates/modules/inventory/inbound_list.html',
        'templates/modules/inventory/transfer_list.html',
        'templates/modules/inventory/adjustment_list.html',
        
        # 财务相关
        'templates/modules/finance/tax_rate_list.html',
        'templates/modules/finance/account_list.html',
        'templates/modules/finance/budget_list.html',
        'templates/modules/finance/payment_receipt_list.html',
        'templates/modules/finance/invoice_list.html',
        'templates/modules/finance/journal_list.html',
        'templates/modules/finance/payment_list.html',
        'templates/modules/finance/supplier_account_payment_list.html',
        'templates/modules/finance/payment_payment_list.html',
        'templates/modules/finance/expense_list.html',
        'templates/modules/finance/report_list.html',
        'templates/modules/finance/supplier_prepayment_list.html',
        'templates/modules/finance/customer_prepayment_list.html',
        'templates/modules/finance/supplier_account_list.html',
        
        # 部门相关
        'templates/modules/departments/budget_list.html',
        'templates/modules/departments/position_list.html',
        'templates/modules/departments/department_list.html',
        
        # 销售相关
        'templates/modules/sales/delivery_list.html',
        'templates/modules/sales/return_list.html',
        'templates/modules/sales/order_list.html',
        'templates/modules/sales/loan_list.html',
        'templates/modules/sales/quote_list.html',
        
        # 客户相关
        'templates/modules/customers/customer_list.html',
        'templates/modules/customers/contact_list.html',
        
        # 产品相关
        'templates/modules/products/brand_list.html',
        'templates/modules/products/category_list.html',
        'templates/modules/products/product_list.html',
        'templates/modules/products/unit_list.html',
        
        # 用户相关
        'templates/modules/users/role_list.html',
        'templates/modules/users/user_list.html',
        
        # 供应商相关
        'templates/modules/suppliers/supplier_list.html',
        
        # 其他
        'templates/modules/ecomm_sync/listing_list.html',
        'templates/modules/ai_assistant/model_config_list.html',
    ]
    
    base_dir = '/Users/janjung/Code_Projects/django_erp'
    
    # 统一的高度样式
    input_pattern = re.compile(r'(<input[^>]+class="[^>]*w-full\s+px-3\s+py-2)([^>]*)(")', re.DOTALL)
    select_pattern = re.compile(r'(<select[^>]+class="[^>]*w-full\s+px-3\s+py-2)([^>]*)(")', re.DOTALL)
    
    for file_path in files:
        full_path = os.path.join(base_dir, file_path)
        if not os.path.exists(full_path):
            print(f"文件不存在: {full_path}")
            continue
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 统一输入框高度
            content = input_pattern.sub(r'\1 h-10\2\3', content)
            
            # 统一下拉选择框高度
            content = select_pattern.sub(r'\1 h-10\2\3', content)
            
            # 写回文件
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"处理完成: {file_path}")
        except Exception as e:
            print(f"处理文件时出错 {file_path}: {e}")

if __name__ == '__main__':
    unify_search_card_heights()
