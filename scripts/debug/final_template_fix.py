#!/usr/bin/env python
"""
最终修复脚本 - 清理所有结构性问题
"""
import re
from pathlib import Path


def final_fix_template(file_path: Path) -> bool:
    """最终修复模板文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    lines = content.split("\n")

    # 步骤1: 删除连续的多个 {% endblock %}，只保留一个
    cleaned_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # 如果当前行是 {% endblock %}
        if "{% endblock %}" in line and "{% block" not in line:
            # 检查下一行是否也是 {% endblock %}
            if (
                i + 1 < len(lines)
                and "{% endblock %}" in lines[i + 1]
                and "{% block" not in lines[i + 1]
            ):
                # 跳过下一个（保留当前这一个，删除下一个）
                i += 2
                cleaned_lines.append(line)
                continue

        cleaned_lines.append(line)
        i += 1

    content = "\n".join(cleaned_lines)
    lines = content.split("\n")

    # 步骤2: 提取 extra_js 块
    extra_js_start = -1
    extra_js_end = -1

    for i, line in enumerate(lines):
        if "{% block extra_js %}" in line:
            extra_js_start = i
            # 查找对应的 endblock
            brace_count = 0
            in_extra_js = False
            for j in range(i, len(lines)):
                if "{% block extra_js %}" in lines[j]:
                    in_extra_js = True
                    brace_count += 1
                elif "{% endblock %}" in lines[j] and in_extra_js:
                    brace_count -= 1
                    if brace_count == 0:
                        extra_js_end = j
                        break
            break

    if extra_js_start == -1:
        return False  # 没有 extra_js 块

    # 提取 extra_js 内容
    extra_js_block = "\n".join(lines[extra_js_start : extra_js_end + 1])

    # 步骤3: 删除所有在 extra_js 块之后的内容（除了可能的空行）
    # 然后在文件末尾添加 extra_js 块

    # 构建新内容：
    # - 文件开头到 extra_js_start 之前（不包含extra_js）
    # - 找到最后一个 {% endblock %}（这应该是 content 块的结束）
    # - 在那之后添加 extra_js

    new_lines = []
    last_content_endblock = -1
    found_extra_js_section = False

    for i, line in enumerate(lines):
        if i == extra_js_start:
            found_extra_js_section = True
            continue

        if found_extra_js_section:
            # 跳过 extra_js 块中的所有行
            if i <= extra_js_end:
                continue
            # 跳过 extra_js 后面的所有非空行（这些都是不应该在后面的内容）
            if line.strip() and not line.strip().startswith("<!--"):
                continue
            # 保留空行和注释
        else:
            new_lines.append(line)

        # 记录最后一个 {% endblock %}（在 extra_js 之前的）
        if not found_extra_js_section and "{% endblock %}" in line and "{% block" not in line:
            last_content_endblock = len(new_lines) - 1

    # 在最后添加 extra_js 块
    new_lines.append("")
    new_lines.append(extra_js_block)

    # 清理末尾的多余空行
    while new_lines and not new_lines[-1].strip():
        new_lines.pop()

    content = "\n".join(new_lines)

    # 步骤4: 删除</script>后的重复JavaScript函数
    # 查找所有</script>标签
    script_end_positions = []
    for i, line in enumerate(content.split("\n")):
        if "</script>" in line:
            script_end_positions.append(i)

    if len(script_end_positions) > 1:
        # 有多个</script>，删除第一个</script>后到{% endblock %}之间的内容
        lines = content.split("\n")
        first_script_end = script_end_positions[0]

        # 从first_script_end+1开始，查找函数定义
        # 删除从那里到最后一个{% endblock %}之前的内容
        new_lines = []
        skip = False

        for i, line in enumerate(lines):
            if i == first_script_end:
                new_lines.append(line)
                skip = True
                continue

            if skip:
                # 如果遇到了{% endblock %}，停止跳过
                if "{% endblock %}" in line:
                    skip = False
                    new_lines.append(line)
                # 否则跳过这一行
                continue

            new_lines.append(line)

        content = "\n".join(new_lines)

    if content != original:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    return False


def main():
    templates_dir = Path("/Users/janjung/Code_Projects/django_erp/templates/modules")

    # 获取所有HTML文件
    html_files = list(templates_dir.rglob("*.html"))

    print(f"🔧 开始最终修复 {len(html_files)} 个模板文件...\n")

    fixed_count = 0
    for i, file_path in enumerate(html_files, 1):
        relative_path = file_path.relative_to(templates_dir)

        # 只处理有问题的文件
        if i % 20 == 0:
            print(f"进度: {i}/{len(html_files)}")

        try:
            if final_fix_template(file_path):
                fixed_count += 1
        except Exception as e:
            print(f"❌ 错误 {relative_path}: {e}")

    print(f"\n{'='*80}")
    print(f"✅ 总共修复了 {fixed_count} 个文件")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
