#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查并修复 SVG 图标属性
确保所有 SVG 都包含核心属性：fill="none", viewBox="0 0 24 24", stroke="currentColor"
"""

import os
import re
from pathlib import Path

def check_svg_attributes(file_path):
    """
    检查文件中的 SVG 属性

    Returns:
        list: 需要修复的 SVG 列表
    """
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找所有 SVG 标签
        svg_pattern = r'<svg[^>]*>'

        for match in re.finditer(svg_pattern, content):
            svg_tag = match.group(0)
            issues_in_svg = []

            # 检查必需属性
            if 'fill="none"' not in svg_tag and "fill='none'" not in svg_tag:
                issues_in_svg.append('fill="none"')
            if 'viewBox="0 0 24 24"' not in svg_tag and "viewBox='0 0 24 24'" not in svg_tag:
                issues_in_svg.append('viewBox="0 0 24 24"')
            if 'stroke="currentColor"' not in svg_tag and "stroke='currentColor'" not in svg_tag:
                issues_in_svg.append('stroke="currentColor"')

            if issues_in_svg:
                # 获取行号
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': file_path,
                    'line': line_num,
                    'tag': svg_tag[:100],  # 前100个字符
                    'missing': issues_in_svg
                })

    except Exception as e:
        print(f"❌ 处理文件 {file_path} 时出错: {str(e)}")

    return issues


def fix_svg_attributes(file_path, dry_run=False):
    """
    修复 SVG 属性

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

        # 查找所有 SVG 标签并修复
        def fix_svg_tag(match):
            svg_tag = match.group(0)

            # 如果已经有所有必需属性，跳过
            if ('fill="none"' in svg_tag or "fill='none'" in svg_tag) and \
               ('viewBox="0 0 24 24"' in svg_tag or "viewBox='0 0 24 24'" in svg_tag) and \
               ('stroke="currentColor"' in svg_tag or "stroke='currentColor'" in svg_tag):
                return svg_tag

            # 添加缺失的属性
            # 1. 确保 fill="none"
            if 'fill=' not in svg_tag:
                # 在 <svg 后面插入
                svg_tag = svg_tag.replace('<svg', '<svg fill="none"', 1)
            elif 'fill="none"' not in svg_tag and "fill='none'" not in svg_tag:
                # 替换现有的 fill 属性
                svg_tag = re.sub(r'fill="[^"]*"', 'fill="none"', svg_tag)
                svg_tag = re.sub(r"fill='[^']*'", "fill='none'", svg_tag)

            # 2. 确保 viewBox="0 0 24 24"
            if 'viewBox=' not in svg_tag:
                # 在第一个属性后面插入
                svg_tag = svg_tag.replace('<svg', '<svg viewBox="0 0 24 24"', 1)
            elif 'viewBox="0 0 24 24"' not in svg_tag and "viewBox='0 0 24 24'" not in svg_tag:
                # 替换现有的 viewBox 属性
                svg_tag = re.sub(r'viewBox="[^"]*"', 'viewBox="0 0 24 24"', svg_tag)
                svg_tag = re.sub(r"viewBox='[^']*'", "viewBox='0 0 24 24'", svg_tag)

            # 3. 确保 stroke="currentColor"
            if 'stroke=' not in svg_tag:
                # 在 class 属性后插入
                svg_tag = re.sub(r'(class="[^"]*")', r'\1 stroke="currentColor"', svg_tag)
            elif 'stroke="currentColor"' not in svg_tag and "stroke='currentColor'" not in svg_tag:
                # 替换现有的 stroke 属性
                svg_tag = re.sub(r'stroke="[^"]*"', 'stroke="currentColor"', svg_tag)
                svg_tag = re.sub(r"stroke='[^']*'", "stroke='currentColor'", svg_tag)

            return svg_tag

        content = re.sub(r'<svg[^>]*>', fix_svg_tag, content)

        if content != original_content:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            return len(re.findall(r'<svg[^>]*>', original_content))

        return 0

    except Exception as e:
        print(f"❌ 处理文件 {file_path} 时出错: {str(e)}")
        return 0


def main():
    """主函数"""
    project_root = Path('/Users/janjung/Code_Projects/django_erp')
    templates_dir = project_root / 'templates'

    print("=" * 60)
    print("🔍 浮浮酱的 SVG 属性检查工具 ฅ'ω'ฅ")
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

    # 阶段1：检查
    print("🔍 阶段1: 检查 SVG 属性...")
    all_issues = []
    for file_path in html_files:
        issues = check_svg_attributes(file_path)
        if issues:
            all_issues.extend(issues)

    if not all_issues:
        print("✅ 所有 SVG 图标属性完整！")
        return

    print(f"⚠️  发现 {len(all_issues)} 个需要修复的 SVG")
    print()

    # 显示前10个问题
    for issue in all_issues[:10]:
        rel_path = issue['file'].relative_to(project_root)
        print(f"  📄 {rel_path}:{issue['line']}")
        print(f"     缺失: {', '.join(issue['missing'])}")
        print(f"     标签: {issue['tag'][:80]}...")
        print()

    if len(all_issues) > 10:
        print(f"  ... 还有 {len(all_issues) - 10} 个问题")
        print()

    # 阶段2：修复
    print("🔧 阶段2: 自动修复 SVG 属性...")
    total_fixed = 0
    fixed_files = 0

    for file_path in html_files:
        count = fix_svg_attributes(file_path, dry_run=False)
        if count > 0:
            total_fixed += count
            fixed_files += 1
            rel_path = file_path.relative_to(project_root)
            print(f"  ✅ {rel_path}: 修复 {count} 个 SVG")

    print()
    print("=" * 60)
    print(f"✨ 修复完成！")
    print(f"   修复文件数: {fixed_files}")
    print(f"   修复 SVG 数: {total_fixed}")
    print("=" * 60)


if __name__ == '__main__':
    main()
