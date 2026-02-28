#!/usr/bin/env python
"""诊断订单 PO260204004 的应付账款生成情况"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")
django.setup()

from apps.finance.models import SupplierAccount, SupplierAccountDetail
from apps.purchase.models import PurchaseOrder, PurchaseReceipt

print("=" * 60)
print("采购订单 PO260204004 诊断报告")
print("=" * 60)

# 1. 检查订单是否存在
try:
    order = PurchaseOrder.objects.get(order_number="PO260204004")
    print(f"\n✅ 订单存在: {order.order_number}")
    print(f'   供应商: {order.supplier.name if order.supplier else "无"}')
    print(f"   订单状态: {order.get_status_display()}")
    print(f"   订单金额: ¥{order.total_amount}")
    print(f"   收货状态: {order.receipt_status}")
except PurchaseOrder.DoesNotExist:
    print("\n❌ 订单不存在")
    exit()

# 2. 检查收货单
print(f"\n--- 收货单检查 ---")
receipts = PurchaseReceipt.objects.filter(purchase_order=order, is_deleted=False)
if receipts.exists():
    for receipt in receipts:
        print(f"收货单号: {receipt.receipt_number}")
        print(f"收货状态: {receipt.get_status_display()}")
        print(f"收货人: {receipt.received_by}")
        print(f"收货时间: {receipt.received_at}")
        print(f"收货明细数: {receipt.items.count()}")

        # 检查收货明细
        total_received = 0
        for item in receipt.items.all():
            received_amount = item.received_quantity * item.order_item.unit_price
            total_received += received_amount
            print(
                f"  - {item.order_item.product.name}: {item.received_quantity}件 × ¥{item.order_item.unit_price} = ¥{received_amount}"
            )
        print(f"收货总金额: ¥{total_received}")
else:
    print("❌ 没有找到收货单")

# 3. 检查应付账款主单
print(f"\n--- 应付账款主单检查 ---")
account = SupplierAccount.objects.filter(purchase_order=order, is_deleted=False).first()

if account:
    print(f"✅ 应付主单存在: {account.invoice_number}")
    print(f'   供应商: {account.supplier.name if account.supplier else "无"}')
    print(f"   发票金额: ¥{account.invoice_amount}")
    print(f"   已付金额: ¥{account.paid_amount}")
    print(f"   应付余额: ¥{account.balance}")
    print(f"   状态: {account.get_status_display()}")
    print(f"   创建时间: {account.created_at}")
else:
    print("❌ 应付主单不存在")

# 4. 检查应付账款明细
print(f"\n--- 应付账款明细检查 ---")
details = SupplierAccountDetail.objects.filter(purchase_order=order, is_deleted=False).order_by(
    "-created_at"
)

if details.exists():
    print(f"✅ 应付明细数量: {details.count()}")
    for detail in details:
        print(f"\n明细单号: {detail.detail_number}")
        print(f"明细类型: {detail.get_detail_type_display()}")
        print(f"金额: ¥{detail.amount}")
        print(f"业务日期: {detail.business_date}")
        print(f'收货单: {detail.receipt.receipt_number if detail.receipt else "无"}')
        print(f"创建时间: {detail.created_at}")
else:
    print("❌ 应付明细不存在")

print("\n" + "=" * 60)
print("诊断结论:")
print("=" * 60)

if not receipts.exists():
    print("❌ 问题根源：订单没有收货单")
elif not account:
    print("❌ 问题根源：收货单存在但未生成应付主单")
elif not details.exists():
    print("❌ 问题根源：应付主单存在但未生成应付明细")
else:
    print("✅ 数据完整：应付账款已正确生成")
    print(f"\n💡 应付主单号: {account.invoice_number}")
    print(f"💡 您可以在列表页搜索该单号或订单号 PO260204004")
