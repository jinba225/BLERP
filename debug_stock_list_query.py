#!/usr/bin/env python
"""
调试库存列表查询性能
"""
import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_erp.settings')
django.setup()

from django.db import connection, reset_queries
from django.db.models import F, Sum
from decimal import Decimal
from apps.inventory.models import InventoryStock

# 启用查询记录
from django.conf import settings
settings.DEBUG = True

def debug_query():
    """调试查询性能"""

    print("=" * 80)
    print("🔍 库存列表查询性能分析")
    print("=" * 80)

    # 模拟 stock_list 视图的查询
    print("\n1️⃣ 基础查询（带 select_related）")
    print("-" * 80)

    reset_queries()
    start_time = time.time()

    stocks = InventoryStock.objects.filter(
        is_deleted=False
    ).select_related(
        'product',
        'product__category',
        'product__unit',
        'warehouse',
        'location'
    ).order_by('-created_at')

    # 模拟"低库存"过滤
    print("\n2️⃣ 添加低库存过滤条件")
    print("-" * 80)
    stocks_filtered = stocks.filter(quantity__lte=F('product__min_stock'))

    print("\n3️⃣ 执行聚合查询（计算总价值）")
    print("-" * 80)
    reset_queries()
    start_agg = time.time()

    total_value_qs = stocks_filtered.aggregate(
        total_value=Sum(F('quantity') * F('cost_price'))
    )
    total_value = total_value_qs['total_value'] or Decimal('0')

    agg_time = time.time() - start_agg
    print(f"聚合查询耗时: {agg_time:.3f} 秒")
    print(f"总价值: {total_value}")
    print(f"查询次数: {len(connection.queries)}")

    for i, query in enumerate(connection.queries, 1):
        print(f"\n查询 #{i}:")
        print(f"SQL: {query['sql'][:200]}...")
        print(f"耗时: {query['time']} 秒")

    print("\n4️⃣ 测试分页查询")
    print("-" * 80)
    from django.core.paginator import Paginator

    reset_queries()
    start_page = time.time()

    paginator = Paginator(stocks_filtered, 20)
    page_obj = paginator.get_page(1)

    page_time = time.time() - start_page
    print(f"分页查询耗时: {page_time:.3f} 秒")
    print(f"查询次数: {len(connection.queries)}")

    for i, query in enumerate(connection.queries, 1):
        print(f"\n查询 #{i}:")
        print(f"SQL: {query['sql'][:200]}...")
        print(f"耗时: {query['time']} 秒")

    total_time = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"📊 总耗时: {total_time:.3f} 秒")
    print("=" * 80)

if __name__ == '__main__':
    debug_query()
