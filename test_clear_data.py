#!/usr/bin/env python
"""
测试脚本：验证 clear_test_data 功能
测试清除测试数据的完整性（包括基础数据）
"""

import os
import sys
import django

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')
django.setup()

from apps.core.utils.database_helper import DatabaseHelper


def print_separator(title=""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    else:
        print(f"{'='*60}")


def test_clear_and_add_data():
    """测试清除数据和添加数据的完整流程"""

    print_separator("完整测试流程：清除 -> 添加 -> 验证")

    # 步骤1: 清除所有测试数据
    print("\n[步骤 1] 清除所有测试数据...")
    success, message, stats = DatabaseHelper.clear_test_data()

    print(f"\n结果: {'✅ 成功' if success else '❌ 失败'}")
    print(f"\n消息:\n{message}")

    if not success:
        print("\n❌ 清除数据失败！")
        return False

    print(f"\n清除统计:")
    for key, value in stats.items():
        if value > 0:
            print(f"  - {key}: {value}")

    # 步骤2: 添加测试数据
    print_separator("添加测试数据")
    print("\n[步骤 2] 添加测试数据...")
    success2, message2, stats2 = DatabaseHelper.add_test_data()

    print(f"\n结果: {'✅ 成功' if success2 else '❌ 失败'}")
    print(f"\n消息:\n{message2}")

    if not success2:
        print("\n❌ 添加数据失败！")
        return False

    print(f"\n添加统计:")
    for key, value in stats2.items():
        if value > 0:
            print(f"  - {key}: {value}")

    # 步骤3: 验证数据
    print_separator("验证数据库内容")

    from apps.products.models import Unit, Brand, ProductCategory, Product
    from apps.customers.models import Customer
    from apps.suppliers.models import Supplier
    from apps.inventory.models import Warehouse, Location
    from apps.finance.models import TaxRate

    print("\n数据库统计（仅未删除记录）:")
    print(f"  - 税率: {TaxRate.objects.filter(is_deleted=False).count()} 条")
    print(f"  - 计量单位: {Unit.objects.filter(is_deleted=False).count()} 条")
    print(f"  - 品牌: {Brand.objects.filter(is_deleted=False).count()} 条")
    print(f"  - 产品分类: {ProductCategory.objects.filter(is_deleted=False).count()} 条")
    print(f"  - 仓库: {Warehouse.objects.filter(is_deleted=False).count()} 条")
    print(f"  - 库位: {Location.objects.filter(is_deleted=False).count()} 条")
    print(f"  - 客户: {Customer.objects.filter(is_deleted=False).count()} 条")
    print(f"  - 供应商: {Supplier.objects.filter(is_deleted=False).count()} 条")
    print(f"  - 产品: {Product.objects.filter(is_deleted=False).count()} 条")

    # 显示税率样本
    print("\n税率数据样本:")
    test_tax_rates = TaxRate.objects.filter(code__startswith='VAT_', is_deleted=False)
    print(f"\n  测试税率 ({test_tax_rates.count()} 个):")
    for tax in test_tax_rates:
        print(f"    - {tax.name} (code: {tax.code}, rate: {tax.rate}, default: {tax.is_default})")

    # 显示计量单位样本
    print("\n计量单位数据样本:")
    test_units = Unit.objects.filter(name__startswith='测试', is_deleted=False)
    print(f"\n  测试计量单位 ({test_units.count()} 个):")
    for unit in test_units[:3]:
        print(f"    - {unit.name} (symbol: {unit.symbol})")

    # 显示仓库样本
    print("\n仓库数据样本:")
    test_warehouses = Warehouse.objects.filter(code__startswith='TEST_', is_deleted=False)
    print(f"\n  测试仓库 ({test_warehouses.count()} 个):")
    for wh in test_warehouses:
        print(f"    - {wh.name} (code: {wh.code}, type: {wh.warehouse_type})")

    print_separator("所有测试完成")
    print("\n✅ 清除和添加数据功能正常！")

    return True


if __name__ == '__main__':
    try:
        result = test_clear_and_add_data()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
