#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BetterLaser ERP - 图标诊断脚本
扫描所有模板文件，检查 heroicon 图标使用情况
"""

import os
import re
from collections import defaultdict
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / 'templates'
HEROICONS_FILE = PROJECT_ROOT / 'static' / 'js' / 'heroicons.js'

def load_heroicons_from_js():
    """从 heroicons.js 加载已定义的图标列表"""
    icons = set()
    try:
        with open(HEROICONS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            # 匹配 'icon-name': { 格式
            pattern = re.compile(r"'([^']+)':\s*\{")
            icons = set(pattern.findall(content))
    except Exception as e:
        print(f"❌ 加载 heroicons.js 失败: {e}")

    return icons

def scan_templates_for_icons():
    """扫描所有模板文件，收集使用的图标"""
    icon_usage = defaultdict(list)

    # 遍历所有模板文件
    for template_file in TEMPLATES_DIR.rglob('*.html'):
        # 跳过备份文件
        if '.bak' in str(template_file):
            continue

        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()

                # 匹配 heroicon('icon-name') 格式
                pattern = re.compile(r"heroicon\(['\"]([^'\"]+)['\"]")
                matches = pattern.findall(content)

                for icon_name in matches:
                    icon_usage[icon_name].append(str(template_file.relative_to(PROJECT_ROOT)))

        except Exception as e:
            print(f"⚠️  读取文件 {template_file} 失败: {e}")

    return icon_usage

def generate_report(icon_usage, defined_icons):
    """生成诊断报告"""
    print("=" * 80)
    print("🔍 BetterLaser ERP - Heroicons 图标诊断报告")
    print("=" * 80)
    print()

    # 统计信息
    total_usage = sum(len(files) for files in icon_usage.values())
    unique_icons = len(icon_usage)
    defined_count = len(defined_icons)

    print(f"📊 统计信息:")
    print(f"   - 已定义图标数: {defined_count}")
    print(f"   - 使用中的图标数: {unique_icons}")
    print(f"   - 总使用次数: {total_usage}")
    print()

    # 分类图标
    missing_icons = set(icon_usage.keys()) - defined_icons
    available_icons = set(icon_usage.keys()) & defined_icons
    unused_icons = defined_icons - set(icon_usage.keys())

    print(f"✅ 可用图标 ({len(available_icons)} 个):")
    if available_icons:
        for icon in sorted(available_icons):
            usage_count = len(icon_usage[icon])
            print(f"   - {icon:30s} (使用 {usage_count:2d} 次)")
    print()

    print(f"❌ 缺失图标 ({len(missing_icons)} 个):")
    if missing_icons:
        for icon in sorted(missing_icons):
            files = icon_usage[icon]
            print(f"   - {icon:30s} (使用 {len(files):2d} 次)")
            for file in files[:3]:  # 只显示前3个文件
                print(f"     → {file}")
            if len(files) > 3:
                print(f"     ... 还有 {len(files) - 3} 个文件")
            print()
    else:
        print("   🎉 所有图标都已定义！")
        print()

    print(f"📦 未使用的图标 ({len(unused_icons)} 个):")
    if unused_icons:
        for icon in sorted(unused_icons):
            print(f"   - {icon}")
    print()

    # 详细问题列表
    if missing_icons:
        print("=" * 80)
        print("⚠️  需要修复的问题")
        print("=" * 80)
        print()
        print(f"发现 {len(missing_icons)} 个缺失的图标，需要添加到 heroicons.js 中:")
        print()
        for icon in sorted(missing_icons):
            print(f"1. {icon}")

        print()
        print("建议操作:")
        print("   - 从 Heroicons 官网获取 SVG 路径数据")
        print("   - 添加到 static/js/heroicons.js")
        print("   - 运行 python manage.py collectstatic")
        print("   - 清除浏览器缓存并重新加载页面")

    return missing_icons, available_icons, unused_icons

def main():
    print()
    print("🔧 开始诊断...")
    print()

    # 加载已定义的图标
    defined_icons = load_heroicons_from_js()
    print(f"✅ 已加载 {len(defined_icons)} 个已定义图标")

    # 扫描模板文件
    icon_usage = scan_templates_for_icons()
    print(f"✅ 已扫描 {len(icon_usage)} 个使用的图标")

    print()
    # 生成报告
    missing_icons, available_icons, unused_icons = generate_report(icon_usage, defined_icons)

    print()
    print("=" * 80)
    print("📋 诊断完成")
    print("=" * 80)

    # 返回退出码
    if missing_icons:
        print(f"\n⚠️  发现 {len(missing_icons)} 个缺失图标，需要修复")
        return 1
    else:
        print(f"\n✅ 所有图标正常，无需修复")
        return 0

if __name__ == '__main__':
    exit(main())
