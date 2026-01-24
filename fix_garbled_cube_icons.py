#!/usr/bin/env python
"""
批量修复乱码的立方体/产品图标
修复80+个模板文件中的乱码SVG路径
"""
import os
import re

# 乱码的立方体图标路径（需要替换）
GARBLED_PATH = r'd="M22 12h-6m-6 0h6m-6 0a3 3 0 01-6 0m6 0a3 3 0 006 0m-6 0V7m6 5V7m-6 5h6m-6 0a3 3 0 01-6 0m6 0a3 3 0 006 0m-6 0V7"'

# 正确的立方体图标路径（产品/盒子图标）
CORRECT_PATH = r'd="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"'

def fix_icon_in_file(file_path):
    """替换单个文件中的乱码图标路径"""
    if not os.path.exists(file_path):
        print(f"⚠️  文件不存在: {file_path}")
        return 0

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 使用正则表达式替换
    pattern = re.compile(GARBLED_PATH)
    matches = pattern.findall(content)

    if not matches:
        print(f"ℹ️  未找到乱码图标: {file_path}")
        return 0

    # 执行替换
    new_content = pattern.sub(CORRECT_PATH, content)

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ 已修复 {file_path} ({len(matches)} 处)")
    return len(matches)

def main():
    """批量处理所有文件"""
    print("🚀 开始批量修复乱码图标...")
    print(f"共需修复所有包含乱码路径的模板文件\n")

    # 通过grep命令找到的所有文件列表
    files_to_fix = [
        'templates/customers/customer_list.html',
        'templates/products/brand_list.html',
        'templates/products/unit_list.html',
        'templates/products/category_list.html',
        'templates/products/product_list.html',
        'templates/core/database_management.html',
        'templates/suppliers/supplier_list.html',
        'templates/sales/loan_detail.html',
        'templates/sales/delivery_list.html',
        'templates/sales/return_list.html',
        'templates/sales/order_list.html',
        'templates/sales/loan_list.html',
        'templates/sales/return_confirm_receive.html',
        'templates/sales/return_detail.html',
        'templates/sales/quote_list.html',
        'templates/departments/budget_list.html',
        'templates/departments/department_tree.html',
        'templates/departments/organization_chart.html',
        'templates/departments/department_list.html',
        'templates/departments/budget_summary.html',
        'templates/departments/position_list.html',
        'templates/dashboard.html',
        'templates/ai_assistant/model_config_list.html',
        'templates/inventory/report_inbound_outbound_statistics.html',
        'templates/inventory/report_stock_transaction.html',
        'templates/inventory/inbound_form.html',
        'templates/inventory/outbound_list.html',
        'templates/inventory/count_list.html',
        'templates/inventory/warehouse_detail.html',
        'templates/inventory/stock_import.html',
        'templates/inventory/inbound_detail.html',
        'templates/inventory/warehouse_list.html',
        'templates/inventory/inbound_list.html',
        'templates/inventory/outbound_form.html',
        'templates/inventory/count_form.html',
        'templates/inventory/outbound_detail.html',
        'templates/inventory/stock_list.html',
        'templates/inventory/transfer_list.html',
        'templates/inventory/adjustment_list.html',
        'templates/inventory/transaction_list.html',
        'templates/inventory/count_detail.html',
        'templates/inventory/transfer_form.html',
        'templates/users/login_log_list.html',
        'templates/users/role_list.html',
        'templates/users/user_list.html',
        'templates/purchase/order_list.html',
        'templates/purchase/quotation_list.html',
        'templates/purchase/inquiry_list.html',
        'templates/purchase/return_detail.html',
        'templates/purchase/borrow_detail.html',
        'templates/purchase/borrow_list.html',
        'templates/finance/account_list.html',
        'templates/finance/expense_list.html',
        'templates/finance/budget_list.html',
        'templates/finance/report_list.html',
        'templates/finance/customer_account_list.html',
        'templates/finance/supplier_account_detail.html',
        'templates/finance/dashboard.html',
        'templates/finance/payment_receipt_list.html',
        'templates/finance/account_detail.html',
        'templates/finance/customer_account_detail.html',
        'templates/finance/invoice_list.html',
        'templates/finance/supplier_account_list.html',
        'templates/finance/tax_rate_list.html',
        'templates/finance/journal_list.html',
        'templates/finance/payment_list.html',
        'templates/finance/payment_payment_list.html',
    ]

    total_fixed = 0
    success_files = 0

    for file_path in files_to_fix:
        full_path = os.path.join('/Users/janjung/Code_Projects/django_erp', file_path)
        count = fix_icon_in_file(full_path)
        if count > 0:
            total_fixed += count
            success_files += 1

    print(f"\n{'='*60}")
    print(f"✨ 批量修复完成！")
    print(f"📊 成功处理: {success_files}/{len(files_to_fix)} 个文件")
    print(f"🔧 总计修复: {total_fixed} 处乱码图标")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
