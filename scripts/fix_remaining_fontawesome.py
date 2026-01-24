#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复剩余的 Font Awesome 特殊用例

包括：
1. Django 模板中的动态类名
2. JavaScript 对象中的图标配置
3. SVG class 属性中的 fa- 类名（残留）
"""

import re
from pathlib import Path


def fix_user_detail(file_path):
    """修复 users/user_detail.html 中的动态图标"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 情况1：账户状态图标
    pattern1 = r'<i class="fas fa-\{% if user\.is_active %\}check-circle\{% else %\}times-circle\{% endif %\} text-\{% if user\.is_active %\}green\{% else %\}red\{% endif %\}-600"></i>'

    replacement1 = '''{% if user.is_active %}
<svg class="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
</svg>
{% else %}
<svg class="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
</svg>
{% endif %}'''

    content = re.sub(pattern1, replacement1, content)

    # 情况2：性别图标（由于转义问题，使用字符串拼接）
    search_str = "<i class=\"fas fa-{% if user.gender == 'M' %}mars{% elif user.gender == 'F' %}venus{% else %}genderless{% endif %} mr-2 text-gray-400\"></i>"

    replacement2 = """{% if user.gender == 'M' %}
<svg class="w-5 h-5 mr-2 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
</svg>
{% elif user.gender == 'F' %}
<svg class="w-5 h-5 mr-2 text-pink-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
</svg>
{% else %}
<svg class="w-5 h-5 mr-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
</svg>
{% endif %}"""

    content = content.replace(search_str, replacement2)

    # 情况3：超级用户图标
    search_str3 = '<i class="fas fa-{% if user.is_superuser %}check-circle text-green-500{% else %}times-circle text-gray-300{% endif %} mr-2"></i>'

    replacement3 = """{% if user.is_superuser %}
<svg class="w-5 h-5 mr-2 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
</svg>
{% else %}
<svg class="w-5 h-5 mr-2 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
</svg>
{% endif %}"""

    content = content.replace(search_str3, replacement3)

    # 情况4：员工图标
    search_str4 = '<i class="fas fa-{% if user.is_staff %}check-circle text-green-500{% else %}times-circle text-gray-300{% endif %} mr-2"></i>'

    replacement4 = """{% if user.is_staff %}
<svg class="w-5 h-5 mr-2 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
</svg>
{% else %}
<svg class="w-5 h-5 mr-2 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
</svg>
{% endif %}"""

    content = content.replace(search_str4, replacement4)

    # 情况5：活跃状态图标
    search_str5 = '<i class="fas fa-{% if user.is_active %}check-circle text-green-500{% else %}times-circle text-red-500{% endif %} mr-2"></i>'

    replacement5 = """{% if user.is_active %}
<svg class="w-5 h-5 mr-2 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
</svg>
{% else %}
<svg class="w-5 h-5 mr-2 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
</svg>
{% endif %}"""

    content = content.replace(search_str5, replacement5)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 已修复: {file_path.name}")


def fix_user_list(file_path):
    """修复 users/user_list.html 中的动态图标"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 用户状态图标
    search_str = '<i class="fas fa-{% if user.is_active %}ban{% else %}check{% endif %}"></i>'

    replacement = """{% if user.is_active %}
<svg class="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
</svg>
{% else %}
<svg class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
</svg>
{% endif %}"""

    content = content.replace(search_str, replacement)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 已修复: {file_path.name}")


def fix_svg_class_attributes(file_path):
    """修复 SVG class 属性中残留的 fa- 类名"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配 SVG class 属性中的 fa- 类名
    pattern = r'<svg class="icon ([^"]*fa-[^"]*)"'

    def replace_svg_class(match):
        classes = match.group(1).split()
        # 移除所有 fa-* 类
        cleaned_classes = [c for c in classes if not c.startswith('fa-')]
        return f'<svg class="icon {" ".join(cleaned_classes)}"'

    new_content = re.sub(pattern, replace_svg_class, content)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✓ 已修复 SVG class: {file_path.name}")
        return True
    return False


def fix_borrow_form_arrow(file_path):
    """修复 purchase/borrow_form.html 中的箭头类名"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r"arrow\.className = 'fas fa-chevron-down searchable-select-arrow';"
    replacement = """arrow.className = 'searchable-select-arrow';"""

    content = content.replace(pattern, replacement)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 已修复: {file_path.name}")


def fix_expense_detail_svg_class(file_path):
    """修复 finance/expense_detail.html 中的 SVG class"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 移除 SVG class 中的 fa- 类名
    pattern = r'<svg class="icon ([^"]*fa-[^"]*)"'

    def replace_svg_class(match):
        classes = match.group(1).split()
        cleaned_classes = [c for c in classes if not c.startswith('fa-')]
        if cleaned_classes:
            return f'<svg class="icon {" ".join(cleaned_classes)}"'
        return '<svg class="icon"'

    new_content = re.sub(pattern, replace_svg_class, content)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✓ 已修复: {file_path.name}")


def main():
    """主函数"""
    templates_dir = Path('templates')

    print("=" * 70)
    print("修复剩余的 Font Awesome 特殊用例")
    print("=" * 70)
    print()

    # 修复 user_detail.html
    user_detail = templates_dir / 'users' / 'user_detail.html'
    if user_detail.exists():
        fix_user_detail(user_detail)

    # 修复 user_list.html
    user_list = templates_dir / 'users' / 'user_list.html'
    if user_list.exists():
        fix_user_list(user_list)

    # 修复 SVG class 属性中的残留
    svg_class_files = [
        'sales/template_editor_hiprint.html',
        'sales/template_editor_hiprint_standalone.html',
        'finance/expense_detail.html',
    ]

    for file_name in svg_class_files:
        file_path = templates_dir / file_name
        if file_path.exists():
            fix_svg_class_attributes(file_path)

    # 修复 borrow_form.html
    borrow_form = templates_dir / 'purchase' / 'borrow_form.html'
    if borrow_form.exists():
        fix_borrow_form_arrow(borrow_form)

    print()
    print("=" * 70)
    print("修复完成！")
    print("=" * 70)
    print()
    print("说明：")
    print("- HiPrint 模板编辑器中的 JavaScript 对象图标配置保持不变")
    print("  (这些只是字符串标识符，不是实际的 HTML 元素)")
    print()


if __name__ == '__main__':
    main()
