#!/usr/bin/env python3
"""
修复模板文件中重复的JavaScript代码
"""

import re
from pathlib import Path


def fix_duplicate_js(content):
    """修复重复的JavaScript代码"""
    # 查找extra_js块
    extra_js_pattern = r"{%\s*block\s+extra_js\s*%}(.*?){%\s*endblock\s*(?:extra_js)?\s*%}"
    match = re.search(extra_js_pattern, content, re.DOTALL)

    if not match:
        return content, False

    extra_js_content = match.group(1)
    extra_js_start = match.start()
    extra_js_end = match.end()

    # 检查是否有重复的函数定义
    # 查找 "function toggleClearButton" 和 "function updateClearButtonPosition" 等
    functions = [
        "function toggleClearButton",
        "function updateClearButtonPosition",
        "function clearSearchInput",
    ]

    has_duplicates = False
    for func in functions:
        # 计算函数出现次数
        count = extra_js_content.count(func)
        if count > 1:
            has_duplicates = True
            break

    if not has_duplicates:
        return content, False

    # 删除重复的代码 - 策略：找到第一个完整的script块，删除后面的重复
    # 查找<script>标签
    script_pattern = r"<script>(.*?)</script>"
    scripts = list(re.finditer(script_pattern, extra_js_content, re.DOTALL))

    if len(scripts) >= 2:
        # 保留第一个script块，删除其他
        first_script = scripts[0]
        # 找到第二个script块的开始和结束位置
        second_script_start = scripts[1].start()
        last_script_end = scripts[-1].end()

        # 重建extra_js内容
        new_extra_js = extra_js_content[:second_script_start].rstrip() + "\n{% endblock %}"

        # 替换整个extra_js块
        new_content = (
            content[:extra_js_start]
            + "{% block extra_js %}"
            + new_extra_js
            + content[extra_js_end:]
        )

        return new_content, True

    return content, False


def main():
    templates_dir = Path("/Users/janjung/Code_Projects/django_erp/templates/modules")

    print("=" * 80)
    print("修复模板文件中的JavaScript代码重复")
    print("=" * 80)

    fixed_count = 0
    error_count = 0

    for html_file in templates_dir.rglob("*.html"):
        try:
            with open(html_file, "r", encoding="utf-8") as f:
                original_content = f.read()

            new_content, was_fixed = fix_duplicate_js(original_content)

            if was_fixed:
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(new_content)

                relative_path = str(html_file).replace(
                    "/Users/janjung/Code_Projects/django_erp/", ""
                )
                print(f"✅ {relative_path}")
                fixed_count += 1

        except Exception as e:
            relative_path = str(html_file).replace("/Users/janjung/Code_Projects/django_erp/", "")
            print(f"❌ {relative_path}: {e}")
            error_count += 1

    print("\n" + "=" * 80)
    print(f"修复完成: ✅ {fixed_count} 个文件, ❌ {error_count} 个错误")
    print("=" * 80)


if __name__ == "__main__":
    main()
