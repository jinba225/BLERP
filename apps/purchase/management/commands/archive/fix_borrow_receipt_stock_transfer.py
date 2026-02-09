"""
修复借用单转采购订单的库存调拨时机问题

业务规则：
1. 借用转采购时：不进行库存调拨
2. 采购订单收货时：才创建借用仓→主仓的调拨单

修复内容：
1. 删除转采购时创建的调拨事务（错误的时机）
2. 对于已收货的订单，重新创建正确的调拨事务（收货时）
3. 重新计算库存

使用方法:
    python manage.py fix_borrow_receipt_stock_transfer [--dry-run]
"""
from django.core.management.base import BaseCommand

from apps.inventory.models import InventoryStock, InventoryTransaction, Warehouse
from apps.purchase.models import Borrow, PurchaseReceipt


class Command(BaseCommand):
    help = "修复借用单转采购订单的库存调拨时机问题"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="只分析不执行修复",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write(self.style.WARNING("=== 干运行模式：只分析不修复 ==="))
        else:
            self.stdout.write(self.style.WARNING("=== 修复模式：将执行库存修复 ==="))

        # 获取仓库
        try:
            borrow_wh = Warehouse.get_borrow_warehouse()
        except Warehouse.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ 借用仓不存在，请先创建借用仓"))
            return

        main_wh = Warehouse.objects.filter(
            warehouse_type="main", is_active=True, is_deleted=False
        ).first()

        if not main_wh:
            self.stdout.write(self.style.ERROR("❌ 主仓不存在"))
            return

        self.stdout.write("\n仓库信息:")
        self.stdout.write(f"  - 借用仓: {borrow_wh.code} - {borrow_wh.name}")
        self.stdout.write(f"  - 主仓: {main_wh.code} - {main_wh.name}")

        # 查找所有借用单转采购的订单
        borrows = Borrow.objects.filter(
            is_deleted=False, converted_order__isnull=False
        ).select_related("converted_order")

        self.stdout.write(f"\n找到 {borrows.count()} 个借用单转采购订单的记录")

        stats = {
            "total": 0,
            "deleted_wrong_transfer": 0,
            "created_correct_transfer": 0,
            "fixed_receipts": 0,
        }

        for borrow in borrows:
            order = borrow.converted_order
            if not order or order.is_deleted:
                continue

            stats["total"] += 1
            self.stdout.write(f'\n{"=" * 60}')
            self.stdout.write(f"借用单: {borrow.borrow_number}")
            self.stdout.write(f"采购订单: {order.order_number} (状态: {order.status})")

            # 1. 删除转采购时创建的错误调拨事务
            # 识别规则：notes 包含"借用转采购"但 reference_type 不是 'purchase_receipt'
            self.stdout.write("\n1. 检查并删除转采购时的错误调拨事务...")

            wrong_transactions = InventoryTransaction.objects.filter(
                reference_number=borrow.borrow_number,
                notes__contains="借用转采购",
            ).exclude(
                reference_type="purchase_receipt"  # 排除收货时创建的正确事务
            )

            if wrong_transactions.exists():
                count = wrong_transactions.count()
                self.stdout.write(self.style.WARNING(f"   ⚠️  发现 {count} 个错误的调拨事务"))

                for t in wrong_transactions:
                    self.stdout.write(
                        f"      - {
                            t.transaction_type}: {
                            t.product.name} | {
                            t.warehouse.name} | 数量: {
                            t.quantity} | ref_type: {
                            t.reference_type}"
                    )

                if not dry_run:
                    wrong_transactions.delete()
                    stats["deleted_wrong_transfer"] += count
                    self.stdout.write(self.style.SUCCESS(f"   ✅ 已删除 {count} 个错误事务"))
            else:
                self.stdout.write(self.style.SUCCESS("   ✅ 无错误调拨事务"))

            # 2. 检查收货单
            receipts = PurchaseReceipt.objects.filter(purchase_order=order, is_deleted=False)

            if receipts.exists():
                self.stdout.write("\n2. 检查收货单...")

                for receipt in receipts:
                    self.stdout.write(f"   收货单: {receipt.receipt_number} (状态: {receipt.status})")

                    # 获取收货单的已收货明细
                    receipt_items = receipt.items.filter(received_quantity__gt=0)

                    if not receipt_items.exists():
                        self.stdout.write("      ⚠️  无已收货明细")
                        continue

                    # 检查是否已有正确的调拨事务
                    existing_transfer = InventoryTransaction.objects.filter(
                        reference_type="purchase_receipt",
                        reference_id=str(receipt.id),
                        warehouse=borrow_wh,
                        transaction_type="out",
                    )

                    if existing_transfer.exists():
                        self.stdout.write(self.style.SUCCESS("      ✅ 已有正确的调拨事务"))
                    else:
                        self.stdout.write(self.style.WARNING("      ⚠️  缺少调拨事务，需要创建"))

                        if not dry_run:
                            # 为每个收货明细创建调拨事务
                            for receipt_item in receipt_items:
                                qty = receipt_item.received_quantity
                                product = receipt_item.order_item.product

                                # 1. 从借用仓出库
                                InventoryTransaction.objects.create(
                                    transaction_type="out",
                                    product=product,
                                    warehouse=borrow_wh,
                                    quantity=-qty,
                                    reference_type="purchase_receipt",
                                    reference_id=str(receipt.id),
                                    reference_number=receipt.receipt_number,
                                    notes=f"借用转采购收货，从借用仓调出到主仓 - {order.order_number}",
                                    operator=receipt.received_by,
                                    created_by=receipt.created_by,
                                )

                                # 2. 主仓入库
                                InventoryTransaction.objects.create(
                                    transaction_type="in",
                                    product=product,
                                    warehouse=main_wh,
                                    quantity=qty,
                                    reference_type="purchase_receipt",
                                    reference_id=str(receipt.id),
                                    reference_number=receipt.receipt_number,
                                    notes=f"借用转采购收货，从借用仓调入 - {order.order_number}",
                                    operator=receipt.received_by,
                                    created_by=receipt.created_by,
                                )

                                stats["created_correct_transfer"] += 2

                            stats["fixed_receipts"] += 1
                            self.stdout.write(self.style.SUCCESS("      ✅ 已创建调拨事务"))
            else:
                self.stdout.write(self.style.SUCCESS("\n2. 订单未收货，无需修复"))

            # 3. 显示最终库存状态
            self.stdout.write("\n3. 当前库存状态:")
            for item in borrow.items.filter(is_deleted=False):
                if item.conversion_quantity > 0:
                    borrow_stock = InventoryStock.objects.filter(
                        product=item.product, warehouse=borrow_wh
                    ).first()

                    main_stock = InventoryStock.objects.filter(
                        product=item.product, warehouse=main_wh
                    ).first()

                    borrow_qty = borrow_stock.quantity if borrow_stock else 0
                    main_qty = main_stock.quantity if main_stock else 0

                    self.stdout.write(f"   {item.product.name}:")
                    self.stdout.write(f"     - 借用仓: {borrow_qty}")
                    self.stdout.write(f"     - 主仓: {main_qty}")
                    self.stdout.write(f"     - 转采购数量: {item.conversion_quantity}")

        # 输出汇总
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("修复完成！统计信息："))
        self.stdout.write(f'  - 处理借用单数量: {stats["total"]}')
        self.stdout.write(f'  - 删除错误事务数量: {stats["deleted_wrong_transfer"]}')
        self.stdout.write(f'  - 创建正确事务数量: {stats["created_correct_transfer"]}')
        self.stdout.write(f'  - 修复收货单数量: {stats["fixed_receipts"]}')

        if dry_run:
            self.stdout.write(self.style.WARNING("\n这是干运行模式，没有实际修复数据"))
            self.stdout.write(
                self.style.WARNING("如需实际修复，请运行: python manage.py fix_borrow_receipt_stock_transfer")
            )
