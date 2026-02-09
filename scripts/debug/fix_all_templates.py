#!/usr/bin/env python
"""
一次性修复所有模板文件的问题
"""
import os
import re
from pathlib import Path

# 问题类型
ISSUE_SCRIPT_IN_TITLE = "script_in_title"
ISSUE_ORPHANED_ENDBLOCK = "orphaned_endblock"
ISSUE_DUPLICATE_BLOCK = "duplicate_block"
ISSUE_MISSING_EXTENDS = "missing_extends"
ISSUE_DUPLICATE_SCRIPT = "duplicate_script"


def extract_blocks(content):
    """提取所有block标签及其行号"""
    blocks = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        # 匹配 {% block xxx %}
        match = re.search(r"{%\s*block\s+(\w+)\s*%}", line)
        if match:
            block_name = match.group(1)
            blocks.append(
                {"name": block_name, "line": i, "type": "start", "full_line": line.strip()}
            )

        # 匹配 {% endblock %}
        if re.search(r"{%\s*endblock\s*(?:\w+)?\s*%}", line):
            blocks.append({"name": "endblock", "line": i, "type": "end", "full_line": line.strip()})

    return blocks


def find_script_blocks(content):
    """找到所有script块的位置"""
    lines = content.split("\n")
    scripts = []

    in_script = False
    script_start = 0
    script_start_line = 0

    for i, line in enumerate(lines, 1):
        if "<script>" in line or "<script " in line:
            in_script = True
            script_start = i - 1
            script_start_line = i
        elif in_script and "</script>" in line:
            scripts.append(
                {
                    "start": script_start,
                    "start_line": script_start_line,
                    "end": i - 1,
                    "end_line": i,
                    "content_start": script_start + 1,
                    "content_end": i - 1,
                }
            )
            in_script = False

    return scripts


def analyze_file(filepath):
    """分析单个文件的问题"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    issues = []
    lines = content.split("\n")

    # 检查是否有 extends
    has_extends = bool(re.search(r"{%\s*extends\s+", content))

    # 检查块结构
    blocks = extract_blocks(content)
    block_counts = {}
    start_blocks = []
    endblock_count = 0

    for block in blocks:
        if block["type"] == "start":
            block_name = block["name"]
            block_counts[block_name] = block_counts.get(block_name, 0) + 1
            start_blocks.append(block)
        else:
            endblock_count += 1

    # 检查孤立的 endblock
    if endblock_count > len(start_blocks):
        issues.append(
            {
                "type": ISSUE_ORPHANED_ENDBLOCK,
                "severity": "high",
                "detail": f"发现 {endblock_count - len(start_blocks)} 个孤立的 endblock",
            }
        )

    # 检查重复的 block
    duplicates = {k: v for k, v in block_counts.items() if v > 1}
    if duplicates:
        for block_name, count in duplicates.items():
            issues.append(
                {
                    "type": ISSUE_DUPLICATE_BLOCK,
                    "severity": "high",
                    "detail": f'Block "{block_name}" 重复定义了 {count} 次',
                }
            )

    # 检查脚本位置
    scripts = find_script_blocks(content)

    # 找到 title block 的位置
    title_block_start = None
    for i, line in enumerate(lines):
        if re.search(r"{%\s*block\s+title\s*%}", line):
            title_block_start = i
            break

    # 找到 extra_js block 的位置
    extra_js_block_start = None
    extra_js_block_end = None
    in_extra_js = False
    for i, line in enumerate(lines):
        if re.search(r"{%\s*block\s+extra_js\s*%}", line):
            extra_js_block_start = i
            in_extra_js = True
        elif in_extra_js and re.search(r"{%\s*endblock\s*%}", line):
            extra_js_block_end = i
            break

    # 检查脚本是否在 title block 中
    if title_block_start is not None:
        # 找到 title endblock
        title_end = None
        for i in range(title_block_start + 1, len(lines)):
            if re.search(r"{%\s*endblock\s*%}", lines[i]):
                title_end = i
                break

        if title_end:
            # 检查在这个范围内是否有 script
            for script in scripts:
                if title_block_start < script["start"] < title_end:
                    issues.append(
                        {
                            "type": ISSUE_SCRIPT_IN_TITLE,
                            "severity": "critical",
                            "detail": f'脚本在 title block 中 (第 {script["start_line"]} 行)',
                        }
                    )
                    break

    # 检查是否有脚本在 extra_js 之外
    if extra_js_block_start is not None and extra_js_block_end is not None:
        for script in scripts:
            if not (extra_js_block_start < script["start"] < extra_js_block_end):
                issues.append(
                    {
                        "type": ISSUE_SCRIPT_IN_TITLE,
                        "severity": "high",
                        "detail": f'脚本不在 extra_js block 中 (第 {script["start_line"]} 行)',
                    }
                )

    # 检查是否缺少 extends（对于非独立页面）
    if not has_extends:
        # 排除一些不需要 extends 的特殊文件
        filepath_str = str(filepath)
        if not any(x in filepath_str for x in ["partials", "emails", "standalone"]):
            issues.append(
                {"type": ISSUE_MISSING_EXTENDS, "severity": "critical", "detail": "缺少 extends 语句"}
            )

    # 检查重复的脚本函数
    if len(scripts) > 1:
        # 检查是否有相同的函数定义
        functions = {}
        for script in scripts:
            script_content = "\n".join(lines[script["content_start"] : script["content_end"]])
            function_names = re.findall(r"function\s+(\w+)\s*\(", script_content)
            for func_name in function_names:
                if func_name not in functions:
                    functions[func_name] = []
                functions[func_name].append(script["start_line"])

        duplicates_funcs = {k: v for k, v in functions.items() if len(v) > 1}
        if duplicates_funcs:
            for func_name, locations in duplicates_funcs.items():
                issues.append(
                    {
                        "type": ISSUE_DUPLICATE_SCRIPT,
                        "severity": "medium",
                        "detail": f'函数 "{func_name}" 在第 {locations} 行重复定义',
                    }
                )

    return issues


def scan_all_templates():
    """扫描所有模板文件"""
    template_dir = Path("templates/modules")
    issues_by_file = {}

    for html_file in template_dir.rglob("*.html"):
        issues = analyze_file(html_file)
        if issues:
            issues_by_file[str(html_file)] = issues

    return issues_by_file


def main():
    print("=" * 80)
    print("Django ERP 模板文件全面诊断")
    print("=" * 80)
    print()

    issues_by_file = scan_all_templates()

    if not issues_by_file:
        print("✅ 没有发现任何问题！")
        return

    # 统计
    total_files = len(issues_by_file)
    total_issues = sum(len(issues) for issues in issues_by_file.values())

    print(f"📊 统计结果：")
    print(f"   - 有问题的文件数：{total_files}")
    print(f"   - 问题总数：{total_issues}")
    print()

    # 按严重程度分类
    critical = []
    high = []
    medium = []

    for filepath, issues in issues_by_file.items():
        for issue in issues:
            if issue["severity"] == "critical":
                critical.append((filepath, issue))
            elif issue["severity"] == "high":
                high.append((filepath, issue))
            elif issue["severity"] == "medium":
                medium.append((filepath, issue))

    print(f"🔴 严重问题 (Critical)：{len(critical)} 个")
    print(f"🟠 高优先级 (High)：{len(high)} 个")
    print(f"🟡 中等优先级 (Medium)：{len(medium)} 个")
    print()

    # 详细问题列表
    print("=" * 80)
    print("详细问题列表")
    print("=" * 80)
    print()

    for filepath, issues in sorted(issues_by_file.items()):
        print(f"📄 {filepath}")
        for issue in issues:
            severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(
                issue["severity"], "⚪"
            )

            print(f"   {severity_icon} {issue['detail']}")
        print()

    # 输出到文件
    output_file = "template_issues.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Django ERP 模板文件问题清单\n")
        f.write("=" * 80 + "\n\n")

        for filepath, issues in sorted(issues_by_file.items()):
            f.write(f"文件: {filepath}\n")
            for issue in issues:
                f.write(f"  [{issue['severity'].upper()}] {issue['type']}: {issue['detail']}\n")
            f.write("\n")

    print(f"✅ 详细报告已保存到：{output_file}")
    print()


if __name__ == "__main__":
    main()
