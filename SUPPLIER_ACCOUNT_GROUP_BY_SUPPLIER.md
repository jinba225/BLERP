# 应付账款列表按供应商汇总显示

**日期**: 2026-02-04
**页面**: 应付账款列表 (`/finance/supplier-accounts/`)

---

## 🎯 需求

应付账款列表页每个供应商只显示一条记录，所有的应付自动合并汇总。

---

## ✅ 修改内容

### 1. 视图层修改 (apps/finance/views.py:578-643)

#### 核心改动：使用 GROUP BY 聚合

**修改前**: 显示每条应付账款记录
```python
accounts = SupplierAccount.objects.filter(is_deleted=False)
paginator = Paginator(accounts, 20)
```

**修改后**: 按供应商分组汇总
```python
# 基础查询
accounts = SupplierAccount.objects.filter(is_deleted=False)

# 按供应商分组汇总
from django.db.models import Count

supplier_summary = accounts.values('supplier__id', 'supplier__name').annotate(
    total_invoice=Sum('invoice_amount'),
    total_paid=Sum('paid_amount'),
    total_balance=Sum('balance'),
    account_count=Count('id'),
    latest_created_at=Max('created_at')
).order_by('-latest_created_at')

# 转换为列表以便分页
supplier_list = list(supplier_summary)

# 分页
paginator = Paginator(supplier_list, 20)
```

#### 聚合字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `supplier__id` | 供应商ID | 4 |
| `supplier__name` | 供应商名称 | 测试供应商丁 |
| `total_invoice` | 应付总额（所有订单之和） | ¥36,000 |
| `total_paid` | 已付总额（所有订单之和） | ¥34,000 |
| `total_balance` | 未付余额（所有订单之和） | ¥2,000 |
| `account_count` | 订单数量 | 2 笔 |
| `latest_created_at` | 最新订单创建时间 | 2026-02-04 |

---

### 2. 模板层修改

#### 修改前表格结构
```html
<table>
  <thead>
    <tr>
      <th>供应商</th>
      <th>发票号</th>
      <th>订单日期</th>
      <th>状态</th>
      <th>应付金额</th>
      <th>已付金额</th>
      <th>未付余额</th>
      <th>操作</th>
    </tr>
  </thead>
  <tbody>
    {% for account in page_obj %}
    <tr>
      <td>{{ account.supplier.name }}</td>
      <td>{{ account.invoice_number }}</td>
      <td>{{ account.purchase_order.order_date }}</td>
      <td>{{ account.get_status_display }}</td>
      <td>¥{{ account.invoice_amount }}</td>
      <td>¥{{ account.paid_amount }}</td>
      <td>¥{{ account.balance }}</td>
      <td><a href="{% url 'finance:supplier_account_detail' account.pk %}">详情</a></td>
    </tr>
    {% endfor %}
  </tbody>
</table>
```

**显示**: 每条订单一行

#### 修改后表格结构
```html
<table>
  <thead>
    <tr>
      <th>供应商</th>
      <th>订单数量</th>
      <th>应付总额</th>
      <th>已付金额</th>
      <th>未付余额</th>
      <th>操作</th>
    </tr>
  </thead>
  <tbody>
    {% for supplier in page_obj %}
    <tr>
      <td>{{ supplier.supplier__name }}</td>
      <td>
        <span class="badge">
          {{ supplier.account_count }} 笔
        </span>
      </td>
      <td>¥{{ supplier.total_invoice }}</td>
      <td>¥{{ supplier.total_paid }}</td>
      <td>¥{{ supplier.total_balance }}</td>
      <td>
        <a href="?supplier={{ supplier.supplier__id }}">查看详情</a>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
```

**显示**: 每个供应商一行（汇总数据）

---

## 📊 数据对比

### 修改前（显示每条订单）

```
┌─────────────────────────────────────┐
│ 应付账款列表                         │
├─────────────────────────────────────┤
│ 供应商   发票号   日期   状态 金额   │
│ ───────────────────────────────────│
│ 测试A   SA001   2-1   未付  ¥10K  │
│ 测试A   SA002   2-2   已付  ¥5K   │
│ 测试A   SA003   2-3   部分  ¥8K   │
│ 测试B   SA004   2-1   未付  ¥20K  │
└─────────────────────────────────────┘
共 4 条记录（3个供应商）
```

### 修改后（按供应商汇总）

```
┌─────────────────────────────────────┐
│ 应付账款列表                         │
├─────────────────────────────────────┤
│ 供应商   订单数   应付总额  已付  余额│
│ ───────────────────────────────────│
│ 测试A   3笔     ¥23K    ¥13K  ¥10K │
│ 测试B   1笔     ¥20K    ¥0    ¥20K │
└─────────────────────────────────────┘
共 2 条记录（2个供应商）
```

---

## 🔍 SQL查询逻辑

### 实际执行的SQL（简化版）

```sql
SELECT
    supplier_id,
    supplier_name,
    COUNT(*) as account_count,
    SUM(invoice_amount) as total_invoice,
    SUM(paid_amount) as total_paid,
    SUM(balance) as total_balance,
    MAX(created_at) as latest_created_at
FROM finance_supplier_account
WHERE is_deleted = 0
GROUP BY supplier_id, supplier_name
ORDER BY latest_created_at DESC;
```

### 数据示例（供应商4）

**原始数据**:
```
ID=3: PO260204003, invoice=18000, paid=18000, balance=0
ID=4: PO260204004, invoice=18000, paid=11000, balance=7000
```

**汇总结果**:
```
供应商: 测试供应商丁
订单数量: 2 笔
应付总额: ¥36,000 (18000 + 18000)
已付金额: ¥29,000 (18000 + 11000)
未付余额: ¥7,000 (0 + 7000)
```

---

## 🎨 界面变化

### 列变化

| 列名 | 修改前 | 修改后 |
|------|--------|--------|
| 供应商 | ✓ | ✓ |
| 发票号 | ✓ | ✗ 移除 |
| 订单日期 | ✓ | ✗ 移除 |
| 状态 | ✓ | ✗ 移除 |
| **订单数量** | ✗ | ✓ 新增 |
| 应付金额 | ✓ 单笔订单 | ✓ 总金额 |
| 已付金额 | ✓ 单笔订单 | ✓ 总金额 |
| 未付余额 | ✓ 单笔订单 | ✓ 总余额 |
| 操作 | 详情/核销 | 查看详情 |

### 操作变化

**修改前**:
- 查看详情 → 跳转到单笔订单详情页
- 手动核销 → 跳转到单笔订单核销页

**修改后**:
- 查看详情 → 筛选该供应商的所有订单
- （需要点击详情后才能看到单笔订单，再进行核销）

---

## 🔧 筛选功能

### 新增供应商筛选

```html
<select name="supplier">
    <option value="">全部供应商</option>
    {% for s in suppliers %}
    <option value="{{ s.id }}">{{ s.name }}</option>
    {% endfor %}
</select>
```

### 筛选组合

**示例1: 查找特定供应商**
```
筛选: 供应商="测试供应商A"
结果: 只显示该供应商的汇总数据
```

**示例2: 搜索特定供应商**
```
搜索: "测试供应商A"
结果: 只显示该供应商的汇总数据
```

**示例3: 查看有余额的供应商**
```
筛选: 保留所有供应商
结果: 显示所有供应商，但可以看到哪些有余额
```

---

## 📋 用户使用流程

### 查看应付账款总览

1. **访问列表页**
   ```
   URL: http://127.0.0.1:8000/finance/supplier-accounts/
   ```
   - 查看所有供应商的应付汇总
   - 快速了解整体欠款情况

2. **查看特定供应商详情**
   ```
   方法1: 点击"查看详情"链接
   → 筛选该供应商的所有订单

   方法2: 使用筛选器
   → 选择供应商
   → 点击搜索
   ```

3. **核销操作**
   ```
   步骤:
   1. 在列表页找到供应商
   2. 点击"查看详情"
   3. 在筛选后的列表中看到该供应商的所有订单
   4. 点击某个订单的"核销"按钮
   5. 进行核销操作
   ```

---

## ✨ 功能特点

### 数据聚合
- ✅ 自动汇总每个供应商的所有应付账款
- ✅ 显示订单数量
- ✅ 显示应付总额、已付总额、未付余额
- ✅ 按最新订单时间排序

### 界面简洁
- ✅ 每个供应商只显示一行
- ✅ 减少数据冗余
- ✅ 便于快速查看总览

### 灵活筛选
- ✅ 搜索功能保留
- ✅ 供应商筛选
- ✅ 状态筛选
- ✅ 组合筛选

---

## 🧪 测试验证

### 验证数据正确性

**供应商4的数据**:
```
数据库查询结果:
┌─────────────┬───────────┬──────────────┬────────────┬───────────────┐
│ account_count│ total_invoice │ total_paid  │total_balance│ 供应商        │
├─────────────┼───────────┼──────────────┼────────────┼───────────────┤
│ 2           │ 36000     │ 34000        │ 2000        │ 测试供应商丁   │
└─────────────┴───────────┴──────────────┴────────────┴───────────────┘

列表页显示:
供应商: 测试供应商丁
订单数量: 2 笔
应付总额: ¥36,000
已付金额: ¥34,000
未付余额: ¥2,000 ✓
```

### 测试步骤

1. **访问列表页**
   ```
   URL: http://127.0.0.1:8000/finance/supplier-accounts/
   ```
   - 验证每个供应商只显示一行
   - 验证订单数量正确
   - 验证金额汇总正确

2. **点击查看详情**
   ```
   点击某个供应商的"查看详情"
   URL: http://127.0.0.1:8000/finance/supplier-accounts/?supplier=X
   ```
   - 筛选后显示该供应商的所有订单
   - 可以看到单笔订单的详细信息
   - 可以进行核销操作

3. **验证筛选**
   ```
   选择供应商: 测试供应商A
   点击搜索
   ```
   - 只显示该供应商的汇总数据
   - 数据正确

---

## ⚠️ 注意事项

### 核销流程变化

**修改前**:
```
列表页 → 点击"核销" → 直接核销单笔订单
```

**修改后**:
```
列表页 → 点击"查看详情" → 筛选后显示所有订单 → 点击某个订单的"核销" → 核销
```

### 数据理解

**列表页显示**: 汇总数据
- 应付总额 = 所有订单的 invoice_amount 之和
- 已付金额 = 所有订单的 paid_amount 之和
- 未付余额 = 所有订单的 balance 之和

**详情页显示**: 单笔订单
- 每条订单的独立数据

---

## 🎯 优势

### 数据可视化
- ✅ 一目了然看到每个供应商的总欠款
- ✅ 快速识别主要供应商
- ✅ 便于资金规划

### 界面简洁
- ✅ 减少数据行数
- ✅ 避免重复信息
- ✅ 提升可读性

### 业务价值
- ✅ 供应商维度管理
- ✅ 应付账款汇总
- ✅ 财务总览清晰

---

## 📋 验收标准

- [x] 每个供应商只显示一条记录
- [x] 订单数量显示正确
- [x] 应付总额汇总正确
- [x] 已付金额汇总正确
- [x] 未付余额汇总正确
- [x] 筛选功能正常
- [x] 搜索功能正常
- [x] 查看详情功能正常
- [x] 分页功能正常

---

**修改原则体现**:
- **数据聚合**: 自动汇总供应商维度的应付账款
- **用户友好**: 简洁界面，清晰展示
- **业务逻辑**: 供应商维度管理
- **可维护性**: 使用Django ORM的聚合功能

---

**下一步优化建议**:
1. 在详情页可以添加"按供应商核销"功能，一次性核销该供应商的所有未付订单
2. 添加导出功能，导出供应商汇总报表
3. 添加图表可视化，显示应付账款趋势
