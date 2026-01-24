#!/usr/bin/env python
"""
修复库存导入页面导入导出按钮宽度不一致的问题
统一所有导入按钮添加 flex-1 和 text-center 类
"""

file_path = '/Users/janjung/Code_Projects/django_erp/templates/inventory/stock_import.html'

# 读取文件
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换所有卡片中的导入按钮（不包含模态框中的按钮）
# 精确匹配卡片区域的导入按钮
import re

# 匹配模式：在 <div class="flex space-x-2"> 块中的 <button class="btn btn-primary">
pattern = r'(<button class=")btn btn-primary(">)'

# 替换为添加 flex-1 和 text-center
replacement = r'\1flex-1 btn btn-primary text-center\2'

# 执行替换
new_content = re.sub(pattern, replacement, content)

# 统计替换次数
count = len(re.findall(pattern, content))

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ 修复完成！共替换 {count} 个导入按钮")
