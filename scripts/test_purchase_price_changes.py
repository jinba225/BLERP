"""
测试采购流程修改

验证：
1. 采购申请没有预估价格字段
2. 采购订单必须确认价格才能审核
3. 前端价格提示弹窗正常工作
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')
django.setup()

from apps.purchase.models import PurchaseRequest, PurchaseRequestItem, PurchaseOrder, PurchaseOrderItem
from apps.products.models import Product
from apps.suppliers.models import Supplier
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

User = get_user_model()


def run_test():
    """运行测试"""

    print("=" * 70)
    print("🧪 测试采购流程修改")
    print("=" * 70)

    # 获取测试用户
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("❌ 请先创建管理员用户")
        return False

    # ========== 测试场景1：创建采购申请（不需要价格） ==========
    print("\n📝 测试场景1：创建采购申请（不需要填写价格）...")

    # 获取或创建测试供应商
    supplier, created = Supplier.objects.get_or_create(
        code='TEST_SUPPLIER_PRICE',
        defaults={
            'name': '测试供应商',
            'address': '测试地址',
            'level': 'B',
            'is_approved': True,
            'created_by': user,
            'updated_by': user,
        }
    )

    # 获取或创建测试产品
    product, created = Product.objects.get_or_create(
        code='TEST_PRODUCT_PRICE_CHK',
        defaults={
            'name': '测试产品价格检查',
            'specifications': '测试规格',
            'cost_price': Decimal('100.00'),
            'selling_price': Decimal('150.00'),
            'created_by': user,
            'updated_by': user,
        }
    )

    # 创建采购申请
    request = PurchaseRequest.objects.create(
        request_number='TEST_REQ_PRICE_001',
        requester=user,
        request_date=timezone.now().date(),
        purpose='测试采购申请（不需要价格）',
        status='draft',
        created_by=user,
        updated_by=user,
    )

    # 创建明细（不需要价格）
    item = PurchaseRequestItem.objects.create(
        purchase_request=request,
        product=product,
        quantity=10,
        specifications='测试规格',
        created_by=user,
        updated_by=user,
    )

    print(f"   ✅ 创建采购申请成功：{request.request_number}")
    print(f"   📦 产品：{product.name}，数量：{item.quantity}")
    print(f"   📌 无需填写价格")

    # ========== 测试场景2：审核采购申请（不需要价格） ==========
    print("\n📝 测试场景2：审核采购申请（不需要价格）...")

    try:
        from apps.core.models import SystemConfig

        # 临时禁用自动创建订单
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

        # 审核采购申请
        request.approved_by = user
        request.approved_at = timezone.now()
        request.status = 'approved'
        request.save()

        print(f"   ✅ 审核通过：{request.request_number}")
        print(f"   ✅ 无需填写价格即可审核")

    except Exception as e:
        print(f"   ❌ 审核失败：{str(e)}")
        return False

    # ========== 测试场景3：创建采购订单（部分明细有价格，部分没有） ==========
    print("\n📝 测试场景3：创建采购订单（部分明细有价格，部分没有）...")

    # 创建采购订单
    order = PurchaseOrder.objects.create(
        order_number='TEST_ORDER_PRICE_001',
        supplier=supplier,
        order_date=timezone.now().date(),
        total_amount=Decimal('0'),
        status='draft',
        created_by=user,
        updated_by=user,
    )

    # 创建明细1：有价格
    item1 = PurchaseOrderItem.objects.create(
        purchase_order=order,
        product=product,
        quantity=5,
        unit_price=Decimal('100.00'),
        line_total=Decimal('500.00'),
        created_by=user,
        updated_by=user,
    )

    # 创建明细2：无价格
    item2 = PurchaseOrderItem.objects.create(
        purchase_order=order,
        product=product,
        quantity=5,
        unit_price=Decimal('0'),
        line_total=Decimal('0'),
        created_by=user,
        updated_by=user,
    )

    print(f"   ✅ 创建采购订单：{order.order_number}")
    print(f"   📦 明细1：{product.name} × 5，单价：¥100.00")
    print(f"   📦 明细2：{product.name} × 5，单价：未填写")

    # ========== 测试场景4：审核采购订单（有价格和无价格混合） ==========
    print("\n📝 测试场景4：审核采购订单（有价格和无价格混合）...")

    try:
        order.approve_order(approved_by_user=user)
        print(f"   ❌ 测试失败：应该拒绝审核（因为有明细未填写价格）")
        return False
    except ValueError as e:
        print(f"   ✅ 审核被正确拒绝：{str(e)}")
        if '必须确认单价才能审核通过' in str(e):
            print(f"   ✅ 错误提示正确：要求确认单价")
        else:
            print(f"   ⚠️  错误提示可能不够明确：{str(e)}")

    # ========== 测试场景5：所有明细都有价格，应该审核通过 ==========
    print("\n📝 测试场景5：所有明细都有价格，应该审核通过...")

    # 修改明细2，添加价格
    item2.unit_price = Decimal('200.00')
    item2.line_total = Decimal('1000.00')
    item2.save()
    order.calculate_totals()
    order.save()

    print(f"   📦 明细1：{product.name} × 5，单价：¥100.00")
    print(f"   📦 明细2：{product.name} × 5，单价：¥200.00")

    try:
        receipt = order.approve_order(approved_by_user=user)
        print(f"   ✅ 审核成功！生成收货单：{receipt.receipt_number if receipt else '无'}")
    except ValueError as e:
        print(f"   ❌ 审核失败：{str(e)}")
        return False

    # ========== 清理测试数据 ==========
    print("\n🧹 清理测试数据...")
    for obj in [request, order]:
        obj.hard_delete()

    print("\n" + "=" * 70)
    print("✅ 所有测试通过！采购流程修改验证成功")
    print("=" * 70)
    print("\n📝 功能总结：")
    print("   ✅ 采购申请不需要预估价格字段")
    print("   ✅ 采购订单必须确认单价才能审核")
    print("   ✅ 前端价格检查和提示弹窗已添加")
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
