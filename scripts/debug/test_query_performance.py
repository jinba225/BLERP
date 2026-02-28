#!/usr/bin/env python
"""
测试查询性能 - 找出真正的瓶颈
"""

import os
import sys
import time

import django

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")

# 必须在 setup 之前设置 DEBUG
from django.conf import settings

settings.DEBUG = True

django.setup()

from django.core.paginator import Paginator
from django.db import connection, reset_queries

from apps.inventory.models import InventoryStock


def test_query_performance():
    """测试查询性能"""
    print("=" * 80)
    print("🔍 库存查询性能分析")
    print("=" * 80)

    # 测试1：低库存查询
    print("\n1️⃣ 低库存查询（使用 is_low_stock_flag）")
    print("-" * 80)

    reset_queries()
    start_time = time.time()

    stocks = (
        InventoryStock.objects.filter(is_deleted=False, is_low_stock_flag=True)
        .select_related("product", "product__category", "product__unit", "warehouse", "location")
        .order_by("-created_at")
    )

    # 执行查询
    list(stocks)  # 强制评估

    elapsed = time.time() - start_time
    query_count = len(connection.queries)

    print(f"✅ 耗时: {elapsed:.3f} 秒")
    print(f"✅ 查询次数: {query_count}")

    if query_count > 0:
        print("\n执行的 SQL 查询:")
        for i, query in enumerate(connection.queries, 1):
            print(f"\n查询 #{i}:")
            print(f"SQL: {query['sql'][:200]}...")
            print(f"耗时: {query['time']} 秒")

    # 测试2：分页查询
    print("\n\n2️⃣ 分页查询")
    print("-" * 80)

    reset_queries()
    start_time = time.time()

    stocks = (
        InventoryStock.objects.filter(is_deleted=False)
        .select_related("product", "product__category", "product__unit", "warehouse", "location")
        .order_by("-created_at")
    )

    paginator = Paginator(stocks, 20)
    page_obj = paginator.get_page(1)

    # 访问分页对象
    list(page_obj)

    elapsed = time.time() - start_time
    query_count = len(connection.queries)

    print(f"✅ 耗时: {elapsed:.3f} 秒")
    print(f"✅ 查询次数: {query_count}")

    if query_count > 0:
        print("\n执行的 SQL 查询:")
        for i, query in enumerate(connection.queries, 1):
            print(f"\n查询 #{i}:")
            print(f"SQL: {query['sql'][:200]}...")
            print(f"耗时: {query['time']} 秒")

    # 测试3：检查是否有 N+1 查询
    print("\n\n3️⃣ 检查 N+1 查询")
    print("-" * 80)

    reset_queries()
    start_time = time.time()

    stocks = (
        InventoryStock.objects.filter(is_deleted=False)
        .select_related("product", "product__category", "product__unit", "warehouse", "location")
        .order_by("-created_at")
    )

    paginator = Paginator(stocks, 20)
    page_obj = paginator.get_page(1)

    # 模拟模板访问
    for stock in page_obj:
        _ = stock.product.code
        _ = stock.product.name
        _ = stock.product.category.name if stock.product.category else None
        _ = stock.product.unit.symbol if stock.product.unit else None
        _ = stock.warehouse.name
        _ = stock.location.name if stock.location else None
        _ = stock.quantity
        _ = stock.available_quantity  # 计算
        _ = stock.reserved_quantity
        _ = stock.cost_price
        _ = stock.is_low_stock  # 访问属性

    elapsed = time.time() - start_time
    query_count = len(connection.queries)

    print(f"✅ 耗时: {elapsed:.3f} 秒")
    print(f"✅ 查询次数: {query_count}")
    print(f"⚠️  如果查询次数 > 1，说明存在 N+1 问题！")

    if query_count > 0:
        print("\n执行的 SQL 查询:")
        for i, query in enumerate(connection.queries, 1):
            print(f"\n查询 #{i}:")
            print(f"SQL: {query['sql'][:300]}...")
            print(f"耗时: {query['time']} 秒")


if __name__ == "__main__":
    try:
        test_query_performance()
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback

        traceback.print_exc()
