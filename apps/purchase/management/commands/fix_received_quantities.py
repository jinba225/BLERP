"""
Django管理命令：修复采购订单已收货数量

使用方法:
    python manage.py fix_received_quantities                    # 修复所有订单
    python manage.py fix_received_quantities --order PO250201001  # 修复指定订单
    python manage.py fix_received_quantities --yes              # 跳过确认
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Sum


class Command(BaseCommand):
    help = "修复采购订单的已收货数量"

    def add_arguments(self, parser):
        parser.add_argument("--order", type=str, help="指定订单号（可选）", default=None)
        parser.add_argument("--yes", action="store_true", help="跳过确认直接执行")

    def handle(self, *args, **options):
        from purchase.models import PurchaseOrder, PurchaseReceiptItem

        order_number = options.get("order")
        skip_confirm = options.get("yes", False)

        if order_number:
            orders = PurchaseOrder.objects.filter(order_number=order_number, is_deleted=False)
        else:
            orders = PurchaseOrder.objects.filter(is_deleted=False).exclude(
                status__in=["draft", "cancelled"]
            )

        fixed_count = 0
        total_count = orders.count()

        self.stdout.write(self.style.SUCCESS("开始检查采购订单已收货数量..."))
        self.stdout.write("=" * 80)

        for order in orders:
            self.stdout.write(f"\n检查订单: {order.order_number}")
            self.stdout.write("-" * 80)

            updated_items = []

            for item in order.items.filter(is_deleted=False):
                # 计算该订单明细的实际已收货数量
                # 从所有已收货状态的收货单明细中汇总
                actual_received = PurchaseReceiptItem.objects.filter(
                    order_item=item, is_deleted=False, receipt__status="received"  # 只计算已确认收货的
                ).aggregate(total=Sum("received_quantity"))["total"] or Decimal("0")

                old_quantity = item.received_quantity

                # 如果数量不一致，更新
                if old_quantity != int(actual_received):
                    item.received_quantity = int(actual_received)
                    item.save(update_fields=["received_quantity", "updated_at"])
                    updated_items.append(
                        {
                            "item_id": item.id,
                            "product": item.product.name,
                            "old": old_quantity,
                            "new": int(actual_received),
                        }
                    )
                    self.stdout.write(f"  ✓ 产品: {item.product.name}")
                    self.stdout.write(f"    旧值: {old_quantity}, 新值: {int(actual_received)}")

            if updated_items:
                fixed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"\n✅ 已修复订单 {order.order_number}，共 {len(updated_items)} 个明细")
                )
            else:
                self.stdout.write(self.style.WARNING(f"\n✓ 订单 {order.order_number} 数据正确，无需修复"))

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS(f"修复完成！"))
        self.stdout.write(f"检查订单数: {total_count}")
        self.stdout.write(f"修复订单数: {fixed_count}")
        self.stdout.write("=" * 80)
