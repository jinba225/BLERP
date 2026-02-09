#!/usr/bin/env python
"""
修复采购退货单的应付账款记录

为已审核但未生成应付账款的退货单补充生成负应付明细

用法:
    python fix_return_ar.py <退货单ID>
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_erp.settings')
django.setup()

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from purchase.models import PurchaseReturn, PurchaseOrderItem
from finance.models import SupplierAccount, SupplierAccountDetail
from common.utils import DocumentNumberGenerator


def fix_return_accounts_receivable(return_id):
    """为退货单补充生成应付账款记录"""

    print(f"\n{'='*60}")
    print(f"修复退货单应付账款 - ID: {return_id}")
    print(f"{'='*60}\n")

    # 1. 获取退货单
    try:
        return_order = PurchaseReturn.objects.get(pk=return_id, is_deleted=False)
    except PurchaseReturn.DoesNotExist:
        print("❌ 退货单不存在或已删除")
        return False

    # 2. 检查是否已审核
    if return_order.status != 'approved':
        print(f"⚠️  退货单状态为 '{return_order.get_status_display()}'，不是 '已审核' 状态")
        print("   只有已审核的退货单才能生成应付账款")
        return False

    # 3. 检查是否已存在应付明细
    existing_details = SupplierAccountDetail.objects.filter(
        return_order=return_order,
        is_deleted=False
    )

    if existing_details.exists():
        print(f"⚠️  该退货单已存在 {existing_details.count()} 条应付明细记录:")
        for detail in existing_details:
            print(f"    - {detail.detail_number}: ¥{detail.amount:.2f}")
        print("   不需要重复生成")
        return False

    # 4. 检查退货明细
    items = return_order.items.all()
    if not items.exists():
        print("❌ 退货单没有任何明细")
        return False

    print(f"📋 退货单信息:")
    print(f"  退货单号: {return_order.return_number}")
    print(f"  采购订单: {return_order.purchase_order.order_number}")
    print(f"  供应商: {return_order.purchase_order.supplier.name}")
    print(f"  退货日期: {return_order.return_date}")
    print(f"  退货状态: {return_order.get_status_display()}")
    print(f"  退货总金额: ¥{return_order.refund_amount:.2f}")
    print()

    # 5. 分析退货明细并生成应付账款
    try:
        with transaction.atomic():
            total_refund = Decimal('0')
            details_created = []

            for item in items:
                order_item = item.order_item
                return_quantity = item.quantity

                # 计算未收货数量
                unreceived_quantity = order_item.quantity - order_item.received_quantity

                # 只有退货量 > 未收货量时才生成应付（即扣减了已收货）
                if return_quantity > unreceived_quantity:
                    # 计算从已收货中扣除的数量
                    unreceived_return = min(return_quantity, unreceived_quantity)
                    received_return = return_quantity - unreceived_return

                    if received_return > 0:
                        print(f"📦 处理明细: {order_item.product.name}")
                        print(f"   订单数量: {order_item.quantity}")
                        print(f"   已收货数量: {order_item.received_quantity}")
                        print(f"   未收货数量: {unreceived_quantity}")
                        print(f"   退货数量: {return_quantity}")
                        print(f"   扣减已收货: {received_return}")
                        print(f"   应负金额: ¥{received_return * item.unit_price:.2f}")

                        # 获取或创建应付主单
                        parent_account = SupplierAccount.get_or_create_for_order(
                            return_order.purchase_order
                        )

                        # 计算负应付金额（负数）
                        negative_amount = -(received_return * item.unit_price)

                        # 生成明细单号
                        detail_number = DocumentNumberGenerator.generate('account_detail')

                        # 创建负应付明细
                        detail = SupplierAccountDetail.objects.create(
                            detail_number=detail_number,
                            detail_type='return',  # 退货负应付
                            supplier=return_order.purchase_order.supplier,
                            purchase_order=return_order.purchase_order,
                            return_order=return_order,
                            amount=negative_amount,  # 负数
                            allocated_amount=Decimal('0'),
                            parent_account=parent_account,
                            business_date=return_order.return_date,
                            notes=f'退货单 {return_order.return_number} 退货 {received_return} 件',
                            created_by=return_order.approved_by
                        )

                        details_created.append(detail)
                        total_refund += received_return * item.unit_price
                        print(f"   ✅ 已创建应付明细: {detail_number}")
                        print()

            # 6. 归集应付主单
            if total_refund > 0:
                parent_account = SupplierAccount.get_or_create_for_order(
                    return_order.purchase_order
                )
                parent_account.aggregate_from_details()

                print(f"💰 生成结果:")
                print(f"   创建明细数: {len(details_created)}")
                print(f"   总负应付金额: ¥{total_refund:.2f}")
                print(f"   应付主单已归集")
                print()

                print(f"✅ 修复完成！")
                return True
            else:
                print(f"⚠️  当前退货场景不需要生成应付账款")
                print(f"   原因: 退货数量 ≤ 未收货数量，只减少订单数量")
                return False

    except Exception as e:
        print(f"❌ 修复失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def list_pending_returns():
    """列出所有已审核但可能缺少应付账款的退货单"""
    print(f"\n{'='*60}")
    print(f"已审核退货单检查")
    print(f"{'='*60}\n")

    # 获取所有已审核的退货单
    approved_returns = PurchaseReturn.objects.filter(
        status='approved',
        is_deleted=False
    ).order_by('-approved_at')

    print(f"找到 {approved_returns.count()} 个已审核的退货单\n")

    for return_order in approved_returns:
        # 检查是否有应付明细
        ar_count = SupplierAccountDetail.objects.filter(
            return_order=return_order,
            is_deleted=False
        ).count()

        # 检查是否有需要生成应付的场景
        needs_ar = False
        for item in return_order.items.all():
            order_item = item.order_item
            unreceived_qty = order_item.quantity - order_item.received_quantity
            if item.quantity > unreceived_qty:
                needs_ar = True
                break

        status_icon = "✅" if (not needs_ar or ar_count > 0) else "❌"
        status_text = "正常" if (not needs_ar or ar_count > 0) else "缺少应付"

        print(f"{status_icon} {return_order.return_number} - {return_order.purchase_order.supplier.name}")
        print(f"   审核时间: {return_order.approved_at}")
        print(f"   退货金额: ¥{return_order.refund_amount:.2f}")
        print(f"   应付记录: {ar_count} 条")
        print(f"   状态: {status_text}")
        print()

    print(f"{'='*60}\n")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  修复单个退货单: python fix_return_ar.py <退货单ID>")
        print("  列出所有退货单: python fix_return_ar.py --list")
        print("\n示例:")
        print("  python fix_return_ar.py 1")
        print("  python fix_return_ar.py --list")
        sys.exit(1)

    if sys.argv[1] == '--list':
        list_pending_returns()
    else:
        try:
            return_id = int(sys.argv[1])
            fix_return_accounts_receivable(return_id)
        except ValueError:
            print("错误: 退货单ID必须是数字")
            sys.exit(1)
