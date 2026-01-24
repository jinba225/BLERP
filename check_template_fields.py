#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, '/Users/janjung/Code_Projects/BLBS_ERP/django_erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')
django.setup()

from apps.sales.models import PrintTemplate
import json

# 获取模板
t = PrintTemplate.objects.filter(pk=1).first()
if not t:
    print("模板不存在")
    sys.exit(1)

config = t.layout_config
elements = config.get('panels', [{}])[0].get('printElements', [])

print(f"模板名称: {t.name}")
print(f"元素总数: {len(elements)}\n")
print("=" * 100)

has_field_binding = False

for i, elem in enumerate(elements):
    title = elem.get('printElementType', {}).get('title', '未知')
    elem_type = elem.get('printElementType', {}).get('type', '未知')

    # 检查两个地方的字段绑定
    field_in_options = elem.get('options', {}).get('field', None)
    field_in_type = elem.get('printElementType', {}).get('field', None)

    test_data = elem.get('options', {}).get('testData', None)

    print(f"\n元素 {i+1}: {title}")
    print(f"  类型: {elem_type}")

    # 检查字段绑定
    if field_in_options:
        print(f"  ✅ options.field: {field_in_options}")
        has_field_binding = True
    else:
        print(f"  ❌ options.field: 无")

    if field_in_type:
        print(f"  ✅ printElementType.field: {field_in_type}")
        has_field_binding = True
    else:
        print(f"  ❌ printElementType.field: 无")

    # 显示测试数据
    if test_data:
        test_data_str = str(test_data)
        if len(test_data_str) > 50:
            print(f"  测试数据: {test_data_str[:50]}...")
        else:
            print(f"  测试数据: {test_data_str}")

print("\n" + "=" * 100)
print("\n📋 诊断结果:")

field_elements = []
no_field_elements = []

for elem in elements:
    has_field = (elem.get('options', {}).get('field') or
                 elem.get('printElementType', {}).get('field'))
    if has_field:
        field_elements.append(elem)
    else:
        no_field_elements.append(elem)

print(f"  - 有字段绑定的元素: {len(field_elements)} 个")
print(f"  - 无字段绑定的元素: {len(no_field_elements)} 个")

if len(no_field_elements) > 0:
    print("\n⚠️ 问题：以下元素没有字段绑定，只会显示固定文本：")
    for elem in no_field_elements[:10]:  # 只显示前10个
        title = elem.get('printElementType', {}).get('title', '未知')
        test_data = elem.get('options', {}).get('testData', '')
        if len(str(test_data)) > 30:
            test_data = str(test_data)[:30] + '...'
        print(f"    - {title}: {test_data}")

if not has_field_binding:
    print("\n❌❌❌ 严重问题：模板中没有任何字段绑定！")
    print("   这就是为什么打印出来全是测试数据的原因。")
    print("\n💡 解决方案：")
    print("   1. 必须从元素库重新拖拽字段到画布")
    print("   2. 不能使用 '📝 基础元素 > 文本' 然后手动输入字段名")
    print("   3. 必须使用 '🔖 基本信息'、'📦 明细项字段' 等分组中的预定义字段")

# 导出完整的模板JSON到文件，方便检查
with open('/Users/janjung/Code_Projects/BLBS_ERP/django_erp/template_debug.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"\n📄 完整模板JSON已导出到: template_debug.json")
