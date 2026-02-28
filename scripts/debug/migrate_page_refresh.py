#!/usr/bin/env python
"""
批量迁移页面到新的刷新系统
"""

import os
import re
from pathlib import Path


def migrate_template_file(file_path):
    """
    迁移单个模板文件到新的刷新系统

    变更：
    1. 在主容器div添加 x-data="usePageRefresh({ interval: 30 })"
    2. 将刷新按钮的 id="refreshPageBtn" 改为 @click="manualRefresh"
    3. 将 :disabled 属性绑定到 isRefreshing
    4. 添加旋转动画 class=":class=\"{ 'animate-spin': isRefreshing }\"
    5. 将 span id="refreshBtnText" 改为 x-text="isRefreshing ? '刷新中...' : '刷新'"
    6. 删除底部的 <script> 标签（整个刷新相关的JavaScript代码）
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # 1. 检查是否已经有 x-data（避免重复迁移）
        if 'x-data="usePageRefresh' in content or "x-data='usePageRefresh" in content:
            return False, "已迁移"

        # 2. 在 {% block content %} 后找到第一个 <div> 标签，添加 x-data
        # 查找 block content 之后的内容
        block_content_pattern = r"{%\s*block\s+content\s*%}(.*?){%\s*endblock\s*%}"
        match = re.search(block_content_pattern, content, re.DOTALL)

        if not match:
            return False, "未找到 content block"

        content_block = match.group(1)

        # 查找第一个 class=" 的div标签
        div_pattern = r'(<div\s+class="[^"]*")'
        div_match = re.search(div_pattern, content_block)

        if not div_match:
            return False, "未找到主容器div"

        original_div = div_match.group(1)
        new_div = f'{original_div} x-data="usePageRefresh({{ interval: 30 }})"'

        # 只替换第一个div（主容器）
        content = content.replace(original_div, new_div, 1)

        # 3. 修改刷新按钮
        # 替换 id="refreshPageBtn" 为 @click="manualRefresh"
        content = re.sub(r'id="refreshPageBtn"', '@click="manualRefresh"', content)

        # 添加 :disabled="isRefreshing" 和 disabled class
        content = re.sub(
            r'(class="[^"]*")(\s*)title="刷新页面"',
            r'\1\2:disabled="isRefreshing"\2title="刷新页面"',
            content,
        )

        # 添加 disabled:opacity-50 disabled:cursor-not-allowed class
        content = re.sub(
            r'border border-gray-300 rounded-lg hover:bg-gray-50"(\s*)title="刷新页面"',
            r'border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"\1title="刷新页面"',
            content,
        )

        # 4. 添加旋转动画
        content = re.sub(
            r'<svg class="w-4 h-4 mr-2" fill="none"',
            r'<svg class="w-4 h-4 mr-2" :class="{ \'animate-spin\': isRefreshing }" fill="none"',
            content,
        )

        # 5. 替换 span 内容
        content = re.sub(
            r'<span id="refreshBtnText">刷新</span>',
            r'<span x-text="isRefreshing ? \'刷新中...\' : \'刷新\'"></span>',
            content,
        )

        # 6. 删除 <script> 标签（从 <script> 到 </script> 的整个块）
        # 只删除包含 refreshPageBtn 或 refreshPage 相关的 script
        script_pattern = r"<script>\n\(function\(\)\s*{[\s\S]*?}\)\(\);\n</script>\n"
        content = re.sub(script_pattern, "", content)

        # 如果没有变化，返回
        if content == original_content:
            return False, "无需变更"

        # 写回文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True, "迁移成功"

    except Exception as e:
        return False, f"错误: {str(e)}"


def main():
    """主函数"""
    base_dir = Path("/Users/janjung/Code_Projects/django_erp/templates/modules")

    # 定义要迁移的文件列表（按优先级）
    files_to_migrate = [
        # 优先级1：核心业务列表页
        "sales/order_list.html",
        "purchase/order_list.html",
        "inventory/inbound_list.html",
        "inventory/outbound_list.html",
        "customers/customer_list.html",
        "products/product_list.html",
        "suppliers/supplier_list.html",
        # 优先级2：财务相关
        "finance/expense_list.html",
        "finance/account_list.html",
        # 优先级3：其他列表页
        "sales/delivery_list.html",
        "sales/return_list.html",
        "sales/quote_list.html",
        "sales/loan_list.html",
        "purchase/receipt_list.html",
        "purchase/return_list.html",
        "purchase/quotation_list.html",
        "purchase/inquiry_list.html",
        "purchase/borrow_list.html",
        "inventory/stock_list.html",
        "inventory/transfer_list.html",
        "inventory/adjustment_list.html",
        "inventory/count_list.html",
        "inventory/transaction_list.html",
        "inventory/warehouse_list.html",
        "customers/contact_list.html",
        "products/category_list.html",
        "products/brand_list.html",
        "products/unit_list.html",
    ]

    print("=" * 60)
    print("Django ERP 页面刷新系统 - 批量迁移工具")
    print("=" * 60)
    print()

    success_count = 0
    skip_count = 0
    error_count = 0

    for file_rel_path in files_to_migrate:
        file_path = base_dir / file_rel_path

        if not file_path.exists():
            print(f"⚠️  跳过（文件不存在）: {file_rel_path}")
            skip_count += 1
            continue

        success, message = migrate_template_file(file_path)

        if success:
            print(f"✅ {message}: {file_rel_path}")
            success_count += 1
        elif "已迁移" in message or "无需变更" in message:
            print(f"⏭️  {message}: {file_rel_path}")
            skip_count += 1
        else:
            print(f"❌ {message}: {file_rel_path}")
            error_count += 1

    print()
    print("=" * 60)
    print("迁移完成！")
    print("=" * 60)
    print(f"✅ 成功: {success_count}")
    print(f"⏭️  跳过: {skip_count}")
    print(f"❌ 失败: {error_count}")
    print(f"📊 总计: {len(files_to_migrate)}")
    print()


if __name__ == "__main__":
    main()
