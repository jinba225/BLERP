#!/usr/bin/env python
"""
测试单号前缀配置功能

验证：
1. 前缀配置是否正确创建
2. 新用法是否正常工作
3. 旧用法兼容性
4. 修改配置后是否生效
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')
django.setup()

from apps.core.models import SystemConfig
from apps.core.utils import DocumentNumberGenerator

print("=== 单号前缀配置功能测试 ===\n")

# 测试1：检查配置是否存在
print("【测试1】检查单号前缀配置")
print("-" * 60)

key_prefixes = {
    'document_prefix_sales_order': 'SO',
    'document_prefix_purchase_order': 'PO',
    'document_prefix_receipt': 'IN',
    'document_prefix_delivery': 'OUT',
}

all_ok = True
for key, expected_value in key_prefixes.items():
    try:
        config = SystemConfig.objects.get(key=key)
        if config.value == expected_value:
            print(f"✓ {key}: {config.value}")
        else:
            print(f"✗ {key}: 期望 {expected_value}, 实际 {config.value}")
            all_ok = False
    except SystemConfig.DoesNotExist:
        print(f"✗ {key}: 配置不存在")
        all_ok = False

if all_ok:
    print("\n✅ 所有关键前缀配置正确")
else:
    print("\n❌ 部分配置有问题")

# 测试2：新用法 - 使用配置键名
print("\n\n【测试2】新用法 - 使用配置键名")
print("-" * 60)

test_cases = [
    ('sales_order', 'SO'),
    ('purchase_order', 'PO'),
    ('quotation', 'QT'),
    ('delivery', 'OUT'),
]

for key, expected_prefix in test_cases:
    prefix = DocumentNumberGenerator.get_prefix(key)
    number = DocumentNumberGenerator.generate(key)

    if prefix == expected_prefix and number.startswith(expected_prefix):
        print(f"✓ {key}: {number}")
    else:
        print(f"✗ {key}: 期望前缀 {expected_prefix}, 实际 {prefix}, 单号 {number}")

# 测试3：旧用法兼容性
print("\n\n【测试3】旧用法兼容性 - 直接使用前缀字符串")
print("-" * 60)

legacy_prefixes = ['SO', 'PO', 'QT', 'DL', 'SR']

for old_prefix in legacy_prefixes:
    try:
        number = DocumentNumberGenerator.generate(old_prefix)
        print(f"✓ {old_prefix}: {number}")
    except Exception as e:
        print(f"✗ {old_prefix}: 错误 - {str(e)}")

# 测试4：修改配置后测试
print("\n\n【测试4】修改配置后测试")
print("-" * 60)

# 临时修改销售订单前缀
test_config = SystemConfig.objects.get(key='document_prefix_sales_order')
original_value = test_config.value
print(f"原始前缀: {original_value}")

test_config.value = 'TEST'
test_config.save()
print(f"修改前缀为: {test_config.value}")

# 生成新单号
new_number = DocumentNumberGenerator.generate('sales_order')
print(f"新生成单号: {new_number}")

if new_number.startswith('TEST'):
    print("✓ 配置修改后单号前缀正确变更")
else:
    print(f"✗ 配置修改后单号前缀未变更，期望 TEST，实际 {new_number[:4]}")

# 恢复原始值
test_config.value = original_value
test_config.save()
print(f"恢复原始前缀: {original_value}")

# 测试5：统计所有单号前缀配置
print("\n\n【测试5】所有单号前缀配置统计")
print("-" * 60)

all_prefix_configs = SystemConfig.objects.filter(
    key__startswith='document_prefix_',
    is_active=True
).order_by('key')

print(f"总计: {all_prefix_configs.count()} 个单号前缀配置\n")

for config in all_prefix_configs:
    # 提取配置名称
    name = config.key.replace('document_prefix_', '')
    desc = config.description.split('-')[0].strip() if config.description else ''
    print(f"  {name:25} → {config.value:6} ({desc})")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)

print("\n💡 提示：")
print("- 可以通过后台修改单号前缀：/admin/core/systemconfig/")
print("- 单号格式：前缀 + YYYYMMDD + 4位序号")
print("- 修改前缀只影响新单据，不影响历史单据")
