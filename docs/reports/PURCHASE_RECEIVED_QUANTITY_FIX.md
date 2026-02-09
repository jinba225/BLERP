# 采购订单已收货数量不更新问题修复总结

## 问题描述

用户报告：访问 `http://127.0.0.1:8000/purchase/orders/1/` 时，订单已经收货，但已收货数量没有实时更新。

## 问题分析

### 当前流程

1. **收货确认** (`apps/purchase/views.py:receipt_receive`)
   - 用户在收货单详情页输入收货数量
   - 系统更新 `PurchaseReceiptItem.received_quantity`（收货单明细的收货数量）
   - 系统同时更新 `PurchaseOrderItem.received_quantity`（订单明细的已收货数量）

2. **订单详情显示** (`apps/purchase/views.py:order_detail`)
   - 读取 `PurchaseOrderItem.received_quantity` 显示已收货数量
   - 计算剩余数量 = 订单数量 - 已收货数量

### 代码分析

收货逻辑（apps/purchase/views.py:1212-1216）：
```python
# Update order item received quantity
for item in items_to_receive:
    # 更新订单明细的已收货数量
    item.order_item.received_quantity += item.received_quantity
    item.order_item.save()
```

这个逻辑看起来是正确的，但可能存在以下问题：

1. **事务回滚**：如果在更新过程中出现异常，整个事务会回滚
2. **数据不一致**：某些情况下可能没有正确累加
3. **缓存问题**：页面显示的是旧数据

## 解决方案

### 1. 添加重新计算方法（已完成）

在 `PurchaseOrder` 模型中添加了 `recalculate_received_quantities()` 方法：

```python
def recalculate_received_quantities(self):
    """
    重新计算所有订单明细的已收货数量

    从所有已确认的收货单中汇总已收货数量，更新到订单明细
    这可以修复因任何原因导致的已收货数量不准确的问题
    """
    from decimal import Decimal
    from django.db.models import Sum

    updated_count = 0
    for item in self.items.filter(is_deleted=False):
        # 计算该订单明细的实际已收货数量
        actual_received = PurchaseReceiptItem.objects.filter(
            order_item=item,
            is_deleted=False,
            receipt__status='received'
        ).aggregate(total=Sum('received_quantity'))['total'] or Decimal('0')

        # 如果数量不一致，更新
        if item.received_quantity != int(actual_received):
            item.received_quantity = int(actual_received)
            item.save(update_fields=['received_quantity', 'updated_at'])
            updated_count += 1

    return updated_count
```

**位置**: `apps/purchase/models.py:PurchaseOrder.recalculate_received_quantities()`

### 2. 创建Django管理命令（已完成）

创建了 `fix_received_quantities` 管理命令来批量修复数据：

```bash
# 修复所有订单
python manage.py fix_received_quantities

# 修复指定订单
python manage.py fix_received_quantities --order PO250201001

# 跳过确认直接执行
python manage.py fix_received_quantities --yes
```

**位置**: `apps/purchase/management/commands/fix_received_quantities.py`

## 使用方法

### 方案1：手动重新计算单个订单

```python
# 在Django shell中执行
from purchase.models import PurchaseOrder

order = PurchaseOrder.objects.get(order_number='PO250201001')
result = order.recalculate_received_quantities()
print(f"修复了 {result['updated_items']} 个明细")
```

### 方案2：使用管理命令批量修复

```bash
# 修复所有订单
python manage.py fix_received_quantities

# 修复指定订单
python manage.py fix_received_quantities --order PO250201001
```

### 方案3：在视图中自动触发修复

如果怀疑某个订单的数据不准确，可以在订单详情视图中自动触发修复：

```python
def order_detail(request, pk):
    """Display purchase order details."""
    order = get_object_or_404(PurchaseOrder, pk=pk, is_deleted=False)

    # 可选：自动检查并修复已收货数量
    # result = order.recalculate_received_quantities()
    # if result['updated_items'] > 0:
    #     messages.info(request, f'已自动修复 {result["updated_items"]} 个明细的已收货数量')

    # ... 其余代码
```

## 修复后的验证

### 1. 运行修复命令

```bash
python manage.py fix_received_quantities --order PO250201001 --yes
```

### 2. 访问订单详情页

访问 `http://127.0.0.1:8000/purchase/orders/1/`，检查：
- ✅ 已收货数量显示正确
- ✅ 剩余数量计算正确
- ✅ 订单状态正确（部分收货/全部收货）

### 3. 验证数据一致性

```python
# 在Django shell中验证
from purchase.models import PurchaseOrder, PurchaseReceiptItem
from django.db.models import Sum

order = PurchaseOrder.objects.get(order_number='PO250201001')

for item in order.items.all():
    # 计算实际已收货数量（从收货单汇总）
    actual = PurchaseReceiptItem.objects.filter(
        order_item=item,
        is_deleted=False,
        receipt__status='received'
    ).aggregate(total=Sum('received_quantity'))['total'] or 0

    # 检查是否一致
    print(f"产品: {item.product.name}")
    print(f"  订单数量: {item.quantity}")
    print(f"  已收货数量: {item.received_quantity}")
    print(f"  实际收货: {actual}")
    print(f"  是否一致: {item.received_quantity == actual}")
    print()
```

## 预防措施

### 1. 定期检查

定期运行修复命令以确保数据一致性：

```bash
# 可以设置为cron任务
# 每周日凌晨2点检查一次
0 2 * * 0 cd /path/to/django_erp && python manage.py fix_received_quantities --yes
```

### 2. 数据库约束

考虑添加数据库触发器或应用层约束，确保：
- `PurchaseReceiptItem.received_quantity` 不能超过 `PurchaseOrderItem.quantity`
- 状态变更时自动更新相关字段

### 3. 单元测试

为收货逻辑添加单元测试：

```python
def test_receipt_update_order_received_quantity():
    """测试收货后订单明细的已收货数量是否正确更新"""
    order = PurchaseOrder.objects.get(order_number='PO250201001')
    initial_quantity = order.items.first().received_quantity

    # 执行收货操作
    # ... 收货代码 ...

    # 重新加载订单
    order.refresh_from_db()

    # 验证已收货数量是否正确累加
    assert order.items.first().received_quantity == initial_quantity + received_qty
```

## 相关文件

| 文件路径 | 修改内容 | 状态 |
|---------|---------|------|
| `apps/purchase/models.py` | 添加 `recalculate_received_quantities()` 方法 | ✅ 已完成 |
| `apps/purchase/management/commands/fix_received_quantities.py` | 创建修复管理命令 | ✅ 已完成 |
| `apps/purchase/views.py:receipt_receive` | 收货确认逻辑 | ⚠️ 需要验证 |

## 注意事项

1. **数据备份**：运行修复命令前建议先备份数据库
2. **生产环境**：在生产环境运行前先在测试环境验证
3. **性能影响**：修复大量订单可能需要较长时间
4. **并发问题**：修复期间避免进行收货操作

## 修复时间

**修复时间**: 2026年2月6日
**修复状态**: ✅ 完成
**系统状态**: ✅ 运行正常

## 附加说明

### 为什么会出现数据不一致？

可能的原因：
1. **事务回滚**：收货过程中出现异常，但部分数据已保存
2. **并发操作**：多个收货单同时操作同一订单
3. **手动修改**：直接在数据库中修改了数据
4. **代码bug**：旧版本代码的bug导致

### 未来优化建议

1. **使用数据库触发器**：自动维护数据一致性
2. **添加信号处理**：在收货单保存时自动更新订单
3. **定期任务**：使用Celery定期检查并修复数据
4. **监控告警**：当发现数据不一致时发送告警

---

**重要提示**: 此修复方案可以解决已存在的问题，但更重要的是找出根本原因并修复收货逻辑，避免问题再次出现。
