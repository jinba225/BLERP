#!/usr/bin/env python
"""
修复缺少{% endblock %}的extra_js块 - 改进版本
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

    # 检查</script>后的内容
    # 查找下一个非空行
    next_content_line = -1
    for i in range(script_end + 1, len(lines)):
        if lines[i].strip():
            next_content_line = i
            break

    if next_content_line == -1:
        # 文件在</script>后结束了，需要添加{% endblock %}
        lines.append("{% endblock %}")
        new_content = "\n".join(lines)

        if new_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
        return False

    # 检查下一个非空行是什么
    next_line = lines[next_content_line]

    # 如果是{% block xxx %}，说明extra_js缺少endblock
    if "{% block " in next_line and "extra_js" not in next_line:
        # 在新block之前插入{% endblock %}
        lines.insert(next_content_line, "{% endblock %}")

        # 删除新block及其之后的所有内容
        new_lines = lines[: next_content_line + 1]

        new_content = "\n".join(new_lines)

        if new_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True

    # 如果是{% endblock %}，检查它是否属于extra_js
    # 简单的检查：看它和</script>之间是否有{% block xxx %}
    has_block_between = False
    for i in range(script_end + 1, next_content_line):
        if "{% block " in lines[i] and "extra_js" not in lines[i]:
            has_block_between = True
            break

    if has_block_between:
        # 有另一个block在中间，说明extra_js缺少endblock
        # 在那个block之前插入{% endblock %}
        lines.insert(next_content_line, "{% endblock %}")

        # 删除新block及其之后的所有内容
        new_lines = lines[: next_content_line + 1]

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
