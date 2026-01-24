#!/usr/bin/env python
"""
测试单号生成规则（日期格式和流水号位数）

验证：
1. YYMMDD + 3位流水号（默认配置）
2. 修改为 YYYYMMDD + 4位流水号
3. 修改为 YYMM + 3位流水号
4. 解析不同格式的单号
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')
django.setup()

from apps.core.models import SystemConfig
from apps.core.utils import DocumentNumberGenerator
from datetime import date

print("=== 单号生成规则测试 ===\n")

# 测试1：默认配置 - YYMMDD + 3位流水号
print("【测试1】默认配置 - YYMMDD + 3位流水号")
print("-" * 60)

date_format = DocumentNumberGenerator.get_date_format()
sequence_digits = DocumentNumberGenerator.get_sequence_digits()

print(f"当前配置：")
print(f"  日期格式: {date_format}")
print(f"  流水号位数: {sequence_digits}")

# 生成示例单号
test_date = date(2025, 11, 8)
samples = []
for doc_type in ['sales_order', 'purchase_order', 'quotation', 'delivery']:
    number = DocumentNumberGenerator.generate(doc_type, test_date)
    samples.append(number)
    print(f"  {doc_type:20} → {number}")

expected_pattern = "前缀 + YYMMDD + 3位流水号"
print(f"\n预期格式: {expected_pattern}")
print(f"示例: SO251108001 (SO + 251108 + 001)")

# 验证格式
all_ok = True
test_prefixes = {'sales_order': 'SO', 'purchase_order': 'PO', 'quotation': 'QT', 'delivery': 'OUT'}
for i, number in enumerate(samples):
    doc_type = ['sales_order', 'purchase_order', 'quotation', 'delivery'][i]
    prefix = test_prefixes[doc_type]
    # 去掉前缀后应该是 6 + 3 = 9 位数字
    number_part = number[len(prefix):]  # 根据实际前缀长度
    if len(number_part) == 9 and number_part[:6].isdigit() and number_part[-3:].isdigit():
        print(f"✓ {number} - 格式正确")
    else:
        print(f"✗ {number} - 格式错误 (预期 {prefix} + 6位日期 + 3位流水号)")
        all_ok = False

if all_ok:
    print("\n✅ 默认配置测试通过")
else:
    print("\n❌ 默认配置测试失败")

# 测试2：修改为 YYYYMMDD + 4位流水号
print("\n\n【测试2】修改配置 - YYYYMMDD + 4位流水号")
print("-" * 60)

config_date = SystemConfig.objects.get(key='document_number_date_format')
config_seq = SystemConfig.objects.get(key='document_number_sequence_digits')

original_date_format = config_date.value
original_seq_digits = config_seq.value

config_date.value = 'YYYYMMDD'
config_seq.value = '4'
config_date.save()
config_seq.save()

print(f"修改配置：")
print(f"  日期格式: {config_date.value}")
print(f"  流水号位数: {config_seq.value}")

# 生成新单号
print(f"\n生成的单号：")
for doc_type in ['sales_order', 'purchase_order']:
    number = DocumentNumberGenerator.generate(doc_type, test_date)
    print(f"  {doc_type:20} → {number}")
    # 验证格式：去掉前缀后应该是 8 + 4 = 12 位数字
    number_part = number[2:]
    if len(number_part) == 12:
        print(f"    ✓ 长度正确 (8位日期 + 4位流水号)")
    else:
        print(f"    ✗ 长度错误，实际 {len(number_part)} 位")

# 测试3：修改为 YYMM + 3位流水号
print("\n\n【测试3】修改配置 - YYMM + 3位流水号")
print("-" * 60)

config_date.value = 'YYMM'
config_seq.value = '3'
config_date.save()
config_seq.save()

print(f"修改配置：")
print(f"  日期格式: {config_date.value}")
print(f"  流水号位数: {config_seq.value}")

# 生成新单号
print(f"\n生成的单号：")
for doc_type in ['quotation', 'delivery']:
    number = DocumentNumberGenerator.generate(doc_type, test_date)
    print(f"  {doc_type:20} → {number}")
    # 验证格式：去掉前缀后应该是 4 + 3 = 7 位数字
    number_part = number[2:]
    if len(number_part) >= 7:
        print(f"    ✓ 包含年月信息 (4位) + 流水号 (3位)")
    else:
        print(f"    ✗ 长度不足")

# 测试4：解析不同格式的单号
print("\n\n【测试4】解析不同格式的单号")
print("-" * 60)

test_numbers = [
    ('SO251108001', 'SO', 'YYMMDD', 3),
    ('PO20251108001', 'PO', 'YYYYMMDD', 3),
    ('QT2511001', 'QT', 'YYMM', 3),
]

for number, prefix, date_fmt, seq_digits in test_numbers:
    parsed = DocumentNumberGenerator.parse_number(number, prefix, date_fmt, seq_digits)
    if parsed:
        print(f"✓ {number}")
        print(f"  前缀: {parsed['prefix']}")
        print(f"  日期: {parsed['date']}")
        print(f"  流水号: {parsed['sequence']}")
    else:
        print(f"✗ {number} - 解析失败")

# 测试5：验证配置修改立即生效
print("\n\n【测试5】验证配置修改立即生效")
print("-" * 60)

# 切换回默认
config_date.value = 'YYMMDD'
config_seq.value = '3'
config_date.save()
config_seq.save()

number1 = DocumentNumberGenerator.generate('sales_order', test_date)
print(f"YYMMDD + 3位: {number1}")

# 切换到8位日期
config_date.value = 'YYYYMMDD'
config_date.save()

number2 = DocumentNumberGenerator.generate('sales_order', test_date)
print(f"YYYYMMDD + 3位: {number2}")

if len(number1[2:]) == 9 and len(number2[2:]) == 11:
    print("✓ 配置修改立即生效")
else:
    print(f"✗ 配置未生效 - 长度: {len(number1[2:])}, {len(number2[2:])}")

# 恢复原始配置
config_date.value = original_date_format
config_seq.value = original_seq_digits
config_date.save()
config_seq.save()

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)

print(f"\n✓ 已恢复原始配置：")
print(f"  日期格式: {original_date_format}")
print(f"  流水号位数: {original_seq_digits}")

print("\n💡 推荐配置：")
print("  日期格式: YYMMDD (6位，简洁明了)")
print("  流水号位数: 3 (支持每天999个单号)")
print("\n  示例单号: SO251108001")
print("    - SO: 销售订单")
print("    - 251108: 2025年11月8日")
print("    - 001: 当天第1号")

print("\n📌 如需修改配置：")
print("  访问后台: http://localhost:8000/admin/core/systemconfig/")
print("  修改:")
print("    - document_number_date_format (YYYYMMDD/YYMMDD/YYMM)")
print("    - document_number_sequence_digits (3/4/5)")
