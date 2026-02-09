#!/usr/bin/env python3
"""
手动修复已归还借用单的库存出库记录

针对已经归还但缺少出库记录的借用单进行修复
"""

import os
import sys

import django

sys.path.insert(0, "/Users/janjung/Code_Projects/django_erp")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")
django.setup()

from decimal import Decimal

from django.contrib.auth import get_user_model
from inventory.models import InventoryStock, InventoryTransaction, Warehouse
from purchase.models import Borrow, BorrowItem

User = get_user_model()


def fix_returned_borrow_stock(borrow_number):
    """
    修复已归还但库存未更新的借用单

    逻辑：
    1. 检查借用单状态是否为 completed
    2. 检查是否有出库记录
    3. 如果没有出库记录，补创建出库记录
    """
    print("=" * 70)
    print(f"🔧 修复借用单库存: {borrow_number}")
    print("=" * 70)

    try:
        # 获取借用单
        borrow = Borrow.objects.get(borrow_number=borrow_number, is_deleted=False)
        print(f"\n✅ 找到借用单: {borrow.borrow_number}")
        print(f"   状态: {borrow.status}")

        if borrow.status != "completed":
            print(f"   ⚠️  借用单状态不是 completed，当前状态: {borrow.status}")
            print(f"   只有已完成状态的借用单才需要修复库存")
            return False

        # 获取借用仓
        try:
            borrow_warehouse = Warehouse.objects.filter(code__icontains="BORROW").first()
            if not borrow_warehouse:
                borrow_warehouse = Warehouse.objects.filter(name__icontains="借用").first()
        except:
            borrow_warehouse = None

        if not borrow_warehouse:
            print("   ❌ 未找到借用仓")
            return False

        print(f"   借用仓: {borrow_warehouse.name}")

        # 获取操作用户
        user = User.objects.first()
        if not user:
            print("   ❌ 未找到用户")
            return False

        # 检查明细
        print(f"\n📦 检查明细:")
        items = borrow.items.filter(is_deleted=False)
        total_returned = 0

        for item in items:
            if item.returned_quantity > 0:
                print(f"\n   产品: {item.product.name}")
                print(f"     已归还数量: {item.returned_quantity}")

                # 检查是否已有出库记录
                existing_out = InventoryTransaction.objects.filter(
                    reference_number=borrow.borrow_number,
                    transaction_type="out",
                    product=item.product,
                    warehouse=borrow_warehouse,
                ).count()

                if existing_out > 0:
                    print(f"     ✅ 已有 {existing_out} 条出库记录，跳过")
                    continue

                # 创建出库记录
                print(f"     🔄 创建出库记录...")
                InventoryTransaction.objects.create(
                    transaction_type="out",
                    product=item.product,
                    warehouse=borrow_warehouse,
                    quantity=-item.returned_quantity,  # 负数表示出库
                    reference_number=borrow.borrow_number,
                    notes=f"采购借用单 {borrow.borrow_number} 归还出库（补录）",
                    operator=user,
                )
                print(f"     ✅ 已创建出库记录: -{item.returned_quantity}")
                total_returned += item.returned_quantity

        if total_returned == 0:
            print(f"\n⚠️  没有需要修复的明细")
            return False

        # 验证库存
        print(f"\n📊 验证库存更新:")
        for item in items:
            if item.returned_quantity > 0:
                stock = InventoryStock.objects.filter(
                    product=item.product, warehouse=borrow_warehouse, is_deleted=False
                ).first()

                if stock:
                    print(f"   {item.product.name}: {stock.quantity} 件")
                else:
                    print(f"   {item.product.name}: 无库存记录")

        print(f"\n✅ 修复完成！共补创建出库记录，总计: -{total_returned} 件")
        print(f"\n💡 提示:")
        print(f"   - 刷新库存查询页面查看更新")
        print(f"   - 借用仓库存应该已减少")

        return True

    except Borrow.DoesNotExist:
        print(f"\n❌ 未找到借用单: {borrow_number}")
        return False
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        borrow_number = sys.argv[1]
    else:
        # 默认修复 BO260203001
        borrow_number = "BO260203001"

    print("\n" + "🔧" * 35)
    print("  借用单库存修复工具")
    print("🔧" * 35 + "\n")

    success = fix_returned_borrow_stock(borrow_number)

    print("\n" + "=" * 70)
    if success:
        print("✅ 修复成功！")
    else:
        print("❌ 修复失败或无需修复")
    print("=" * 70 + "\n")
