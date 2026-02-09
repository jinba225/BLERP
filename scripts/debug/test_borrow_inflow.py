#!/usr/bin/env python3
"""
验证借用单一键入库功能的完整流程

测试场景：
1. 创建借用单
2. 一键入库
3. 验证详情页按钮状态
4. 验证累计已借用数量更新
"""

import os
import sys

import django

sys.path.insert(0, "/Users/janjung/Code_Projects/django_erp")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")
django.setup()

from django.contrib.auth import get_user_model
from purchase.models import Borrow, BorrowItem

User = get_user_model()


def test_borrow_inflow(borrow_number):
    """测试借用单一键入库流程"""
    print("=" * 70)
    print(f"🔍 测试借用单: {borrow_number}")
    print("=" * 70)

    try:
        # 1. 获取借用单
        borrow = Borrow.objects.get(borrow_number=borrow_number, is_deleted=False)
        print(f"\n✅ 找到借用单")
        print(f"   状态: {borrow.status}")

        # 2. 检查明细
        items = borrow.items.filter(is_deleted=False)
        print(f"\n📦 借用明细（一键入库前）:")
        for item in items:
            print(f"   {item.product.name}")
            print(f"     计划数量: {item.quantity}")
            print(f"     累计已借用: {item.borrowed_quantity}")
            print(f"     剩余可借用: {item.borrowable_quantity}")
            print(f"     待归还数量: {item.remaining_quantity}")

        # 3. 检查按钮显示逻辑
        total_borrowable = sum(item.borrowable_quantity for item in items)
        can_confirm_receipt = borrow.status == "borrowed" and total_borrowable > 0
        can_return = borrow.status == "borrowed" and borrow.total_remaining_quantity > 0
        can_request_conversion = borrow.status == "borrowed" and borrow.total_remaining_quantity > 0

        print(f"\n🎯 按钮显示逻辑:")
        print(f"   can_confirm_receipt (一键入库): {can_confirm_receipt}")
        print(f"     原因: 状态={borrow.status}, 剩余可借用={total_borrowable}")
        print(f"   can_return (归还): {can_return}")
        print(f"     原因: 状态={borrow.status}, 待归还={borrow.total_remaining_quantity}")
        print(f"   can_request_conversion (转采购): {can_request_conversion}")
        print(f"     原因: 状态={borrow.status}, 待归还={borrow.total_remaining_quantity}")

        # 4. 如果有可借用数量，模拟一键入库
        if total_borrowable > 0:
            user = User.objects.first()
            if not user:
                print("\n❌ 未找到用户，无法测试入库")
                return False

            print(f"\n🔄 执行一键入库...")
            try:
                borrow.confirm_borrow_receipt(user, None)
                print(f"✅ 一键入库成功")

                # 重新查询借用单（刷新数据）
                borrow.refresh_from_db()

                print(f"\n📦 借用明细（一键入库后）:")
                items = borrow.items.filter(is_deleted=False)
                for item in items:
                    print(f"   {item.product.name}")
                    print(f"     累计已借用: {item.borrowed_quantity} ⬅️ 应该增加了")
                    print(f"     剩余可借用: {item.borrowable_quantity} ⬅️ 应该减少了")
                    print(f"     待归还数量: {item.remaining_quantity} ⬅️ 应该大于0")

                # 重新检查按钮显示逻辑
                total_borrowable = sum(item.borrowable_quantity for item in items)
                can_confirm_receipt = borrow.status == "borrowed" and total_borrowable > 0
                can_return = borrow.status == "borrowed" and borrow.total_remaining_quantity > 0
                can_request_conversion = (
                    borrow.status == "borrowed" and borrow.total_remaining_quantity > 0
                )

                print(f"\n🎯 入库后按钮显示:")
                print(f"   can_confirm_receipt (一键入库): {can_confirm_receipt} ⬅️ 应该是 False")
                print(f"   can_return (归还): {can_return} ⬅️ 应该是 True")
                print(f"   can_request_conversion (转采购): {can_request_conversion} ⬅️ 应该是 True")

                # 验证预期结果
                print(f"\n✅ 验证结果:")
                if not can_confirm_receipt and can_return and can_request_conversion:
                    print(f"   ✅ 按钮状态正确！一键入库后应显示归还和转采购按钮")
                else:
                    print(f"   ❌ 按钮状态异常！")
                    if can_confirm_receipt:
                        print(f"      - 一键入库按钮仍然显示（应该隐藏）")
                    if not can_return:
                        print(f"      - 归还按钮不显示（应该显示）")
                    if not can_request_conversion:
                        print(f"      - 转采购按钮不显示（应该显示）")

                return True

            except ValueError as e:
                print(f"❌ 入库失败: {e}")
                return False
        else:
            print(f"\n⚠️  该借用单没有可借用数量，无需测试入库")
            return False

    except Borrow.DoesNotExist:
        print(f"\n❌ 未找到借用单: {borrow_number}")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        borrow_number = sys.argv[1]
    else:
        # 默认测试 BO260203003
        borrow_number = "BO260203003"

    print("\n" + "🔧" * 35)
    print("  借用单一键入库测试工具")
    print("🔧" * 35 + "\n")

    success = test_borrow_inflow(borrow_number)

    print("\n" + "=" * 70)
    if success:
        print("✅ 测试完成")
    else:
        print("❌ 测试失败")
    print("=" * 70 + "\n")
