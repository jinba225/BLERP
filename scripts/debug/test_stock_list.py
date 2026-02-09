#!/usr/bin/env python3
"""
测试库存列表页面的查询逻辑
模拟 stock_list 视图的完整查询
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_erp.settings')
django.setup()

from inventory.models import InventoryStock, Warehouse
from products.models import ProductCategory
from django.core.paginator import Paginator
from django.db.models import Q

print('='*70)
print('🔍 模拟 stock_list 视图查询')
print('='*70)

# 1. 基础查询
print('\n步骤1: 基础查询')
stocks = InventoryStock.objects.filter(
    is_deleted=False
).select_related(
    'product',
    'product__category',
    'product__unit',
    'warehouse',
    'location'
).order_by('-created_at')

print(f'  查询结果数量: {stocks.count()}')

for stock in stocks:
    print(f'    - [{stock.warehouse.name}] {stock.product.name}: {stock.quantity}')

# 2. 筛选测试
print('\n步骤2: 模拟各种筛选条件')

# 2.1 搜索测试
search = '激光'
if search:
    filtered = stocks.filter(
        Q(product__name__icontains=search) |
        Q(product__code__icontains=search) |
        Q(product__barcode__icontains=search)
    )
    print(f'  搜索 "{search}": {filtered.count()} 条')

# 2.2 仓库筛选
warehouse_id = ''  # 空表示不筛选
if warehouse_id:
    filtered = stocks.filter(warehouse_id=warehouse_id)
    print(f'  仓库ID={warehouse_id}: {filtered.count()} 条')
else:
    print(f'  仓库筛选: 未启用（显示所有仓库）')

# 2.3 分类筛选
category_id = ''
if category_id:
    filtered = stocks.filter(product__category_id=category_id)
    print(f'  分类ID={category_id}: {filtered.count()} 条')
else:
    print(f'  分类筛选: 未启用（显示所有分类）')

# 2.4 库存状态筛选
stock_status = ''
if stock_status == 'low':
    filtered = [s for s in stocks if s.is_low_stock]
    print(f'  低库存: {len(filtered)} 条')
elif stock_status == 'out':
    filtered = stocks.filter(quantity=0)
    print(f'  缺货: {filtered.count()} 条')
elif stock_status == 'normal':
    filtered = [s for s in stocks if not s.is_low_stock and s.quantity > 0]
    print(f'  正常: {len(filtered)} 条')
else:
    print(f'  库存状态筛选: 未启用（显示所有状态）')

# 3. 分页测试
print('\n步骤3: 分页测试')
paginator = Paginator(stocks, 20)  # 每页20条
print(f'  总记录数: {paginator.count}')
print(f'  总页数: {paginator.num_pages}')

# 获取第一页
page_obj = paginator.get_page(1)
print(f'  第1页记录数: {len(page_obj)}')
print(f'  第1页内容:')
for stock in page_obj:
    print(f'    - [{stock.warehouse.name}] {stock.product.name}: {stock.quantity}')

# 4. 获取筛选选项
print('\n步骤4: 筛选选项')
warehouses = Warehouse.objects.filter(is_deleted=False, is_active=True)
categories = ProductCategory.objects.filter(is_deleted=False)

print(f'  仓库数量: {warehouses.count()}')
for wh in warehouses:
    print(f'    - {wh.name} (ID:{wh.id}, 代码:{wh.code})')

print(f'  分类数量: {categories.count()}')

# 5. 计算总价值
print('\n步骤5: 计算总价值')
total_value = sum(
    stock.quantity * stock.cost_price
    for stock in stocks
)
print(f'  库存总价值: ¥{total_value:.2f}')

# 6. 最终上下文
print('\n步骤6: 模拟传递给模板的上下文')
context = {
    'page_obj': page_obj,
    'search': '',
    'warehouse_id': '',
    'category_id': '',
    'stock_status': '',
    'warehouses': warehouses,
    'categories': categories,
    'total_count': paginator.count,
    'total_value': total_value,
}

print(f'  page_obj 数量: {len(context["page_obj"])}')
print(f'  total_count: {context["total_count"]}')
print(f'  total_value: ¥{context["total_value"]:.2f}')
print(f'  warehouses 选项: {context["warehouses"].count()} 个')
print(f'  categories 选项: {context["categories"].count()} 个')

# 7. 诊断
print('\n' + '='*70)
print('📊 诊断结论')
print('='*70)

if paginator.count == 0:
    print('❌ 库存列表为空！')
    print('\n可能原因:')
    print('  1. 所有库存记录都被标记为已删除 (is_deleted=True)')
    print('  2. 确实没有任何库存记录')
else:
    print(f'✅ 库存列表正常，共有 {paginator.count} 条记录')
    print('\n库存明细:')
    for stock in stocks:
        print(f'  [{stock.warehouse.name}] {stock.product.name}: {stock.quantity}')

    print('\n💡 如果网页上不显示，请检查:')
    print('  1. 是否有前端筛选条件生效')
    print('  2. 浏览器是否缓存了旧页面')
    print('  3. 网络请求是否成功（检查浏览器开发者工具）')
    print('  4. 是否有 JavaScript 错误（检查控制台）')

print('\n建议操作:')
print('  1. 清除浏览器缓存 (Ctrl+Shift+Delete)')
print('  2. 硬刷新页面 (Ctrl+Shift+R)')
print('  3. 检查 URL 是否有筛选参数')
print('  4. 使用无痕模式测试')
print('  5. 检查浏览器开发者工具的 Network 面板')
print()
