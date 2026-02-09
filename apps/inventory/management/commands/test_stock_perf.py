"""
测试库存查询性能的管理命令
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.paginator import Paginator
from apps.inventory.models import InventoryStock, Warehouse
from django.conf import settings
import time


class Command(BaseCommand):
    help = '测试库存查询性能'

    def handle(self, *args, **options):
        # 启用查询日志
        settings.DEBUG = True

        self.stdout.write("=" * 80)
        self.stdout.write("🔍 库存查询性能测试")
        self.stdout.write("=" * 80)

        # 测试 Warehouse 查询
        self.stdout.write("\n测试1: Warehouse 查询")
        self.stdout.write("-" * 80)
        start = time.time()
        warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
        list(warehouses)
        elapsed = time.time() - start
        self.stdout.write(f"✅ Warehouse 查询耗时: {elapsed:.3f} 秒")
        self.stdout.write(f"✅ 查询次数: {len(connection.queries)}")
        connection.queries.clear()

        # 测试库存查询
        self.stdout.write("\n测试2: 库存列表查询")
        self.stdout.write("-" * 80)
        start = time.time()

        stocks = InventoryStock.objects.filter(
            is_deleted=False
        ).select_related(
            'product',
            'product__category',
            'product__unit',
            'warehouse',
            'location'
        ).order_by('-created_at')

        paginator = Paginator(stocks, 20)
        page_obj = paginator.get_page(1)

        # 模拟模板访问
        for stock in page_obj:
            _ = stock.product.name
            _ = stock.is_low_stock

        elapsed = time.time() - start
        self.stdout.write(f"✅ 库存查询耗时: {elapsed:.3f} 秒")
        self.stdout.write(f"✅ 查询次数: {len(connection.queries)}")

        # 显示所有查询
        if connection.queries:
            self.stdout.write("\n执行的 SQL:")
            for i, q in enumerate(connection.queries, 1):
                self.stdout.write(f"{i}. {q['sql'][:150]}... ({q['time']}s)")
