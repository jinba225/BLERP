#!/usr/bin/env python
"""
修复被错误扣减的received_quantity字段

问题：退货审核时错误地扣减了received_quantity
解决：恢复正确的收货数量，退货记录单独计算
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")
django.setup()

from django.db import transaction
from django.db.models import Sum
from purchase.models import PurchaseOrder, PurchaseOrderItem, PurchaseReturn, PurchaseReturnItem


@transaction.atomic
def fix_received_quantity():
    """修复被错误扣减的received_quantity字段"""

    print("=== 修复received_quantity字段 ===\n")

    # 查找所有有退货记录的订单
    orders = PurchaseOrder.objects.filter(is_deleted=False)

    fixed_count = 0
    for order in orders:
        order_modified = False

        for item in order.items.all():
            # 计算该明细的已退货数量（只计算已审核的）
            returned = (
                PurchaseReturnItem.objects.filter(
                    order_item=item,
                    purchase_return__purchase_order=order,
                    purchase_return__is_deleted=False,
                    purchase_return__status__in=["approved", "returned", "completed"],
                ).aggregate(total=Sum("quantity"))["total"]
                or 0
            )

            if returned > 0:
                # 当前记录的收货数量
                current_received = item.received_quantity

                # 预期的收货数量 = 当前收货 + 已退货（因为被错误扣减了）
                expected_received = current_received + returned

                print(f"订单 {order.order_number} | 产品 {item.product.name}")
                print(f"  当前收货数量: {current_received}")
                print(f"  已退货数量: {returned}")
                print(f"  期望收货数量: {expected_received}")
                print(f"  修复中...")

                # 恢复正确的收货数量
                item.received_quantity = expected_received
                item.save()

                print(f"  ✅ 已修复: {current_received} → {expected_received}\n")
                fixed_count += 1
                order_modified = True

        if order_modified:
            # 重新计算订单总金额
            order.calculate_totals()

    print(f"\n=== 修复完成 ===")
    print(f"共修复 {fixed_count} 条订单明细")


if __name__ == "__main__":
    fix_received_quantity()
