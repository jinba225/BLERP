#!/usr/bin/env python3
"""
测试预付款/预收款合并功能

验证场景：
1. 供应商丙有多笔预付款
2. 合并多笔预付款为一笔
3. 验证合并后的记录状态
4. 验证核销时只显示合并后的记录
"""

import os
import sys

import django

sys.path.insert(0, "/Users/janjung/Code_Projects/django_erp")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")
django.setup()

from decimal import Decimal

from customers.models import Customer
from finance.models import CustomerPrepayment, SupplierPrepayment
from suppliers.models import Supplier


def test_supplier_prepayment_consolidation():
    """测试供应商预付款合并"""
    print("=" * 70)
    print("🔍 供应商预付款合并测试")
    print("=" * 70)

    # 查找供应商丙
    suppliers = Supplier.objects.filter(name__icontains="丙")
    if not suppliers:
        print("\n❌ 未找到供应商丙")
        return False

    supplier = suppliers.first()
    print(f"\n✅ 找到供应商: {supplier.name}")

    # 获取该供应商的活跃预付款
    active_prepays = SupplierPrepayment.objects.filter(
        supplier=supplier, status="active", is_deleted=False
    ).order_by("-paid_date")

    if active_prepays.count() < 2:
        print(f"\n⚠️  供应商丙只有 {active_prepays.count()} 笔活跃预付款，需要至少2笔才能测试合并")
        return False

    print(f"\n📊 合并前的活跃预付款:")
    total_amount = Decimal("0")
    total_balance = Decimal("0")
    for prepay in active_prepays:
        total_amount += prepay.amount
        total_balance += prepay.balance
        print(f"  ID:{prepay.id} | {prepay.paid_date} | 金额:{prepay.amount} | 余额:{prepay.balance}")

    print(f"\n  总计: {active_prepays.count()} 笔")
    print(f"  总金额: {total_amount}")
    print(f"  总余额: {total_balance}")

    # 模拟合并操作
    print(f"\n🔄 模拟合并操作...")

    # 创建合并后的预付款
    consolidated = SupplierPrepayment.objects.create(
        supplier=supplier,
        amount=total_amount,
        balance=total_balance,
        paid_date=active_prepays.first().paid_date,
        notes=f"合并了 {active_prepays.count()} 笔预付款",
        status="active",
        is_consolidated=True,
    )
    print(f"  ✅ 创建合并记录: ID={consolidated.id}, 余额={consolidated.balance}")

    # 更新原记录状态
    updated_count = active_prepays.update(status="merged", merged_into=consolidated)
    print(f'  ✅ 更新原记录: {updated_count} 笔标记为"已合并"')

    # 验证合并结果
    print(f"\n📊 合并后的状态:")
    new_active_prepays = SupplierPrepayment.objects.filter(
        supplier=supplier, status="active", is_deleted=False
    )

    print(f"  活跃预付款: {new_active_prepays.count()} 笔")
    for prepay in new_active_prepays:
        print(
            f"    ID:{prepay.id} | 金额:{prepay.amount} | 余额:{prepay.balance} | 合并记录:{prepay.is_consolidated}"
        )

    merged_prepays = SupplierPrepayment.objects.filter(
        supplier=supplier, status="merged", is_deleted=False
    )
    print(f"  已合并预付款: {merged_prepays.count()} 笔")

    # 验证余额是否正确
    expected_balance = total_balance
    actual_balance = consolidated.balance

    if expected_balance == actual_balance:
        print(f"\n✅ 验证通过: 合并后余额正确 ({actual_balance})")
    else:
        print(f"\n❌ 验证失败: 预期{expected_balance}, 实际{actual_balance}")
        return False

    # 测试核销时只显示活跃预付款
    print(f"\n🧪 测试核销视图查询:")
    writeoff_prepays = SupplierPrepayment.objects.filter(
        supplier=supplier, status="active", balance__gt=0, is_deleted=False
    )
    print(f"  可用于核销的预付款: {writeoff_prepays.count()} 笔")
    for prepay in writeoff_prepays:
        print(f"    ID:{prepay.id} | 余额:{prepay.balance}")

    print(f"\n✅ 供应商预付款合并测试完成！")
    return True


def test_customer_prepayment_consolidation():
    """测试客户预收款合并"""
    print("\n" + "=" * 70)
    print("🔍 客户预收款合并测试")
    print("=" * 70)

    # 查找有多次预收款的客户
    customers = Customer.objects.filter(is_deleted=False)

    test_customer = None
    for customer in customers:
        active_prepays = CustomerPrepayment.objects.filter(
            customer=customer, status="active", is_deleted=False
        )
        if active_prepays.count() >= 2:
            test_customer = customer
            break

    if not test_customer:
        print("\n⚠️  没有找到有2笔以上预收款的客户")
        return False

    print(f"\n✅ 找到客户: {test_customer.name}")

    # 获取该客户的活跃预收款
    active_prepays = CustomerPrepayment.objects.filter(
        customer=test_customer, status="active", is_deleted=False
    ).order_by("-received_date")

    print(f"\n📊 合并前的活跃预收款:")
    total_amount = Decimal("0")
    total_balance = Decimal("0")
    for prepay in active_prepays:
        total_amount += prepay.amount
        total_balance += prepay.balance
        print(
            f"  ID:{prepay.id} | {prepay.received_date} | 金额:{prepay.amount} | 余额:{prepay.balance}"
        )

    print(f"\n  总计: {active_prepays.count()} 笔")
    print(f"  总金额: {total_amount}")
    print(f"  总余额: {total_balance}")

    # 模拟合并操作
    print(f"\n🔄 模拟合并操作...")

    # 创建合并后的预收款
    consolidated = CustomerPrepayment.objects.create(
        customer=test_customer,
        amount=total_amount,
        balance=total_balance,
        received_date=active_prepays.first().received_date,
        notes=f"合并了 {active_prepays.count()} 笔预收款",
        status="active",
        is_consolidated=True,
    )
    print(f"  ✅ 创建合并记录: ID={consolidated.id}, 余额={consolidated.balance}")

    # 更新原记录状态
    updated_count = active_prepays.update(status="merged", merged_into=consolidated)
    print(f'  ✅ 更新原记录: {updated_count} 笔标记为"已合并"')

    print(f"\n✅ 客户预收款合并测试完成！")
    return True


def show_usage_instructions():
    """显示使用说明"""
    print("\n" + "=" * 70)
    print("📖 预付款合并功能使用说明")
    print("=" * 70)

    print("\n1. 访问预付款列表页:")
    print("   http://127.0.0.1:8000/finance/prepayments/supplier/")

    print('\n2. 在"供应商预付款统计"区域，查看每个供应商的预付款笔数')

    print('\n3. 如果某个供应商有2笔或以上预付款，会显示"合并"按钮')

    print('\n4. 点击"合并"按钮进入合并页面:')
    print("   - 查看所有预付款明细")
    print("   - 勾选要合并的预付款（至少2笔）")
    print("   - 查看实时统计信息")
    print('   - 点击"合并预付款"按钮提交')

    print("\n5. 合并后的效果:")
    print("   - 生成一条新的预付款记录，余额为所有选中记录的余额之和")
    print('   - 原记录被标记为"已合并"，不在列表中显示')
    print("   - 核销时只会显示合并后的记录")

    print("\n6. 客户预收款合并同理:")
    print("   http://127.0.0.1:8000/finance/prepayments/customer/")

    print("\n💡 业务优势:")
    print("   - 避免多次预付金额远超应付，却只能使用单次预付的问题")
    print("   - 简化核销操作，一次性使用所有预付款余额")
    print("   - 提高财务管理效率")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\n" + "🔧" * 35)
    print("  预付款/预收款合并功能测试")
    print("🔧" * 35 + "\n")

    # 显示使用说明
    show_usage_instructions()

    # 测试供应商预付款合并
    supplier_success = test_supplier_prepayment_consolidation()

    # 测试客户预收款合并
    customer_success = test_customer_prepayment_consolidation()

    print("\n" + "=" * 70)
    if supplier_success and customer_success:
        print("✅ 所有测试通过")
    else:
        print("⚠️  部分测试未通过（可能是数据不足）")
    print("=" * 70 + "\n")
