#!/usr/bin/env python
"""
自动修复所有模板文件的结构问题
修复内容:
1. 按钮结构错误 (按钮内容没有正确缩进)
2. HTML压缩问题 (所有内容在一行)
3. 表单字段间距缺失 (form fields之间没有空行)
4. extra_js块位置错误 (不在文件末尾)
5. JavaScript代码重复 (函数定义重复)
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


class TemplateAutoFixer:
    def __init__(self, templates_dir: str):
        self.templates_dir = Path(templates_dir)
        self.fix_stats = {
            "button_fixed": 0,
            "html_expanded": 0,
            "spacing_added": 0,
            "extra_js_moved": 0,
            "duplicate_js_removed": 0,
            "total_files": 0,
        }

    def fix_all_templates(self):
        """修复所有模板文件"""
        html_files = list(self.templates_dir.rglob("*.html"))
        total = len(html_files)

        print(f"🔧 开始修复 {total} 个模板文件...\n")

        for i, html_file in enumerate(html_files, 1):
            relative_path = html_file.relative_to(self.templates_dir)
            print(f"[{i}/{total}] 修复: {relative_path}")

            try:
                fixed = self.fix_file(html_file)
                if fixed:
                    self.fix_stats["total_files"] += 1
                    print(f"         ✅ 已修复\n")
                else:
                    print(f"         ⏭️  无需修复\n")
            except Exception as e:
                print(f"         ❌ 错误: {e}\n")

    def fix_file(self, file_path: Path) -> bool:
        """修复单个文件，返回是否进行了修改"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        fixes_applied = []

        # 修复1: extra_js块位置
        content = self.fix_extra_js_position(content)
        if content != original_content:
            fixes_applied.append("extra_js位置")
            self.fix_stats["extra_js_moved"] += 1
            original_content = content

        # 修复2: JavaScript代码重复
        content = self.fix_duplicate_js(content)
        if content != original_content:
            fixes_applied.append("JS重复")
            self.fix_stats["duplicate_js_removed"] += 1
            original_content = content

        # 修复3: 按钮结构
        content = self.fix_button_structure(content)
        if content != original_content:
            fixes_applied.append("按钮结构")
            self.fix_stats["button_fixed"] += 1
            original_content = content

        # 修复4: 表单字段间距
        content = self.fix_form_spacing(content)
        if content != original_content:
            fixes_applied.append("表单间距")
            self.fix_stats["spacing_added"] += 1
            original_content = content

        # 修复5: HTML压缩
        content = self.expand_compressed_html(content)
        if content != original_content:
            fixes_applied.append("HTML展开")
            self.fix_stats["html_expanded"] += 1
            original_content = content

        # 如果有修改，写回文件
        if fixes_applied:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False

    def fix_extra_js_position(self, content: str) -> str:
        """修复extra_js块位置，移到文件末尾"""
        # 查找 extra_js 块
        extra_js_pattern = r"({%\s*block\s+extra_js\s*%}.*?{%\s*endblock\s*%})"

        matches = list(re.finditer(extra_js_pattern, content, re.DOTALL))

        if not matches or len(matches) != 1:
            return content

        extra_js_block = matches[0].group(1)
        extra_js_start = matches[0].start()
        extra_js_end = matches[0].end()

        # 查找最后一个 {% endblock %} (应该是content块的结束)
        last_endblock_pos = content.rfind("{% endblock %}")

        if last_endblock_pos == -1:
            return content

        # 如果extra_js已经在最后，不需要修复
        if extra_js_start > last_endblock_pos:
            return content

        # 移除原位置的extra_js块
        new_content = content[:extra_js_start] + content[extra_js_end:]

        # 在最后添加extra_js块
        # 在最后一个 {% endblock %} 之后添加
        insert_pos = new_content.rfind("{% endblock %}")
        if insert_pos != -1:
            # 找到该行的结尾
            newline_pos = new_content.find("\n", insert_pos)
            if newline_pos != -1:
                # 在该行之后插入
                new_content = (
                    new_content[: newline_pos + 1]
                    + "\n"
                    + extra_js_block
                    + new_content[newline_pos + 1 :]
                )
            else:
                # 文件末尾
                new_content = new_content + "\n" + extra_js_block

        return new_content

    def fix_duplicate_js(self, content: str) -> str:
        """删除重复的JavaScript函数定义"""
        # 常见的函数模式
        patterns = [
            (r"(function\s+toggleClearButton\s*\(.*?\)\s*{.*?})", "toggleClearButton"),
            (
                r"(function\s+updateClearButtonPosition\s*\(.*?\)\s*{.*?})",
                "updateClearButtonPosition",
            ),
            (r"(function\s+clearSearchInput\s*\(.*?\)\s*{.*?})", "clearSearchInput"),
        ]

        modified = False

        for pattern, func_name in patterns:
            # 查找所有匹配
            matches = list(re.finditer(pattern, content, re.DOTALL))

            if len(matches) > 1:
                # 保留第一个，删除其他的
                # 从后往前删除，避免位置偏移
                for match in reversed(matches[1:]):
                    start = match.start()
                    end = match.end()

                    # 删除该函数定义（包括前后的空白行）
                    # 向前找到空白开始
                    temp_start = start
                    while temp_start > 0 and content[temp_start - 1] in "\n\r ":
                        temp_start -= 1

                    # 向后找到空白结束
                    temp_end = end
                    while temp_end < len(content) and content[temp_end] in "\n\r ":
                        temp_end += 1

                    content = content[:temp_start] + content[temp_end:]
                    modified = True

        return content

    def fix_button_structure(self, content: str) -> str:
        """修复按钮结构，确保正确缩进"""
        lines = content.split("\n")
        fixed_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # 检测按钮开始
            button_match = re.match(r'^(\s*)<a\s+class="btn\s+btn-[\w-]+[^>]*>(.*)$', line)

            if button_match:
                indent = button_match.group(1)
                button_content = button_match.group(2).strip()

                # 如果按钮内容在同一行，尝试拆分
                if button_content:
                    # 添加按钮开始标签
                    fixed_lines.append(line[: line.index(">") + 1])

                    # 提取SVG和文本
                    svg_match = re.search(r"(<svg[^>]*>.*?</svg>)", button_content)
                    text = button_content

                    if svg_match:
                        svg = svg_match.group(1)
                        text = button_content.replace(svg, "").strip()

                        # 添加SVG行（缩进）
                        fixed_lines.append(f"    {indent}{svg}")

                        # 如果有文本，添加文本行
                        if text:
                            fixed_lines.append(f"    {indent}{text}")
                    else:
                        # 没有SVG，只有文本
                        if text:
                            fixed_lines.append(f"    {indent}{text}")
                else:
                    fixed_lines.append(line)

                i += 1

                # 处理按钮内的内容（直到</a>）
                while i < len(lines):
                    next_line = lines[i].strip()

                    if next_line == "</a>":
                        fixed_lines.append(f"{indent}</a>")
                        i += 1
                        break
                    elif next_line:
                        # 按钮内的内容，确保缩进
                        if not lines[i].startswith("    "):
                            fixed_lines.append(f"    {lines[i].strip()}")
                        else:
                            fixed_lines.append(lines[i])
                    else:
                        fixed_lines.append(lines[i])

                    i += 1
            else:
                fixed_lines.append(line)
                i += 1

        return "\n".join(fixed_lines)

    def fix_form_spacing(self, content: str) -> str:
        """在表单字段之间添加空行"""
        lines = content.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            fixed_lines.append(line)

            # 检测表单字段结束
            if re.search(r"</select>\s*</div>", line):
                # 检查下一个非空行是否是新的字段
                if i + 1 < len(lines):
                    next_idx = i + 1
                    while next_idx < len(lines) and not lines[next_idx].strip():
                        next_idx += 1

                    if next_idx < len(lines):
                        next_line = lines[next_idx]
                        # 如果是新的字段且当前没有空行，添加一个
                        if re.match(r"\s*<div>", next_line) and next_idx == i + 1:
                            fixed_lines.append("")

        return "\n".join(fixed_lines)

    def expand_compressed_html(self, content: str) -> str:
        """展开压缩的HTML内容"""
        lines = content.split("\n")

        # 如果行数少但有超长行，可能是压缩的
        if len(lines) < 30:
            # 检查是否有超长行
            has_long_line = any(len(line) > 500 for line in lines)

            if has_long_line:
                # 尝试在合适的位置拆分
                fixed_lines = []

                for line in lines:
                    if len(line) > 500:
                        # 在合适的位置拆分
                        # 在>后拆分
                        parts = re.split(r"(>)", line)

                        current_line = ""
                        for part in parts:
                            current_line += part
                            if part == ">" and current_line.strip():
                                fixed_lines.append(current_line)
                                current_line = ""

                        if current_line.strip():
                            fixed_lines.append(current_line)
                    else:
                        fixed_lines.append(line)

                return "\n".join(fixed_lines)

        return content

    def print_summary(self):
        """打印修复汇总"""
        print(f"\n{'='*80}")
        print(f"修复完成汇总")
        print(f"{'='*80}")
        print(f"✅ 已修复文件数: {self.fix_stats['total_files']}")
        print(f"   - 按钮结构修复: {self.fix_stats['button_fixed']}")
        print(f"   - HTML展开: {self.fix_stats['html_expanded']}")
        print(f"   - 表单间距添加: {self.fix_stats['spacing_added']}")
        print(f"   - extra_js位置修复: {self.fix_stats['extra_js_moved']}")
        print(f"   - JS重复删除: {self.fix_stats['duplicate_js_removed']}")
        print(f"{'='*80}\n")


def main():
    # 模板目录
    templates_dir = "/Users/janjung/Code_Projects/django_erp/templates/modules"

    fixer = TemplateAutoFixer(templates_dir)
    fixer.fix_all_templates()
    fixer.print_summary()


if __name__ == "__main__":
    main()
