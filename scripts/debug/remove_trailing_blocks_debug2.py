#!/usr/bin/env python
"""
删除extra_js块之后的所有内容 - 调试版本2
"""

from pathlib import Path


def remove_content_after_extra_js(file_path: Path) -> bool:
    """删除extra_js块后的所有内容"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    print(f"文件总行数: {len(lines)}")

    # 查找 {% block extra_js %}
    extra_js_start = -1
    for i, line in enumerate(lines):
        if "{% block extra_js %}" in line:
            extra_js_start = i
            print(f"找到 extra_js 开始于行 {i+1}")
            break

    if extra_js_start == -1:
        print("未找到 extra_js 块")
        return False

    # 查找extra_js块的结束 - 简化版本
    # 直接查找extra_js后的第一个 {% endblock %}
    extra_js_end = -1
    for i in range(extra_js_start + 1, len(lines)):
        if "{% endblock %}" in lines[i]:
            extra_js_end = i
            print(f"找到 extra_js 结束于行 {i+1}")
            break

    if extra_js_end == -1:
        print("未找到 extra_js 结束标签")
        return False

    # 检查extra_js块后是否有内容
    print(f"\n检查行 {extra_js_end+2} 到文件末尾:")
    has_content_after = False
    for i in range(extra_js_end + 1, min(extra_js_end + 20, len(lines))):
        line_content = lines[i].strip()
        print(f"  行{i+1}: '{line_content[:50] if line_content else '(空)'}'")
        if line_content and not line_content.startswith("//"):
            has_content_after = True

    if not has_content_after:
        print("\n没有找到需要删除的内容")
        return False  # 没有需要删除的内容

    print(f"\n发现内容，准备删除...")

    # 删除extra_js块后的所有内容
    new_lines = lines[: extra_js_end + 1]

    # 清理末尾的空行
    while new_lines and not new_lines[-1].strip():
        new_lines.pop()

    new_content = "\n".join(new_lines)

    print(f"原文件: {len(content)} 字符")
    print(f"新文件: {len(new_content)} 字符")

    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    return False


def main():
    # 只测试 customer_list.html
    test_file = Path(
        "/Users/janjung/Code_Projects/django_erp/templates/modules/customers/customer_list.html"
    )

    print(f"🔧 测试修复: {test_file.name}\n")
    print("=" * 80 + "\n")

    result = remove_content_after_extra_js(test_file)

    print("\n" + "=" * 80)
    if result:
        print("✅ 文件已修复")
    else:
        print("⏭️ 无需修复或无法修复")


if __name__ == "__main__":
    main()
