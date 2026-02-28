#!/usr/bin/env python3
"""
检查 Django 模板文件的结构问题

查找以下问题：
1. {% block extra_js %} 在文件开头（前100行）而不是在文件末尾
2. 按钮容器结构错误（缺少正确的闭合标签）
"""

import os
import re
from pathlib import Path


def check_template_structure(file_path):
    """检查单个模板文件的结构"""
    issues = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 检查1：extra_js 块位置
        extra_js_start = None
        extra_js_end = None
        content_end = None
        breadcrumb_start = None

        for i, line in enumerate(lines, 1):
            if "{% block extra_js %}" in line:
                extra_js_start = i
            elif "{% endblock %}" in line and "extra_js" in lines[max(0, i - 2) : i + 1]:
                # 查找与 extra_js 对应的 endblock
                if extra_js_start and not extra_js_end:
                    # 检查前面几行是否有 extra_js 相关内容
                    for j in range(max(0, i - 3), i):
                        if "extra_js" in lines[j]:
                            extra_js_end = i
                            break
            elif "{% block content %}" in line:
                content_end = i
            elif "{% block breadcrumb %}" in line:
                breadcrumb_start = i

        total_lines = len(lines)

        # 判断：extra_js 在前100行且不在最后50行，说明位置错误
        if extra_js_start:
            if extra_js_start < 100 and extra_js_end and (total_lines - extra_js_end) > 50:
                issues.append(
                    {
                        "type": "extra_js_position",
                        "severity": "high",
                        "message": f"extra_js 块在第 {extra_js_start} 行，应该在文件末尾",
                        "line": extra_js_start,
                    }
                )

        # 检查2：按钮容器结构
        # 查找缺少缩进的新建按钮
        for i, line in enumerate(lines, 1):
            # 检查新建按钮是否缺少缩进
            if re.search(r'<a\s+class="btn btn-primary"', line) and not line.startswith(
                "            "
            ):
                # 但这不是以正确缩进开始的
                if line.startswith("        <a") or line.startswith("      <a"):
                    issues.append(
                        {
                            "type": "button_indent",
                            "severity": "medium",
                            "message": f"按钮可能缺少正确缩进（第 {i} 行）",
                            "line": i,
                        }
                    )

        # 检查3：统计卡片注释位置
        for i, line in enumerate(lines, 1):
            if "<!-- Statistics Cards -->" in line:
                # 检查下一行是否是 </div>
                if i < len(lines) and "</div>" in lines[i]:
                    issues.append(
                        {
                            "type": "comment_position",
                            "severity": "medium",
                            "message": f'注释 "Statistics Cards" 位置可能在错误的容器结束标签处（第 {i} 行）',
                            "line": i,
                        }
                    )

        return issues

    except Exception as e:
        return [
            {
                "type": "error",
                "severity": "high",
                "message": f"无法读取文件: {str(e)}",
                "line": 0,
            }
        ]


def main():
    """主函数"""
    templates_dir = Path("/Users/janjung/Code_Projects/django_erp/templates")

    # 查找所有包含 extra_js 的模板文件
    problem_files = []

    print("正在检查模板文件...")
    print("=" * 80)

    for html_file in templates_dir.rglob("*.html"):
        # 跳过 base.html
        if html_file.name == "base.html":
            continue

        file_path = str(html_file)

        # 只检查包含 extra_js 的文件
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "{% block extra_js %}" not in content:
                    continue
        except:
            continue

        issues = check_template_structure(file_path)

        if issues:
            problem_files.append({"file": file_path, "issues": issues})

    # 输出结果
    if problem_files:
        print(f"\n发现 {len(problem_files)} 个文件存在问题：\n")

        for item in problem_files:
            relative_path = item["file"].replace("/Users/janjung/Code_Projects/django_erp/", "")
            print(f"\n📄 {relative_path}")

            for issue in item["issues"]:
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue["severity"], "⚪")

                print(f"  {severity_icon} 第 {issue['line']} 行: {issue['message']}")

        print("\n" + "=" * 80)
        print(f"\n总计: {len(problem_files)} 个文件需要修复")

        # 生成修复列表
        print("\n建议修复的文件列表：")
        for item in problem_files:
            relative_path = item["file"].replace("/Users/janjung/Code_Projects/django_erp/", "")
            print(f"  - {relative_path}")

    else:
        print("\n✅ 未发现结构问题！")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
