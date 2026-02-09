# 预付款字段错误修复报告

**日期**: 2026-02-04
**错误**: `AttributeError: 'SupplierPrepayment' object has no attribute 'payment_number'`

---

## 🐛 问题描述

在创建预付款时，系统抛出错误：
```
AttributeError: 'SupplierPrepayment' object has no attribute 'payment_number'
```

---

## 🔍 问题根源

`SupplierPrepayment` 和 `CustomerPrepayment` 模型没有 `payment_number` 字段。模型定义如下：

```python
class SupplierPrepayment(BaseModel):
    """供应商预付款模型"""
    supplier = models.ForeignKey('suppliers.Supplier', ...)
    amount = models.DecimalField('预付金额', ...)
    balance = models.DecimalField('剩余余额', ...)
    paid_date = models.DateField('付款日期')
    notes = models.TextField('备注', ...)
    status = models.CharField('状态', ...)
    # 没有 payment_number 字段！

class CustomerPrepayment(BaseModel):
    """客户预收款模型"""
    customer = models.ForeignKey('customers.Customer', ...)
    amount = models.DecimalField('预收金额', ...)
    balance = models.DecimalField('剩余余额', ...)
    received_date = models.DateField('收到日期')
    notes = models.TextField('备注', ...)
    status = models.CharField('状态', ...)
    # 没有 payment_number 字段！
```

---

## ✅ 修复内容

### 修复位置

#### 1. 客户预收款创建成功消息（views.py:1216）
**修改前**:
```python
f'预收款已自动合并到现有记录（单号: {existing_prepay.payment_number}）。'
```

**修改后**:
```python
f'预收款已自动合并到现有记录（ID: {existing_prepay.id}）。'
```

#### 2. 供应商预付款创建成功消息（views.py:1303）
**修改前**:
```python
f'预付款已自动合并到现有记录（单号: {existing_prepay.payment_number}）。'
```

**修改后**:
```python
f'预付款已自动合并到现有记录（ID: {existing_prepay.id}）。'
```

#### 3. API返回数据结构（views.py:1128-1134）
**修改前**:
```python
prepayments_data.append({
    'id': prepay.id,
    'payment_number': prepay.payment_number,  # ❌ 字段不存在
    'paid_date': prepay.paid_date.strftime('%Y-%m-%d') if prepay.paid_date else '',
    'amount': float(prepay.amount),
    'balance': float(prepay.balance),
    'created_at': prepay.created_at.isoformat(),
})
```

**修改后**:
```python
prepayments_data.append({
    'id': prepay.id,
    'paid_date': prepay.paid_date.strftime('%Y-%m-%d') if prepay.paid_date else '',
    'amount': float(prepay.amount),
    'balance': float(prepay.balance),
    'created_at': prepay.created_at.isoformat(),
})
```

---

## 📋 验证结果

### 修复验证清单

- [x] 客户预收款自动合并消息使用ID字段
- [x] 供应商预付款自动合并消息使用ID字段
- [x] API返回数据移除payment_number字段
- [x] 代码中不存在对prepay.payment_number的引用
- [x] 代码中不存在对existing_prepay.payment_number的引用

### 测试用例

| 测试场景 | 预期结果 |
|---------|---------|
| 为供应商创建第1笔预付款 | 创建成功，显示"预付款创建成功" |
| 为同一供应商创建第2笔预付款 | 自动合并，显示"预付款已自动合并到现有记录（ID: X）。原余额 ¥10000 → 新余额 ¥15000" |
| 为客户创建第1笔预收款 | 创建成功，显示"预收款创建成功" |
| 为同一客户创建第2笔预收款 | 自动合并，显示"预收款已自动合并到现有记录（ID: X）。原余额 ¥10000 → 新余额 ¥15000" |

---

## 🎯 用户影响

### 修复前
- ❌ 创建预付款时抛出 `AttributeError`
- ❌ 无法创建预付款
- ❌ 自动合并功能不可用

### 修复后
- ✅ 可以正常创建预付款
- ✅ 自动合并功能正常工作
- ✅ 成功消息正确显示记录ID
- ✅ API返回正确的数据结构

---

## 🔧 技术细节

### 为什么使用ID而不是单号？

1. **模型设计**: `SupplierPrepayment` 和 `CustomerPrepayment` 模型没有设计单号字段
2. **ID唯一性**: 数据库主键ID天然唯一，可以唯一标识一条记录
3. **简单直接**: 使用ID是最简单的方式，不需要额外的字段

### 未来改进建议

如果需要更友好的标识方式，可以考虑：

**选项1**: 添加单号字段
```python
class SupplierPrepayment(BaseModel):
    prepayment_number = CharField('预付款单号', max_length=50, unique=True)
    # ...
```

**选项2**: 使用组合标识
```
{供应商名称}-{日期}-{序号}
例如：测试供应商A-20260204-001
```

**选项3**: 使用ID + 日期
```
ID: 123 → [2026-02-04] #123
```

---

## ✅ 验收标准

- [x] 创建预付款不再抛出AttributeError
- [x] 自动合并功能正常工作
- [x] 成功消息正确显示
- [x] API返回正确的数据结构
- [x] 前端下拉框能正常显示预付款列表

---

**修复原则体现**:
- **YAGNI**: 使用现有的ID字段，无需添加新字段
- **KISS**: 简单使用ID标识，不过度设计
- **快速修复**: 移除不存在的字段引用，使用ID替代
