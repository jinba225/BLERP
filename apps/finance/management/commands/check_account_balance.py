from django.core.management.base import BaseCommand
from apps.finance.models import SupplierAccount, SupplierAccountDetail
from decimal import Decimal


class Command(BaseCommand):
    help = '检查供应商应付账款余额是否正确'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=int,
            help='指定账户ID检查',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='自动修复不一致的数据',
        )

    def handle(self, *args, **options):
        account_id = options.get('account_id')
        fix = options.get('fix')

        if account_id:
            accounts = SupplierAccount.objects.filter(id=account_id, is_deleted=False)
        else:
            # 检查所有余额大于0的账户
            accounts = SupplierAccount.objects.filter(is_deleted=False, balance__gt=0)

        for account in accounts:
            self.check_account(account, fix)

    def check_account(self, account, fix=False):
        """检查单个账户"""
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'检查账户: {account.invoice_number} (ID: {account.id})')
        self.stdout.write(f'{"="*60}')
        self.stdout.write(f'供应商: {account.supplier.name if account.supplier else "N/A"}')
        self.stdout.write(f'订单号: {account.purchase_order.order_number if account.purchase_order else "N/A"}')
        self.stdout.write('')
        self.stdout.write('【主单数据】')
        self.stdout.write(f'  实际应付(invoice_amount): ¥{account.invoice_amount}')
        self.stdout.write(f'  已核销(paid_amount):     ¥{account.paid_amount}')
        self.stdout.write(f'  未付余额(balance):       ¥{account.balance}')
        self.stdout.write(f'  状态: {account.get_status_display()}')

        # 检查是否有明细
        details = SupplierAccountDetail.objects.filter(
            parent_account=account,
            is_deleted=False
        )

        if details.exists():
            self.stdout.write('')
            self.stdout.write('【明细记录】')
            total_detail_amount = Decimal('0')
            total_allocated = Decimal('0')

            for detail in details:
                self.stdout.write(f'  {detail.detail_number}:')
                self.stdout.write(f'    类型: {detail.get_detail_type_display()}')
                self.stdout.write(f'    应付金额: ¥{detail.amount}')
                self.stdout.write(f'    已核销:   ¥{detail.allocated_amount}')
                self.stdout.write(f'    未核销:   ¥{detail.balance}')
                self.stdout.write(f'    状态: {detail.get_status_display()}')

                total_detail_amount += detail.amount
                total_allocated += detail.allocated_amount

            expected_balance = total_detail_amount - total_allocated
            self.stdout.write('')
            self.stdout.write('【明细汇总】')
            self.stdout.write(f'  总应付:   ¥{total_detail_amount}')
            self.stdout.write(f'  总已核销: ¥{total_allocated}')
            self.stdout.write(f'  总未核销: ¥{expected_balance}')

            # 对比主单和明细
            self.stdout.write('')
            self.stdout.write('【数据一致性检查】')

            if account.invoice_amount != total_detail_amount:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ 实际应付不一致! '
                        f'主单¥{account.invoice_amount} vs 明细汇总¥{total_detail_amount}'
                    )
                )
            else:
                self.stdout.write(self.style.SUCCESS(f'  ✓ 实际应付一致: ¥{account.invoice_amount}'))

            if account.paid_amount != total_allocated:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ 已核销金额不一致! '
                        f'主单¥{account.paid_amount} vs 明细汇总¥{total_allocated}'
                    )
                )
            else:
                self.stdout.write(self.style.SUCCESS(f'  ✓ 已核销金额一致: ¥{account.paid_amount}'))

            if account.balance != expected_balance:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ 未付余额不一致! '
                        f'主单¥{account.balance} vs 应该¥{expected_balance}'
                    )
                )

                # 修复
                if fix:
                    self.stdout.write('')
                    self.stdout.write(self.style.WARNING('  正在修复...'))
                    account.invoice_amount = total_detail_amount
                    account.paid_amount = total_allocated
                    account.balance = expected_balance
                    account.save()
                    self.stdout.write(self.style.SUCCESS('  ✓ 修复完成'))
            else:
                self.stdout.write(self.style.SUCCESS(f'  ✓ 未付余额一致: ¥{account.balance}'))

            # 验证公式
            expected_balance_calc = account.invoice_amount - account.paid_amount
            self.stdout.write('')
            self.stdout.write('【公式验证】')
            self.stdout.write(f'  未付余额 = 实际应付 - 已核销')
            self.stdout.write(f'  ¥{account.balance} = ¥{account.invoice_amount} - ¥{account.paid_amount}')

            if abs(account.balance - expected_balance_calc) > Decimal('0.01'):
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ 公式不成立! '
                        f'¥{account.balance} ≠ ¥{account.invoice_amount} - ¥{account.paid_amount} = ¥{expected_balance_calc}'
                    )
                )
            else:
                self.stdout.write(self.style.SUCCESS('  ✓ 公式成立'))
        else:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('  ⚠ 没有明细记录'))

            # 验证公式
            expected_balance_calc = account.invoice_amount - account.paid_amount
            self.stdout.write('')
            self.stdout.write('【公式验证】')
            self.stdout.write(f'  未付余额 = 实际应付 - 已核销')
            self.stdout.write(f'  ¥{account.balance} = ¥{account.invoice_amount} - ¥{account.paid_amount}')

            if abs(account.balance - expected_balance_calc) > Decimal('0.01'):
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ 公式不成立! '
                        f'¥{account.balance} ≠ ¥{account.invoice_amount} - ¥{account.paid_amount} = ¥{expected_balance_calc}'
                    )
                )

                if fix:
                    self.stdout.write('')
                    self.stdout.write(self.style.WARNING('  正在修复...'))
                    account.balance = expected_balance_calc
                    account.save()
                    self.stdout.write(self.style.SUCCESS(f'  ✓ 修复完成，余额已更新为 ¥{expected_balance_calc}'))
            else:
                self.stdout.write(self.style.SUCCESS('  ✓ 公式成立'))
