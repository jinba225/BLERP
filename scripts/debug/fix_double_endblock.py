#!/usr/bin/env python3
"""
修复双重 {% endblock %} 问题的脚本
"""
import re
from pathlib import Path


def fix_double_endblock(file_path):
    """修复文件中的双重 endblock"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 查找连续的 {% endblock %}（中间只有空白字符）
        pattern = r'{%\s*endblock\s*%}\s*\n\s*{%\s*endblock\s*%}'

        # 替换为单个 endblock
        content = re.sub(pattern, '{% endblock %}\n', content)

        if content != original_content:
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "已修复"
        else:
            return False, "无需修复"

    except Exception as e:
        return False, f"错误: {str(e)}"


def main():
    """主函数"""
    base_dir = Path("/Users/janjung/Code_Projects/django_erp/templates/modules")

    print("=" * 70)
    print("修复双重 {% endblock %} 问题")
    print("=" * 70)
    print()

    # 查找所有HTML文件
    html_files = list(base_dir.rglob("*.html"))

    fixed_count = 0
    checked_count = 0

    for file_path in sorted(html_files):
        # 只检查我们修改过的列表文件
        if 'list.html' not in str(file_path):
            continue

        checked_count += 1
        success, message = fix_double_endblock(file_path)

        if success:
            rel_path = file_path.relative_to(base_dir)
            print(f"✅ {message}: {rel_path}")
            fixed_count += 1

    print()
    print("=" * 70)
    print(f"检查了 {checked_count} 个列表文件")
    print(f"修复了 {fixed_count} 个文件")
    print("=" * 70)


if __name__ == "__main__":
    main()
