#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, '/Users/janjung/Code_Projects/BLBS_ERP/django_erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')
django.setup()

from apps.sales.models import PrintTemplate

# 获取模板
t = PrintTemplate.objects.filter(pk=1).first()
if not t:
    print("模板不存在")
    sys.exit(1)

config = t.layout_config
elements = config.get('panels', [{}])[0].get('printElements', [])

print(f"模板名称: {t.name}")
print(f"元素总数: {len(elements)}\n")
print("=" * 80)

for i, elem in enumerate(elements):
    title = elem.get('printElementType', {}).get('title', '未知')
    elem_type = elem.get('printElementType', {}).get('type', '未知')
    field = elem.get('options', {}).get('field', None)
    test_data = elem.get('options', {}).get('testData', None)

    print(f"\n元素 {i+1}:")
    print(f"  标题: {title}")
    print(f"  类型: {elem_type}")

    if field:
        print(f"  ✅ 字段绑定: {field}")
    else:
        print(f"  ❌ 字段绑定: 无（这是问题！）")

    if test_data:
        test_data_str = str(test_data)
        if len(test_data_str) > 50:
            print(f"  测试数据: {test_data_str[:50]}...")
        else:
            print(f"  测试数据: {test_data_str}")

print("\n" + "=" * 80)
print("\n📋 诊断结果:")

field_elements = [e for e in elements if e.get('options', {}).get('field')]
text_only_elements = [e for e in elements if not e.get('options', {}).get('field')]

print(f"  - 绑定了字段的元素: {len(field_elements)} 个")
print(f"  - 仅有测试数据的元素: {len(text_only_elements)} 个")

if len(text_only_elements) > 5:
    print("\n⚠️ 问题：大量元素没有绑定字段，只显示固定文本！")
    print("   这就是为什么打印出来是测试数据的原因。")
