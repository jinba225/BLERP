#!/usr/bin/env python3
"""
检查并报告所有Django模板的结构问题
"""

import os
import re
from pathlib import Path


def check_button_structure(content):
    """检查按钮结构问题"""
    issues = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        # 检查按钮是否在同一行闭合（缺少缩进）
        if '<a class="btn btn-primary"' in line and "href" in line:
            # 如果下一行是 <svg 而不是同一行，可能有问题
            if i < len(lines) and "<svg" in lines[i] and not lines[i].startswith("            "):
                issues.append(
                    {"type": "button_structure", "line": i, "message": f"按钮可能缺少正确的缩进或闭合标签"}
                )

    return issues


def check_duplicate_js(content):
    """检查JavaScript代码重复"""
    issues = []

    # 查找 toggleClearButton 函数定义
    pattern = r"function toggleClearButton\(\)"
    matches = list(re.finditer(pattern, content))

    if len(matches) > 1:
        issues.append(
            {
                "type": "duplicate_js",
                "line": matches[1].start(),
                "message": f"JavaScript函数 toggleClearButton 重复定义 {len(matches)} 次",
            }
        )

    return issues


def check_form_spacing(content):
    """检查表单字段之间缺少空行"""
    issues = []
    lines = content.split("\n")

    for i in range(len(lines) - 1):
        # 检查 </div> 后直接跟 <div> 的情况（缺少空行）
        if "</div>" in lines[i] and "<div>" in lines[i + 1] and "class=" in lines[i + 1]:
            # 如果是在表单中，可能是字段分隔
            if i > 10:  # 跳过文件开头部分
                issues.append(
                    {"type": "missing_spacing", "line": i + 1, "message": f"表单字段之间可能缺少空行"}
                )

    return issues


def main():
    templates_dir = Path("/Users/janjung/Code_Projects/django_erp/templates/modules")

    print("=" * 80)
    print("Django 模板结构问题全面检查")
    print("=" * 80)

    all_issues = {}

    for html_file in templates_dir.rglob("*.html"):
        try:
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            file_issues = []
            file_issues.extend(check_button_structure(content))
            file_issues.extend(check_duplicate_js(content))
            file_issues.extend(check_form_spacing(content))

            if file_issues:
                relative_path = str(html_file).replace(
                    "/Users/janjung/Code_Projects/django_erp/", ""
                )
                all_issues[relative_path] = file_issues

        except Exception as e:
            print(f"⚠️  无法读取 {html_file}: {e}")

    if all_issues:
        print(f"\n发现 {len(all_issues)} 个文件存在问题：\n")

        for file_path, issues in all_issues.items():
            print(f"\n📄 {file_path}")
            for issue in issues:
                print(f"  ⚠️  第 {issue['line']} 行: {issue['message']}")

        print("\n" + "=" * 80)
        print(f"总计: {len(all_issues)} 个文件需要检查")

    else:
        print("\n✅ 未发现明显的结构问题！")

    print("=" * 80)


if __name__ == "__main__":
    main()
