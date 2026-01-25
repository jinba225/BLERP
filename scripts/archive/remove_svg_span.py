#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
移除模板中多余的 <span x-html="svg"></span> 标签
"""

import os
import re
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / 'templates'

def remove_svg_span_from_templates():
    """从所有模板文件中移除 <span x-html="svg"></span>"""
    count = 0
    files_processed = 0

    # 遍历所有模板文件
    for template_file in TEMPLATES_DIR.rglob('*.html'):
        # 跳过备份文件
        if '.bak' in str(template_file):
            continue

        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查是否包含需要替换的内容
            if '<span x-html="svg"></span>' in content:
                # 创建备份
                backup_file = str(template_file) + '.span.bak'
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(content)

                # 替换
                new_content = content.replace('<span x-html="svg"></span>', '')

                # 写回原文件
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                count += content.count('<span x-html="svg"></span>')
                files_processed += 1
                print(f"✅ 处理: {template_file.relative_to(PROJECT_ROOT)}")

        except Exception as e:
            print(f"❌ 处理文件 {template_file} 失败: {e}")

    return files_processed, count

def main():
    print("=" * 80)
    print("🔧 移除模板中的 <span x-html=\"svg\"></span> 标签")
    print("=" * 80)
    print()

    files_processed, count = remove_svg_span_from_templates()

    print()
    print("=" * 80)
    print("✅ 处理完成!")
    print(f"   - 处理文件数: {files_processed}")
    print(f"   - 替换标签数: {count}")
    print(f"   - 备份文件扩展名: .span.bak")
    print("=" * 80)

if __name__ == '__main__':
    main()
