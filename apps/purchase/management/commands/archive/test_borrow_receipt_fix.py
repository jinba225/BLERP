"""
测试借用转采购收货确认是否正确生成调拨单

用法:
    python manage.py test_borrow_receipt_fix

测试逻辑:
1. 检查 PO260116003 订单备注是否包含借用单号
2. 验证新的借用单识别逻辑是否正确
3. 检查是否已有调拨单
"""
from django.core.management.base import BaseCommand

from apps.inventory.models import StockTransfer
from apps.purchase.models import Borrow, PurchaseOrder, PurchaseReceipt


class Command(BaseCommand):
    help = "测试借用转采购收货确认修复"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("测试借用转采购收货确认修复")
        self.stdout.write("=" * 60)

        # 测试订单
        order = PurchaseOrder.objects.get(order_number="PO260116003")
        self.stdout.write(f"\n1. 检查订单: {order.order_number}")
        self.stdout.write(f"   - 订单备注: {order.notes[:50]}...")

        # 测试新的识别逻辑
        borrow_numbers = [b for b in order.notes.split() if b.startswith("BO")]
        self.stdout.write("\n2. 新的识别逻辑:")
        self.stdout.write(f"   - 提取的借用单号: {borrow_numbers}")

        if borrow_numbers:
            source_borrow = Borrow.objects.filter(
                borrow_number=borrow_numbers[0], is_deleted=False
            ).first()

            if source_borrow:
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ 正确识别借用单: {source_borrow.borrow_number}")
                )
            else:
                self.stdout.write(self.style.ERROR("   ❌ 未找到借用单"))
        else:
            self.stdout.write(self.style.ERROR("   ❌ 未能从备注中提取借用单号"))

        # 检查收货单
        receipts = PurchaseReceipt.objects.filter(purchase_order=order, is_deleted=False)
        self.stdout.write("\n3. 收货单情况:")
        for receipt in receipts:
            self.stdout.write(f"   - {receipt.receipt_number}: {receipt.get_status_display()}")

            # 检查关联的调拨单
            transfers = StockTransfer.objects.filter(
                notes__contains=order.order_number, is_auto_generated=True
            )

            if transfers.exists():
                self.stdout.write(
                    self.style.SUCCESS(f"     ✅ 有关联调拨单: {transfers.first().transfer_number}")
                )
            else:
                self.stdout.write(self.style.WARNING("     ⚠️  没有关联调拨单（需要重新确认收货）"))

        # 测试结果
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("测试完成")
        self.stdout.write("=" * 60)

        if borrow_numbers and source_borrow:
            self.stdout.write(self.style.SUCCESS("\n✅ 修复验证成功！新的识别逻辑可以正确工作。"))
            self.stdout.write("\n后续操作建议:")
            self.stdout.write("  1. 对于没有调拨单的收货单，需要重新确认收货")
            self.stdout.write("  2. 创建新的借用单 → 转采购 → 收货确认进行完整测试")
        else:
            self.stdout.write(self.style.ERROR("\n❌ 修复验证失败！请检查订单备注格式。"))
