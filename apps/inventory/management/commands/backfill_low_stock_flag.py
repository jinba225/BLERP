"""
回填库存的 is_low_stock_flag 字段
运行方式：python manage.py backfill_low_stock_flag
"""
from django.core.management.base import BaseCommand
from apps.inventory.models import InventoryStock


class Command(BaseCommand):
    help = '回填库存的 is_low_stock_flag 字段'

    def handle(self, *args, **options):
        """执行回填操作"""
        self.stdout.write('开始回填库存的 is_low_stock_flag 字段...')

        stocks = InventoryStock.objects.filter(is_deleted=False)
        total_count = stocks.count()
        updated_count = 0

        self.stdout.write(f'共有 {total_count} 条库存记录需要处理')

        for stock in stocks:
            # 保存会触发 save() 方法，自动计算 is_low_stock_flag
            stock.save(update_fields=['is_low_stock_flag'])
            updated_count += 1

            if updated_count % 100 == 0:
                self.stdout.write(f'已处理 {updated_count}/{total_count} 条记录...')

        self.stdout.write(
            self.style.SUCCESS(f'✅ 成功回填 {updated_count} 条记录！')
        )
