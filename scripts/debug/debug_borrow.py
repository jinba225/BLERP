#!/usr/bin/env python
"""调试借用单一键全部入库功能"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_erp.settings')
django.setup()

from apps.purchase.models import Borrow
from decimal import Decimal

print("=" * 60)
print("借用单调试信息")
print("=" * 60)

borrow = Borrow.objects.filter(pk=6).select_related('supplier').first()

if not borrow:
    print("\n❌ 借用单 #6 不存在或已删除")
    exit(1)

print(f"\n借用单号: {borrow.borrow_number}")
print(f"状态: {borrow.status}")
print(f"供应商: {borrow.supplier.name}")
print(f"借用日期: {borrow.borrow_date}")
print(f"是否删除: {borrow.is_deleted}")

# 检查状态是否允许入库
if borrow.status != "borrowed":
    print(f"\n⚠️  状态检查失败: 当前状态为 '{borrow.status}'，需要 'borrowed' 状态才能入库")
    print("建议：请检查借用单是否已经完成或其他状态")
else:
    print(f"\n✅ 状态检查通过: 可以进行入库操作")

# 检查明细
print("\n借用明细:")
print("-" * 60)
items = borrow.items.filter(is_deleted=False)
total_borrowable = Decimal('0')

for item in items:
    print(f"\n产品: {item.product.name} ({item.product.code})")
    print(f"  借用数量: {item.quantity}")
    print(f"  累计已借用: {item.borrowed_quantity}")
    print(f"  已归还: {item.returned_quantity}")
    print(f"  可借用数量: {item.borrowable_quantity}")
    total_borrowable += item.borrowable_quantity

print("\n" + "=" * 60)
print(f"总可借用数量: {total_borrowable}")
print("=" * 60)

if total_borrowable == 0:
    print("\n⚠️  没有可入库的产品")
    print("所有产品已经全部入库，无需再次入库")
else:
    print(f"\n✅ 可以入库 {total_borrowable} 件产品")

# 模拟入库操作（不实际执行）
print("\n" + "=" * 60)
print("模拟入库操作（不实际执行）")
print("=" * 60)
print(f"✓ 将调用: borrow.confirm_borrow_receipt(request.user, None)")
print(f"✓ 将添加消息: 借用单 {borrow.borrow_number} 已全部入库成功！共入库 {total_borrowable} 件产品")
print(f"✓ 将重定向到: /purchase/borrows/{borrow.pk}/")
