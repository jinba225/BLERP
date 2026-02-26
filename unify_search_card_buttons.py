#!/usr/bin/env python3
"""
统一所有页面搜索卡片按钮的大小
"""

import os
import re

# 定义要搜索的目录
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')

# 匹配搜索按钮的正则表达式
search_button_pattern = re.compile(r'(<button[^>]*class="[^"]*btn btn-primary[^"]*"[^>]*>.*?</button>)', re.DOTALL)

# 匹配重置按钮的正则表达式
reset_button_pattern = re.compile(r'(<a[^>]*href="[^"]*"[^>]*class="[^"]*border border-gray-300[^"]*"[^>]*>.*?</a>)', re.DOTALL)

# 统一的按钮样式
unified_search_button = '<button class="btn btn-primary h-10 px-4" type="submit">'
unified_reset_button = '<a href="{href}" class="h-10 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center">'

def unify_buttons_in_file(file_path):
    """统一单个文件中的按钮样式"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 处理搜索按钮
    def replace_search_button(match):
        button_content = match.group(1)
        # 提取按钮内部内容（图标和文本）
        inner_content_match = re.search(r'<button[^>]*>(.*?)</button>', button_content, re.DOTALL)
        if inner_content_match:
            inner_content = inner_content_match.group(1)
            return f'{unified_search_button}{inner_content}</button>'
        return button_content
    
    # 处理重置按钮
    def replace_reset_button(match):
        button_content = match.group(1)
        # 提取href和内部内容
        href_match = re.search(r'href="([^"]+)"', button_content)
        inner_content_match = re.search(r'<a[^>]*>(.*?)</a>', button_content, re.DOTALL)
        if href_match and inner_content_match:
            href = href_match.group(1)
            inner_content = inner_content_match.group(1)
            return f'{unified_reset_button.format(href=href)}{inner_content}</a>'
        return button_content
    
    # 应用替换
    new_content = search_button_pattern.sub(replace_search_button, content)
    new_content = reset_button_pattern.sub(replace_reset_button, new_content)
    
    # 如果内容有变化，写回文件
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    """主函数"""
    modified_files = []
    
    # 遍历所有HTML文件
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                if unify_buttons_in_file(file_path):
                    modified_files.append(file_path)
    
    # 输出结果
    if modified_files:
        print(f"已统一以下文件的搜索卡片按钮样式：")
        for file_path in modified_files:
            print(f"  - {os.path.relpath(file_path, os.path.dirname(__file__))}")
    else:
        print("没有需要修改的文件")

if __name__ == "__main__":
    main()
