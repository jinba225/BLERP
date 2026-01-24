#!/usr/bin/env python
"""
初始化采购模块系统配置
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')
django.setup()

from apps.core.models import SystemConfig

print("=== 初始化采购模块系统配置 ===\n")

# 1. 采购申请审核后自动生成采购订单配置
config, created = SystemConfig.objects.get_or_create(
    key='purchase_auto_create_order_on_approve',
    defaults={
        'value': 'true',
        'config_type': 'business',
        'description': '采购申请审核后自动生成采购订单（true/false）',
        'is_active': True
    }
)

if created:
    print(f"✓ 创建配置: {config.key}")
    print(f"  默认值: {config.value}")
    print(f"  说明: {config.description}")
else:
    print(f"✓ 配置已存在: {config.key}")
    print(f"  当前值: {config.value}")

print("\n提示: 可在后台 /admin/core/systemconfig/ 修改配置")
print("  - true: 采购申请审核后自动生成采购订单（当前设置）")
print("  - false: 采购申请审核后不自动生成采购订单，需手动转换")
print("\n✅ 配置初始化完成！")
