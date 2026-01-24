#!/usr/bin/env python
"""
初始化单号生成规则配置

配置单号的日期格式和流水号位数
运行方式：python init_document_number_rules.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')
django.setup()

from apps.core.models import SystemConfig

# 定义单号生成规则配置
DOCUMENT_NUMBER_RULES = {
    'document_number_date_format': {
        'value': 'YYMMDD',
        'description': '单号日期格式 - 可选值：YYYYMMDD（8位）、YYMMDD（6位）、YYMM（4位）',
        'config_type': 'business',
    },
    'document_number_sequence_digits': {
        'value': '3',
        'description': '单号流水号位数 - 推荐值：3位、4位、5位',
        'config_type': 'business',
    },
}

def init_rules():
    """初始化单号生成规则配置"""
    print("开始初始化单号生成规则配置...\n")

    created_count = 0
    updated_count = 0

    for key, config_data in DOCUMENT_NUMBER_RULES.items():
        config, created = SystemConfig.objects.get_or_create(
            key=key,
            defaults={
                'value': config_data['value'],
                'description': config_data['description'],
                'config_type': config_data['config_type'],
            }
        )

        if created:
            created_count += 1
            print(f"✓ 创建配置: {key} = {config.value}")
        else:
            updated_count += 1
            print(f"  已存在: {key} = {config.value} (保留现有配置)")

    print(f"\n完成！创建 {created_count} 个新配置，跳过 {updated_count} 个已存在的配置")
    print("\n配置说明：")
    print("1. 单号日期格式 (document_number_date_format)：")
    print("   - YYMMDD  : 6位日期，例如：251108 (2025年11月8日) [推荐]")
    print("   - YYYYMMDD: 8位日期，例如：20251108 (2025年11月8日)")
    print("   - YYMM    : 4位日期，例如：2511 (2025年11月)")
    print("\n2. 单号流水号位数 (document_number_sequence_digits)：")
    print("   - 3: 三位流水号 001-999 [推荐]")
    print("   - 4: 四位流水号 0001-9999")
    print("   - 5: 五位流水号 00001-99999")
    print("\n示例单号格式：")
    print("  SO251108001   (前缀 + YYMMDD + 3位流水号) [推荐]")
    print("  SO20251108001 (前缀 + YYYYMMDD + 3位流水号)")
    print("  SO2511001     (前缀 + YYMM + 3位流水号)")
    print("\n这些配置可以在系统后台 /admin/core/systemconfig/ 中修改")

if __name__ == '__main__':
    init_rules()
