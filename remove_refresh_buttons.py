#!/usr/bin/env python3
import os
import re

def remove_refresh_buttons():
    """移除所有HTML文件中的刷新按钮和相关代码"""
    # 要处理的文件列表
    files = [
        # 采购相关
        'templates/modules/purchase/quotation_list.html',
        'templates/modules/purchase/inquiry_list.html',
        
        # 部门相关
        'templates/modules/departments/department_list.html',
        'templates/modules/departments/position_list.html',
        'templates/modules/departments/budget_list.html',
        
        # 财务相关
        'templates/modules/finance/payment_payment_list.html',
        'templates/modules/finance/supplier_account_payment_list.html',
        'templates/modules/finance/payment_list.html',
        'templates/modules/finance/journal_list.html',
        'templates/modules/finance/invoice_list.html',
        'templates/modules/finance/payment_receipt_list.html',
        'templates/modules/finance/budget_list.html',
        'templates/modules/finance/account_list.html',
        'templates/modules/finance/tax_rate_list.html',
        
        # 库存相关
        'templates/modules/inventory/adjustment_list.html',
        'templates/modules/inventory/transfer_list.html',
        'templates/modules/inventory/inbound_list.html',
        'templates/modules/inventory/count_list.html',
        'templates/modules/inventory/outbound_list.html',
        'templates/modules/inventory/warehouse_list.html',
        'templates/modules/inventory/transaction_list.html',
        'templates/modules/inventory/stock_list.html',
        
        # 销售相关
        'templates/modules/sales/quote_list.html',
        'templates/modules/sales/loan_list.html',
        'templates/modules/sales/order_list.html',
        'templates/modules/sales/return_list.html',
        'templates/modules/sales/delivery_list.html',
        
        # 客户相关
        'templates/modules/customers/customer_list.html',
        
        # 产品相关
        'templates/modules/products/unit_list.html',
        'templates/modules/products/product_list.html',
        'templates/modules/products/category_list.html',
        'templates/modules/products/brand_list.html',
        
        # 用户相关
        'templates/modules/users/user_list.html',
        'templates/modules/users/login_log_list.html',
        'templates/modules/users/role_list.html',
        
        # AI助手相关
        'templates/modules/ai_assistant/model_config_list.html',
        
        # 电商同步相关
        'templates/modules/ecomm_sync/listing_list.html',
    ]
    
    base_dir = '/Users/janjung/Code_Projects/django_erp'
    
    for file_path in files:
        full_path = os.path.join(base_dir, file_path)
        if not os.path.exists(full_path):
            print(f"文件不存在: {full_path}")
            continue
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 移除 usePageRefresh 指令
            content = re.sub(r'\s*x-data="usePageRefresh\(\{[^}]*\}\)"', '', content)
            
            # 移除刷新按钮
            refresh_button_pattern = re.compile(r'\s*<button type="button" @click="manualRefresh"[^>]*>.*?<\/button>', re.DOTALL)
            content = refresh_button_pattern.sub('', content)
            
            # 移除 isRefreshing 相关代码
            content = re.sub(r':disabled="isRefreshing"', '', content)
            content = re.sub(r':class="\{ \'animate-spin\': isRefreshing \}"', '', content)
            content = re.sub(r'x-text="isRefreshing \? \'刷新中\.\.\.\' : \'刷新\'"', '刷新', content)
            
            # 写回文件
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"处理完成: {file_path}")
        except Exception as e:
            print(f"处理文件时出错 {file_path}: {e}")

if __name__ == '__main__':
    remove_refresh_buttons()
