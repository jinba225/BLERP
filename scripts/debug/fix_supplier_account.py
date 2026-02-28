#!/usr/bin/env python
"""
修复供应商应付账款的跨账户核销问题

场景：供应商3预付了100000，但只核销了账户5（24000），剩余76000未核销
目标：将剩余76000自动核销到账户6、7、8
"""

import os
import sys

import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")
django.setup()

from decimal import Decimal

# 直接使用ORM查询
from django.db import connection
from django.utils import timezone


def fix_cross_account_writeoff():
    """修复跨账户核销问题"""

    print("=" * 80)
    print("供应商应付账款跨账户核销修复工具")
    print("=" * 80)

    with transaction.atomic():
        # 1. 查找供应商3的预付款
        prepay = (
            SupplierPrepayment.objects.filter(supplier_id=3, is_deleted=False)
            .order_by("-balance")
            .first()
        )

        if not prepay:
            print("✗ 未找到供应商3的预付款")
            return

        print(f"\n预付款信息:")
        print(f"  ID: {prepay.id}")
        print(f"  供应商: {prepay.supplier.name}")
        print(f"  预付金额: ¥{prepay.amount}")
        print(f"  剩余余额: ¥{prepay.balance}")
        print(f"  状态: {prepay.get_status_display()}")

        if prepay.balance <= 0:
            print("\n✗ 预付款余额为0，无需修复")
            return

        # 2. 查找供应商3的所有未付账户
        unpaid_accounts = (
            SupplierAccount.objects.filter(supplier_id=3, is_deleted=False)
            .exclude(balance=0)
            .order_by("created_at")
        )

        print(f"\n未付账户:")
        for acc in unpaid_accounts:
            print(f"  {acc.invoice_number}: 余额 ¥{acc.balance}")

        total_unpaid = sum(acc.balance for acc in unpaid_accounts)
        print(f"\n总未付: ¥{total_unpaid}")
        print(f"预付款余额: ¥{prepay.balance}")

        # 3. 计算可核销金额
        available = min(prepay.balance, total_unpaid)
        print(f"\n可核销金额: ¥{available}")

        if available <= 0:
            print("\n✗ 无可核销金额")
            return

        # 4. 逐个核销
        print(f"\n开始核销...")
        remaining = available
        allocated = []

        for account in unpaid_accounts:
            if remaining <= 0:
                break

            can_allocate = min(remaining, account.balance)

            if can_allocate > 0:
                print(f"\n核销账户 {account.invoice_number}:")
                print(f"  核销前: 已付 ¥{account.paid_amount}, 余额 ¥{account.balance}")

                # 更新账户
                account.paid_amount += can_allocate
                account.balance -= can_allocate

                # 检查是否结清
                if account.balance <= Decimal("0.00"):
                    account.balance = Decimal("0.00")
                    account.paid_amount = account.invoice_amount
                    account.status = "paid"

                # 添加备注
                account.notes = account.notes or ""
                account.notes += (
                    f"\n[{timezone.now().strftime('%Y-%m-%d')}] 自动修复跨账户核销 ¥{can_allocate}"
                )

                account.save()

                print(f"  核销后: 已付 ¥{account.paid_amount}, 余额 ¥{account.balance}")

                allocated.append({"number": account.invoice_number, "amount": can_allocate})

                remaining -= can_allocate

        # 5. 更新预付款
        prepay.balance -= available
        if prepay.balance <= 0:
            prepay.balance = Decimal("0.00")
            prepay.status = "exhausted"

        prepay.save()

        print(f"\n预付款更新后: 剩余 ¥{prepay.balance}, 状态 {prepay.get_status_display()}")

        # 6. 显示总结
        print(f"\n" + "=" * 80)
        print("核销完成总结:")
        print("=" * 80)
        for item in allocated:
            print(f"  {item['number']}: ¥{item['amount']}")

        print(f"\n总核销: ¥{available}")
        print(f"预付款剩余: ¥{prepay.balance}")

        print(f"\n✓ 修复完成！")


if __name__ == "__main__":
    try:
        fix_cross_account_writeoff()
    except Exception as e:
        print(f"\n✗ 修复失败: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
