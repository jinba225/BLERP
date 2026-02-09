#!/usr/bin/env python
"""
最终清理 - 删除重复的{% endblock %}和多余空行
"""
from pathlib import Path


def final_cleanup_template(file_path: Path) -> bool:
    """最终清理模板"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # 步骤1: 查找并删除连续的{% endblock %}（跳过空行）
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # 如果当前行是{% endblock %}
        if line.strip() == "{% endblock %}":
            # 查找下一个非空行
            next_non_empty = i + 1
            while next_non_empty < len(lines) and not lines[next_non_empty].strip():
                next_non_empty += 1

            # 如果下一个非空行也是{% endblock %}，跳过当前行（删除第一个，保留第二个）
            if next_non_empty < len(lines) and lines[next_non_empty].strip() == "{% endblock %}":
                # 跳过当前行，直接处理下一个非空行
                i = next_non_empty
                continue

        new_lines.append(line)
        i += 1

    lines = new_lines

    # 步骤2: 删除文件末尾的空行（保留最后{% endblock %}后的最多2个）
    # 找到最后一个非空行
    last_non_empty = len(lines) - 1
    while last_non_empty >= 0 and not lines[last_non_empty].strip():
        last_non_empty -= 1

    if last_non_empty >= 0 and last_non_empty < len(lines) - 1:
        # 保留最后2个空行
        lines = lines[: last_non_empty + 1] + [""] * min(2, len(lines) - last_non_empty - 1)

    # 步骤3: 删除extra_js块后的所有内容
    # 查找extra_js块的结束
    extra_js_end = -1
    for i, line in enumerate(lines):
        if "{% block extra_js %}" in line:
            # 查找对应的{% endblock %}
            depth = 0
            for j in range(i, len(lines)):
                if "{% block " in lines[j]:
                    depth += 1
                if "{% endblock %}" in lines[j]:
                    depth -= 1
                    if depth == 0:
                        extra_js_end = j
                        break
            break

    if extra_js_end != -1 and extra_js_end < len(lines) - 3:
        # 删除extra_js endblock之后的所有内容（保留2个空行）
        lines = lines[: extra_js_end + 1] + ["", ""]

    new_content = "\n".join(lines)

    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    return False


def main():
    templates_dir = Path("/Users/janjung/Code_Projects/django_erp/templates/modules")

    html_files = list(templates_dir.rglob("*.html"))

    print(f"🔧 开始最终清理 {len(html_files)} 个模板文件...\n")

    fixed_count = 0
    for i, file_path in enumerate(html_files, 1):
        if i % 50 == 0:
            print(f"进度: {i}/{len(html_files)}")

        try:
            if final_cleanup_template(file_path):
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
