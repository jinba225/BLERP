#!/usr/bin/env python
"""
诊断采购退货单的应付账款生成情况

用法:
    python diagnose_return.py <退货单ID>
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_erp.settings')
django.setup()

from decimal import Decimal
from purchase.models import PurchaseReturn, PurchaseOrder, PurchaseOrderItem
from finance.models import SupplierAccount, SupplierAccountDetail


def diagnose_return(return_id):
    """诊断退货单"""
    print(f"\n{'='*60}")
    print(f"退货单诊断报告 - ID: {return_id}")
    print(f"{'='*60}\n")

    # 1. 获取退货单
    try:
        return_order = PurchaseReturn.objects.get(pk=return_id, is_deleted=False)
    except PurchaseReturn.DoesNotExist:
        print("❌ 退货单不存在或已删除")
        return

    # 2. 基本信息
    print("📋 基本信息:")
    print(f"  退货单号: {return_order.return_number}")
    print(f"  采购订单: {return_order.purchase_order.order_number}")
    print(f"  供应商: {return_order.purchase_order.supplier.name}")
    print(f"  退货状态: {return_order.get_status_display()}")
    print(f"  退货日期: {return_order.return_date}")
    print(f"  退货总金额: ¥{return_order.refund_amount:.2f}")
    print()

    # 3. 退货明细分析
    print("📦 退货明细分析:")
    total_refund_should = Decimal('0')
    total_refund_actual = Decimal('0')

    for idx, item in enumerate(return_order.items.all(), 1):
        order_item = item.order_item
        return_qty = item.quantity
        order_qty = order_item.quantity
        received_qty = order_item.received_quantity
        unreceived_qty = order_qty - received_qty

        print(f"\n  明细 {idx}:")
        print(f"    产品: {order_item.product.name}")
        print(f"    订单数量: {order_qty}")
        print(f"    已收货数量: {received_qty}")
        print(f"    未收货数量: {unreceived_qty}")
        print(f"    退货数量: {return_qty}")
        print(f"    单价: ¥{item.unit_price:.2f}")

        # 判断场景
        if return_qty <= unreceived_qty:
            print(f"    ⚠️  场景: 退货量 ≤ 未收货量")
            print(f"    🔧 处理: 只减订单数量，不生成应付账款")
            should_generate_ar = False
        else:
            unreceived_return = min(return_qty, unreceived_qty)
            received_return = return_qty - unreceived_return
            print(f"    ✅ 场景: 退货量 > 未收货量")
            print(f"    🔧 处理:")
            print(f"       - 扣减未收货: {unreceived_return} 件")
            print(f"       - 扣减已收货: {received_return} 件")
            print(f"       - 生成应付: ¥{received_return * item.unit_price:.2f}")
            total_refund_should += received_return * item.unit_price
            should_generate_ar = True

    print(f"\n  💰 应生成应付金额: ¥{total_refund_should:.2f}")
    print()

    # 4. 检查应付账款记录
    print("💳 应付账款记录检查:")

    # 查找相关的应付账款明细
    ar_details = SupplierAccountDetail.objects.filter(
        return_order=return_order,
        is_deleted=False
    )

    if ar_details.exists():
        print(f"  ✅ 找到 {ar_details.count()} 条应付明细记录:")
        for detail in ar_details:
            print(f"    - 单号: {detail.detail_number}")
            print(f"      类型: {detail.get_detail_type_display()}")
            print(f"      金额: ¥{detail.amount:.2f}")
            print(f"      已分配: ¥{detail.allocated_amount:.2f}")
            print(f"      业务日期: {detail.business_date}")
            print(f"      备注: {detail.notes}")
            total_refund_actual += detail.amount
        print(f"  💰 实际应付金额: ¥{total_refund_actual:.2f}")
    else:
        print(f"  ❌ 未找到任何应付明细记录")

    print()

    # 5. 检查应付主单
    print("📊 应付主单检查:")
    try:
        parent_account = SupplierAccount.get_or_create_for_order(return_order.purchase_order)
        print(f"  应付主单ID: {parent_account.id}")
        print(f"  供应商: {parent_account.supplier.name}")
        print(f"  采购订单: {parent_account.purchase_order.order_number if parent_account.purchase_order else 'N/A'}")
        print(f"  当前余额: ¥{parent_account.balance:.2f}")
        print(f"  原始余额: ¥{parent_account.original_balance:.2f}")
        print(f"  已分配金额: ¥{parent_account.allocated_amount:.2f}")
        print(f"  状态: {parent_account.get_status_display()}")

        # 检查主单下的所有明细
        all_details = parent_account.details.filter(is_deleted=False)
        print(f"\n  主单下所有明细 (共 {all_details.count()} 条):")
        for detail in all_details:
            print(f"    - {detail.detail_number}: {detail.get_detail_type_display()} ¥{detail.amount:.2f}")
    except Exception as e:
        print(f"  ❌ 获取应付主单失败: {e}")

    print()

    # 6. 诊断结论
    print("🔍 诊断结论:")
    if total_refund_should > 0 and total_refund_actual == 0:
        print(f"  ❌ 问题确认: 应该生成 ¥{total_refund_should:.2f} 应付账款，但实际未生成")
        print(f"  📝 建议: 检查退货审核流程是否正确执行")
    elif total_refund_should == 0:
        print(f"  ⚠️  当前退货场景不需要生成应付账款")
        print(f"  📝 说明: 退货数量 ≤ 未收货数量，只减少订单数量")
    elif abs(total_refund_should - total_refund_actual) < Decimal('0.01'):
        print(f"  ✅ 应付账款生成正常")
    else:
        print(f"  ⚠️  应付金额不匹配")
        print(f"     应该: ¥{total_refund_should:.2f}")
        print(f"     实际: ¥{total_refund_actual:.2f}")

    print(f"\n{'='*60}\n")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法: python diagnose_return.py <退货单ID>")
        print("示例: python diagnose_return.py 1")
        sys.exit(1)

    try:
        return_id = int(sys.argv[1])
    except ValueError:
        print("错误: 退货单ID必须是数字")
        sys.exit(1)

    diagnose_return(return_id)
