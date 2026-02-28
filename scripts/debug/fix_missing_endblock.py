#!/usr/bin/env python
"""
修复缺少{% endblock %}的extra_js块
"""

from pathlib import Path


def fix_missing_extra_js_endblock(file_path: Path) -> bool:
    """修复extra_js块缺少闭合标签的问题"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # 查找 {% block extra_js %}
    extra_js_start = -1
    for i, line in enumerate(lines):
        if "{% block extra_js %}" in line:
            extra_js_start = i
            break

    if extra_js_start == -1:
        return False

    # 从extra_js开始，查找</script>标签
    script_end = -1
    for i in range(extra_js_start, len(lines)):
        if "</script>" in lines[i]:
            script_end = i
            break

    if script_end == -1:
        return False

    # 检查</script>后是否有{% endblock %}
    has_endblock = False
    endblock_line = -1
    for i in range(script_end + 1, min(script_end + 10, len(lines))):
        if "{% endblock %}" in lines[i]:
            has_endblock = True
            endblock_line = i
            break

    # 如果没有找到{% endblock %}，添加一个
    if not has_endblock:
        # 在</script>后添加{% endblock %}
        lines.insert(script_end + 1, "{% endblock %}")

        # 删除之后的所有内容
        new_lines = lines[: script_end + 2]

        new_content = "\n".join(new_lines)

        if new_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
    else:
        # 找到了{% endblock %}，但检查之后是否还有其他内容
        has_more_content = False
        for i in range(endblock_line + 1, len(lines)):
            if lines[i].strip():
                has_more_content = True
                break

        if has_more_content:
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

    return False


def main():
    templates_dir = Path("/Users/janjung/Code_Projects/django_erp/templates/modules")

    html_files = list(templates_dir.rglob("*.html"))

    print(f"🔧 开始修复 {len(html_files)} 个模板文件...\n")

    fixed_count = 0
    for i, file_path in enumerate(html_files, 1):
        if i % 50 == 0:
            print(f"进度: {i}/{len(html_files)}")

        try:
            if fix_missing_extra_js_endblock(file_path):
                relative_path = file_path.relative_to(templates_dir)
                print(f"[{fixed_count + 1}] ✅ {relative_path}")
                fixed_count += 1
        except Exception as e:
            relative_path = file_path.relative_to(templates_dir)
            print(f"❌ {relative_path}: {e}")

    print(f"\n{'='*80}")
    print(f"✅ 总共修复了 {fixed_count} 个文件")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
