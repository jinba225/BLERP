#!/usr/bin/env python3
"""
测试借用单一键入库后库存更新是否及时

验证流程：
1. 检查借用单状态
2. 模拟一键入库
3. 查询借用仓库存
4. 验证库存是否更新
"""

import os
import sys

import django

sys.path.insert(0, "/Users/janjung/Code_Projects/django_erp")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")
django.setup()

from django.contrib.auth import get_user_model
from inventory.models import InventoryStock, Warehouse
from purchase.models import Borrow

User = get_user_model()


def test_stock_update(borrow_number):
    """测试库存更新"""
    print("=" * 70)
    print(f"🔍 测试借用单: {borrow_number}")
    print("=" * 70)

    try:
        # 1. 获取借用单
        borrow = Borrow.objects.get(borrow_number=borrow_number, is_deleted=False)
        print(f"\n✅ 找到借用单")
        print(f"   状态: {borrow.status}")

        # 2. 获取借用仓
        try:
            borrow_warehouse = Warehouse.objects.filter(code__icontains="BORROW").first()
            if not borrow_warehouse:
                borrow_warehouse = Warehouse.objects.filter(name__icontains="借用").first()

            if not borrow_warehouse:
                print("\n❌ 未找到借用仓")
                return False

            print(f"   借用仓: {borrow_warehouse.name}")
        except Exception as e:
            print(f"\n❌ 获取借用仓失败: {e}")
            return False

        # 3. 检查明细
        items = borrow.items.filter(is_deleted=False)
        print(f"\n📦 借用明细:")
        total_borrowable = 0
        for item in items:
            borrowable = item.borrowable_quantity
            total_borrowable += borrowable
            print(f"   {item.product.name}")
            print(f"     计划数量: {item.quantity}")
            print(f"     已借用: {item.borrowed_quantity}")
            print(f"     剩余可借用: {borrowable}")

        if total_borrowable == 0:
            print(f"\n⚠️  该借用单没有可入库数量")
            return False

        # 4. 检查入库前的库存
        print(f"\n📊 入库前借用仓库存:")
        pre_stock = {}
        for item in items:
            if item.borrowable_quantity > 0:
                stock = InventoryStock.objects.filter(
                    product=item.product, warehouse=borrow_warehouse, is_deleted=False
                ).first()

                if stock:
                    pre_stock[item.product.id] = stock.quantity
                    print(f"   {item.product.name}: {stock.quantity} 件")
                else:
                    pre_stock[item.product.id] = 0
                    print(f"   {item.product.name}: 0 件 (无库存记录)")

        # 5. 执行一键入库
        user = User.objects.first()
        if not user:
            print("\n❌ 未找到用户")
            return False

        print(f"\n🔄 执行一键入库...")
        try:
            borrow.confirm_borrow_receipt(user, None)
            print(f"✅ 入库成功")
        except ValueError as e:
            print(f"❌ 入库失败: {e}")
            return False

        # 6. 立即查询库存（模拟访问库存查询页面）
        print(f"\n📊 入库后借用仓库存:")
        post_stock = {}
        for item in items:
            stock = InventoryStock.objects.filter(
                product=item.product, warehouse=borrow_warehouse, is_deleted=False
            ).first()

            if stock:
                post_stock[item.product.id] = stock.quantity
                print(f"   {item.product.name}: {stock.quantity} 件")

                # 验证库存是否增加
                expected_increase = item.borrowable_quantity
                actual_increase = post_stock[item.product.id] - pre_stock.get(item.product.id, 0)

                if actual_increase == expected_increase:
                    print(f"     ✅ 库存增加正确: +{actual_increase} 件")
                else:
                    print(f"     ❌ 库存增加错误: 预期+{expected_increase}, 实际+{actual_increase}")
            else:
                post_stock[item.product.id] = 0
                print(f"   {item.product.name}: 0 件 (无库存记录)")
                print(f"     ⚠️  库存记录未创建")

        # 7. 强制刷新查询（测试是否有查询缓存问题）
        print(f"\n🔄 强制刷新查询（模拟页面刷新）:")
        from django.db import connection

        connection.close()  # 关闭连接，强制重新查询

        print(f"   数据库连接已关闭并重新打开")

        # 重新查询
        for item in items:
            stock = InventoryStock.objects.filter(
                product=item.product, warehouse=borrow_warehouse, is_deleted=False
            ).first()

            if stock:
                print(f"   {item.product.name}: {stock.quantity} 件 (刷新后)")
                if post_stock.get(item.product.id, 0) != stock.quantity:
                    print(f"     ⚠️  刷新前后数据不一致！")
                    print(f"        刷新前: {post_stock[item.product.id]}")
                    print(f"        刷新后: {stock.quantity}")

        return True

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
        print("\n使用方法:")
        print("  python3 test_stock_update.py <借用单号>")
        print("\n示例:")
        print("  python3 test_stock_update.py BO260203003")
        sys.exit(1)

    print("\n" + "🔧" * 35)
    print("  库存更新测试工具")
    print("🔧" * 35 + "\n")

    success = test_stock_update(borrow_number)

    print("\n" + "=" * 70)
    if success:
        print("✅ 测试完成")
    else:
        print("❌ 测试失败")
    print("=" * 70 + "\n")
