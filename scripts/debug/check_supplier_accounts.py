#!/usr/bin/env python
"""
检查供应商应付账款详细信息
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")
django.setup()

from finance.models import SupplierAccount, SupplierAccountDetail


def check_supplier_account(account_id):
    """查看应付账款主单详情"""

    print(f"\n{'='*70}")
    print(f"应付账款主单详情 - ID: {account_id}")
    print(f"{'='*70}\n")

    try:
        account = SupplierAccount.objects.get(pk=account_id, is_deleted=False)
    except SupplierAccount.DoesNotExist:
        print("❌ 应付账款主单不存在或已删除")
        return

    # 主单基本信息
    print("📋 主单基本信息:")
    print(f"  ID: {account.id}")
    print(f"  供应商: {account.supplier.name}")
    if account.purchase_order:
        print(f"  采购订单: {account.purchase_order.order_number}")
    if account.sales_return:
        print(f"  销售退货: {account.sales_return.return_number}")
    print(f"  当前余额: ¥{account.balance:.2f}")
    print(f"  实际应付: ¥{account.invoice_amount:.2f}")
    print(f"  已核销: ¥{account.paid_amount:.2f}")
    print(f"  状态: {account.get_status_display()}")
    print(f"  创建时间: {account.created_at}")
    print()

    # 查询所有明细
    details = account.details.filter(is_deleted=False).order_by("created_at")

    print(f"💳 应付明细记录 (共 {details.count()} 条):")
    print(f"{'='*70}")

    if not details.exists():
        print("  ⚠️  没有任何明细记录")
    else:
        total_amount = 0
        total_allocated = 0

        for idx, detail in enumerate(details, 1):
            print(f"\n  明细 {idx}:")
            print(f"    单号: {detail.detail_number}")
            print(f"    类型: {detail.get_detail_type_display()}")
            print(f"    金额: ¥{detail.amount:.2f}", end="")
            if detail.amount < 0:
                print(" (负应付)", end="")
            print()
            print(f"    已分配: ¥{detail.allocated_amount:.2f}")
            print(f"    未分配: ¥{detail.amount - detail.allocated_amount:.2f}")
            print(f"    业务日期: {detail.business_date}")
            print(f"    创建时间: {detail.created_at}")
            print(f"    备注: {detail.notes}")

            # 关联单据
            if detail.purchase_order:
                print(f"    关联采购订单: {detail.purchase_order.order_number}")
            if detail.receipt:
                print(f"    关联收货单: {detail.receipt.receipt_number}")
            if detail.return_order:
                print(f"    关联退货单: {detail.return_order.return_number}")

            total_amount += detail.amount
            total_allocated += detail.allocated_amount

        print(f"\n  {'='*70}")
        print(f"  📊 汇总统计:")
        print(f"     总金额: ¥{total_amount:.2f}")
        print(f"     已分配: ¥{total_allocated:.2f}")
        print(f"     未分配: ¥{total_amount - total_allocated:.2f}")
        print(f"     主单余额: ¥{account.balance:.2f}")

        # 验证余额是否正确
        expected_balance = total_amount - total_allocated
        if abs(account.balance - expected_balance) < 0.01:
            print(f"  ✅ 余额计算正确")
        else:
            print(f"  ⚠️  余额不一致！")
            print(f"     预期余额: ¥{expected_balance:.2f}")
            print(f"     实际余额: ¥{account.balance:.2f}")

    print(f"\n{'='*70}\n")


def list_supplier_accounts(supplier_id=None):
    """列出所有应付账款主单"""
    from django.db.models import Sum

    print(f"\n{'='*70}")
    print(f"应付账款主单列表")
    print(f"{'='*70}\n")

    accounts = SupplierAccount.objects.filter(is_deleted=False)

    if supplier_id:
        accounts = accounts.filter(supplier_id=supplier_id)
        print(f"过滤条件: 供应商ID = {supplier_id}\n")

    print(f"找到 {accounts.count()} 个应付账款主单\n")

    if not accounts.exists():
        print("没有找到任何应付账款主单")
        return

    for account in accounts.order_by("-created_at"):
        # 统计明细数量
        details_count = account.details.filter(is_deleted=False).count()

        print(f"ID: {account.id:3d} | {account.account_number}")
        print(f"  供应商: {account.supplier.name}")
        if account.purchase_order:
            print(f"  采购订单: {account.purchase_order.order_number}")
        print(f"  当前余额: ¥{account.balance:>10.2f}")
        print(f"  已分配: ¥{account.allocated_amount:>10.2f}")
        print(f"  状态: {account.get_status_display()}")
        print(f"  明细数: {details_count}")
        print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  查看主单详情: python check_supplier_accounts.py <主单ID>")
        print("  列出所有主单: python check_supplier_accounts.py --list")
        print("  按供应商筛选: python check_supplier_accounts.py --list <供应商ID>")
        print("\n示例:")
        print("  python check_supplier_accounts.py 3")
        print("  python check_supplier_accounts.py --list")
        sys.exit(1)

    if sys.argv[1] == "--list":
        supplier_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        list_supplier_accounts(supplier_id)
    else:
        try:
            account_id = int(sys.argv[1])
            check_supplier_account(account_id)
        except ValueError:
            print("错误: 主单ID必须是数字")
            sys.exit(1)
