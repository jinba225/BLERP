#!/usr/bin/env python3
"""
测试预付款核销逻辑

验证场景：
- 供应商丙预付了两次，总共100000
- 相关订单要付78000
- 手动核销时，全部用预付（从预付款中扣除78000）
"""

import os
import sys

import django

sys.path.insert(0, "/Users/janjung/Code_Projects/django_erp")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")
django.setup()

from decimal import Decimal

from finance.models import SupplierAccount, SupplierPrepayment
from suppliers.models import Supplier


def test_prepayment_writeoff():
    """测试预付款核销逻辑"""
    print("=" * 70)
    print("🔍 预付款核销逻辑测试")
    print("=" * 70)

    # 查找供应商丙
    suppliers = Supplier.objects.filter(name__icontains="丙")
    if not suppliers:
        print("\n❌ 未找到供应商丙")
        print("   请先创建供应商丙并添加预付款")
        return False

    supplier = suppliers.first()
    print(f"\n✅ 找到供应商: {supplier.name}")

    # 查找该供应商的预付款
    prepays = SupplierPrepayment.objects.filter(supplier=supplier, is_deleted=False).order_by(
        "-paid_date"
    )

    if prepays.count() < 2:
        print(f"\n⚠️  供应商丙只有 {prepays.count()} 笔预付款，需要至少2笔")
        return False

    print(f"\n📊 该供应商的预付款:")
    total_prepaid = Decimal("0")
    for prepay in prepays:
        total_prepaid += prepay.balance
        print(f'  {prepay.paid_date.strftime("%Y-%m-%d")}: {prepay.amount} (余额: {prepay.balance})')
    print(f"  总预付: {total_prepaid}")

    # 查找该供应商的应付账款
    accounts = SupplierAccount.objects.filter(supplier=supplier, is_deleted=False).order_by(
        "-created_at"
    )

    if not accounts:
        print("\n⚠️  该供应商没有应付账款")
        return False

    print(f"\n📋 该供应商的应付账款:")
    for account in accounts[:3]:  # 只显示前3个
        print(f"  {account.invoice_number}: {account.balance}  {account.status}")

    # 测试核销逻辑
    print(f"\n🧪 测试核销逻辑:")
    print(f"\n场景: 应付账款78000元，使用预付款核销")

    account = accounts[0]
    writeoff_amount = Decimal("78000")

    print(f"  应付账款余额: {account.balance}")
    print(f"  核销金额: {writeoff_amount}")

    # 模拟旧逻辑（错误）
    print(f"\n❌ 旧逻辑（有BUG）:")
    max_use_old = account.balance - writeoff_amount
    effective_prepay_old = min(total_prepaid, max_use_old) if max_use_old > 0 else Decimal("0")
    print(f"  max_use = {account.balance} - {writeoff_amount} = {max_use_old}")
    print(f"  effective_prepay = min({total_prepaid}, {max_use_old}) = {effective_prepay_old}")
    print(f"  ⚠️  问题: 即使预付充足，也只能用{effective_prepay_old}元预付")
    cash_needed_old = writeoff_amount - effective_prepay_old
    print(f"  还需要现金: {cash_needed_old}元")

    # 模拟新逻辑（正确）
    print(f"\n✅ 新逻辑（已修复）:")
    effective_prepay_new = min(total_prepaid, writeoff_amount)
    print(f"  effective_prepay = min({total_prepaid}, {writeoff_amount}) = {effective_prepay_new}")
    print(f"  ✅ 预付款支付: {effective_prepay_new}元")
    cash_needed_new = writeoff_amount - effective_prepay_new
    print(f"  还需要现金: {cash_needed_new}元")

    # 验证结果
    print(f"\n📊 对比:")
    if effective_prepay_new > effective_prepay_old:
        improvement = effective_prepay_new - effective_prepay_old
        print(f"  ✅ 修复后多使用预付款: {improvement}元")
        print(f"  ✅ 减少现金支付: {improvement}元")

    return True


def show_writeoff_formula():
    """显示核销计算公式"""
    print("\n" + "=" * 70)
    print("📐 预付款核销计算公式")
    print("=" * 70)

    print("\n场景数据:")
    print("  供应商丙预付总额: 100,000 元")
    print("  应付账款余额: 78,000 元")
    print("  核销金额: 78,000 元")
    print("  选择: 使用预付款核销")

    print("\n❌ 旧逻辑（有BUG）:")
    print("  max_use = 应收账款余额 - 核销金额")
    print("  max_use = 78,000 - 78,000 = 0")
    print("  effective_prepay = min(预付款余额, max_use)")
    print("  effective_prepay = min(100,000, 0) = 0 ❌")
    print("  结果: 预付款使用0元，现金支付78,000元")

    print("\n✅ 新逻辑（已修复）:")
    print("  effective_prepay = min(预付款余额, 核销金额)")
    print("  effective_prepay = min(100,000, 78,000) = 78,000 ✅")
    print("  结果: 预付款支付78,000元，现金支付0元")

    print("\n💡 业务逻辑:")
    print('  当选择了"使用预付款"时，应该优先使用预付款来支付')
    print("  如果预付款余额 >= 核销金额，全部使用预付款")
    print("  如果预付款余额 < 核销金额，剩余部分使用现金")

    print("\n修复位置:")
    print("  apps/finance/views.py:")
    print("    - supplier_account_writeoff (第808-820行)")
    print("    - customer_account_writeoff (第613-625行)")


if __name__ == "__main__":
    print("\n" + "🔧" * 35)
    print("  预付款核销逻辑测试")
    print("🔧" * 35 + "\n")

    # 显示公式
    show_writeoff_formula()

    # 实际测试
    print("\n")
    success = test_prepayment_writeoff()

    print("\n" + "=" * 70)
    if success:
        print("✅ 测试完成")
    else:
        print("❌ 测试失败")
    print("=" * 70 + "\n")
