#!/usr/bin/env python
"""
诊断订单 PO260204003 的收货和应付账款状态
"""

import os
import sys

import django

# 设置 Django 环境
sys.path.insert(0, "/Users/janjung/Code_Projects/django_erp")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")
django.setup()

from apps.finance.models import SupplierAccount, SupplierAccountDetail
from apps.purchase.models import PurchaseOrder, PurchaseReceipt, PurchaseReceiptItem

print("=" * 60)
print("订单 PO260204003 诊断报告")
print("=" * 60)

# 1. 检查收货单
print("\n[1/4] 检查收货单状态")
receipt = PurchaseReceipt.objects.filter(receipt_number="IN260204003", is_deleted=False).first()

if receipt:
    print(f"✅ 收货单存在: {receipt.receipt_number}")
    print(f"   收货单状态: {receipt.status}")
    print(f"   采购订单: {receipt.purchase_order.order_number}")
    print(f"   订单状态: {receipt.purchase_order.status}")
    print(f"   收货人: {receipt.received_by}")
    print(f"   收货时间: {receipt.received_at}")

    # 检查收货单明细
    print(f"\n   收货明细:")
    for item in receipt.items.all():
        print(f"   - {item.order_item.product.name}")
        print(f"     订单数量: {item.order_item.quantity}")
        print(f"     收货数量: {item.received_quantity}")
        print(f"     单价: ¥{item.order_item.unit_price}")
        print(f"     收货金额: ¥{item.received_quantity * item.order_item.unit_price}")
else:
    print("❌ 收货单不存在")
    sys.exit(1)

# 2. 检查应付账款主单
print("\n[2/4] 检查应付账款主单")
order = receipt.purchase_order
account = SupplierAccount.objects.filter(purchase_order=order, is_deleted=False).first()

if account:
    print(f"✅ 应付主单存在")
    print(f"   单号: {account.invoice_number}")
    print(f'   供应商: {account.supplier.name if account.supplier else "无"}')
    print(f"   订单金额: ¥{account.invoice_amount}")
    print(f"   已付金额: ¥{account.paid_amount}")
    print(f"   应付余额: ¥{account.balance}")
    print(f"   状态: {account.get_status_display()}")
    print(f"   创建时间: {account.created_at}")
else:
    print("❌ 应付主单不存在 - 这就是问题！")
    print("\n可能原因:")
    print("1. 收货确认流程没有执行到生成应付账款的代码")
    print("2. 生成应付账款时发生异常但被捕获")
    print("3. get_or_create_for_order 方法失败")

# 3. 检查应付账款明细
print("\n[3/4] 检查应付账款明细")
details = SupplierAccountDetail.objects.filter(purchase_order=order, is_deleted=False).order_by(
    "-created_at"
)

print(f"   应付明细数量: {details.count()}")
if details.count() > 0:
    print("\n   明细列表:")
    for detail in details[:10]:  # 只显示前10条
        print(f"   - {detail.detail_number}")
        print(f"     类型: {detail.get_detail_type_display()}")
        print(f"     金额: ¥{detail.amount}")
        print(f"     业务日期: {detail.business_date}")
        print(f'     收货单: {detail.receipt.receipt_number if detail.receipt else "无"}')
        print(f"     创建时间: {detail.created_at}")
        if detail.allocated_amount > 0:
            print(f"     已核销: ¥{detail.allocated_amount}")
else:
    print("❌ 没有应付明细 - 这就是问题！")

# 4. 总结
print("\n" + "=" * 60)
print("诊断总结")
print("=" * 60)

if account and details.count() > 0:
    print("✅ 应付账款已生成")
    print(f"   主单: {account.invoice_number}")
    print(f"   明细: {details.count()} 条")
    print("\n建议: 检查应付账款列表页的搜索和过滤条件")
elif account and details.count() == 0:
    print("⚠️  应付主单存在但没有明细")
    print("\n建议: 运行 aggregate_from_details() 重新归集")
elif not account:
    print("❌  应付主单和明细都不存在")
    print("\n建议: 重新执行收货确认流程，或手动生成应付账款")

print("\n建议操作:")
print("1. 查看收货单详情页，确认收货状态")
print("2. 检查是否有错误日志")
print("3. 如果确认数据不完整，可以手动补充生成应付账款")

print("\n" + "=" * 60)
