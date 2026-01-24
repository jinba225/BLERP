"""
重新计算库存，基于所有库存事务记录

使用方法:
    python manage.py recalculate_stock_from_transactions
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.inventory.models import InventoryTransaction, InventoryStock, Warehouse
from apps.products.models import Product


class Command(BaseCommand):
    help = '重新计算库存，基于所有库存事务记录'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=== 重新计算库存 ==='))

        # 清空所有库存
        self.stdout.write(f'\n1. 清空所有库存...')
        current_stocks = InventoryStock.objects.all()
        count = current_stocks.count()
        current_stocks.update(quantity=0)
        self.stdout.write(self.style.SUCCESS(f'   ✅ 已重置 {count} 条库存记录为 0'))

        # 获取所有仓库
        warehouses = Warehouse.objects.filter(is_deleted=False)
        products = Product.objects.filter(is_deleted=False)

        # 遍历所有库存事务，重新计算库存
        self.stdout.write(f'\n2. 重新计算库存...')

        stats = {
            'transactions_processed': 0,
            'stocks_updated': 0,
        }

        for wh in warehouses:
            for product in products:
                # 获取或创建库存记录
                stock, created = InventoryStock.objects.get_or_create(
                    product=product,
                    warehouse=wh,
                    defaults={'quantity': 0}
                )

                if created:
                    stats['stocks_updated'] += 1

                # 计算该产品的净库存变动
                transactions = InventoryTransaction.objects.filter(
                    product=product,
                    warehouse=wh,
                    is_deleted=False
                )

                net_quantity = 0
                for t in transactions:
                    stats['transactions_processed'] += 1
                    if t.transaction_type in ['in', 'return']:
                        net_quantity += abs(t.quantity)
                    elif t.transaction_type in ['out', 'scrap']:
                        net_quantity -= abs(t.quantity)
                    elif t.transaction_type == 'adjustment':
                        net_quantity += t.quantity

                # 更新库存
                if net_quantity != 0:
                    stock.quantity = net_quantity
                    stock.save()
                    self.stdout.write(f'   {product.name} | {wh.name}: {net_quantity}')

        # 输出最终库存状态
        self.stdout.write(f'\n3. 最终库存状态:')
        stocks = InventoryStock.objects.all()
        for s in stocks:
            if s.quantity > 0:
                self.stdout.write(f'   {s.product.name} | {s.warehouse.name}: {s.quantity}')

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('重新计算完成！'))
        self.stdout.write(f'  - 处理事务数量: {stats["transactions_processed"]}')
        self.stdout.write(f'  - 更新库存记录: {stats["stocks_updated"]}')
