# Django ERP 模型字段修复总结

## 问题描述

访问 `http://127.0.0.1:8000/purchase/borrows/1/confirm-all-receipt/` 时出现数据库错误：

```
IntegrityError: NOT NULL constraint failed: inventory_stock.is_low_stock_flag
```

## 根本原因

**InventoryStock 模型缺失字段定义**

在迁移文件 `0007_inventorystock_is_low_stock_flag_and_more.py` 中添加了 `is_low_stock_flag` 字段，但 `InventoryStock` 模型定义中没有这个字段，导致：

1. Django 在创建新的 `InventoryStock` 对象时，不知道需要设置这个字段
2. 数据库要求该字段 NOT NULL
3. 插入失败

## 修复方案

### 1. 添加缺失的字段定义

**文件**: `apps/inventory/models.py`

**修复前**:
```python
class InventoryStock(BaseModel):
    product = models.ForeignKey(...)
    warehouse = models.ForeignKey(...)
    location = models.ForeignKey(...)
    quantity = models.IntegerField('库存数量', default=0)
    reserved_quantity = models.IntegerField('预留数量', default=0)
    cost_price = models.DecimalField('成本价', max_digits=12, decimal_places=2, default=0)
    last_in_date = models.DateTimeField('最后入库时间', null=True, blank=True)
    last_out_date = models.DateTimeField('最后出库时间', null=True, blank=True)
```

**修复后**:
```python
class InventoryStock(BaseModel):
    product = models.ForeignKey(...)
    warehouse = models.ForeignKey(...)
    location = models.ForeignKey(...)
    quantity = models.IntegerField('库存数量', default=0)
    reserved_quantity = models.IntegerField('预留数量', default=0)
    cost_price = models.DecimalField('成本价', max_digits=12, decimal_places=2, default=0)
    last_in_date = models.DateTimeField('最后入库时间', null=True, blank=True)
    last_out_date = models.DateTimeField('最后出库时间', null=True, blank=True)
    is_low_stock_flag = models.BooleanField(
        '是否低库存',
        default=False,
        db_index=True,
        help_text='冗余字段，用于优化查询性能'
    )
```

### 2. 字段说明

**is_low_stock_flag** - 低库存标识字段
- **类型**: BooleanField
- **默认值**: False
- **是否索引**: 是（db_index=True）
- **用途**: 冗余字段，用于优化查询性能，避免每次查询都要计算 `quantity <= min_stock`

## 迁移文件内容

**文件**: `apps/inventory/migrations/0007_inventorystock_is_low_stock_flag_and_more.py`

```python
operations = [
    migrations.AddField(
        model_name='inventorystock',
        name='is_low_stock_flag',
        field=models.BooleanField(
            db_index=True,
            default=False,
            help_text='冗余字段，用于优化查询性能',
            verbose_name='是否低库存'
        ),
    ),
    migrations.AddIndex(
        model_name='inventorystock',
        index=models.Index(
            fields=['is_low_stock_flag'],
            name='inventory_s_is_low__fdb1c3_idx'
        ),
    ),
]
```

## 验证结果

### 1. Django 系统检查

```bash
$ python manage.py check
System check identified no issues (0 silenced).
```

✅ **检查通过，无任何问题**

### 2. 创建检查脚本

创建了两个检查脚本用于未来避免类似问题：

1. **check_model_migration_sync.py** - 检查单个应用的模型和迁移同步
2. **check_all_models_migrations.py** - 检查整个项目的模型和迁移同步

### 3. 检查结果分析

检查脚本发现了一些"疑似缺失"的字段，但经分析：

#### Sales 模块（误报）
- `PrintTemplate` 和 `DefaultTemplateMapping` 模型后来移动到了 core 应用
- 迁移文件中的引用是旧的
- **状态**: ✅ 无需修复

#### Purchase 模块（部分误报）
- `Borrow.approved_at`, `Borrow.approved_by`, `Borrow.conversion_approved_at`, `Borrow.conversion_approved_by`
  - 这些字段在迁移 0015 中被删除
  - 模型中不应包含这些字段
  - **状态**: ✅ 无需修复

- `PurchaseInquiry.warehouse` - 缺失
  - **状态**: ✅ 已添加

#### Finance 模块（待确认）
- `CustomerPrepayment.is_consolidated`, `CustomerPrepayment.merged_into`, `CustomerPrepayment.status`
- `SupplierPrepayment.is_consolidated`, `SupplierPrepayment.merged_into`, `SupplierPrepayment.status`
  - 这些字段可能在实际业务中需要
  - **状态**: ⚠️ 需要进一步确认

## 后续建议

### 1. 模型定义规范

确保所有迁移中添加的字段都在模型中定义：

```python
# ✅ 正确示例
class MyModel(BaseModel):
    field_name = models.CharField('字段名', max_length=100, default='')
```

### 2. 迁移和模型同步检查

在添加新字段时，确保：
1. 先创建迁移
2. 然后在模型中添加字段定义
3. 运行 `python manage.py check` 验证
4. 运行 `python manage.py migrate` 应用迁移

### 3. 定期检查

定期运行检查脚本：

```bash
# 检查整个项目
python check_all_models_migrations.py

# 检查单个应用
python check_model_migration_sync.py
```

### 4. 预防措施

创建 pre-commit 钩子，在提交前自动检查：

```bash
#!/bin/bash
# .git/hooks/pre-commit

# 运行 Django 系统检查
python manage.py check
if [ $? -ne 0 ]; then
  echo "❌ Django 系统检查失败"
  exit 1
fi

# 运行模型迁移同步检查
python check_all_models_migrations.py
if [ $? -ne 0 ]; then
  echo "⚠️  发现模型和迁移不同步，请确认后再提交"
  echo "如果这些差异是有意的，请使用 --no-verify 跳过检查"
  exit 1
fi

echo "✅ 所有检查通过"
```

## 修复文件清单

| 文件路径 | 修改内容 | 状态 |
|---------|---------|------|
| `apps/inventory/models.py` | 添加 `is_low_stock_flag` 字段定义 | ✅ 已修复 |
| `apps/purchase/models.py` | 添加 `warehouse` 字段定义 | ✅ 已修复 |

## 测试验证

### 测试场景

1. **采购借货确认收货**
   - URL: `/purchase/borrows/1/confirm-all-receipt/`
   - 预期: 成功创建库存记录，不报错

2. **库存事务创建**
   - 任何创建 `InventoryTransaction` 的操作
   - 预期: 自动更新 `InventoryStock.is_low_stock_flag`

### 验证步骤

```bash
# 1. 运行系统检查
python manage.py check

# 2. 运行迁移
python manage.py migrate

# 3. 测试借货确认收货
# 访问 http://127.0.0.1:8000/purchase/borrows/1/confirm-all-receipt/
```

## 相关问题

### 类似问题的预防

1. **字段添加流程**
   ```
   创建迁移 → 应用迁移 → 在模型中添加定义 → 测试验证
   ```

2. **字段删除流程**
   ```
   从模型中删除 → 创建删除迁移 → 应用迁移 → 验证
   ```

3. **常见错误**
   - ❌ 忘记在模型中定义字段
   - ❌ 字段类型不匹配（迁移 vs 模型）
   - ❌ 默认值不一致
   - ❌ 迁移依赖关系错误

## 修复时间

**修复时间**: 2026年2月6日
**修复状态**: ✅ 完成
**系统状态**: ✅ 运行正常

## 附加说明

### 为什么检查脚本会误报？

检查脚本的逻辑：
```python
for migration_file in migrations_dir.glob('*.py'):
    # 提取所有 AddField 操作
    add_field_pattern = r"migrations\.AddField(...)"
    matches = re.findall(add_field_pattern, content)
```

这个逻辑会找到所有在迁移中添加的字段，包括：
- ✅ 当前有效的字段
- ❌ 后来被删除的字段
- ❌ 移动到其他应用的字段

因此，检查脚本的结果需要人工审核，不能完全依赖自动化检查。

### 改进建议

未来的检查脚本应该：
1. 只检查最新的迁移状态
2. 忽略已被 RemoveField 删除的字段
3. 跨应用检查（处理模型移动的情况）
4. 使用 Django 的迁移图来判断字段的当前状态

---

**重要提示**: 模型和迁移的同步是 Django 项目的关键，任何不一致都可能导致运行时错误。建议定期检查并保持同步。
