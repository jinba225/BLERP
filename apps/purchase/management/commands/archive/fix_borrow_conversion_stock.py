"""
修复借用单转采购订单的库存调拨问题

使用方法:
    python manage.py fix_borrow_conversion_stock [--dry-run]

选项:
    --dry-run: 只分析不执行修复，用于查看将要修复的内容
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.purchase.models import Borrow, PurchaseOrder, PurchaseReceipt
from apps.inventory.models import InventoryTransaction, InventoryStock, Warehouse


class Command(BaseCommand):
    help = '修复借用单转采购订单的库存调拨问题'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='只分析不执行修复',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('=== 干运行模式：只分析不修复 ==='))
        else:
            self.stdout.write(self.style.WARNING('=== 修复模式：将执行库存修复 ==='))

        # 查找所有有转采购订单的借用单
        borrows = Borrow.objects.filter(
            is_deleted=False,
            converted_order__isnull=False
        ).select_related('converted_order')

        self.stdout.write(f'\n找到 {borrows.count()} 个借用单转采购订单的记录')

        # 统计信息
        stats = {
            'total_borrows': 0,
            'duplicate_transactions': 0,
            'borrow_warehouse_correct': 0,
            'main_warehouse_correct': 0,
            'fixes_applied': 0,
        }

        for borrow in borrows:
            order = borrow.converted_order
            if not order or order.is_deleted:
                continue

            stats['total_borrows'] += 1
            self.stdout.write(f'\n处理借用单: {borrow.borrow_number} -> 采购订单: {order.order_number}')

            # 1. 检查转采购时是否正确创建了库存调拨事务
            self.stdout.write(f'  1. 检查转采购时的库存调拨事务...')

            # 获取借用仓和主仓
            try:
                borrow_wh = Warehouse.get_borrow_warehouse()
            except Warehouse.DoesNotExist:
                self.stdout.write(self.style.ERROR('    ❌ 借用仓不存在'))
                continue

            # 查找目标仓库（主仓）
            main_wh = Warehouse.objects.filter(
                warehouse_type='main',
                is_active=True,
                is_deleted=False
            ).first()

            if not main_wh:
                self.stdout.write(self.style.ERROR('    ❌ 主仓不存在'))
                continue

            # 检查转采购时的调拨事务
            transfer_out = InventoryTransaction.objects.filter(
                reference_number=borrow.borrow_number,
                warehouse=borrow_wh,
                transaction_type='out'
            )

            transfer_in = InventoryTransaction.objects.filter(
                reference_number=borrow.borrow_number,
                warehouse=main_wh,
                transaction_type='in'
            )

            if transfer_out.exists() and transfer_in.exists():
                self.stdout.write(self.style.SUCCESS(f'    ✅ 转采购调拨事务存在 (出库: {transfer_out.count()}, 入库: {transfer_in.count()})'))
            else:
                self.stdout.write(self.style.WARNING(f'    ⚠️  转采购调拨事务不完整 (出库: {transfer_out.count()}, 入库: {transfer_in.count()})'))

                # 如果调拨事务不存在，需要创建
                if not dry_run:
                    self.create_transfer_transactions(borrow, borrow_wh, main_wh)
                    stats['fixes_applied'] += 1

            # 2. 检查收货时是否创建了重复的库存事务
            self.stdout.write(f'  2. 检查收货时的重复库存事务...')

            receipts = PurchaseReceipt.objects.filter(
                purchase_order=order,
                is_deleted=False
            )

            duplicate_count = 0
            for receipt in receipts:
                # 查找该收货单创建的库存事务
                receipt_transactions = InventoryTransaction.objects.filter(
                    reference_type='purchase_receipt',
                    reference_id=str(receipt.id),
                    transaction_type='in'
                )

                if receipt_transactions.exists():
                    duplicate_count += receipt_transactions.count()
                    self.stdout.write(self.style.WARNING(f'    ⚠️  收货单 {receipt.receipt_number} 创建了 {receipt_transactions.count()} 个重复事务'))

                    if not dry_run:
                        # 删除重复事务
                        count, _ = receipt_transactions.delete()
                        stats['duplicate_transactions'] += count
                        self.stdout.write(self.style.SUCCESS(f'    ✅ 已删除 {count} 个重复事务'))

            if duplicate_count == 0:
                self.stdout.write(self.style.SUCCESS(f'    ✅ 收货单无重复事务'))
            else:
                stats['duplicate_transactions'] += duplicate_count

            # 3. 验证库存是否正确
            self.stdout.write(f'  3. 验证库存状态...')

            for item in borrow.items.filter(is_deleted=False):
                if item.conversion_quantity > 0:
                    # 检查借用仓库存
                    borrow_stock = InventoryStock.objects.filter(
                        product=item.product,
                        warehouse=borrow_wh
                    ).first()

                    # 检查主仓库存
                    main_stock = InventoryStock.objects.filter(
                        product=item.product,
                        warehouse=main_wh
                    ).first()

                    borrow_qty = borrow_stock.quantity if borrow_stock else 0
                    main_qty = main_stock.quantity if main_stock else 0

                    self.stdout.write(f'    产品: {item.product.name}')
                    self.stdout.write(f'      借用仓库存: {borrow_qty}')
                    self.stdout.write(f'      主仓库存: {main_qty}')

        # 输出汇总
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('修复完成！统计信息：'))
        self.stdout.write(f'  - 处理借用单数量: {stats["total_borrows"]}')
        self.stdout.write(f'  - 发现重复事务数量: {stats["duplicate_transactions"]}')
        self.stdout.write(f'  - 应用修复数量: {stats["fixes_applied"]}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n这是干运行模式，没有实际修复数据'))
            self.stdout.write(self.style.WARNING('如需实际修复，请运行: python manage.py fix_borrow_conversion_stock'))

    def create_transfer_transactions(self, borrow, borrow_wh, main_wh):
        """创建转采购时的库存调拨事务"""
        from decimal import Decimal

        for item in borrow.items.filter(is_deleted=False):
            if item.conversion_quantity > 0:
                convert_qty = item.conversion_quantity

                # 从借用仓出库
                InventoryTransaction.objects.create(
                    transaction_type='out',
                    product=item.product,
                    warehouse=borrow_wh,
                    quantity=-convert_qty,
                    reference_number=borrow.borrow_number,
                    notes=f'借用转采购，从借用仓调出到主仓',
                    operator=borrow.updated_by or borrow.created_by,
                    created_by=borrow.created_by
                )

                # 主仓入库
                InventoryTransaction.objects.create(
                    transaction_type='in',
                    product=item.product,
                    warehouse=main_wh,
                    quantity=convert_qty,
                    reference_number=borrow.borrow_number,
                    notes=f'借用转采购，从借用仓调入',
                    operator=borrow.updated_by or borrow.created_by,
                    created_by=borrow.created_by
                )

        self.stdout.write(self.style.SUCCESS(f'    ✅ 已为借用单 {borrow.borrow_number} 创建调拨事务'))
