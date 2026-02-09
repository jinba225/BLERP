#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查 Font Awesome 图标映射覆盖率

扫描 templates/ 目录，提取所有使用的 Font Awesome 图标，
检查映射表是否完整，输出缺失的图标列表
"""

import re
from collections import Counter
from pathlib import Path

from fontawesome_to_svg_mapping import ICON_ALIASES, ICON_MAPPING


def extract_fontawesome_icons(content):
    """从内容中提取 Font Awesome 图标"""
    # 匹配 <i class="fa-* ..."></i> 标签
    pattern = r'<i\s+class="([^"]*fa-[^"]*)"[^>]*>\s*</i>'
    matches = re.findall(pattern, content)

    icons = []
    for class_attr in matches:
        # 提取图标名称
        match = re.search(r"\bfa-([a-z0-9-]+)\b", class_attr)
        if match:
            icons.append(match.group(1))

    return icons


def main():
    """主函数"""
    templates_dir = Path("templates")

    if not templates_dir.exists():
        print("错误：templates/ 目录不存在")
        return

    print("=" * 70)
    print("Font Awesome 图标映射覆盖率检查")
    print("=" * 70)
    print()

    # 收集所有 HTML 文件
    html_files = list(templates_dir.rglob("*.html"))
    html_files = [f for f in html_files if ".bak" not in f.name]

    print(f"扫描 {len(html_files)} 个 HTML 文件...")
    print()

    # 统计所有图标
    all_icons = []
    file_icons = {}

    for file_path in html_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            icons = extract_fontawesome_icons(content)
            if icons:
                all_icons.extend(icons)
                file_icons[file_path] = icons
        except Exception as e:
            print(f"警告：读取文件 {file_path} 失败：{e}")

    # 统计
    icon_counts = Counter(all_icons)
    unique_icons = set(all_icons)

    print(f"发现 {len(all_icons)} 个图标引用，{len(unique_icons)} 个不同图标")
    print()

    # 检查映射覆盖率
    mapped_icons = set(ICON_MAPPING.keys()) | set(ICON_ALIASES.keys())
    unmapped_icons = unique_icons - mapped_icons

    print("-" * 70)
    print("映射覆盖率统计")
    print("-" * 70)
    print(f"总图标数：{len(unique_icons)}")
    print(
        f"已映射：{len(unique_icons) - len(unmapped_icons)} ({(len(unique_icons) - len(unmapped_icons)) / len(unique_icons) * 100:.1f}%)"
    )
    print(f"未映射：{len(unmapped_icons)} ({len(unmapped_icons) / len(unique_icons) * 100:.1f}%)")
    print()

    # 显示最常见的图标
    print("-" * 70)
    print("最常见的 20 个图标")
    print("-" * 70)
    for icon, count in icon_counts.most_common(20):
        status = "✓" if icon in ICON_MAPPING or icon in ICON_ALIASES else "✗"
        print(f"  {status} fa-{icon}: {count} 次")
    print()

    # 显示未映射的图标
    if unmapped_icons:
        print("-" * 70)
        print(f"未映射的 {len(unmapped_icons)} 个图标（需要添加到映射表）")
        print("-" * 70)
        for icon in sorted(unmapped_icons):
            count = icon_counts[icon]
            print(f"  - fa-{icon} (使用 {count} 次)")
        print()

    # 显示每个文件使用的图标
    print("-" * 70)
    print("每个文件的图标使用情况")
    print("-" * 70)

    files_with_icons = {
        k: v
        for k, v in sorted(file_icons.items(), key=lambda item: len(item[1]), reverse=True)
        if len(v) > 0
    }

    for file_path, icons in list(files_with_icons.items())[:20]:
        relative_path = file_path.relative_to(templates_dir)
        icon_count = len(icons)
        unique_count = len(set(icons))
        print(f"  {relative_path}: {icon_count} 个引用 ({unique_count} 个不同)")

    if len(files_with_icons) > 20:
        print(f"  ... 还有 {len(files_with_icons) - 20} 个文件")

    print()
    print("=" * 70)
    print("检查完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
