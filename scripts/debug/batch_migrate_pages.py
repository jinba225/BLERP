#!/usr/bin/env python3
"""
智能批量迁移脚本 - 页面刷新系统
自动检测并迁移所有未迁移的列表页
"""

import os
import re
from pathlib import Path


def check_if_migrated(file_path):
    """检查文件是否已经迁移"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        # 检查是否包含 usePageRefresh
        return "usePageRefresh" in content
    except:
        return False


def migrate_template(file_path):
    """迁移单个模板文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # 检查是否已迁移
        if "usePageRefresh" in content:
            return False, "已迁移"

        # 1. 在主容器添加 x-data
        # 查找 {% block content %} 后的第一个 <div class="space-y-6">
        pattern = r'({%\s*block\s+content\s*%}.*?<div\s+class="space-y-6")'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            content = content.replace(
                match.group(1),
                match.group(1).replace(
                    'class="space-y-6"',
                    'class="space-y-6" x-data="usePageRefresh({ interval: 30 })"',
                ),
            )

        # 2. 查找header部分，添加刷新按钮
        # 查找 <div class="flex justify-between items-center">
        header_pattern = r'(<div class="flex justify-between items-center">.*?<div>.*?</div>.*?)(<a class="btn btn-primary"|</div>)'

        def add_refresh_button(match):
            header_start = match.group(1)
            next_tag = match.group(2)

            # 如果已经有刷新按钮，跳过
            if '@click="manualRefresh"' in header_start:
                return match.group(0)

            # 插入刷新按钮
            refresh_button = """<div class="flex items-center space-x-3">
            <button type="button" @click="manualRefresh"
                :disabled="isRefreshing"
                class="text-sm text-gray-600 hover:text-theme-600 flex items-center transition-colors px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                title="刷新页面">
                <svg class="w-4 h-4 mr-2" :class="{ 'animate-spin': isRefreshing }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
                <span x-text="isRefreshing ? '刷新中...' : '刷新'"></span>
            </button>
            """

            # 如果下一个标签是按钮，添加到按钮组
            if '<a class="btn btn-primary"' in next_tag:
                return header_start + refresh_button + next_tag
            else:
                # 如果是结束div，替换整个结构
                return header_start + refresh_button + "</div></div>"

        content = re.sub(header_pattern, add_refresh_button, content, count=1, flags=re.DOTALL)

        # 如果没有变化，返回
        if content == original_content:
            return False, "无需变更（可能是结构不匹配）"

        # 写回文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True, "迁移成功"

    except Exception as e:
        return False, f"错误: {str(e)}"


def main():
    """主函数"""
    base_dir = Path("/Users/janjung/Code_Projects/django_erp/templates/modules")

    # 查找所有列表页
    list_files = list(base_dir.rglob("*_list.html"))

    print("=" * 70)
    print("Django ERP 页面自动刷新系统 - 智能批量迁移工具")
    print("=" * 70)
    print(f"\n找到 {len(list_files)} 个列表页文件\n")

    success_count = 0
    skip_count = 0
    error_count = 0

    for file_path in sorted(list_files):
        rel_path = file_path.relative_to(base_dir)

        # 检查是否已迁移
        if check_if_migrated(file_path):
            print(f"⏭️  跳过（已迁移）: {rel_path}")
            skip_count += 1
            continue

        # 尝试迁移
        success, message = migrate_template(file_path)

        if success:
            print(f"✅ {message}: {rel_path}")
            success_count += 1
        elif "已迁移" in message or "无需变更" in message:
            print(f"⏭️  {message}: {rel_path}")
            skip_count += 1
        else:
            print(f"❌ {message}: {rel_path}")
            error_count += 1

    print("\n" + "=" * 70)
    print("迁移完成！")
    print("=" * 70)
    print(f"✅ 成功: {success_count}")
    print(f"⏭️  跳过: {skip_count}")
    print(f"❌ 失败: {error_count}")
    print(f"📊 总计: {len(list_files)}")
    print()

    # 计算总进度
    total_migrated = success_count + skip_count
    total_files = len(list_files)
    progress = (total_migrated / total_files * 100) if total_files > 0 else 0

    print(f"🎯 总体进度: {total_migrated}/{total_files} ({progress:.1f}%)")
    print()


if __name__ == "__main__":
    main()
