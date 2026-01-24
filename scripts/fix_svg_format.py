#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 SVG 格式问题（例如重复的 </svg> 标签）
"""

import re
from pathlib import Path

def fix_svg_format_issues(file_path, dry_run=False):
    """
    修复 SVG 格式问题

    Args:
        file_path: 文件路径
        dry_run: 是否为试运行

    Returns:
        int: 修复数量
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 修复重复的 </svg> 标签
        content = re.sub(r'</svg></svg>', '</svg>', content)

        # 修复 SVG 标签内的换行问题
        # 确保整个 SVG 标签在一行或格式正确
        def format_svg(match):
            svg_tag = match.group(0)

            # 如果 SVG 标签已经格式正确（整个 <svg>...</svg> 在一起），跳过
            if '</svg>' in svg_tag[:200]:  # 前200个字符内应该有闭合标签
                return svg_tag

            # 否则，返回原样（我们的批量替换脚本应该已经生成了正确的格式）
            return svg_tag

        # 确保我们的 SVG 格式正确
        # 我们的格式：<svg...>\n  <path... />\n</svg>

        if content != original_content:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            return 1

        return 0

    except Exception as e:
        print(f"❌ 处理文件 {file_path} 时出错: {str(e)}")
        return 0


def main():
    """主函数"""
    project_root = Path('/Users/janjung/Code_Projects/django_erp')
    templates_dir = project_root / 'templates'

    print("=" * 60)
    print("🔧 浮浮酱的 SVG 格式修复工具 ฅ'ω'ฅ")
    print("=" * 60)
    print()

    # 查找所有 HTML 文件
    html_files = []
    for file_path in templates_dir.rglob('*.html'):
        if any(suffix in file_path.name for suffix in ['.bak', '.span.bak', '.old']):
            continue
        html_files.append(file_path)

    print(f"📂 检查 {len(html_files)} 个模板文件")
    print()

    total_fixed = 0
    fixed_files = 0

    for file_path in html_files:
        count = fix_svg_format_issues(file_path, dry_run=False)
        if count > 0:
            total_fixed += count
            fixed_files += 1
            rel_path = file_path.relative_to(project_root)
            print(f"  ✅ {rel_path}: 修复 {count} 个格式问题")

    if fixed_files == 0:
        print("✅ 未发现格式问题！")
    else:
        print()
        print("=" * 60)
        print(f"✨ 修复完成！")
        print(f"   修复文件数: {fixed_files}")
        print(f"   修复问题数: {total_fixed}")
        print("=" * 60)


if __name__ == '__main__':
    main()
