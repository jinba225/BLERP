#!/usr/bin/env python
"""
扫描Django项目中所有URL配置和对应的模板文件
找出缺失的模板
"""
import os
import re
import sys

# 添加Django项目路径
sys.path.insert(0, '/Users/janjung/Code_Projects/BLBS_ERP/django_erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')

import django
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

def extract_views_from_file(filepath):
    """从Python文件中提取render调用的模板"""
    templates = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # 匹配 render(request, 'template_name.html', ...)
            pattern = r"render\s*\(\s*request\s*,\s*['\"]([^'\"]+\.html)['\"]"
            matches = re.findall(pattern, content)
            templates.extend(matches)
    except Exception as e:
        pass
    return templates

def get_all_url_patterns(resolver=None, namespace='', prefix=''):
    """递归获取所有URL模式"""
    if resolver is None:
        resolver = get_resolver()

    patterns = []

    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLResolver):
            # 递归处理include的URL
            new_namespace = f"{namespace}:{pattern.namespace}" if pattern.namespace else namespace
            new_prefix = prefix + str(pattern.pattern)
            patterns.extend(get_all_url_patterns(pattern, new_namespace, new_prefix))
        elif isinstance(pattern, URLPattern):
            # 单个URL模式
            url_name = f"{namespace}:{pattern.name}" if pattern.name else None
            url_path = prefix + str(pattern.pattern)

            # 获取视图函数/类
            callback = pattern.callback
            view_name = None
            view_file = None

            if hasattr(callback, '__name__'):
                view_name = callback.__name__
            elif hasattr(callback, 'view_class'):
                view_name = callback.view_class.__name__

            if hasattr(callback, '__module__'):
                module = sys.modules.get(callback.__module__)
                if module and hasattr(module, '__file__'):
                    view_file = module.__file__

            patterns.append({
                'url_path': url_path,
                'url_name': url_name,
                'view_name': view_name,
                'view_file': view_file,
            })

    return patterns

def check_template_exists(template_name):
    """检查模板文件是否存在"""
    template_dirs = [
        '/Users/janjung/Code_Projects/BLBS_ERP/django_erp/templates',
    ]

    for template_dir in template_dirs:
        template_path = os.path.join(template_dir, template_name)
        if os.path.exists(template_path):
            return True
    return False

def main():
    print("="*80)
    print("Django项目URL和模板扫描报告")
    print("="*80)

    # 获取所有URL模式
    patterns = get_all_url_patterns()

    # 统计信息
    total_urls = len(patterns)
    urls_with_views = 0
    templates_needed = set()
    templates_missing = set()

    print(f"\n发现 {total_urls} 个URL模式\n")

    # 分析每个URL
    view_files_checked = set()

    for p in patterns:
        if p['view_file'] and p['view_file'] not in view_files_checked:
            view_files_checked.add(p['view_file'])
            templates = extract_views_from_file(p['view_file'])
            templates_needed.update(templates)

    # 检查模板是否存在
    for template in templates_needed:
        if not check_template_exists(template):
            templates_missing.add(template)

    # 输出结果
    print("\n" + "="*80)
    print("需要的模板文件:")
    print("="*80)
    for template in sorted(templates_needed):
        exists = "✓" if check_template_exists(template) else "✗"
        print(f"{exists} {template}")

    print("\n" + "="*80)
    print(f"缺失的模板文件 ({len(templates_missing)} 个):")
    print("="*80)
    for template in sorted(templates_missing):
        print(f"  ✗ {template}")

    print("\n" + "="*80)
    print("统计摘要:")
    print("="*80)
    print(f"总URL数量: {total_urls}")
    print(f"需要模板: {len(templates_needed)}")
    print(f"已存在: {len(templates_needed) - len(templates_missing)}")
    print(f"缺失: {len(templates_missing)}")
    print("="*80)

if __name__ == '__main__':
    main()
