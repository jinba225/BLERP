#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BetterLaser ERP - Font Awesome → Heroicons 批量替换脚本
版本: v1.0
用途: 自动将模板中的 Font Awesome 图标替换为 Heroicons 图标
"""

import os
import re
from pathlib import Path

# Font Awesome → Heroicons 映射表
ICON_MAPPING = {
    # 基础图标
    'fa-times': ('x-mark', '1.5'),
    'fa-plus': ('plus', '1.5'),
    'fa-check': ('check', '1.5'),
    'fa-check-circle': ('check-circle', '1.5'),
    'fa-chevron-left': ('chevron-left', '1.5'),
    'fa-chevron-right': ('chevron-right', '1.5'),
    'fa-arrow-left': ('arrow-left', '1.5'),
    'fa-arrow-right': ('arrow-right', '1.5'),
    'fa-bars': ('bars-3', '1.5'),

    # 操作图标
    'fa-edit': ('pencil', '1.5'),
    'fa-trash': ('trash', '1.5'),
    'fa-trash-alt': ('trash', '1.5'),  # Font Awesome 6 别名
    'fa-search': ('magnifying-glass', '1.5'),
    'fa-eye': ('eye', '1.5'),
    'fa-save': ('check', '1.5'),  # 使用 check 图标代替
    'fa-file-alt': ('document', '1.5'),
    'fa-file': ('document', '1.5'),
    'fa-print': ('printer', '1.5'),
    'fa-sync': ('arrow-path', '1.5'),
    'fa-redo': ('arrow-path', '1.5'),
    'fa-refresh': ('arrow-path', '1.5'),
    'fa-list': ('queue-list', '1.5'),
    'fa-list-ul': ('queue-list', '1.5'),
    'fa-download': ('arrow-down-tray', '1.5'),

    # 状态图标
    'fa-info-circle': ('information-circle', '1.5'),
    'fa-exclamation-triangle': ('exclamation-triangle', '1.5'),
    'fa-exclamation-circle': ('exclamation-circle', '1.5'),
    'fa-times-circle': ('x-circle', '1.5'),
    'fa-check-circle': ('check-circle', '1.5'),

    # 用户相关
    'fa-user': ('user', '1.5'),
    'fa-users': ('users', '1.5'),
    'fa-user-tag': ('user-shield', '1.5'),
    'fa-user-shield': ('user-shield', '1.5'),

    # 其他常用
    'fa-clock': ('clock', '1.5'),
    'fa-envelope': ('envelope', '1.5'),
    'fa-star': ('star', '1.5'),
    'fa-inbox': ('inbox', '1.5'),
    'fa-building': ('building', '1.5'),
    'fa-money-bill-wave': ('currency-dollar', '1.5'),
    'fa-dollar-sign': ('currency-dollar', '1.5'),
    'fa-external-link-alt': ('external-link', '1.5'),
    'fa-external-link': ('external-link', '1.5'),
    'fa-bell': ('bell', '1.5'),
    'fa-home': ('home', '1.5'),
    'fa-calendar': ('calendar-days', '1.5'),
    'fa-calendar-alt': ('calendar-days', '1.5'),
    'fa-chart-bar': ('chart-bar', '1.5'),
    'fa-cog': ('cog', '1.5'),
    'fa-cogs': ('cog', '1.5'),
    'fa-key': ('key', '1.5'),
    'fa-lock': ('lock-closed', '1.5'),
    'fa-unlock': ('lock-open', '1.5'),
    'fa-chevron-down': ('chevron-down', '1.5'),
    'fa-chevron-up': ('chevron-up', '1.5'),

    # 补充缺失的图标
    'fa-shopping-cart': ('shopping-cart', '1.5'),  # 需要添加
    'fa-file-invoice': ('document', '1.5'),  # 使用 document 代替
    'fa-boxes': ('inbox', '1.5'),  # 使用 inbox 代替
    'fa-box': ('inbox', '1.5'),  # 使用 inbox 代替
    'fa-circle': ('circle', '1.5'),  # 需要添加
    'fa-times-circle': ('x-circle', '1.5'),
    'fa-industry': ('building', '1.5'),  # 使用 building 代替
    'fa-sign-in-alt': ('arrow-right-on-rectangle', '1.5'),  # 需要添加
    'fa-spin': ('arrow-path', '1.5'),  # 使用 arrow-path 代替
    'fa-arrow-up': ('arrow-up', '1.5'),  # 需要添加
    'fa-chart-line': ('chart-bar', '1.5'),  # 使用 chart-bar 代替
    'fa-warehouse': ('building', '1.5'),  # 使用 building 代替
    'fa-palette': ('sparkles', '1.5'),  # 使用 sparkles 代替
    'fa-shopping-bag': ('shopping-bag', '1.5'),  # 需要添加
    'fa-hand-holding': ('gift', '1.5'),  # 使用 gift 代替
    'fa-clipboard-list': ('clipboard', '1.5'),  # 使用 clipboard 代替
    'fa-filter': ('funnel', '1.5'),  # 需要添加
    'fa-th': ('squares-2x2', '1.5'),  # 需要添加
    'fa-columns': ('columns', '1.5'),  # 需要添加
    'fa-sort': ('bars-arrow-up', '1.5'),  # 需要添加
    'fa-sort-amount-down': ('bars-arrow-down', '1.5'),  # 需要添加
    'fa-caret-down': ('chevron-down', '1.5'),  # 使用 chevron-down
    'fa-caret-up': ('chevron-up', '1.5'),  # 使用 chevron-up
    'fa-caret-left': ('chevron-left', '1.5'),  # 使用 chevron-left
    'fa-caret-right': ('chevron-right', '1.5'),  # 使用 chevron-right
    'fa-angle-left': ('chevron-left', '1.5'),  # 使用 chevron-left
    'fa-angle-right': ('chevron-right', '1.5'),  # 使用 chevron-right
    'fa-angle-down': ('chevron-down', '1.5'),  # 使用 chevron-down
    'fa-angle-up': ('chevron-up', '1.5'),  # 使用 chevron-up
    'fa-question-circle': ('question-mark-circle', '1.5'),  # 需要添加
    'fa-minus': ('minus', '1.5'),  # 需要添加
    'fa-plus-circle': ('plus-circle', '1.5'),  # 需要添加
    'fa-minus-circle': ('minus-circle', '1.5'),  # 需要添加
    'fa-ellipsis-h': ('ellipsis-horizontal', '1.5'),  # 需要添加
    'fa-ellipsis-v': ('ellipsis-vertical', '1.5'),  # 需要添加
    'fa-copy': ('document-duplicate', '1.5'),  # 需要添加
    'fa-paste': ('clipboard-document', '1.5'),  # 需要添加
    'fa-cog': ('cog', '1.5'),
    'fa-cogs': ('cog', '1.5'),
    'fa-wrench': ('wrench', '1.5'),  # 需要添加
    'fa-tools': ('wrench', '1.5'),  # 使用 wrench 代替
    'fa-expand': ('arrows-pointing-out', '1.5'),  # 需要添加
    'fa-compress': ('arrows-pointing-in', '1.5'),  # 需要添加
    'fa-expand-alt': ('arrows-pointing-out', '1.5'),
    'fa-compress-alt': ('arrows-pointing-in', '1.5'),
    'fa-calendar-alt': ('calendar-days', '1.5'),
}


def replace_fontawesome_icon(match):
    """
    替换单个 Font Awesome 图标为 Heroicons 图标
    """
    full_match = match.group(0)
    icon_class = match.group(1)

    # 提取图标名称（去除 fa- 前缀）
    icon_name = icon_class.replace('fa-', '')

    # 获取对应的 Heroicons 图标
    if icon_name not in ICON_MAPPING:
        print(f"⚠️  警告: 未找到映射 '{icon_name}'，保持原样")
        return full_match

    heroicon_name, stroke_width = ICON_MAPPING[icon_name]

    # 提取额外的 class
    extra_classes = re.findall(r'class="([^"]*)"', full_match)
    if extra_classes:
        # 保留原有的 class，但移除 Font Awesome 相关的
        classes = extra_classes[0].split()
        filtered_classes = [c for c in classes if not c.startswith('fa-') and c != 'fas' and c != 'far' and c != 'fab']
        class_str = ' '.join(filtered_classes) if filtered_classes else 'w-5 h-5'
    else:
        class_str = 'w-5 h-5'

    # 生成 Heroicons SVG
    heroicon_svg = f'''<svg x-data="heroicon('{heroicon_name}', {stroke_width})" class="{class_str}" fill="none" :view-box="viewBox" :stroke-width="strokeWidth" stroke="currentColor" x-cloak><span x-html="svg"></span></svg>'''

    return heroicon_svg


def process_file(file_path):
    """
    处理单个 HTML 文件，替换 Font Awesome 图标
    """
    print(f"📄 处理文件: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 匹配 Font Awesome 图标
    # 匹配格式: <i class="fas fa-icon-name"></i> 或 <i class="fas fa-icon-name extra-class"></i>
    # 更宽松的正则表达式，匹配各种 Font Awesome 图标格式
    pattern = re.compile(r'<i\s+class="[^"]*\bfa[sr]?\b[^"]*?\bfa-([a-z-]+)\b[^"]*"[^>]*>\s*</i>')

    # 替换所有匹配的图标
    content = pattern.sub(replace_fontawesome_icon, content)

    # 如果内容有变化，写回文件
    if content != original_content:
        # 备份原文件
        backup_path = str(file_path) + '.bak'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)

        # 写入新内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 统计替换数量
        original_count = len(pattern.findall(original_content))
        new_count = len(pattern.findall(content))
        replaced_count = original_count - new_count

        print(f"  ✅ 已替换 {replaced_count} 个图标")
        print(f"  💾 备份文件: {backup_path}")
        return replaced_count
    else:
        print(f"  ℹ️  无需替换")
        return 0


def main():
    """
    主函数：批量替换模板中的 Font Awesome 图标
    """
    # 项目根目录
    project_root = Path(__file__).parent.parent
    templates_dir = project_root / 'templates'

    print("=" * 60)
    print("BetterLaser ERP - Font Awesome → Heroicons 批量替换")
    print("=" * 60)
    print()

    # 统计信息
    total_files = 0
    total_replaced = 0

    # 遍历所有 HTML 模板文件
    for html_file in templates_dir.rglob('*.html'):
        # 跳过备份文件
        if html_file.name.endswith('.bak'):
            continue

        try:
            replaced = process_file(html_file)
            total_files += 1
            total_replaced += replaced
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            print()

    print()
    print("=" * 60)
    print(f"✅ 处理完成!")
    print(f"   - 处理文件数: {total_files}")
    print(f"   - 替换图标数: {total_replaced}")
    print(f"   - 备份文件扩展名: .bak")
    print()
    print("⚠️  注意:")
    print("   1. 所有原文件都已备份为 .bak 文件")
    print("   2. 如有问题，可以手动恢复备份文件")
    print("   3. 确认无误后，可以删除 .bak 备份文件")
    print("=" * 60)


if __name__ == '__main__':
    main()
