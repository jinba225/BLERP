#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BetterLaser ERP - Font Awesome → Heroicons 批量替换脚本 v2
版本: v2.0 - 修复映射表键名问题
用途: 自动将模板中的 Font Awesome 图标替换为 Heroicons 图标
"""

import os
import re
from pathlib import Path

# Font Awesome → Heroicons 映射表
# 注意：键名不包含 'fa-' 前缀
ICON_MAPPING = {
    # 基础图标
    'times': 'x-mark',
    'plus': 'plus',
    'check': 'check',
    'check-circle': 'check-circle',
    'chevron-left': 'chevron-left',
    'chevron-right': 'chevron-right',
    'chevron-down': 'chevron-down',
    'chevron-up': 'chevron-up',
    'arrow-left': 'arrow-left',
    'arrow-right': 'arrow-right',
    'arrow-up': 'arrow-up',
    'bars': 'bars-3',
    'angle-left': 'chevron-left',
    'angle-right': 'chevron-right',
    'angle-down': 'chevron-down',
    'angle-up': 'chevron-up',
    'caret-down': 'chevron-down',
    'caret-up': 'chevron-up',
    'caret-left': 'chevron-left',
    'caret-right': 'chevron-right',

    # 操作图标
    'pencil': 'pencil',
    'trash': 'trash',
    'trash-alt': 'trash',
    'search': 'magnifying-glass',
    'eye': 'eye',
    'save': 'check',
    'file-alt': 'document',
    'file': 'document',
    'print': 'printer',
    'sync': 'arrow-path',
    'redo': 'arrow-path',
    'refresh': 'arrow-path',
    'list': 'queue-list',
    'list-ul': 'queue-list',
    'download': 'arrow-down-tray',
    'edit': 'pencil',

    # 状态图标
    'info-circle': 'information-circle',
    'exclamation-triangle': 'exclamation-triangle',
    'exclamation-circle': 'exclamation-circle',
    'times-circle': 'x-circle',
    'check-circle': 'check-circle',
    'question-circle': 'question-mark-circle',

    # 用户相关
    'user': 'user',
    'users': 'users',
    'user-tag': 'user-shield',
    'user-shield': 'user-shield',
    'user-tie': 'user',

    # 其他常用
    'clock': 'clock',
    'envelope': 'envelope',
    'star': 'star',
    'inbox': 'inbox',
    'building': 'building',
    'money-bill-wave': 'currency-dollar',
    'dollar-sign': 'currency-dollar',
    'external-link-alt': 'external-link',
    'external-link': 'external-link',
    'bell': 'bell',
    'home': 'home',
    'calendar': 'calendar-days',
    'calendar-alt': 'calendar-days',
    'chart-bar': 'chart-bar',
    'chart-line': 'chart-bar',
    'cog': 'cog',
    'cogs': 'cog',
    'key': 'key',
    'lock': 'lock-closed',
    'unlock': 'lock-open',
    'warehouse': 'building',
    'industry': 'building',
    'palette': 'sparkles',
    'shopping-cart': 'shopping-cart',
    'shopping-bag': 'shopping-cart',
    'shopping-bag': 'shopping-cart',
    'file-invoice': 'document',
    'boxes': 'inbox',
    'box': 'inbox',
    'circle': 'circle',
    'sign-in-alt': 'arrow-right-on-rectangle',
    'spin': 'arrow-path',
    'filter': 'funnel',
    'th': 'squares-2x2',
    'columns': 'columns',
    'sort': 'bars-arrow-up',
    'sort-amount-down': 'bars-arrow-down',
    'sort-amount-up': 'bars-arrow-up',
    'minus': 'minus',
    'plus-circle': 'plus-circle',
    'minus-circle': 'minus-circle',
    'ellipsis-h': 'ellipsis-horizontal',
    'ellipsis-v': 'ellipsis-vertical',
    'copy': 'document-duplicate',
    'paste': 'clipboard-document',
    'wrench': 'wrench',
    'tools': 'wrench',
    'expand': 'arrows-pointing-out',
    'compress': 'arrows-pointing-in',
    'expand-alt': 'arrows-pointing-out',
    'compress-alt': 'arrows-pointing-in',
    'clipboard-list': 'clipboard',
    'hand-holding': 'gift',
    'gift': 'gift',
    'sparkles': 'sparkles',
}


def replace_fontawesome_icon(match):
    """
    替换单个 Font Awesome 图标为 Heroicons 图标
    """
    full_match = match.group(0)

    # 提取图标名称（去掉 fa- 前缀）
    icon_class = match.group(1)  # 这是 'fa-times' 或 'fas'
    icon_name = match.group(2)  # 这是 'times' 或 'plus'

    # 查找对应的 Heroicons 图标
    if icon_name not in ICON_MAPPING:
        print(f"⚠️  警告: 未找到映射 '{icon_name}'，保持原样")
        return full_match

    heroicon_name = ICON_MAPPING[icon_name]

    # 提取额外的 class
    extra_classes = re.findall(r'class="([^"]*)"', full_match)
    if extra_classes:
        # 保留原有的 class，但移除 Font Awesome 相关的
        classes = extra_classes[0].split()
        filtered_classes = []
        for c in classes:
            if not c.startswith('fa-') and c != 'fas' and c != 'far' and c != 'fab':
                filtered_classes.append(c)

        if filtered_classes:
            class_str = ' '.join(filtered_classes)
        else:
            class_str = 'w-5 h-5'
    else:
        class_str = 'w-5 h-5'

    # 生成 Heroicons SVG
    heroicon_svg = f'''<svg x-data="heroicon('{heroicon_name}')" class="{class_str}" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" x-cloak><span x-html="svg"></span></svg>'''

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
    # 匹配格式: <i class="fas fa-times"></i> 或 <i class="fas fa-times mr-2"></i>
    # 捕获组1: fa前缀（fas/far/fab/fa）
    # 捕获组2: 图标名称（times/plus/check等）
    pattern = re.compile(r'<i\s+class="[^"]*\b(fa[sr]?\b|fa)\b[^"]*?\bfa-([a-z-]+)\b[^"]*"[^>]*>\s*</i>')

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
    print("BetterLaser ERP - Font Awesome → Heroicons 批量替换 v2")
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
