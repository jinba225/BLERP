#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查找错误使用 heroicon 的地方
找出在非 <svg> 标签上使用 x-data="heroicon(...)" 的地方
"""

import os
import re
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / 'templates'

def find_wrong_heroicon_usage():
    """查找错误使用 heroicon 的地方"""
    issues = []

    # 遍历所有模板文件
    for template_file in TEMPLATES_DIR.rglob('*.html'):
        # 跳过备份文件
        if '.bak' in str(template_file):
            continue

        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # 查找所有 x-data="heroicon(...)" 的使用
            for i, line in enumerate(lines, 1):
                # 匹配 x-data="heroicon(...)"
                pattern = re.compile(r'<([a-z]+)[^>]*x-data=["\']heroicon\(["\']([^"\']+)["\']["\'][^>]*>')
                matches = pattern.finditer(line)

                for match in matches:
                    tag_name = match.group(1)
                    icon_name = match.group(2)

                    # 检查是否是 svg 标签
                    if tag_name != 'svg':
                        issues.append({
                            'file': str(template_file.relative_to(PROJECT_ROOT)),
                            'line': i,
                            'tag': tag_name,
                            'icon': icon_name,
                            'content': line.strip()
                        })

        except Exception as e:
            print(f"⚠️  读取文件 {template_file} 失败: {e}")

    return issues

def main():
    print("=" * 80)
    print("🔍 查找错误使用 heroicon 的地方")
    print("=" * 80)
    print()

    issues = find_wrong_heroicon_usage()

    if issues:
        print(f"❌ 发现 {len(issues)} 个错误使用 heroicon 的地方:")
        print()

        for issue in issues:
            print(f"文件: {issue['file']}:{issue['line']}")
            print(f"  标签: <{issue['tag']}> (应该是 <svg>)")
            print(f"  图标: {issue['icon']}")
            print(f"  内容: {issue['content'][:100]}")
            print()

        print("=" * 80)
        print("⚠️  需要修复以上问题")
        print("=" * 80)
    else:
        print("✅ 没有发现错误使用 heroicon 的地方")
        print()

    return len(issues)

if __name__ == '__main__':
    exit(main())
