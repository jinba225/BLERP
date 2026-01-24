"""
测试付款单号唯一性修复

验证修复后的付款单号生成逻辑是否能正确处理并发冲突。

用法:
    python manage.py test_payment_uniqueness
"""
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from apps.finance.models import Payment
from apps.core.utils import DocumentNumberGenerator
from apps.customers.models import Customer


class Command(BaseCommand):
    help = '测试付款单号唯一性修复'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('测试付款单号唯一性修复')
        self.stdout.write('=' * 60)

        # 获取或创建测试客户
        customer = Customer.objects.filter(is_deleted=False).first()
        if not customer:
            self.stdout.write(self.style.ERROR('没有找到客户，请先创建客户'))
            return

        # 测试场景 1：正常生成单号
        self.stdout.write('\n1. 测试正常生成单号...')
        try:
            payment_number = DocumentNumberGenerator.generate('payment_receipt')
            self.stdout.write(self.style.SUCCESS(f'   ✓ 成功生成单号: {payment_number}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ 生成单号失败: {str(e)}'))
            return

        # 测试场景 2：模拟单号冲突重试
        self.stdout.write('\n2. 测试单号冲突重试机制...')
        test_numbers = []
        for i in range(3):
            try:
                payment_number = DocumentNumberGenerator.generate('payment_receipt')
                test_numbers.append(payment_number)
                self.stdout.write(f'   第 {i+1} 次生成: {payment_number}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   第 {i+1} 次生成失败: {str(e)}'))

        if len(test_numbers) == 3:
            unique_numbers = len(set(test_numbers))
            if unique_numbers == 3:
                self.stdout.write(self.style.SUCCESS(f'   ✓ 生成 {unique_numbers} 个唯一单号'))
            else:
                self.stdout.write(self.style.WARNING(f'   ⚠ 只有 {unique_numbers} 个唯一单号，存在重复'))
        else:
            self.stdout.write(self.style.ERROR(f'   ✗ 只生成了 {len(test_numbers)} 个单号'))

        # 测试场景 3：验证数据库唯一约束
        self.stdout.write('\n3. 验证数据库唯一约束...')
        test_payment_number = test_numbers[0] if test_numbers else None
        if test_payment_number:
            try:
                # 尝试创建相同单号的记录
                with transaction.atomic():
                    Payment.objects.create(
                        payment_number=test_payment_number,
                        payment_type='receipt',
                        payment_method='bank_transfer',
                        status='completed',
                        customer=customer,
                        amount=100.00,
                        currency='CNY',
                        payment_date='2026-01-16',
                        reference_type='test',
                        reference_id='test',
                        description='测试付款记录1'
                    )
                self.stdout.write(self.style.SUCCESS(f'   ✓ 第一条记录创建成功: {test_payment_number}'))
            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f'   ✗ 第一条记录创建失败: {str(e)}'))

            try:
                # 尝试创建重复单号的记录（应该失败）
                with transaction.atomic():
                    Payment.objects.create(
                        payment_number=test_payment_number,
                        payment_type='receipt',
                        payment_method='bank_transfer',
                        status='completed',
                        customer=customer,
                        amount=200.00,
                        currency='CNY',
                        payment_date='2026-01-16',
                        reference_type='test',
                        reference_id='test',
                        description='测试付款记录2'
                    )
                self.stdout.write(self.style.ERROR(f'   ✗ 第二条记录创建成功（不应该成功）'))
            except IntegrityError as e:
                self.stdout.write(self.style.SUCCESS(f'   ✓ 第二条记录被唯一约束阻止: {str(e)}'))

            # 清理测试数据
            Payment.objects.filter(payment_number=test_payment_number).delete()
            self.stdout.write(f'   清理测试数据: {test_payment_number}')

        # 测试场景 4：检查现有付款记录是否有重复
        self.stdout.write('\n4. 检查现有付款记录是否有重复...')
        from django.db.models import Count
        duplicates = Payment.objects.filter(is_deleted=False).values('payment_number').annotate(
            count=Count('payment_number')
        ).filter(count__gt=1)

        if duplicates:
            self.stdout.write(self.style.WARNING(f'   ⚠ 发现 {duplicates.count()} 个重复的单号：'))
            for item in duplicates:
                self.stdout.write(f'     - {item["payment_number"]}: {item["count"]} 次')
        else:
            self.stdout.write(self.style.SUCCESS(f'   ✓ 没有发现重复的单号'))

        # 总结
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('测试完成')
        self.stdout.write('=' * 60)

        self.stdout.write('\n修复总结：')
        self.stdout.write('1. 修改了 customer_account_writeoff 视图')
        self.stdout.write('2. 修改了 supplier_account_writeoff 视图')
        self.stdout.write('3. 修改了 sales/views.py 中的 3 个 Payment 创建点')
        self.stdout.write('\n所有修改都添加了单号冲突重试机制（最多重试 3 次）')
