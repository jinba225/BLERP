# 使用GET请求进行数据修改操作的问题清单

## 问题描述
当前系统中存在大量使用GET请求进行数据修改操作的情况，这违反了HTTP语义规范（GET应该只用于读取数据），并且可能导致：
- 消息显示在错误的页面
- 搜索引擎爬虫意外触发操作
- 浏览器预加载误触发
- CSRF安全风险

## 问题汇总

### 采购模块 (Purchase)

| 视图函数 | 操作 | 模板位置 | 风险等级 |
|---------|------|---------|---------|
| `borrow_return` | 借用归还 | borrow_detail.html:43 | 中 |
| `borrow_request_conversion` | 借用转采购 | borrow_detail.html:49 | 中 |
| `borrow_confirm_receipt` | 借用入库确认 | borrow_confirm_receipt.html | 中 |
| `quotation_select` | 选定报价 | quotation_detail.html:21, quotation_compare.html:119 | 中 |
| `inquiry_delete` | 删除询价单 | inquiry_detail.html:29, inquiry_list.html:145 | 高 |

### 销售模块 (Sales)

| 视图函数 | 操作 | 模板位置 | 风险等级 |
|---------|------|---------|---------|
| `loan_return` | 借出归还 | loan_detail.html:31 | 中 |
| `return_approve` | 退货审批 | return_detail.html:57 | 高 |
| `return_receive` | 退货收货 | return_detail.html:64 | 高 |
| `return_process` | 处理退货 | return_detail.html:71 | 中 |
| `return_reject` | 退货拒绝 | return_detail.html:78 | 中 |
| `order_unapprove` | 订单取消审核 | order_detail.html:53 | 中 |
| `quote_convert` | 报价转订单 | quote_detail.html:90 | 中 |
| `quote_delete` | 删除报价 | quote_detail.html:94, quote_list.html:142 | 高 |

### 库存模块 (Inventory)

| 视图函数 | 操作 | 模板位置 | 风险等级 |
|---------|------|---------|---------|
| `inbound_delete` | 删除入库单 | inbound_detail.html:29 | 高 |
| `inbound_approve` | 入库审批 | inbound_detail.html:35 | 高 |
| `outbound_delete` | 删除出库单 | outbound_detail.html:29 | 高 |
| `outbound_approve` | 出库审批 | outbound_detail.html:35 | 高 |
| `transfer_approve` | 调拨审批 | transfer_detail.html:61 | 高 |
| `transfer_delete` | 删除调拨单 | transfer_detail.html:86 | 高 |
| `adjustment_approve` | 调整审批 | adjustment_detail.html:53 | 高 |
| `adjustment_delete` | 删除调整单 | adjustment_detail.html:60 | 高 |

### 财务模块 (Finance)

| 视图函数 | 操作 | 模板位置 | 风险等级 |
|---------|------|---------|---------|
| `expense_delete` | 删除费用 | expense_detail.html:32, 55 | 高 |
| `expense_approve` | 费用审批 | expense_detail.html:38 | 高 |
| `expense_reject` | 费用拒绝 | expense_detail.html:43 | 高 |
| `customer_prepayment_delete` | 删除客户预付款 | customer_prepayment_list.html:193 | 高 |

**总计：约 23 个高风险操作**

## 修复方案

### 方案A：全部改为POST请求（推荐）
将所有修改数据的操作改为POST请求，符合HTTP语义和最佳实践。

**优点：**
- 符合RESTful规范
- 防止CSRF攻击
- 消息显示可靠

**缺点：**
- 需要大量修改
- 需要测试所有功能

### 方案B：仅修复高风险操作
只修复删除、审批等高风险操作。

**优点：**
- 修改量小
- 快速提升安全性

**缺点：**
- 仍存在部分不规范操作
- 仍可能出现消息显示问题

## 实施建议

### 阶段1：立即修复（高优先级）
- 所有删除操作（delete）
- 所有审批操作（approve）
- 所有确认/拒绝操作（confirm/reject）

### 阶段2：逐步修复（中优先级）
- 转换操作（convert）
- 归还操作（return）
- 其他状态变更操作

## 代码示例

### 修改前（GET请求）
```html
<a href="{% url 'purchase:borrow_confirm_all_receipt' borrow.pk %}"
   onclick="return confirm('确认？')">
    一键全部入库
</a>
```

### 修改后（POST请求）
```html
<form method="post" action="{% url 'purchase:borrow_confirm_all_receipt' borrow.pk %}" class="inline">
    {% csrf_token %}
    <button type="submit" class="btn btn-primary"
            onclick="return confirm('确认？')">
        一键全部入库
    </button>
</form>
```

### 视图函数修改
```python
from django.views.decorators.http import require_http_methods

@require_http_methods(["POST"])
@login_required
@transaction.atomic
def borrow_confirm_all_receipt(request, pk):
    # ... 处理逻辑
```

## 测试清单

修改后需要测试：
- [ ] 操作是否正常执行
- [ ] 消息是否正确显示
- [ ] 页面是否正确重定向
- [ ] CSRF保护是否生效
- [ ] 确认对话框是否正常显示

## 备注

- 修复borrow_confirm_all_receipt已完成 ✅
- 建议按优先级逐步修复其他操作
- 每次修复后都要进行完整测试
