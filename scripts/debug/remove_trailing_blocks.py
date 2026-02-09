#!/usr/bin/env python
"""
删除extra_js块之后的所有内容
"""
from pathlib import Path


def remove_content_after_extra_js(file_path: Path) -> bool:
    """删除extra_js块后的所有内容"""
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

    # 查找extra_js块的结束
    extra_js_end = -1
    depth = 0
    for i in range(extra_js_start, len(lines)):
        if "{% block" in lines[i]:
            depth += 1
        if "{% endblock %}" in lines[i]:
            depth -= 1
            if depth == 0:
                extra_js_end = i
                break

    if extra_js_end == -1:
        return False

    # 检查extra_js块后是否有内容
    has_content_after = False
    for i in range(extra_js_end + 1, len(lines)):
        if lines[i].strip() and not lines[i].strip().startswith("//"):
            has_content_after = True
            break

    if not has_content_after:
        return False  # 没有需要删除的内容

    # 删除extra_js块后的所有内容
    new_lines = lines[: extra_js_end + 1]

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

    print(f"🔧 开始清理 {len(html_files)} 个模板文件...\n")

    fixed_count = 0
    for file_path in html_files:
        try:
            if remove_content_after_extra_js(file_path):
                relative_path = file_path.relative_to(templates_dir)
                print(f"✅ {relative_path}")
                fixed_count += 1
        except Exception as e:
            relative_path = file_path.relative_to(templates_dir)
            print(f"❌ {relative_path}: {e}")

    print(f"\n{'='*80}")
    print(f"✅ 清理了 {fixed_count} 个文件")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
