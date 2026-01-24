"""
测试采购申请价格验证功能

验证：
1. 审核时如果没有输入预估单价，应该拒绝
2. 转换订单时如果没有输入预估单价，应该拒绝
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')
django.setup()

from apps.purchase.models import PurchaseRequest, PurchaseRequestItem
from apps.products.models import Product
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


def run_test():
    """运行测试"""

    print("=" * 70)
    print("🧪 测试采购申请价格验证功能")
    print("=" * 70)

    # 获取测试用户
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("❌ 请先创建管理员用户")
        return False

    # 获取或创建测试产品
    product, created = Product.objects.get_or_create(
        code='TEST_PRODUCT_PRICE',
        defaults={
            'name': '测试产品价格验证',
            'specifications': '测试规格',
            'cost_price': Decimal('100.00'),
            'selling_price': Decimal('150.00'),
            'created_by': user,
            'updated_by': user,
        }
    )

    # ========== 测试场景1：审核时没有输入价格 ==========
    print("\n📝 测试场景1：审核时没有输入预估单价...")

    # 创建采购申请（无价格）
    request1 = PurchaseRequest.objects.create(
        request_number='TEST_PRICE_001',
        requester=user,
        request_date='2026-01-17',
        purpose='测试',
        status='draft',
        created_by=user,
        updated_by=user,
    )

    # 创建明细（无预估单价）
    item1 = PurchaseRequestItem.objects.create(
        purchase_request=request1,
        product=product,
        quantity=10,
        estimated_price=None,  # 没有价格
        estimated_total=Decimal('0'),
        created_by=user,
        updated_by=user,
    )

    print(f"   ✅ 创建采购申请：{request1.request_number}")
    print(f"   📦 产品：{product.name}，数量：10，预估单价：未填写")

    # 尝试审核
    try:
        order, message = request1.approve_and_convert_to_order(
            approved_by_user=user,
            supplier_id=1,  # 假设存在供应商
            warehouse_id=1,  # 假设存在仓库
        )
        print(f"   ❌ 测试失败：应该拒绝审核，但通过了")
        return False
    except ValueError as e:
        print(f"   ✅ 审核被拒绝：{str(e)}")
        if '预估单价' in str(e) or '必须输入' in str(e):
            print(f"   ✅ 错误提示正确：要求输入预估单价")
        else:
            print(f"   ⚠️  错误提示可能不够明确：{str(e)}")

    # ========== 测试场景2：审核时输入了价格 ==========
    print("\n📝 测试场景2：审核时输入了预估单价...")

    # 创建采购申请（有价格）
    request2 = PurchaseRequest.objects.create(
        request_number='TEST_PRICE_002',
        requester=user,
        request_date='2026-01-17',
        purpose='测试',
        status='draft',
        created_by=user,
        updated_by=user,
    )

    # 创建明细（有预估单价）
    item2 = PurchaseRequestItem.objects.create(
        purchase_request=request2,
        product=product,
        quantity=10,
        estimated_price=Decimal('100.00'),  # 有价格
        estimated_total=Decimal('1000.00'),
        created_by=user,
        updated_by=user,
    )

    print(f"   ✅ 创建采购申请：{request2.request_number}")
    print(f"   📦 产品：{product.name}，数量：10，预估单价：¥100.00")

    # 尝试审核（不自动创建订单，只验证价格）
    try:
        # 暂时禁用自动创建订单
        from apps.core.models import SystemConfig
        config, _ = SystemConfig.objects.get_or_create(
            key='purchase_auto_create_order_on_approve',
            defaults={
                'value': 'false',
                'config_type': 'business',
                'description': '测试配置',
                'is_active': True
            }
        )
        config.value = 'false'
        config.save()

        order, message = request2.approve_and_convert_to_order(
            approved_by_user=user,
            supplier_id=1,  # 假设存在供应商
            warehouse_id=1,  # 假设存在仓库
        )
        print(f"   ✅ 审核通过：{message}")
        print(f"   ✅ 生成订单：{order.order_number if order else '无'}")

    except ValueError as e:
        print(f"   ❌ 测试失败：有价格但还是被拒绝了：{str(e)}")
        return False

    # ========== 测试场景3：转换订单时没有输入价格 ==========
    print("\n📝 测试场景3：手动转换订单时没有输入预估单价...")

    # 创建已审核的采购申请（无价格）
    request3 = PurchaseRequest.objects.create(
        request_number='TEST_PRICE_003',
        requester=user,
        request_date='2026-01-17',
        purpose='测试',
        status='approved',
        approved_by=user,
        approved_at='2026-01-17 00:00:00',
        created_by=user,
        updated_by=user,
    )

    item3 = PurchaseRequestItem.objects.create(
        purchase_request=request3,
        product=product,
        quantity=10,
        estimated_price=None,  # 没有价格
        estimated_total=Decimal('0'),
        created_by=user,
        updated_by=user,
    )

    print(f"   ✅ 创建采购申请：{request3.request_number}")
    print(f"   📦 产品：{product.name}，数量：10，预估单价：未填写")

    # 尝试手动转换订单
    try:
        from apps.purchase.services import PurchaseRequestService
        order = PurchaseRequestService.convert_request_to_order(
            request3,
            user,
            supplier_id=1,
            warehouse_id=1
        )
        print(f"   ❌ 测试失败：应该拒绝转换，但通过了")
        return False
    except ValueError as e:
        print(f"   ✅ 转换被拒绝：{str(e)}")
        if '预估单价' in str(e) or '必须输入' in str(e):
            print(f"   ✅ 错误提示正确：要求输入预估单价")
        else:
            print(f"   ⚠️  错误提示可能不够明确：{str(e)}")

    # ========== 测试场景4：转换订单时输入了价格 ==========
    print("\n📝 测试场景4：手动转换订单时输入了预估单价...")

    # 创建已审核的采购申请（有价格）
    request4 = PurchaseRequest.objects.create(
        request_number='TEST_PRICE_004',
        requester=user,
        request_date='2026-01-17',
        purpose='测试',
        status='approved',
        approved_by=user,
        approved_at='2026-01-17 00:00:00',
        created_by=user,
        updated_by=user,
    )

    item4 = PurchaseRequestItem.objects.create(
        purchase_request=request4,
        product=product,
        quantity=10,
        estimated_price=Decimal('100.00'),  # 有价格
        estimated_total=Decimal('1000.00'),
        created_by=user,
        updated_by=user,
    )

    print(f"   ✅ 创建采购申请：{request4.request_number}")
    print(f"   📦 产品：{product.name}，数量：10，预估单价：¥100.00")

    # 尝试手动转换订单
    try:
        order = PurchaseRequestService.convert_request_to_order(
            request4,
            user,
            supplier_id=1,
            warehouse_id=1
        )
        print(f"   ✅ 转换成功：采购订单 {order.order_number}")
        print(f"   ✅ 订单明细数量：{order.items.count()}")
    except ValueError as e:
        print(f"   ❌ 测试失败：有价格但还是被拒绝了：{str(e)}")
        return False

    # 清理测试数据
    print("\n🧹 清理测试数据...")
    for obj in [request1, request2, request3, request4]:
        obj.hard_delete()

    print("\n" + "=" * 70)
    print("✅ 所有测试通过！采购申请价格验证功能正常工作")
    print("=" * 70)

    return True


if __name__ == '__main__':
    try:
        success = run_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试执行失败：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
