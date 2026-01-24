#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Font Awesome 图标批量替换为 Tailwind SVG 图标

此脚本会：
1. 扫描 templates/ 目录下的所有 HTML 文件
2. 将 Font Awesome <i class="fa-*"> 图标替换为 Tailwind SVG 图标
3. 保留原有的 Tailwind CSS 类
4. 生成详细报告
"""

import os
import re
from pathlib import Path
from datetime import datetime

# 导入图标映射表
from fontawesome_to_svg_mapping import ICON_MAPPING, ICON_ALIASES


class FontAwesomeReplacer:
    def __init__(self, templates_dir='templates'):
        self.templates_dir = Path(templates_dir)
        self.stats = {
            'files_processed': 0,
            'icons_replaced': 0,
            'icons_skipped': 0,
            'files_modified': 0,
        }
        self.replacement_log = []
        self.skipped_icons = set()

    def extract_icon_name(self, class_attr):
        """从 class 属性中提取 Font Awesome 图标名称"""
        # 匹配 fa-* 或 fas fa-* 或 far fa-* 等模式
        match = re.search(r'\bfa-[a-z0-9-]+\b', class_attr)
        if match:
            icon_name = match.group(0)
            # 移除 fa- 前缀
            return icon_name.replace('fa-', '', 1)
        return None

    def extract_tailwind_classes(self, class_attr):
        """从 class 属性中提取 Tailwind 类（移除 fa-* 类）"""
        # 移除所有 fa-* 相关的类
        classes = class_attr.split()
        tailwind_classes = [
            cls for cls in classes
            if not cls.startswith('fa') and cls != 'fas' and cls != 'far' and cls != 'fab'
        ]
        return ' '.join(tailwind_classes)

    def get_replacement_svg(self, fa_icon_name):
        """获取 Font Awesome 图标对应的 SVG"""
        # 检查别名
        if fa_icon_name in ICON_ALIASES:
            fa_icon_name = ICON_ALIASES[fa_icon_name]

        # 查找映射
        if fa_icon_name in ICON_MAPPING:
            mapping = ICON_MAPPING[fa_icon_name]
            return mapping['svg_template'], mapping['default_classes']
        else:
            return None, None

    def replace_icon_tag(self, match):
        """替换单个图标标签"""
        full_tag = match.group(0)
        class_attr = match.group(1)

        # 提取图标名称
        icon_name = self.extract_icon_name(class_attr)
        if not icon_name:
            return full_tag

        # 获取替换 SVG
        svg_template, default_classes = self.get_replacement_svg(icon_name)
        if not svg_template:
            self.stats['icons_skipped'] += 1
            self.skipped_icons.add(icon_name)
            return full_tag

        # 提取 Tailwind 类
        tailwind_classes = self.extract_tailwind_classes(class_attr)

        # 组合类名：如果有 Tailwind 类，使用它；否则使用默认类
        if tailwind_classes:
            final_classes = tailwind_classes
        else:
            final_classes = default_classes

        # 生成 SVG
        replacement = svg_template.format(classes=final_classes)

        # 记录日志
        self.stats['icons_replaced'] += 1
        self.replacement_log.append({
            'icon_name': icon_name,
            'original_tag': full_tag,
            'replacement': replacement,
        })

        return replacement

    def process_file(self, file_path):
        """处理单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 记录原始内容用于比较
            original_content = content

            # 匹配 <i class="fa-* ..."></i> 标签
            # 支持多种模式：
            # - <i class="fas fa-times"></i>
            # - <i class="fas fa-edit mr-2"></i>
            # - <i class="fa fa-user text-blue-600"></i>
            pattern = r'<i\s+class="([^"]*fa-[^"]*)"[^>]*>\s*</i>'

            # 替换所有图标
            content = re.sub(pattern, self.replace_icon_tag, content)

            # 如果内容有变化，写回文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.stats['files_modified'] += 1
                return True

            return False

        except Exception as e:
            print(f"错误：处理文件 {file_path} 时出错：{str(e)}")
            return False

    def run(self):
        """执行批量替换"""
        print("=" * 70)
        print("Font Awesome 图标批量替换为 Tailwind SVG")
        print("=" * 70)
        print()

        # 验证模板目录
        if not self.templates_dir.exists():
            print(f"错误：模板目录不存在：{self.templates_dir}")
            return

        # 收集所有 HTML 文件（排除备份文件）
        html_files = [
            f for f in self.templates_dir.rglob('*.html')
            if not f.suffix in ['.bak', '.span', '.bak2'] and '.bak' not in f.name
        ]

        if not html_files:
            print("未找到任何 HTML 文件")
            return

        print(f"找到 {len(html_files)} 个 HTML 文件")
        print(f"映射表包含 {len(ICON_MAPPING)} 个图标")
        print()
        print("开始处理...")
        print("-" * 70)

        # 处理每个文件
        for i, file_path in enumerate(html_files, 1):
            self.stats['files_processed'] += 1

            # 显示进度
            relative_path = file_path.relative_to(self.templates_dir)
            modified = self.process_file(file_path)

            status = "✓ 已修改" if modified else "- 未修改"
            print(f"[{i}/{len(html_files)}] {status} - {relative_path}")

        print()
        print("=" * 70)
        print("替换完成！")
        print("=" * 70)
        print()

        # 打印统计信息
        print("统计信息：")
        print(f"  - 处理文件数：{self.stats['files_processed']}")
        print(f"  - 修改文件数：{self.stats['files_modified']}")
        print(f"  - 替换图标数：{self.stats['icons_replaced']}")
        print(f"  - 跳过图标数：{self.stats['icons_skipped']}")
        print()

        # 打印跳过的图标
        if self.skipped_icons:
            print("跳过的图标（未在映射表中）：")
            for icon in sorted(self.skipped_icons):
                print(f"  - fa-{icon}")
            print()

        # 保存详细报告
        self.save_report()

    def save_report(self):
        """保存详细报告"""
        report_dir = Path('scripts/reports')
        report_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f'fontawesome_replacement_report_{timestamp}.txt'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("Font Awesome 图标替换详细报告\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("统计信息：\n")
            f.write(f"  - 处理文件数：{self.stats['files_processed']}\n")
            f.write(f"  - 修改文件数：{self.stats['files_modified']}\n")
            f.write(f"  - 替换图标数：{self.stats['icons_replaced']}\n")
            f.write(f"  - 跳过图标数：{self.stats['icons_skipped']}\n\n")

            if self.skipped_icons:
                f.write("跳过的图标：\n")
                for icon in sorted(self.skipped_icons):
                    f.write(f"  - fa-{icon}\n")
                f.write("\n")

            if self.replacement_log:
                f.write("替换详情（前50条）：\n")
                f.write("-" * 70 + "\n")
                for i, log in enumerate(self.replacement_log[:50], 1):
                    f.write(f"\n{i}. fa-{log['icon_name']}\n")
                    f.write(f"   原始标签：{log['original_tag'][:80]}...\n")
                    f.write(f"   替换为：{log['replacement'][:80]}...\n")

        print(f"详细报告已保存至：{report_file}")


def main():
    """主函数"""
    import sys
    import subprocess

    # 检查是否在项目根目录
    if not Path('templates').exists():
        print("错误：请在项目根目录运行此脚本")
        print("提示：cd /path/to/django_erp && python scripts/replace_fontawesome_to_svg.py")
        sys.exit(1)

    # 创建替换器并运行
    replacer = FontAwesomeReplacer(templates_dir='templates')
    replacer.run()

    # 验证结果
    print("\n验证结果...")
    print("-" * 70)

    # 检查是否还有 Font Awesome 引用
    result = subprocess.run(
        ['grep', '-r', '-n', 'fa-', 'templates/', '--include=*.html'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        lines = [line for line in result.stdout.split('\n') if line and '.bak' not in line]
        if lines:
            print(f"⚠ 警告：仍然存在 {len(lines)} 个 Font Awesome 引用")
            print("\n前20个：")
            for line in lines[:20]:
                print(f"  {line}")
            if len(lines) > 20:
                print(f"  ... 还有 {len(lines) - 20} 个")
        else:
            print("✓ 验证通过：所有 Font Awesome 图标已替换")
    else:
        print("✓ 验证通过：未发现 Font Awesome 引用")

    print("\n" + "=" * 70)
    print("任务完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
