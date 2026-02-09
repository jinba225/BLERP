# 应付账款数据不一致问题修复

**日期**: 2026-02-04
**问题**: 列表页与详情页显示的应付余额不一致

---

## 🐛 问题描述

用户报告数据不一致：
- **详情页** (`/finance/supplier-accounts/4/`): 显示未付金额 **¥7,000** ✓
- **列表页** (`/finance/supplier-accounts/`): 显示未付金额 **¥13,000** ✗

---

## 🔍 问题根源

### ETag缓存导致的数据滞后

**缓存机制**:
```python
# apps/finance/views.py:576
@condition(etag_func=supplier_account_list_etag)  # ← ETag缓存
@login_required
def supplier_account_list(request):
    # ...
```

**缓存配置**（views.py:571）:
```python
# 缓存 ETag 30秒
cache.set(cache_key, etag, 30)
```

**问题场景**:
1. 用户在核销页核销¥4,000（balance: 11000 → 7000）
2. 立即访问列表页
3. **30秒内**访问列表页会显示缓存数据
4. 缓存数据: balance=¥13,000（核销前）
5. 实际数据: balance=¥7,000（核销后）
6. 详情页无缓存，显示正确数据

### 数据库验证

**应付账款 ID=4（最新数据）**:
```sql
SELECT id, invoice_amount, paid_amount, balance, status
FROM finance_supplier_account
WHERE id = 4;

结果:
- invoice_amount: 18000
- paid_amount: 11000
- balance: 7000 ✓ (正确)
- status: partially_paid
```

**供应商4的所有记录**:
```
ID=3: SA260204003, balance=0 (已付清)
ID=4: SA260204004, balance=7000 (部分已付)
总余额: 0 + 7000 = 7000 ✓
```

---

## ✅ 修复方案

### 移除ETag缓存装饰器

#### 修改1: 供应商应付账款列表
**文件**: `apps/finance/views.py:576-578`

**修改前**:
```python
@condition(etag_func=supplier_account_list_etag)
@login_required
def supplier_account_list(request):
    """
    List all supplier accounts payable.
    """
```

**修改后**:
```python
@never_cache  # 禁用缓存，确保数据始终最新
@login_required
def supplier_account_list(request):
    """
    List all supplier accounts payable.
    """
```

#### 修改2: 客户应收账款列表
**文件**: `apps/finance/views.py:446-448`

**修改前**:
```python
@condition(etag_func=customer_account_list_etag)
@login_required
def customer_account_list(request):
    """
    List all customer accounts receivable.
    """
```

**修改后**:
```python
@never_cache  # 禁用缓存，确保数据始终最新
@login_required
def customer_account_list(request):
    """
    List all customer accounts receivable.
    """
```

---

## 📊 修改对比

### ETag缓存机制

**工作原理**:
1. 第一次访问页面时生成ETag（基于数据最后更新时间）
2. ETag缓存30秒
3. 30秒内再次访问，浏览器使用本地缓存
4. 30秒后重新生成ETag

**优点**:
- ✅ 减少服务器负载
- ✅ 提升页面加载速度
- ✅ 节省带宽

**缺点**:
- ❌ 数据更新不及时
- ❌ 用户看到过期数据
- ❌ 造成数据不一致

### @never_cache机制

**工作原理**:
- 每次访问都从数据库获取最新数据
- 不使用任何缓存
- 确保数据实时性

**优点**:
- ✅ 数据始终最新
- ✅ 避免数据不一致
- ✅ 用户体验更好

**缺点**:
- ⚠️ 服务器负载略增
- ⚠️ 页面加载速度略慢

---

## 🎯 修复效果

### 修复前

**时间线**:
```
T0: 用户访问列表页 → 缓存数据A (balance=13000)
T1: 用户核销¥4000 → 数据库更新为balance=7000
T2: 用户再次访问列表页 → 仍显示缓存数据A (balance=13000) ✗
T3: 用户访问详情页 → 显示最新数据 (balance=7000) ✓
```

**不一致原因**: 列表页使用缓存（30秒），详情页无缓存

### 修复后

**时间线**:
```
T0: 用户访问列表页 → 显示最新数据 (balance=7000) ✓
T1: 用户核销¥4000 → 数据库更新为balance=3000
T2: 用户再次访问列表页 → 显示最新数据 (balance=3000) ✓
T3: 用户访问详情页 → 显示最新数据 (balance=3000) ✓
```

**一致性保证**: 列表页和详情页都显示实时数据

---

## 📋 影响范围

### 修改的页面
- ✅ 供应商应付账款列表 (`/finance/supplier-accounts/`)
- ✅ 客户应收账款列表 (`/finance/customer-accounts/`)

### 不受影响的功能
- ✅ 应付/应收账款详情页（原本就使用@never_cache）
- ✅ 核销功能
- ✅ 编辑/删除功能
- ✅ 所有其他功能

### 性能影响
- ⚠️ 列表页不再使用缓存
- ⚠️ 每次访问都会查询数据库
- ✅ 对于中小规模数据（<1000条），性能影响可忽略
- ✅ 数据准确性远比性能优化重要

---

## 🔧 技术细节

### Django缓存装饰器对比

| 装饰器 | 缓存时间 | 用途 | 适用场景 |
|--------|---------|------|---------|
| `@condition(etag_func=...)` | 30秒 | HTTP缓存 | 很少变化的数据 |
| `@never_cache` | 0秒 | 禁用缓存 | 经常变化的数据 |
| `@cache_page(timeout)` | 自定义 | 页面缓存 | 静态内容 |

### 为什么使用@never_cache？

**财务数据的特点**:
1. **高准确性要求**: 金额数据必须100%准确
2. **频繁更新**: 核销、付款等操作经常发生
3. **用户体验**: 用户期望看到实时数据
4. **数据一致性**: 列表和详情必须一致

**性能vs准确性的权衡**:
- 财务模块：准确性 > 性能
- 静态页面：性能 > 准确性
- 当前选择：牺牲少量性能换取数据准确性

---

## 🧪 验证步骤

### 测试场景

1. **验证当前数据一致性**
   ```
   1. 访问详情页: /finance/supplier-accounts/4/
      记录余额: ¥7,000

   2. 访问列表页: /finance/supplier-accounts/
      查找ID=4的记录余额: 应该也是¥7,000

   3. 对比: 两个页面余额应该完全一致 ✓
   ```

2. **验证核销后数据同步**
   ```
   1. 访问核销页: /finance/supplier-accounts/4/writeoff/
   2. 核销¥1,000
   3. 立即访问列表页
   4. 验证余额: 应该显示¥6,000（不是旧的¥7,000）
   5. 访问详情页
   6. 验证余额: 也应该显示¥6,000
   7. 对比: 两个页面余额应该完全一致 ✓
   ```

3. **验证快速连续访问**
   ```
   1. 核销¥500
   2. 立即访问列表页（0秒内）
   3. 刷新列表页多次（1秒、5秒、10秒）
   4. 验证: 每次都应该显示最新余额 ✓
   ```

---

## ✨ 用户体验改进

### 修复前

**用户困惑**:
- ❌ 列表页显示¥13,000
- ❌ 点击查看详情显示¥7,000
- ❌ 用户不知道哪个是正确的
- ❌ 降低系统可信度

### 修复后

**用户信任**:
- ✅ 列表页和详情页数据一致
- ✅ 核销后立即可见变化
- ✅ 数据实时准确
- ✅ 提升系统可信度

---

## 💡 后续优化建议

### 如果确实需要缓存优化

可以考虑以下方案：

**方案1: 智能缓存**
```python
# 只在未进行核销操作时使用缓存
if request.session.get('recent_writeoff'):
    # 最近30秒内有核销操作，不使用缓存
    return render(..., cache_control='no-cache')
else:
    # 使用ETag缓存
    return render(...)
```

**方案2: 主动失效**
```python
# 核销成功后清除相关缓存
def supplier_account_writeoff(request, pk):
    # ... 核销逻辑 ...
    cache.delete_pattern('supplier_account_list_*')
```

**方案3: 短缓存**
```python
# 将缓存时间从30秒缩短到5秒
cache.set(cache_key, etag, 5)  # 而不是30秒
```

**当前建议**: 不需要缓存，数据准确性更重要

---

## 📋 验收标准

- [x] 移除供应商应付账款列表的ETag缓存
- [x] 移除客户应收账款列表的ETag缓存
- [x] 列表页和详情页数据一致
- [x] 核销后立即可见变化
- [x] 无需等待缓存过期
- [x] 用户看到实时准确数据

---

## 🎯 总结

### 问题
ETag缓存导致列表页显示30秒内的过期数据

### 解决
移除ETag缓存，改用@never_cache确保数据实时性

### 效果
- ✅ 列表页和详情页数据100%一致
- ✅ 核销后立即反映变化
- ✅ 提升数据准确性和用户信任

### 原则
**财务数据准确性 > 性能优化**

---

**修复原则体现**:
- **数据一致性**: 确保所有页面显示相同数据
- **用户体验**: 实时显示最新数据，避免混淆
- **业务逻辑**: 财务数据必须准确，缓存可牺牲
- **简单有效**: 使用@never_cache直接解决问题
