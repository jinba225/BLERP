#!/usr/bin/env python
"""
完整修复打印模板的明细项显示问题
修复内容：
1. 添加 table 配置（关键！）
2. 修复所有字段名错误
3. 删除重复的字段
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, '/Users/janjung/Code_Projects/BLBS_ERP/django_erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')
django.setup()

from apps.sales.models import PrintTemplate
import json

def fix_template():
    """完整修复模板"""

    # 获取模板
    template = PrintTemplate.objects.filter(pk=1).first()
    if not template:
        print("❌ 模板不存在")
        return False

    print(f"📄 修复模板: {template.name}")
    print("=" * 80)

    config = template.layout_config
    panel = config.get('panels', [{}])[0]
    elements = panel.get('printElements', [])

    # ===== 步骤1: 修复字段名并去重 =====
    print("\n步骤1: 修复字段名并去重")
    print("-" * 80)

    field_mapping = {
        'items.#.specification': 'items.#.specifications',
        'items.#.subtotal': 'items.#.line_total',
    }

    seen_fields = set()
    unique_elements = []
    fixed_count = 0
    removed_count = 0

    for i, elem in enumerate(elements):
        title = elem.get('printElementType', {}).get('title', '未知')
        field = elem.get('options', {}).get('field', None)

        # 修复字段名
        if field in field_mapping:
            old_field = field
            new_field = field_mapping[field]
            elem['options']['field'] = new_field
            if 'printElementType' in elem and 'field' in elem['printElementType']:
                elem['printElementType']['field'] = new_field

            print(f"✅ 修复字段: {title:15s} {old_field} → {new_field}")
            field = new_field
            fixed_count += 1

        # 去重：如果是明细项字段且已存在，则跳过
        if field and 'items.#' in field:
            if field in seen_fields:
                print(f"⚠️ 删除重复: {title:15s} ({field})")
                removed_count += 1
                continue
            seen_fields.add(field)

        unique_elements.append(elem)

    panel['printElements'] = unique_elements

    print(f"\n修复 {fixed_count} 个字段，删除 {removed_count} 个重复字段")

    # ===== 步骤2: 添加 table 配置 =====
    print("\n步骤2: 添加 table 配置")
    print("-" * 80)

    # 找出所有明细项字段的位置范围
    item_elements = [(i, e) for i, e in enumerate(unique_elements)
                     if 'items.#' in str(e.get('options', {}).get('field', ''))]

    if item_elements:
        # 获取明细项元素的位置范围
        item_positions = [e.get('options', {}).get('top', 0) for _, e in item_elements]
        min_top = min(item_positions) if item_positions else 100
        max_top = max(item_positions) if item_positions else 200

        # 计算表格高度（从第一个明细项到最后一个，留一些边距）
        table_height = max(50, max_top - min_top + 30)

        # 添加 table 配置
        panel['table'] = {
            'top': min_top - 5,  # 表格起始位置（略微往上，留出表头空间）
            'height': table_height,  # 表格高度
            'columns': []  # HiPrint 会自动处理列
        }

        print(f"✅ 添加 table 配置:")
        print(f"   - top: {panel['table']['top']}")
        print(f"   - height: {panel['table']['height']}")
        print(f"   - 包含 {len(item_elements)} 个明细项字段")
    else:
        print("⚠️ 没有找到明细项字段，跳过 table 配置")

    # ===== 步骤3: 保存模板 =====
    print("\n步骤3: 保存模板")
    print("-" * 80)

    template.layout_config = config
    template.save()

    print("✅ 模板已保存到数据库")

    # 导出修复后的模板
    output_path = '/Users/janjung/Code_Projects/BLBS_ERP/django_erp/template_fixed_complete.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"📄 修复后的模板已导出到: {output_path}")

    print("\n" + "=" * 80)
    print("✅ 模板修复完成！")
    print("\n💡 下一步：刷新打印页面测试")
    print("   URL: http://127.0.0.1:8000/sales/quotes/13/print/?template_id=1")

    return True

if __name__ == '__main__':
    success = fix_template()
    sys.exit(0 if success else 1)
