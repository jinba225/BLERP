#!/usr/bin/env python3
"""
统一所有页面搜索卡片的布局，确保按钮与输入框在同一行
"""

import os
import re

# 定义要搜索的目录
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')

# 匹配搜索卡片表单的正则表达式
form_pattern = re.compile(r'<form method="get" class="grid grid-cols-1 ([^"]*)">.*?</form>', re.DOTALL)

# 匹配输入字段的正则表达式
input_field_pattern = re.compile(r'<div>.*?<label.*?</div>', re.DOTALL)

# 匹配按钮区域的正则表达式
button_area_pattern = re.compile(r'<div class="flex items-end[^"]*">.*?</div>', re.DOTALL)

def adjust_search_card_layout(file_path):
    """调整单个文件的搜索卡片布局"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有搜索表单
    forms = form_pattern.findall(content)
    
    if not forms:
        return False
    
    new_content = content
    
    for form_class in forms:
        # 分析表单中的输入字段数量
        # 提取表单内容
        form_match = re.search(rf'<form method="get" class="grid grid-cols-1 {re.escape(form_class)}">(.*?)</form>', content, re.DOTALL)
        if not form_match:
            continue
        
        form_content = form_match.group(1)
        
        # 计算输入字段数量
        input_fields = input_field_pattern.findall(form_content)
        button_area = button_area_pattern.search(form_content)
        
        if not button_area:
            continue
        
        # 根据输入字段数量调整布局
        field_count = len(input_fields)
        
        # 计算新的网格布局
        if field_count == 1:
            # 1个输入字段 + 1个按钮区域 = 2列
            new_form_class = 'md:grid-cols-2 lg:grid-cols-2 gap-4'
        elif field_count == 2:
            # 2个输入字段 + 1个按钮区域 = 3列
            new_form_class = 'md:grid-cols-3 lg:grid-cols-3 gap-4'
        elif field_count == 3:
            # 3个输入字段 + 1个按钮区域 = 4列
            new_form_class = 'md:grid-cols-4 lg:grid-cols-4 gap-4'
        elif field_count == 4:
            # 4个输入字段 + 1个按钮区域 = 5列
            new_form_class = 'md:grid-cols-5 lg:grid-cols-5 gap-4'
        else:
            # 更多字段，使用默认布局
            continue
        
        # 替换表单类
        old_form_pattern = rf'<form method="get" class="grid grid-cols-1 {re.escape(form_class)}"'
        new_form = f'<form method="get" class="grid grid-cols-1 {new_form_class}">'
        new_content = re.sub(old_form_pattern, new_form, new_content)
        
        # 为每个输入字段添加适当的列类
        for i, field in enumerate(input_fields):
            old_field_pattern = re.escape(field)
            # 为每个输入字段添加列类
            new_field = field.replace('<div>', f'<div class="lg:col-span-1">')
            new_content = new_content.replace(field, new_field)
        
        # 为按钮区域添加列类
        button_html = button_area.group(0)
        new_button_html = button_html.replace('<div class="flex items-end', '<div class="lg:col-span-1 flex items-end')
        new_content = new_content.replace(button_html, new_button_html)
    
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
                if adjust_search_card_layout(file_path):
                    modified_files.append(file_path)
    
    # 输出结果
    if modified_files:
        print(f"已调整以下文件的搜索卡片布局：")
        for file_path in modified_files:
            print(f"  - {os.path.relpath(file_path, os.path.dirname(__file__))}")
    else:
        print("没有需要修改的文件")

if __name__ == "__main__":
    main()
