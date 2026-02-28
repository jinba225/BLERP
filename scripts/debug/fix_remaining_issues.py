#!/usr/bin/env python
"""
修复剩余的模板问题 - 更强大的版本
"""

import re
from pathlib import Path


def fix_extra_js_and_duplicates(file_path: Path) -> bool:
    """修复extra_js位置和JS重复"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    lines = content.split("\n")

    # 找到所有的 {% endblock %} 位置
    endblock_positions = []
    for i, line in enumerate(lines):
        if "{% endblock %}" in line:
            endblock_positions.append(i)

    if not endblock_positions:
        return False

    # 最后一个 endblock 应该是 content 块的结束
    last_endblock_idx = endblock_positions[-1]

    # 查找 extra_js 块
    extra_js_start = -1
    extra_js_end = -1
    extra_js_content = None

    for i, line in enumerate(lines):
        if "{% block extra_js %}" in line:
            extra_js_start = i
            # 查找对应的 {% endblock %}
            for j in range(i + 1, len(lines)):
                if "{% endblock %}" in lines[j]:
                    extra_js_end = j
                    extra_js_content = "\n".join(lines[i : j + 1])
                    break
            break

    if extra_js_start == -1 or extra_js_content is None:
        return False

    # 检查是否需要移动
    if extra_js_start > last_endblock_idx:
        # 已经在正确位置，只需要检查重复
        pass
    else:
        # 需要移动到文件末尾
        # 移除原位置的 extra_js
        new_lines = lines[:extra_js_start] + lines[extra_js_end + 1 :]

        # 在最后添加 extra_js
        new_lines.append("")
        new_lines.append(extra_js_content)

        content = "\n".join(new_lines)
        lines = content.split("\n")
        last_endblock_idx = lines.index([l for l in lines if "{% endblock %}" in l][-1])

    # 现在处理JavaScript重复
    # 查找<script>标签位置
    script_tags = []
    for i, line in enumerate(lines):
        if "<script>" in line:
            script_tags.append(i)

    if len(script_tags) < 2:
        # 没有重复的script标签
        if content != original:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        return False

    # 找到第一个和最后一个script标签
    first_script = script_tags[0]
    last_script = script_tags[-1]

    # 删除第一个script标签后的所有内容直到</script>（不包括</script>本身）
    # 然后删除</script>后到第二个<script>之前的内容

    # 策略：保留最后一个<script>块，删除之前的所有<script>块及其后的重复内容

    # 找到最后一个</script>的位置
    last_script_end = -1
    for i in range(last_script, len(lines)):
        if "</script>" in lines[i]:
            last_script_end = i
            break

    if last_script_end == -1:
        return False

    # 保留文件开头到最后一个<script>之前的内容
    # 但要删除之前的<script>块

    # 更简单的方法：查找并删除</script>和{% endblock %}之间的所有JavaScript函数定义
    new_lines = []
    skip_until_endblock = False
    seen_endblock_after_script = False

    for i, line in enumerate(lines):
        if seen_endblock_after_script:
            new_lines.append(line)
            continue

        # 检测是否在</script>后，且遇到了{% endblock %}
        if skip_until_endblock:
            if "{% endblock %}" in line:
                skip_until_endblock = False
                seen_endblock_after_script = True
                new_lines.append(line)
            continue

        # 检测</script>标签
        if "</script>" in line and i < last_endblock_idx:
            # 检查后面是否有函数定义
            skip_until_endblock = True
            new_lines.append(line)
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

    # 读取问题列表
    issue_file = Path("/Users/janjung/Code_Projects/django_erp/template_issues_report.txt")

    if not issue_file.exists():
        print("问题报告文件不存在，请先运行检查脚本")
        return

    with open(issue_file, "r", encoding="utf-8") as f:
        issue_content = f.read()

    # 提取有问题的文件
    problem_files = set()
    for line in issue_content.split("\n"):
        if line.startswith("文件:"):
            file_path = line.split(":", 1)[1].strip()
            problem_files.add(templates_dir / file_path)

    print(f"🔧 开始修复 {len(problem_files)} 个问题文件...\n")

    fixed_count = 0
    for file_path in sorted(problem_files):
        if not file_path.exists():
            continue

        relative_path = file_path.relative_to(templates_dir)
        print(f"修复: {relative_path}")

        try:
            if fix_extra_js_and_duplicates(file_path):
                print(f"     ✅ 已修复\n")
                fixed_count += 1
            else:
                print(f"     ⏭️  无需修复或无法修复\n")
        except Exception as e:
            print(f"     ❌ 错误: {e}\n")

    print(f"\n{'='*80}")
    print(f"✅ 已修复文件数: {fixed_count}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
