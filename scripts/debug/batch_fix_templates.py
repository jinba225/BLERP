#!/usr/bin/env python3
"""
批量修复 Django 模板文件的结构问题

将 {% block extra_js %} 从文件开头移动到文件末尾
"""

import os
import re
from pathlib import Path


def fix_template_structure(file_path):
    """修复单个模板文件的结构"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查是否包含 extra_js 块
        if "{% block extra_js %}" not in content:
            return {"status": "skip", "message": "不包含 extra_js 块"}

        # 查找 extra_js 块
        extra_js_pattern = r"{%\s*block\s+extra_js\s*%}(.*?){%\s*endblock(?:\s+extra_js)?\s*%}"
        match = re.search(extra_js_pattern, content, re.DOTALL)

        if not match:
            return {"status": "skip", "message": "无法找到完整的 extra_js 块"}

        extra_js_block = match.group(0)
        extra_js_content = match.group(1).strip()

        # 移除原来的 extra_js 块
        content_without_extra_js = content[: match.start()] + content[match.end() :]

        # 在最后的 {% endblock %} 之后添加 extra_js
        # 查找最后一个 endblock（不考虑缩进和空格）
        endblock_pattern = r"{%\s*endblock\s*%}"
        endblock_matches = list(re.finditer(endblock_pattern, content_without_extra_js))

        if endblock_matches:
            # 在最后一个 endblock 后添加
            last_endblock = endblock_matches[-1]
            before = content_without_extra_js[: last_endblock.end()]
            after = content_without_extra_js[last_endblock.end() :]

            new_content = (
                before.rstrip()
                + "\n\n{% block extra_js %}\n"
                + extra_js_content
                + "\n{% endblock %}\n"
                + after
            )
        else:
            # 如果没有 endblock，在文件末尾添加
            new_content = (
                content_without_extra_js.rstrip()
                + "\n\n{% block extra_js %}\n"
                + extra_js_content
                + "\n{% endblock %}\n"
            )

        # 写回文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return {"status": "fixed", "message": "已修复"}

    except Exception as e:
        return {"status": "error", "message": f"错误: {str(e)}"}


def main():
    """主函数"""
    # 需要修复的文件列表
    files_to_fix = [
        "templates/modules/customers/customer_list.html",
        "templates/modules/customers/contact_list.html",
        "templates/modules/products/brand_list.html",
        "templates/modules/products/unit_list.html",
        "templates/modules/products/category_list.html",
        "templates/modules/products/product_list.html",
        "templates/modules/suppliers/supplier_list.html",
        "templates/modules/sales/delivery_list.html",
        "templates/modules/sales/order_list.html",
        "templates/modules/ecomm_sync/listing_list.html",
        "templates/modules/departments/budget_list.html",
        "templates/modules/departments/department_list.html",
        "templates/modules/departments/position_list.html",
        "templates/modules/ai_assistant/model_config_list.html",
        "templates/modules/inventory/report_stock_transaction.html",
        "templates/modules/inventory/inventory_order_report.html",
        "templates/modules/inventory/outbound_list.html",
        "templates/modules/inventory/count_list.html",
        "templates/modules/inventory/warehouse_list.html",
        "templates/modules/inventory/inbound_list.html",
        "templates/modules/inventory/report_stock_summary.html",
        "templates/modules/inventory/stock_list.html",
        "templates/modules/inventory/transfer_list.html",
        "templates/modules/inventory/adjustment_list.html",
        "templates/modules/inventory/report_stock_alert.html",
        "templates/modules/inventory/transaction_list.html",
        "templates/modules/users/role_list.html",
        "templates/modules/users/user_list.html",
        "templates/modules/purchase/return_list.html",
        "templates/modules/purchase/order_list.html",
        "templates/modules/purchase/quotation_list.html",
        "templates/modules/purchase/receipt_list.html",
        "templates/modules/purchase/inquiry_list.html",
        "templates/modules/purchase/borrow_list.html",
        "templates/modules/finance/account_list.html",
        "templates/modules/finance/expense_list.html",
        "templates/modules/finance/budget_list.html",
        "templates/modules/finance/report_list.html",
        "templates/modules/finance/customer_prepayment_list.html",
        "templates/modules/finance/payment_receipt_list.html",
        "templates/modules/finance/invoice_list.html",
        "templates/modules/finance/tax_rate_list.html",
        "templates/modules/finance/journal_list.html",
        "templates/modules/finance/payment_list.html",
        "templates/modules/finance/supplier_account_payment_list.html",
        "templates/modules/finance/payment_payment_list.html",
    ]

    base_dir = Path("/Users/janjung/Code_Projects/django_erp")

    print("=" * 80)
    print("批量修复 Django 模板文件结构")
    print("=" * 80)
    print(f"\n总共需要检查 {len(files_to_fix)} 个文件\n")

    fixed_count = 0
    error_count = 0
    skip_count = 0

    for file_path in files_to_fix:
        full_path = base_dir / file_path

        if not full_path.exists():
            print(f"⚠️  {file_path} - 文件不存在")
            continue

        result = fix_template_structure(full_path)

        if result["status"] == "fixed":
            print(f"✅ {file_path}")
            fixed_count += 1
        elif result["status"] == "error":
            print(f"❌ {file_path} - {result['message']}")
            error_count += 1
        else:
            print(f"⏭️  {file_path} - {result['message']}")
            skip_count += 1

    print("\n" + "=" * 80)
    print("修复完成统计：")
    print(f"  ✅ 成功修复: {fixed_count} 个文件")
    print(f"  ⏭️  跳过: {skip_count} 个文件")
    print(f"  ❌ 错误: {error_count} 个文件")
    print("=" * 80)


if __name__ == "__main__":
    main()
