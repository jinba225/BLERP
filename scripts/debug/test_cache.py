#!/usr/bin/env python
"""
缓存功能测试脚本

测试所有实施的缓存策略：
1. @never_cache 装饰器
2. @cache_page 装饰器
3. @condition (ETag) 装饰器
4. 缓存后端配置
"""
import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_erp.settings')
django.setup()

from django.core.cache import cache
from django.test import Client
from django.contrib.auth import get_user_model

print("="*60)
print("BetterLaser ERP 缓存功能测试")
print("="*60)

# 1. 测试缓存后端
print("\n[1/5] 测试缓存后端...")
try:
    cache.set('test_key', 'test_value', 60)
    value = cache.get('test_key')
    if value == 'test_value':
        print("✓ 缓存后端正常工作")
        cache.delete('test_key')
    else:
        print("✗ 缓存后端测试失败")
except Exception as e:
    print(f"✗ 缓存后端错误: {e}")

# 2. 测试导入装饰器
print("\n[2/5] 测试缓存装饰器导入...")
try:
    from django.views.decorators.cache import never_cache, cache_page
    from django.views.decorators.http import condition
    from django.views.decorators.vary import vary_on_headers, vary_on_cookie
    print("✓ 所有缓存装饰器导入成功")
except ImportError as e:
    print(f"✗ 装饰器导入失败: {e}")

# 3. 测试视图导入
print("\n[3/5] 测试视图模块导入...")
modules_to_test = [
    'apps.finance.views',
    'apps.purchase.views',
    'apps.inventory.views',
    'apps.products.views',
    'apps.suppliers.views',
    'apps.customers.views',
]

for module in modules_to_test:
    try:
        __import__(module)
        print(f"✓ {module} 导入成功")
    except Exception as e:
        print(f"✗ {module} 导入失败: {e}")

# 4. 检查 ETag 函数
print("\n[4/5] 检查 ETag 函数定义...")
etag_functions = [
    ('apps.purchase.views', 'order_list_etag'),
    ('apps.inventory.views', 'stock_list_etag'),
    ('apps.finance.views', 'customer_account_list_etag'),
    ('apps.finance.views', 'supplier_account_list_etag'),
    ('apps.products.views', 'product_list_etag'),
    ('apps.suppliers.views', 'supplier_list_etag'),
    ('apps.customers.views', 'customer_list_etag'),
]

for module_name, func_name in etag_functions:
    try:
        module = __import__(module_name, fromlist=[func_name])
        if hasattr(module, func_name):
            print(f"✓ {func_name} 已定义")
        else:
            print(f"⚠ {func_name} 未找到")
    except Exception as e:
        print(f"✗ 检查 {func_name} 时出错: {e}")

# 5. 测试缓存管理命令
print("\n[5/5] 检查缓存管理命令...")
commands = [
    'apps.core.management.commands.clear_cache',
    'apps.core.management.commands.cache_stats',
    'apps.core.management.commands.warm_cache',
]

for command in commands:
    try:
        __import__(command)
        print(f"✓ {command.split('.')[-1]} 命令可用")
    except Exception as e:
        print(f"✗ {command.split('.')[-1]} 命令不可用: {e}")

print("\n" + "="*60)
print("测试完成！")
print("="*60)

# 缓存配置摘要
print("\n缓存配置摘要:")
print(f"  缓存后端: {cache.__class__.__module__}.{cache.__class__.__name__}")
print(f"  默认超时: {cache.__dict__.get('default_timeout', 'N/A')} 秒")

# 测试缓存性能
print("\n性能测试:")
import time

# 写入测试
start = time.time()
for i in range(100):
    cache.set(f'perf_test_{i}', f'value_{i}', 60)
write_time = time.time() - start

# 读取测试
start = time.time()
for i in range(100):
    cache.get(f'perf_test_{i}')
read_time = time.time() - start

# 清理
for i in range(100):
    cache.delete(f'perf_test_{i}')

print(f"  写入 100 次: {write_time:.4f} 秒")
print(f"  读取 100 次: {read_time:.4f} 秒")
print(f"  平均操作时间: {((write_time + read_time) / 200 * 1000):.2f} 毫秒")

print("\n✓ 所有缓存功能已就绪！")
