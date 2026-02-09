#!/usr/bin/env python
"""
使用 Django shell 测试
"""
import os
import sys
import time

import django

# 设置路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")

# 启动 Django
django.setup()

from django.conf import settings
from django.core.paginator import Paginator

# 现在导入模型
from django.db import connection

from apps.inventory.models import InventoryStock, Warehouse

# 启用查询日志
settings.DEBUG = True


def main():
    print("=" * 80)
    print("🔍 库存查询性能测试")
    print("=" * 80)

    # 测试 Warehouse 查询
    print("\n测试1: Warehouse 查询")
    print("-" * 80)
    start = time.time()
    warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
    list(warehouses)
    elapsed = time.time() - start
    print(f"✅ Warehouse 查询耗时: {elapsed:.3f} 秒")
    print(f"✅ 查询次数: {len(connection.queries)}")
    connection.queries.clear()

    # 测试库存查询
    print("\n测试2: 库存列表查询")
    print("-" * 80)
    start = time.time()

    stocks = (
        InventoryStock.objects.filter(is_deleted=False)
        .select_related("product", "product__category", "product__unit", "warehouse", "location")
        .order_by("-created_at")
    )

    paginator = Paginator(stocks, 20)
    page_obj = paginator.get_page(1)

    # 模拟模板访问
    for stock in page_obj:
        _ = stock.product.name
        _ = stock.is_low_stock

    elapsed = time.time() - start
    print(f"✅ 库存查询耗时: {elapsed:.3f} 秒")
    print(f"✅ 查询次数: {len(connection.queries)}")

    # 显示所有查询
    if connection.queries:
        print("\n执行的 SQL:")
        for i, q in enumerate(connection.queries, 1):
            print(f"{i}. {q['sql'][:150]}... ({q['time']}s)")


if __name__ == "__main__":
    main()
