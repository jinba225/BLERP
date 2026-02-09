#!/usr/bin/env python3
"""
全面检查所有模板文件的语法问题
"""
import re
from pathlib import Path


def check_template_syntax(file_path):
    """检查模板文件的常见语法问题"""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 检查连续的 {% endblock %}
        for i in range(len(lines) - 1):
            line1 = lines[i].strip()
            line2 = lines[i+1].strip()

            # 检查连续的endblock
            if line1 == '{% endblock %}' and line2 == '{% endblock %}':
                issues.append(f"第{i+1}行：连续的 {{% endblock %}}")

        # 检查未闭合的标签
        open_blocks = 0
        for i, line in enumerate(lines):
            if '{% block' in line:
                open_blocks += 1
            if '{% endblock %}' in line:
                open_blocks -= 1
            if open_blocks < 0:
                issues.append(f"第{i+1}行：多余的 {{% endblock %}}")

        if open_blocks > 0:
            issues.append(f"文件末尾：缺少 {{% endblock %}}（缺少{open_blocks}个）")

        return issues

    except Exception as e:
        return [f"读取文件错误: {str(e)}"]


def main():
    """主函数"""
    base_dir = Path("/Users/janjung/Code_Projects/django_erp/templates/modules")

    print("=" * 70)
    print("Django ERP 模板语法全面检查")
    print("=" * 70)
    print()

    # 查找所有列表页
    list_files = list(base_dir.rglob("*_list.html"))

    total_issues = 0
    problem_files = []

    for file_path in sorted(list_files):
        rel_path = file_path.relative_to(base_dir)
        issues = check_template_syntax(file_path)

        if issues:
            problem_files.append(rel_path)
            total_issues += len(issues)
            print(f"❌ {rel_path}")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print(f"✅ {rel_path}")

    print()
    print("=" * 70)
    if total_issues == 0:
        print("✅ 所有文件检查通过！没有发现语法问题。")
    else:
        print(f"⚠️  发现 {total_issues} 个问题，涉及 {len(problem_files)} 个文件")
        print()
        print("问题文件列表：")
        for f in problem_files:
            print(f"  - {f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
