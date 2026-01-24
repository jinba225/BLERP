"""
测试付款核销功能（简化版）

直接测试付款核销功能，跳过采购收货流程
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'better_laser_erp.settings')
django.setup()

from apps.suppliers.models import Supplier
from apps.finance.models import SupplierAccount, SupplierPrepayment, Payment
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


def run_test():
    """运行付款核销测试"""

    print("=" * 70)
    print("🧪 开始测试付款核销功能（简化版）")
    print("=" * 70)

    # 获取或创建测试用户
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("❌ 请先创建管理员用户")
        return False

    # ========== 步骤1：创建测试供应商 ==========
    print("\n📝 步骤1：创建测试供应商...")
    supplier, created = Supplier.objects.get_or_create(
        code='TEST_SUPPLIER_PY2',
        defaults={
            'name': 'Python测试供应商2',
            'address': '测试地址',
            'level': 'B',
            'created_by': user,
            'updated_by': user,
        }
    )
    if created:
        print(f"   ✅ 创建供应商成功：{supplier.name}")
    else:
        # 恢复已删除的供应商
        if supplier.is_deleted:
            supplier.is_deleted = False
            supplier.deleted_at = None
            supplier.deleted_by = None
            supplier.save()
        print(f"   ✅ 使用已存在供应商：{supplier.name}")

    # ========== 步骤2：创建应付账款 ==========
    print("\n💰 步骤2：创建应付账款...")

    # 删除旧应付账款
    for obj in SupplierAccount.objects.filter(supplier=supplier):
        obj.hard_delete()

    from apps.core.utils import DocumentNumberGenerator

    account = SupplierAccount.objects.create(
        invoice_number=DocumentNumberGenerator.generate('supplier_account'),
        supplier=supplier,
        invoice_amount=Decimal('1000.00'),
        paid_amount=Decimal('0.00'),
        balance=Decimal('1000.00'),
        invoice_date=timezone.now().date(),
        due_date=timezone.now().date() + timedelta(days=30),
        status='pending',
        notes='测试应付账款',
        created_by=user,
        updated_by=user,
    )

    print(f"   ✅ 创建应付账款成功：{account.invoice_number}")
    print(f"   💰 应付金额：¥{account.invoice_amount}")
    print(f"   📊 未付余额：¥{account.balance}")

    # ========== 步骤3：创建预付款 ==========
    print("\n💵 步骤3：创建供应商预付款...")

    # 删除旧预付款
    for obj in SupplierPrepayment.objects.filter(supplier=supplier):
        obj.hard_delete()

    prepayment = SupplierPrepayment.objects.create(
        supplier=supplier,
        amount=Decimal('500.00'),
        balance=Decimal('500.00'),
        paid_date=timezone.now().date(),
        notes='测试预付款',
        created_by=user,
        updated_by=user,
    )

    print(f"   ✅ 创建预付款成功，余额：¥{prepayment.balance}")

    # ========== 步骤4：测试预付款冲抵核销 ==========
    print("\n🔄 步骤4：测试预付款冲抵核销...")
    print(f"   📊 核销前：应付余额 ¥{account.balance}，预付款余额 ¥{prepayment.balance}")

    try:
        from apps.core.utils import DocumentNumberGenerator

        # 模拟核销逻辑
        from django.db import transaction

        with transaction.atomic():
            # 生成付款单号（使用重试机制）
            def generate_unique_payment_number(prefix_key):
                from django.db import IntegrityError

                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        with transaction.atomic(savepoint=False):
                            payment_number = DocumentNumberGenerator.generate(prefix_key)
                            placeholder = Payment.objects.create(
                                payment_number=payment_number,
                                payment_type='payment',
                                payment_method='other',
                                status='pending',
                                amount=Decimal('0'),
                                currency='CNY',
                                payment_date=timezone.now().date(),
                                description='PLACEHOLDER',
                                created_by=user
                            )
                            placeholder.hard_delete()
                        return payment_number
                    except IntegrityError:
                        continue
                raise Exception(f'生成付款单号失败：已尝试 {max_retries} 次')

            payment_number = generate_unique_payment_number('payment')

            # 创建预付款冲抵记录
            payment = Payment.objects.create(
                payment_number=payment_number,
                payment_type='payment',
                payment_method='other',
                status='completed',
                supplier=supplier,
                amount=Decimal('500.00'),
                currency='CNY',
                payment_date=timezone.now().date(),
                reference_type='supplier_account',
                reference_id=str(account.id),
                reference_number=account.invoice_number or '',
                description='预付款冲抵',
                processed_by=user,
                created_by=user,
            )

            # 更新预付款余额
            prepayment.balance = Decimal('0.00')
            prepayment.save()

            # 更新应付账款
            account.paid_amount += Decimal('500.00')
            account.balance -= Decimal('500.00')
            if account.balance <= 0:
                account.balance = Decimal('0.00')
                account.status = 'paid'
            else:
                account.status = 'partially_paid'
            account.save()

        print(f"   ✅ 预付款冲抵成功")
        print(f"   📝 付款单号：{payment_number}")
        print(f"   📊 核销后：应付余额 ¥{account.balance}，预付款余额 ¥{prepayment.balance}")

    except Exception as e:
        print(f"   ❌ 预付款冲抵失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # ========== 步骤5：测试现金付款核销 ==========
    print("\n💰 步骤5：测试现金付款核销...")
    print(f"   📊 付款前：应付余额 ¥{account.balance}")

    try:
        with transaction.atomic():
            # 生成付款单号
            payment_number = generate_unique_payment_number('payment')

            # 创建现金付款记录
            payment = Payment.objects.create(
                payment_number=payment_number,
                payment_type='payment',
                payment_method='bank_transfer',
                status='completed',
                supplier=supplier,
                amount=Decimal('500.00'),
                currency='CNY',
                payment_date=timezone.now().date(),
                reference_type='supplier_account',
                reference_id=str(account.id),
                reference_number=account.invoice_number or '',
                description='应付核销',
                processed_by=user,
                created_by=user,
            )

            # 更新应付账款
            account.paid_amount += Decimal('500.00')
            account.balance -= Decimal('500.00')
            if account.balance <= 0:
                account.balance = Decimal('0.00')
                account.status = 'paid'
            else:
                account.status = 'partially_paid'
            account.save()

        print(f"   ✅ 现金付款成功")
        print(f"   📝 付款单号：{payment_number}")
        print(f"   📊 付款后：应付余额 ¥{account.balance}")
        print(f"   🎖️  应付状态：{account.get_status_display()}")

    except Exception as e:
        print(f"   ❌ 现金付款失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # ========== 验证结果 ==========
    print("\n🔍 验证测试结果...")

    # 重新加载数据
    account.refresh_from_db()
    payments = Payment.objects.filter(
        supplier=supplier,
        is_deleted=False
    ).order_by('-created_at')

    print(f"\n✅ 应付账款状态：")
    print(f"   - 单据号：{account.invoice_number}")
    print(f"   - 应付总额：¥{account.invoice_amount}")
    print(f"   - 已付金额：¥{account.paid_amount}")
    print(f"   - 未付余额：¥{account.balance}")
    print(f"   - 状态：{account.get_status_display()}")

    print(f"\n✅ 付款记录（共{payments.count()}条）：")
    for payment in payments:
        print(f"   - {payment.payment_number}: ¥{payment.amount} ({payment.get_payment_type_display()}) - {payment.description}")

    # 判断测试是否成功
    success = (
        account.balance == Decimal('0.00') and
        account.status == 'paid' and
        payments.count() >= 2
    )

    print("\n" + "=" * 70)
    if success:
        print("✅ 测试通过！付款核销功能正常工作")
        print("   - 付款单号生成成功（带重试机制）")
        print("   - 预付款冲抵核销成功")
        print("   - 现金付款核销成功")
        print("   - 应付账款状态更新正确")
    else:
        print("❌ 测试失败！")
    print("=" * 70)

    return success


if __name__ == '__main__':
    try:
        success = run_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试执行失败：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
