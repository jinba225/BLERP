#!/usr/bin/env python
"""
自动修复打印模板中的字段名不匹配问题
修复内容：
1. specification → specifications (单数改复数)
2. subtotal → line_total (修正字段名)
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

def fix_template_fields():
    """修复模板字段名"""

    # 获取模板
    template = PrintTemplate.objects.filter(pk=1).first()
    if not template:
        print("❌ 模板不存在")
        return False

    print(f"📄 修复模板: {template.name}")
    print("=" * 80)

    config = template.layout_config
    elements = config.get('panels', [{}])[0].get('printElements', [])

    # 字段映射关系
    field_mapping = {
        'items.#.specification': 'items.#.specifications',  # 单数 → 复数
        'items.#.subtotal': 'items.#.line_total',          # 修正字段名
    }

    fixed_count = 0

    for i, elem in enumerate(elements):
        title = elem.get('printElementType', {}).get('title', '未知')
        old_field = elem.get('options', {}).get('field', None)

        # 检查是否需要修复
        if old_field in field_mapping:
            new_field = field_mapping[old_field]

            # 修复 options.field
            elem['options']['field'] = new_field

            # 修复 printElementType.field（如果存在）
            if 'printElementType' in elem and 'field' in elem['printElementType']:
                elem['printElementType']['field'] = new_field

            print(f"✅ 元素 {i+1}: {title:15s}")
            print(f"   修复前: {old_field}")
            print(f"   修复后: {new_field}")
            print()

            fixed_count += 1

    if fixed_count > 0:
        # 保存修复后的模板
        template.layout_config = config
        template.save()

        print("=" * 80)
        print(f"✅ 成功修复 {fixed_count} 个字段")
        print(f"📝 模板已保存到数据库")

        # 输出修复后的完整模板（用于验证）
        output_path = '/Users/janjung/Code_Projects/BLBS_ERP/django_erp/template_fixed.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"📄 修复后的模板已导出到: {output_path}")

        return True
    else:
        print("⚠️ 没有找到需要修复的字段")
        return False

if __name__ == '__main__':
    success = fix_template_fields()
    sys.exit(0 if success else 1)
