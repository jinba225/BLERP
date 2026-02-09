#!/usr/bin/env python
"""
清理重复的{% endblock %}标签和多余的空行
"""
from pathlib import Path


def clean_template_structure(file_path: Path) -> bool:
    """清理模板结构"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    original_lines = lines[:]

    # 步骤1: 删除连续的{% endblock %}行，只保留一个
    cleaned_lines = []
    i = 0
    while i < len(lines):
        current_line = lines[i]

        # 如果当前行只有{% endblock %}
        if current_line.strip() == "{% endblock %}":
            # 检查下一行是否也是{% endblock %}
            if i + 1 < len(lines) and lines[i + 1].strip() == "{% endblock %}":
                # 删除下一个，保留当前
                i += 1  # 跳过下一个

        cleaned_lines.append(current_line)
        i += 1

    lines = cleaned_lines

    # 步骤2: 删除文件末尾的多余空行
    while lines and not lines[-1].strip():
        lines.pop()

    # 步骤3: 删除extra_js的{% endblock %}后的多余空行（保留最多2个）
    # 找到extra_js的endblock
    extra_js_endblock_idx = -1
    for i, line in enumerate(lines):
        if "{% block extra_js %}" in line:
            # 从这里开始查找对应的{% endblock %}
            depth = 0
            for j in range(i, len(lines)):
                if "{% block " in lines[j]:
                    depth += 1
                if "{% endblock %}" in lines[j]:
                    depth -= 1
                    if depth == 0:
                        extra_js_endblock_idx = j
                        break
            break

    if extra_js_endblock_idx != -1 and extra_js_endblock_idx < len(lines) - 1:
        # 检查后面有多少空行
        empty_count = 0
        for i in range(extra_js_endblock_idx + 1, len(lines)):
            if not lines[i].strip():
                empty_count += 1
            else:
                break

        # 如果超过2个空行，删除多余的
        if empty_count > 2:
            # 保留2个空行，删除其余
            new_lines = lines[: extra_js_endblock_idx + 1]
            # 添加2个空行
            new_lines.append("")
            new_lines.append("")
            # 添加后面的非空内容
            for i in range(extra_js_endblock_idx + 1 + empty_count, len(lines)):
                new_lines.append(lines[i])

            lines = new_lines

    new_content = "\n".join(lines)

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
    for i, file_path in enumerate(html_files, 1):
        if i % 50 == 0:
            print(f"进度: {i}/{len(html_files)}")

        try:
            if clean_template_structure(file_path):
                relative_path = file_path.relative_to(templates_dir)
                print(f"[{fixed_count + 1}] ✅ {relative_path}")
                fixed_count += 1
        except Exception as e:
            relative_path = file_path.relative_to(templates_dir)
            print(f"❌ {relative_path}: {e}")

    print(f"\n{'='*80}")
    print(f"✅ 总共清理了 {fixed_count} 个文件")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
