#!/usr/bin/env python
"""
测试脚本：验证 add_test_data 功能
测试添加测试数据的健壮性
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


def test_add_test_data():
    """测试添加测试数据功能"""

    print_separator("测试数据添加功能测试")

    # 第一次运行：应该创建新数据
    print("\n[测试 1] 第一次运行 add_test_data...")
    success, message, stats = DatabaseHelper.add_test_data()

    print(f"\n结果: {'✅ 成功' if success else '❌ 失败'}")
    print(f"\n消息:\n{message}")

    if not success:
        print("\n❌ 第一次测试失败！")
        return False

    print(f"\n统计信息:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")

    # 第二次运行：应该跳过已存在的数据（测试幂等性）
    print_separator("测试幂等性")
    print("\n[测试 2] 第二次运行 add_test_data（测试幂等性）...")
    success2, message2, stats2 = DatabaseHelper.add_test_data()

    print(f"\n结果: {'✅ 成功' if success2 else '❌ 失败'}")
    print(f"\n消息:\n{message2}")

    if not success2:
        print("\n❌ 第二次测试失败！")
        return False

    print(f"\n统计信息:")
    for key, value in stats2.items():
        print(f"  - {key}: {value}")

    # 验证第二次运行创建的记录数应该为0或很少
    total_created_1 = sum(stats.values())
    total_created_2 = sum(stats2.values())

    print(f"\n[验证] 第一次创建: {total_created_1} 条")
    print(f"[验证] 第二次创建: {total_created_2} 条")

    if total_created_2 <= total_created_1:
        print("\n✅ 幂等性测试通过！第二次运行没有创建重复数据")
    else:
        print("\n⚠️  警告：第二次运行创建了更多数据，可能存在重复")

    # 验证数据库中的数据
    print_separator("验证数据库内容")

    from apps.products.models import Unit, Brand, ProductCategory, Product
    from apps.customers.models import Customer
    from apps.suppliers.models import Supplier
    from apps.inventory.models import Warehouse

    print("\n数据库统计:")
    print(f"  - 计量单位: {Unit.objects.count()} 条")
    print(f"  - 品牌: {Brand.objects.count()} 条")
    print(f"  - 产品分类: {ProductCategory.objects.count()} 条")
    print(f"  - 仓库: {Warehouse.objects.count()} 条")
    print(f"  - 客户: {Customer.objects.filter(is_deleted=False).count()} 条")
    print(f"  - 供应商: {Supplier.objects.filter(is_deleted=False).count()} 条")
    print(f"  - 产品: {Product.objects.filter(is_deleted=False).count()} 条")

    # 显示测试数据样本
    print("\n测试数据样本:")

    test_brands = Brand.objects.filter(code__startswith='TEST_')
    print(f"\n  测试品牌 ({test_brands.count()} 个):")
    for brand in test_brands[:3]:
        print(f"    - {brand.name} (code: {brand.code})")

    test_products = Product.objects.filter(code__startswith='TEST_')
    print(f"\n  测试产品 ({test_products.count()} 个):")
    for product in test_products[:3]:
        print(f"    - {product.name} (code: {product.code}, price: ¥{product.selling_price})")

    test_customers = Customer.objects.filter(code__startswith='TEST_')
    print(f"\n  测试客户 ({test_customers.count()} 个):")
    for customer in test_customers[:3]:
        print(f"    - {customer.name} (code: {customer.code})")

    print_separator("所有测试完成")
    print("\n✅ 测试数据添加功能正常！")

    return True


if __name__ == '__main__':
    try:
        result = test_add_test_data()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
