#!/usr/bin/env python
"""
测试修复customer_list.html
"""
from pathlib import Path


def fix_missing_extra_js_endblock(file_path: Path) -> bool:
    """修复extra_js块缺少闭合标签的问题"""
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

    # 从extra_js开始，查找</script>标签
    script_end = -1
    for i in range(extra_js_start, len(lines)):
        if "</script>" in lines[i]:
            script_end = i
            print(f"找到 </script> 于行 {i+1}: {lines[i][:50]}")
            break

    if script_end == -1:
        print("未找到 </script> 标签")
        return False

    # 检查</script>后是否有{% endblock %}
    has_endblock = False
    endblock_line = -1
    print(f"\n检查行 {script_end+2} 到 {min(script_end+12, len(lines))}:")

    for i in range(script_end + 1, min(script_end + 10, len(lines))):
        line_content = lines[i].strip()
        print(f"  行{i+1}: '{line_content[:80] if line_content else '(空)'}'")
        if "{% endblock %}" in lines[i]:
            has_endblock = True
            endblock_line = i
            print(f"    --> 找到 endblock 于行 {i+1}!")
            break

    # 如果没有找到{% endblock %}，添加一个
    if not has_endblock:
        print(f"\n没有找到 endblock，将在行 {script_end+2} 添加")
        # 在</script>后添加{% endblock %}
        lines.insert(script_end + 1, "{% endblock %}")

        # 删除之后的所有内容
        new_lines = lines[: script_end + 2]

        new_content = "\n".join(new_lines)

        print(f"原文件: {len(content)} 字符, {len(lines)} 行")
        print(f"新文件: {len(new_content)} 字符, {len(new_lines)} 行")

        if new_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
    else:
        print(f"\n找到了 endblock 于行 {endblock_line+1}")

        # 检查之后是否还有其他内容
        has_more_content = False
        for i in range(endblock_line + 1, len(lines)):
            if lines[i].strip():
                has_more_content = True
                print(f"  还有内容于行 {i+1}: {lines[i][:50]}")
                break

        if has_more_content:
            print("删除 endblock 后的所有内容...")
            # 删除endblock后的所有内容
            new_lines = lines[: endblock_line + 1]

            # 清理末尾的空行
            while new_lines and not new_lines[-1].strip():
                new_lines.pop()

            new_content = "\n".join(new_lines)

            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return True
        else:
            print("没有更多内容需要删除")

    return False


def main():
    test_file = Path(
        "/Users/janjung/Code_Projects/django_erp/templates/modules/customers/customer_list.html"
    )

    print(f"🔧 测试修复: {test_file.name}\n")
    print("=" * 80 + "\n")

    result = fix_missing_extra_js_endblock(test_file)

    print("\n" + "=" * 80)
    if result:
        print("✅ 文件已修复")
    else:
        print("⏭️ 无需修复或无法修复")


if __name__ == "__main__":
    main()
