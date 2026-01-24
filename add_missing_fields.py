#!/usr/bin/env python
"""
添加缺失的明细项字段：specifications 和 line_total
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

def add_missing_fields():
    """添加缺失的字段"""

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

    # 找到现有明细项字段的位置
    item_elements = [e for e in elements if 'items.#' in str(e.get('options', {}).get('field', ''))]

    if not item_elements:
        print("❌ 没有找到明细项字段")
        return False

    # 计算新字段的位置（基于现有字段）
    first_elem = item_elements[0]
    base_top = first_elem.get('options', {}).get('top', 241.5)
    base_left = first_elem.get('options', {}).get('left', 100)

    print(f"📍 基准位置: top={base_top}, left={base_left}")

    # 检查是否已存在
    has_specifications = any('items.#.specifications' == e.get('options', {}).get('field') for e in elements)
    has_line_total = any('items.#.line_total' == e.get('options', {}).get('field') for e in elements)

    added_count = 0

    # 添加 specifications 字段（规格型号）
    if not has_specifications:
        spec_elem = {
            "options": {
                "left": 169.5,  # 在产品名称和数量之间
                "top": base_top,
                "height": 20,
                "width": 120,
                "field": "items.#.specifications",
                "testData": "示例规格",
                "fontSize": 11,
                "fontWeight": "normal",
                "textAlign": "left",
                "hideTitle": True,
                "borderWidth": 1,
                "borderColor": "#d1d5db",
                "borderStyle": "solid"
            },
            "printElementType": {
                "title": "规格型号",
                "type": "text",
                "field": "items.#.specifications"
            }
        }
        elements.append(spec_elem)
        added_count += 1
        print("✅ 添加字段: 规格型号 (items.#.specifications)")

    # 添加 line_total 字段（小计）
    if not has_line_total:
        total_elem = {
            "options": {
                "left": 438.5,  # 最右边
                "top": base_top,
                "height": 20,
                "width": 90,
                "field": "items.#.line_total",
                "testData": "1000.00",
                "fontSize": 11,
                "fontWeight": "normal",
                "textAlign": "right",
                "hideTitle": True,
                "borderWidth": 1,
                "borderColor": "#d1d5db",
                "borderStyle": "solid"
            },
            "printElementType": {
                "title": "小计",
                "type": "text",
                "field": "items.#.line_total"
            }
        }
        elements.append(total_elem)
        added_count += 1
        print("✅ 添加字段: 小计 (items.#.line_total)")

    if added_count > 0:
        # 保存模板
        panel['printElements'] = elements
        template.layout_config = config
        template.save()

        print("\n" + "=" * 80)
        print(f"✅ 成功添加 {added_count} 个字段")
        print(f"📝 模板已保存到数据库")

        # 导出修复后的模板
        output_path = '/Users/janjung/Code_Projects/BLBS_ERP/django_erp/template_with_missing_fields.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"📄 修复后的模板已导出到: {output_path}")

        return True
    else:
        print("\n⚠️ 所有字段都已存在，无需添加")
        return False

if __name__ == '__main__':
    success = add_missing_fields()
    sys.exit(0 if success else 1)
