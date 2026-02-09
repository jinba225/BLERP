"""
修复特定借用单转采购订单的关联和库存问题

使用方法:
    python manage.py fix_specific_borrow_order BO260116001 PO260116001 [--dry-run]
"""
from django.core.management.base import BaseCommand

from apps.inventory.models import InventoryStock, InventoryTransaction, Warehouse
from apps.purchase.models import Borrow, PurchaseOrder, PurchaseReceipt


class Command(BaseCommand):
    help = "修复特定借用单转采购订单的关联和库存问题"

    def add_arguments(self, parser):
        parser.add_argument(
            "borrow_number",
            type=str,
            help="借用单号",
        )
        parser.add_argument(
            "order_number",
            type=str,
            help="采购订单号",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="只分析不执行修复",
        )

    def handle(self, *args, **options):
        borrow_number = options["borrow_number"]
        order_number = options["order_number"]
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write(self.style.WARNING("=== 干运行模式：只分析不修复 ==="))
        else:
            self.stdout.write(self.style.WARNING("=== 修复模式：将执行修复 ==="))

        # 获取借用单和采购订单
        try:
            borrow = Borrow.objects.get(borrow_number=borrow_number, is_deleted=False)
        except Borrow.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ 借用单 {borrow_number} 不存在"))
            return

        try:
            order = PurchaseOrder.objects.get(order_number=order_number, is_deleted=False)
        except PurchaseOrder.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ 采购订单 {order_number} 不存在"))
            return

        self.stdout.write(f"\n借用单: {borrow.borrow_number}")
        self.stdout.write(f"  - 状态: {borrow.status}")
        self.stdout.write(f"  - 转采购订单ID: {borrow.converted_order_id}")

        self.stdout.write(f"\n采购订单: {order.order_number}")
        self.stdout.write(f"  - 状态: {order.status}")
        self.stdout.write(f"  - 来源借用单: {order.source_borrow.first()}")

        # 1. 修复关联关系
        self.stdout.write("\n1. 检查关联关系...")
        if borrow.converted_order_id is None:
            self.stdout.write(self.style.WARNING("   ⚠️  借用单未关联到采购订单"))
            if not dry_run:
                borrow.converted_order = order
                borrow.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"   ✅ 已设置关联: {borrow.borrow_number} -> {order.order_number}"
                    )
                )
        elif borrow.converted_order_id != order.id:
            self.stdout.write(
                self.style.WARNING(f"   ⚠️  借用单已关联到其他订单: {borrow.converted_order.order_number}")
            )
        else:
            self.stdout.write(self.style.SUCCESS("   ✅ 关联正确"))

        # 2. 检查转采购时的库存调拨事务
        self.stdout.write("\n2. 检查转采购时的库存调拨事务...")

        try:
            borrow_wh = Warehouse.get_borrow_warehouse()
            main_wh = Warehouse.objects.filter(
                warehouse_type="main", is_active=True, is_deleted=False
            ).first()

            if not borrow_wh:
                self.stdout.write(self.style.ERROR("   ❌ 借用仓不存在"))
                return
            if not main_wh:
                self.stdout.write(self.style.ERROR("   ❌ 主仓不存在"))
                return

            # 检查调拨事务
            transfer_out = InventoryTransaction.objects.filter(
                reference_number=borrow.borrow_number, warehouse=borrow_wh, transaction_type="out"
            )

            transfer_in = InventoryTransaction.objects.filter(
                reference_number=borrow.borrow_number, warehouse=main_wh, transaction_type="in"
            )

            if transfer_out.exists() and transfer_in.exists():
                self.stdout.write(self.style.SUCCESS("   ✅ 调拨事务存在"))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"   ⚠️  调拨事务不完整 (出库: {transfer_out.count()}, 入库: {transfer_in.count()})"
                    )
                )

                if not dry_run:
                    # 创建调拨事务
                    for item in borrow.items.filter(is_deleted=False):
                        if item.conversion_quantity > 0:
                            # 从借用仓出库
                            InventoryTransaction.objects.create(
                                transaction_type="out",
                                product=item.product,
                                warehouse=borrow_wh,
                                quantity=-item.conversion_quantity,
                                reference_number=borrow.borrow_number,
                                notes="借用转采购，从借用仓调出到主仓",
                                operator=borrow.updated_by or borrow.created_by,
                                created_by=borrow.created_by,
                            )

                            # 主仓入库
                            InventoryTransaction.objects.create(
                                transaction_type="in",
                                product=item.product,
                                warehouse=main_wh,
                                quantity=item.conversion_quantity,
                                reference_number=borrow.borrow_number,
                                notes="借用转采购，从借用仓调入",
                                operator=borrow.updated_by or borrow.created_by,
                                created_by=borrow.created_by,
                            )

                    self.stdout.write(self.style.SUCCESS("   ✅ 已创建调拨事务"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ 创建调拨事务失败: {str(e)}"))

        # 3. 检查收货时的重复库存事务
        self.stdout.write("\n3. 检查收货时的重复库存事务...")

        receipts = PurchaseReceipt.objects.filter(purchase_order=order, is_deleted=False)
        for receipt in receipts:
            self.stdout.write(f"   收货单: {receipt.receipt_number}")

            receipt_transactions = InventoryTransaction.objects.filter(
                reference_type="purchase_receipt",
                reference_id=str(receipt.id),
                transaction_type="in",
            )

            if receipt_transactions.exists():
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  发现 {receipt_transactions.count()} 个重复事务")
                )

                if not dry_run:
                    count, _ = receipt_transactions.delete()
                    self.stdout.write(self.style.SUCCESS(f"   ✅ 已删除 {count} 个重复事务"))
            else:
                self.stdout.write(self.style.SUCCESS("   ✅ 无重复事务"))

        # 4. 显示当前库存状态
        self.stdout.write("\n4. 当前库存状态:")
        for item in borrow.items.filter(is_deleted=False):
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

        if dry_run:
            self.stdout.write(self.style.WARNING("\n这是干运行模式，没有实际修复数据"))
            self.stdout.write(
                self.style.WARNING(
                    "如需实际修复，请运行: python manage.py fix_specific_borrow_order BO260116001 PO260116001"
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("\n修复完成！"))
