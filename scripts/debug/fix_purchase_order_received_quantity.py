#!/usr/bin/env python
"""
修复采购订单已收货数量问题

运行此脚本可以重新计算所有采购订单的已收货数量

使用方法:
    python fix_purchase_order_received_quantity.py              # 修复所有订单
    python fix_purchase_order_received_quantity.py --order PO250201001  # 修复指定订单
"""
import os
import sys

# 设置项目路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_erp.settings')

import django
django.setup()

from purchase.models import PurchaseOrder, PurchaseReceiptItem
from django.db.models import Sum
from decimal import Decimal


def fix_order_received_quantities(order_number=None):
    """
    修复采购订单的已收货数量

    Args:
        order_number: 指定订单号，如果为None则修复所有订单
    """
    if order_number:
        orders = PurchaseOrder.objects.filter(
            order_number=order_number,
            is_deleted=False
        )
    else:
        orders = PurchaseOrder.objects.filter(
            is_deleted=False
        ).exclude(status__in=['draft', 'cancelled'])

    fixed_count = 0
    total_count = orders.count()

    print(f"开始检查 {total_count} 个采购订单...")
    print("=" * 80)

    for order in orders:
        print(f"\n检查订单: {order.order_number}")
        print("-" * 80)

        updated_items = []

        for item in order.items.filter(is_deleted=False):
            # 计算该订单明细的实际已收货数量
            # 从所有已收货状态的收货单明细中汇总
            actual_received = PurchaseReceiptItem.objects.filter(
                order_item=item,
                is_deleted=False,
                receipt__status='received'  # 只计算已确认收货的
            ).aggregate(
                total=Sum('received_quantity')
            )['total'] or Decimal('0')

            old_quantity = item.received_quantity

            # 如果数量不一致，更新
            if old_quantity != int(actual_received):
                item.received_quantity = int(actual_received)
                item.save(update_fields=['received_quantity', 'updated_at'])
                updated_items.append({
                    'item_id': item.id,
                    'product': item.product.name,
                    'old': old_quantity,
                    'new': int(actual_received)
                })
                print(f"  ✓ 产品: {item.product.name}")
                print(f"    旧值: {old_quantity}, 新值: {int(actual_received)}")

        if updated_items:
            fixed_count += 1
            print(f"\n✅ 已修复订单 {order.order_number}，共 {len(updated_items)} 个明细")
        else:
            print(f"\n✓ 订单 {order.order_number} 数据正确，无需修复")

    print("\n" + "=" * 80)
    print(f"修复完成！")
    print(f"检查订单数: {total_count}")
    print(f"修复订单数: {fixed_count}")
    print("=" * 80)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='修复采购订单已收货数量')
    parser.add_argument(
        '--order',
        type=str,
        help='指定订单号（可选）',
        default=None
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='跳过确认直接执行'
    )

    args = parser.parse_args()

    print("采购订单已收货数量修复工具")
    print("=" * 80)

    if args.order:
        print(f"目标订单: {args.order}")
    else:
        print("目标: 所有非草稿和非取消状态的订单")

    print("=" * 80 + "\n")

    # 确认操作（除非指定了 --yes）
    if not args.yes:
        if args.order:
            confirm = input(f"确认要修复订单 {args.order} 吗？(yes/no): ")
        else:
            confirm = input("确认要修复所有订单吗？(yes/no): ")

        if confirm.lower() not in ['yes', 'y']:
            print("操作已取消")
            sys.exit(0)

    fix_order_received_quantities(args.order)
