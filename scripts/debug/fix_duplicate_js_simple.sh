#!/bin/bash
# 修复模板文件中</script>标签后的重复JavaScript代码

cd /Users/janjung/Code_Projects/django_erp/templates/modules

# 查找所有包含重复JavaScript的文件
for file in $(find . -name "*.html" -type f); do
  # 检查文件是否包含</script>后面跟着重复的函数定义
  if grep -q "</script>" "$file" && grep -A 5 "</script>" "$file" | grep -q "function toggleClearButton"; then
    # 使用sed删除</script>后到{% endblock %}之间的重复内容
    # 策略：找到最后一个</script>，删除它后面直到{% endblock %}的所有内容（除了空行）

    # 创建临时文件
    temp_file=$(mktemp)

    # 使用awk处理：在</script>后，如果遇到"function toggleClearButton"或"// 搜索框清除按钮功能"
    # 则删除该行到{% endblock %}之间的所有非空行
    awk '
    BEGIN { in_script = 0; skip = 0 }
    /<\/script>/ { in_script = 1; print; next }
    in_script && /{%\s*endblock/ { in_script = 0; skip = 0; print; next }
    in_script && /function toggleClearButton|\/\/ 搜索框清除按钮功能/ { skip = 1; next }
    in_script && skip == 1 && !/^[[:space:]]*$/ { next }
    in_script && skip == 1 && /^[[:space:]]*$/ { print }
    { if (!in_script || skip == 0) print }
    ' "$file" > "$temp_file"

    # 替换原文件
    mv "$temp_file" "$file"

    relative_path=${file#./}
    echo "✅ $relative_path"
  fi
done

echo "修复完成"
