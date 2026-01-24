#!/usr/bin/env python
"""
批量替换复杂user-group图标为简单user图标
替换20+个模板文件中的问题SVG路径
"""
import os
import re

# 复杂的user-group图标路径（导致乱码）
COMPLEX_PATH = r'd="M12 4\.354a4 4 0 110 5\.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5\.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"'

# 简单的user图标路径（可靠渲染）
SIMPLE_PATH = r'd="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"'

# 需要处理的文件列表
FILES_TO_FIX = [
    'templates/dashboard.html',
    'templates/index.html',
    'templates/departments/partials/tree_node.html',
    'templates/departments/department_list.html',
    'templates/departments/department_detail.html',
    'templates/departments/position_detail.html',
    'templates/departments/organization_chart.html',
    'templates/users/role_list.html',
    'templates/users/role_detail.html',
    'templates/users/role_permissions.html',
    'templates/users/role_confirm_delete.html',
    'templates/users/role_assign_users.html',
    'templates/customers/contact_list.html',
    'templates/customers/list.html',
    'templates/sales/template_list.html',
    'templates/core/database_management.html',
]

def fix_icon_in_file(file_path):
    """替换单个文件中的图标路径"""
    if not os.path.exists(file_path):
        print(f"⚠️  文件不存在: {file_path}")
        return 0

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 使用正则表达式替换
    pattern = re.compile(COMPLEX_PATH)
    matches = pattern.findall(content)

    if not matches:
        print(f"ℹ️  未找到问题图标: {file_path}")
        return 0

    # 执行替换
    new_content = pattern.sub(SIMPLE_PATH, content)

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ 已修复 {file_path} ({len(matches)} 处)")
    return len(matches)

def main():
    """批量处理所有文件"""
    print("🚀 开始批量修复图标...")
    print(f"共需处理 {len(FILES_TO_FIX)} 个文件\n")

    total_fixed = 0
    success_files = 0

    for file_path in FILES_TO_FIX:
        full_path = os.path.join('/Users/janjung/Code_Projects/django_erp', file_path)
        count = fix_icon_in_file(full_path)
        if count > 0:
            total_fixed += count
            success_files += 1

    print(f"\n{'='*60}")
    print(f"✨ 批量修复完成！")
    print(f"📊 成功处理: {success_files}/{len(FILES_TO_FIX)} 个文件")
    print(f"🔧 总计修复: {total_fixed} 处图标")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
