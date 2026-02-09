#!/usr/bin/env python
"""
批量修复模板文件中的页面标题

将所有 "{% block title %}Page{% endblock %}" 替换为正确的中文标题
"""

import os
import re

# 定义每个模块的正确标题
TITLE_MAPPING = {
    # 采购模块
    'templates/modules/purchase/': {
        'order_list.html': '采购订单',
        'return_list.html': '采购退货',
        'request_list.html': '采购申请',
        'inquiry_list.html': '采购询价',
        'quotation_list.html': '供应商报价',
        'receipt_list.html': '采购收货',
        'borrow_list.html': '采购借用',
    },
    # 销售模块
    'templates/modules/sales/': {
        'order_list.html': '销售订单',
        'quote_list.html': '销售报价',
        'delivery_list.html': '销售发货',
        'return_list.html': '销售退货',
        'loan_list.html': '销售借货',
    },
    # 库存模块
    'templates/modules/inventory/': {
        'inbound_list.html': '采购入库',
        'outbound_list.html': '销售出库',
        'transfer_list.html': '库存调拨',
        'adjustment_list.html': '库存调整',
        'count_list.html': '库存盘点',
        'stock_list.html': '库存查询',
        'warehouse_list.html': '仓库管理',
        'location_list.html': '库位管理',
    },
    # 客户模块
    'templates/modules/customers/': {
        'customer_list.html': '客户管理',
        'contact_list.html': '联系人管理',
    },
    # 供应商模块
    'templates/modules/suppliers/': {
        'supplier_list.html': '供应商管理',
    },
    # 产品模块
    'templates/modules/products/': {
        'product_list.html': '产品管理',
        'category_list.html': '产品分类',
        'brand_list.html': '品牌管理',
        'unit_list.html': '计量单位',
    },
    # 财务模块
    'templates/modules/finance/': {
        'expense_list.html': '费用管理',
        'payment_list.html': '收付款管理',
        'invoice_list.html': '发票管理',
        'journal_list.html': '会计凭证',
        'account_list.html': '会计科目',
        'budget_list.html': '预算管理',
        'report_list.html': '财务报表',
        'supplier_account_list.html': '供应商应付',
        'customer_account_list.html': '客户应收',
    },
    # 部门模块
    'templates/modules/departments/': {
        'department_list.html': '部门管理',
        'position_list.html': '职位管理',
        'budget_list.html': '部门预算',
    },
    # AI助手模块
    'templates/modules/ai_assistant/': {
        'model_config_list.html': 'AI模型配置',
    },
    # 电商同步模块
    'templates/modules/ecomm_sync/': {
        'listing_list.html': '商品列表同步',
    },
}


def fix_title(file_path, correct_title):
    """修复单个文件的标题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找并替换标题
        pattern = r'\{% block title %\}Page\{% endblock %\}'
        replacement = f'{{% block title %}}{correct_title} - BetterLaser ERP{{% endblock %}}'

        if re.search(pattern, content):
            new_content = re.sub(pattern, replacement, content)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, '已修复'
        else:
            # 检查是否有其他形式的标题
            title_pattern = r'\{% block title %\}(.+?)\{% endblock %\}'
            match = re.search(title_pattern, content)
            if match:
                current_title = match.group(1).strip()
                if current_title == 'Page':
                    return False, f'已是Page（未匹配到标准格式）'
                else:
                    return False, f'已有标题: {current_title}'
            return False, '未找到标题块'
    except Exception as e:
        return False, f'错误: {str(e)}'


def scan_and_fix():
    """扫描并修复所有模板文件"""
    print(f"\n{'='*70}")
    print(f"批量修复模板页面标题")
    print(f"{'='*70}\n")

    fixed_count = 0
    skipped_count = 0
    error_count = 0

    for base_dir, files in TITLE_MAPPING.items():
        if not os.path.exists(base_dir):
            print(f"⚠️  目录不存在: {base_dir}")
            continue

        for filename, correct_title in files.items():
            file_path = os.path.join(base_dir, filename)

            # 跳过备份文件
            if file_path.endswith('.bak'):
                continue

            if not os.path.exists(file_path):
                print(f"⚠️  文件不存在: {file_path}")
                skipped_count += 1
                continue

            # 修复标题
            is_fixed, message = fix_title(file_path, correct_title)

            if is_fixed:
                print(f"✅ {file_path}")
                print(f"   → 修复为: {correct_title}")
                fixed_count += 1
            elif '错误' in message:
                print(f"❌ {file_path}")
                print(f"   → {message}")
                error_count += 1
            else:
                print(f"⊘ {file_path}")
                print(f"   → {message}")
                skipped_count += 1

    print(f"\n{'='*70}")
    print(f"修复统计:")
    print(f"  ✅ 已修复: {fixed_count} 个文件")
    print(f"  ⊘ 已跳过: {skipped_count} 个文件")
    print(f"  ❌ 错误: {error_count} 个文件")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    scan_and_fix()
