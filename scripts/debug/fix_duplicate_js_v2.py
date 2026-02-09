#!/usr/bin/env python3
"""
修复模板文件中</script>标签后的重复JavaScript代码
"""

import re
from pathlib import Path


def fix_duplicate_js_after_script(content):
    """修复</script>标签后的重复JavaScript代码"""
    # 查找 </script> 后面跟着重复函数定义的情况
    # 模式: </script> + 空行 + // 搜索框清除按钮功能 + 函数定义

    # 匹配 </script> 后到 {% endblock %} 之间的所有内容
    pattern = r"(</script>)(.*?){%\s*endblock\s*(?:extra_js)?\s*%}"

    def replacer(match):
        script_tag = match.group(1)
        middle_content = match.group(2)
        endblock = match.group(3)

        # 检查middle_content是否包含重复的函数定义
        # 如果包含 "// 搜索框清除按钮功能" 或 "function toggleClearButton"，则删除
        if "// 搜索框清除按钮功能" in middle_content or "function toggleClearButton" in middle_content:
            # 删除middle_content中的所有内容
            return script_tag + "\n\n" + endblock

        return match.group(0)

    new_content, count = re.subn(pattern, replacer, content, flags=re.DOTALL)

    return new_content, count > 0


def main():
    templates_dir = Path("/Users/janjung/Code_Projects/django_erp/templates/modules")

    print("=" * 80)
    print("修复模板文件中</script>后的重复JavaScript代码")
    print("=" * 80)

    fixed_count = 0
    error_count = 0

    for html_file in templates_dir.rglob("*.html"):
        try:
            with open(html_file, "r", encoding="utf-8") as f:
                original_content = f.read()

            new_content, was_fixed = fix_duplicate_js_after_script(original_content)

            if was_fixed:
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(new_content)

                relative_path = str(html_file).replace(
                    "/Users/janjung/Code_Projects/django_erp/", ""
                )
                print(f"✅ {relative_path}")
                fixed_count += 1

        except Exception as e:
            relative_path = str(html_file).replace("/Users/janjung/Code_Projects/django_erp/", "")
            print(f"❌ {relative_path}: {e}")
            error_count += 1

    print("\n" + "=" * 80)
    print(f"修复完成: ✅ {fixed_count} 个文件, ❌ {error_count} 个错误")
    print("=" * 80)


if __name__ == "__main__":
    main()
