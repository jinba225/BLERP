#!/usr/bin/env python
"""
正确删除extra_js块后的所有内容
"""

from pathlib import Path


def fix_template_structure(file_path: Path) -> bool:
    """修复模板结构 - 删除extra_js块后的所有内容"""
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

    # 从extra_js开始，向后查找第一个{% endblock %}
    # 但要确保它不是某个内部块的开始
    extra_js_end = -1
    for i in range(extra_js_start + 1, len(lines)):
        line = lines[i]

        # 如果遇到了另一个 {% block xxx %}，跳过它
        if "{% block " in line and "extra_js" not in line:
            continue

        # 找到 {% endblock %}
        if "{% endblock %}" in line:
            extra_js_end = i
            break

    if extra_js_end == -1:
        return False

    # 检查extra_js块后是否还有非空行
    has_content_after = False
    for i in range(extra_js_end + 1, len(lines)):
        if lines[i].strip():
            has_content_after = True
            break

    if not has_content_after:
        return False  # 已经是正确的结构

    # 删除extra_js块后的所有内容（包括空行）
    new_lines = lines[: extra_js_end + 1]

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
            if fix_template_structure(file_path):
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
