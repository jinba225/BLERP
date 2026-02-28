#!/usr/bin/env python
"""
全面检查所有模板文件的结构问题
检查项目:
1. 按钮结构错误 (按钮内容没有正确缩进)
2. HTML压缩问题 (所有内容在一行)
3. 表单字段间距缺失 (form fields之间没有空行)
4. extra_js块位置错误 (不在文件末尾)
5. JavaScript代码重复 (函数定义重复)
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


class TemplateChecker:
    def __init__(self, templates_dir: str):
        self.templates_dir = Path(templates_dir)
        self.issues = []

    def check_all_templates(self) -> Dict[str, List[Dict]]:
        """检查所有HTML模板文件"""
        results = {}

        # 遍历所有HTML文件
        for html_file in self.templates_dir.rglob("*.html"):
            relative_path = html_file.relative_to(self.templates_dir)
            file_issues = self.check_file(html_file)

            if file_issues:
                results[str(relative_path)] = file_issues

        return results

    def check_file(self, file_path: Path) -> List[Dict]:
        """检查单个文件"""
        issues = []

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

        # 检查1: 按钮结构错误
        button_issues = self.check_button_structure(lines)
        if button_issues:
            issues.extend(button_issues)

        # 检查2: HTML压缩问题
        if self.check_compressed_html(content):
            issues.append(
                {
                    "type": "compressed_html",
                    "severity": "high",
                    "description": "HTML内容被压缩在一行中",
                }
            )

        # 检查3: 表单字段间距缺失
        spacing_issues = self.check_form_field_spacing(lines)
        if spacing_issues:
            issues.extend(spacing_issues)

        # 检查4: extra_js块位置
        js_position_issue = self.check_extra_js_position(content, lines)
        if js_position_issue:
            issues.append(js_position_issue)

        # 检查5: JavaScript代码重复
        dup_issues = self.check_duplicate_js(content)
        if dup_issues:
            issues.extend(dup_issues)

        return issues

    def check_button_structure(self, lines: List[str]) -> List[Dict]:
        """检查按钮结构是否正确"""
        issues = []
        in_button = False
        button_start = 0

        for i, line in enumerate(lines, 1):
            # 检测按钮开始 (btn btn-primary 或类似的链接)
            if re.search(r'<a\s+class="btn\s+btn-[\w-]+', line):
                in_button = True
                button_start = i
                # 检查同一行是否有内容（应该是新行）
                if not line.strip().endswith(">"):
                    issues.append(
                        {
                            "type": "button_structure",
                            "severity": "medium",
                            "line": i,
                            "description": f"按钮标签没有正确闭合在行尾",
                        }
                    )
                continue

            # 如果在按钮内，检查缩进
            if in_button:
                # 检查子元素是否缩进
                if (
                    line.strip()
                    and not line.startswith("    ")
                    and not line.strip().startswith("</a>")
                ):
                    issues.append(
                        {
                            "type": "button_structure",
                            "severity": "medium",
                            "line": i,
                            "description": f"按钮内部元素没有正确缩进 (行{i})",
                        }
                    )

                # 检测按钮结束
                if "</a>" in line:
                    in_button = False
                    # 检查是否在同一行有其他内容
                    if line.strip() != "</a>":
                        issues.append(
                            {
                                "type": "button_structure",
                                "severity": "medium",
                                "line": i,
                                "description": f"按钮闭合标签后有其他内容 (行{i})",
                            }
                        )

        return issues

    def check_compressed_html(self, content: str) -> bool:
        """检查HTML是否被压缩（内容过长且行数少）"""
        lines = content.split("\n")
        total_chars = len(content)
        total_lines = len(lines)

        # 如果文件少于30行但总字符数超过2000，可能是压缩的
        if total_lines < 30 and total_chars > 2000:
            # 检查是否有超长行
            for line in lines:
                if len(line) > 500:  # 单行超过500字符
                    return True
        return False

    def check_form_field_spacing(self, lines: List[str]) -> List[Dict]:
        """检查表单字段之间是否有空行"""
        issues = []
        in_form = False

        for i in range(len(lines) - 1):
            line = lines[i].strip()

            # 检测表单字段开始
            if re.match(r'<div>\s*<label class="block text-sm', lines[i]):
                in_form = True
                # 检查下一个字段之间是否有空行
                for j in range(i + 1, min(i + 10, len(lines))):
                    next_line = lines[j].strip()
                    # 如果遇到下一个字段
                    if re.match(r'<div>\s*<label class="block text-sm', lines[j]):
                        # 检查中间是否有空行
                        has_blank = any(not lines[k].strip() for k in range(i, j))
                        if not has_blank:
                            issues.append(
                                {
                                    "type": "form_spacing",
                                    "severity": "low",
                                    "line": j,
                                    "description": f"表单字段之间缺少空行 (行{i}和行{j})",
                                }
                            )
                        break

        return issues

    def check_extra_js_position(self, content: str, lines: List[str]) -> Dict:
        """检查extra_js块是否在正确位置"""
        # 查找 {% block extra_js %}
        extra_js_match = re.search(r"{%\s*block\s+extra_js\s*%}", content)

        if not extra_js_match:
            return {}

        # 查找 {% endblock %} (content块的结束)
        last_endblock = content.rfind("{% endblock %}")

        if last_endblock == -1:
            return {}

        # extra_js应该在最后一个endblock之后
        extra_js_pos = extra_js_match.start()

        if extra_js_pos < last_endblock:
            # 计算行号
            line_num = content[:extra_js_pos].count("\n") + 1
            total_lines = len(lines)

            return {
                "type": "extra_js_position",
                "severity": "high",
                "line": line_num,
                "description": f"extra_js块位置错误，应该在文件末尾 (当前在第{line_num}行，共{total_lines}行)",
            }

        return {}

    def check_duplicate_js(self, content: str) -> List[Dict]:
        """检查JavaScript函数是否重复定义"""
        issues = []

        # 常见的函数名模式
        function_patterns = [
            r"function\s+(toggleClearButton|updateClearButtonPosition|clearSearchInput)",
            r"const\s+(toggleClearButton|updateClearButtonPosition|clearSearchInput)\s*=",
        ]

        for pattern in function_patterns:
            matches = list(re.finditer(pattern, content))

            if len(matches) > 1:
                for match in matches[1:]:  # 从第二个开始报告
                    line_num = content[: match.start()].count("\n") + 1
                    func_name = match.group(1) if match.groups() else pattern.split(r"\s+")[-1]
                    issues.append(
                        {
                            "type": "duplicate_js",
                            "severity": "high",
                            "line": line_num,
                            "description": f"JavaScript函数重复定义: {func_name} (行{line_num})",
                        }
                    )

        return issues

    def print_results(self, results: Dict[str, List[Dict]]):
        """打印检查结果"""
        total_files = len(results)
        total_issues = sum(len(issues) for issues in results.values())

        print(f"\n{'='*80}")
        print(f"模板检查结果汇总")
        print(f"{'='*80}")
        print(f"发现问题的文件数: {total_files}")
        print(f"总问题数: {total_issues}")
        print(f"{'='*80}\n")

        # 按严重程度分组
        by_severity = {"high": [], "medium": [], "low": []}

        for file_path, issues in results.items():
            for issue in issues:
                by_severity[issue["severity"]].append((file_path, issue))

        # 打印高严重性问题
        if by_severity["high"]:
            print(f"\n🔴 高严重性问题 ({len(by_severity['high'])}):")
            print("-" * 80)
            for file_path, issue in by_severity["high"]:
                print(f"  📁 {file_path}")
                print(f"     {issue['description']} (行{issue.get('line', 'N/A')})")
                print()

        # 打印中等严重性问题
        if by_severity["medium"]:
            print(f"\n🟡 中等严重性问题 ({len(by_severity['medium'])}):")
            print("-" * 80)
            for file_path, issue in by_severity["medium"]:
                print(f"  📁 {file_path}")
                print(f"     {issue['description']} (行{issue.get('line', 'N/A')})")
                print()

        # 打印低严重性问题
        if by_severity["low"]:
            print(f"\n🟢 低严重性问题 ({len(by_severity['low'])}):")
            print("-" * 80)
            for file_path, issue in by_severity["low"]:
                print(f"  📁 {file_path}")
                print(f"     {issue['description']} (行{issue.get('line', 'N/A')})")
                print()

        # 打印所有有问题的文件列表
        print(f"\n📋 需要修复的文件列表:")
        print("-" * 80)
        for i, file_path in enumerate(results.keys(), 1):
            issue_count = len(results[file_path])
            print(f"  {i}. {file_path} ({issue_count} 个问题)")

        print(f"\n{'='*80}\n")


def main():
    # 模板目录
    templates_dir = "/Users/janjung/Code_Projects/django_erp/templates/modules"

    print("🔍 开始检查所有模板文件...")
    print(f"📂 目录: {templates_dir}\n")

    checker = TemplateChecker(templates_dir)
    results = checker.check_all_templates()

    if results:
        checker.print_results(results)

        # 保存结果到文件
        output_file = "/Users/janjung/Code_Projects/django_erp/template_issues_report.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("模板文件问题报告\n")
            f.write("=" * 80 + "\n\n")

            for file_path, issues in results.items():
                f.write(f"文件: {file_path}\n")
                f.write("-" * 80 + "\n")
                for issue in issues:
                    severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[issue["severity"]]
                    f.write(
                        f"  {severity_icon} [{issue['severity'].upper()}] {issue['description']}\n"
                    )
                f.write("\n")

        print(f"✅ 报告已保存到: {output_file}")
    else:
        print("✅ 没有发现任何问题！")


if __name__ == "__main__":
    main()
