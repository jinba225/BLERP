#!/usr/bin/env python
"""
清理供应商丁的错误付款记录

问题：
- 应付主单ID=3 (SA260208002) 有7笔付款，总计¥30,000
- 实际应付只有¥6,000（收货¥12,000 + 退货-¥6,000）
- 多付款¥24,000

解决方案：
1. 删除2月4日的2笔付款（关联到已删除的主单SA260204003）
2. 删除2月8日的部分付款（保留¥6,000）
3. 重新核销应付账款明细
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")
django.setup()

from finance.models import Payment, SupplierAccount, SupplierAccountDetail
from django.db import transaction


@transaction.atomic
def cleanup_payments():
    print("=" * 60)
    print("供应商丁付款记录清理")
    print("=" * 60)

    # 1. 删除2月4日的付款（关联到已删除主单）
    print("\n步骤1: 删除2月4日的错误付款...")
    feb4_payments = Payment.objects.filter(
        payment_date="2026-02-04", reference_id="3", reference_type="supplier_account"
    )

    print(f"找到 {feb4_payments.count()} 笔2月4日的付款：")
    for p in feb4_payments:
        print(f"  - {p.payment_number}: ¥{p.amount}")
        p.is_deleted = True
        p.save()

    print(f"✅ 已软删除 {feb4_payments.count()} 笔付款")

    # 2. 删除2月8日的部分付款（保留¥6,000）
    print("\n步骤2: 删除2月8日的部分付款（保留¥6,000）...")

    # 保留PY260208004 (5000) + PY260208006 (500) + PY260208007 (500) = 6000
    # 删除PY260208005 (5000) + PY260208008 (1000) = 6000

    payments_to_delete = [
        "PY260208005",  # ¥5000
        "PY260208008",  # ¥1000
    ]

    for payment_number in payments_to_delete:
        try:
            p = Payment.objects.get(payment_number=payment_number)
            print(f"  - 删除 {p.payment_number}: ¥{p.amount}")
            p.is_deleted = True
            p.save()
        except Payment.DoesNotExist:
            print(f"  - {payment_number} 不存在")

    print("✅ 已删除部分2月8日的付款")

    # 3. 重置核销状态
    print("\n步骤3: 重置应付账款明细核销状态...")
    account = SupplierAccount.objects.get(id=3)

    for detail in account.details.all():
        detail.allocated_amount = 0
        detail.status = "pending"
        detail.save()
        print(f"  - 重置明细 {detail.id}: {detail.get_detail_type_display()}")

    print("✅ 已重置所有明细")

    # 4. 重新核销（只核销¥6,000）
    print("\n步骤4: 重新核销应付账款明细...")

    # 收货明细核销6000
    receipt_detail = account.details.filter(detail_type="receipt").first()
    if receipt_detail:
        receipt_detail.allocate(6000)
        print(f"  - 收货明细核销: ¥6,000")

    # 退货明细不核销（已自动减少应付）

    # 5. 重新归集主单
    print("\n步骤5: 重新归集应付主单...")
    account.aggregate_from_details()
    account.refresh_from_db()

    print(f"  - 发票金额: ¥{account.invoice_amount}")
    print(f"  - 已付金额: ¥{account.paid_amount}")
    print(f"  - 余额: ¥{account.balance}")
    print(f"  - 状态: {account.get_status_display()}")

    # 6. 验证
    print("\n步骤6: 验证结果...")
    remaining_payments = Payment.objects.filter(
        reference_id="3", reference_type="supplier_account", is_deleted=False
    )

    total = sum([p.amount for p in remaining_payments])
    print(f"剩余付款记录: {remaining_payments.count()} 笔")
    print(f"付款总额: ¥{total}")
    print(f"主单余额: ¥{account.balance}")

    if account.balance == 0 and total == 6000:
        print("\n✅ 清理成功！余额正确归零。")
    else:
        print(f"\n⚠️ 警告：余额应该为0，当前为¥{account.balance}")

    print("\n=" * 60)
    print("清理完成")
    print("=" * 60)


if __name__ == "__main__":
    cleanup_payments()
