# 采购退货数量约束增强 - 手动测试步骤

## 测试环境准备

1. 启动开发服务器：
```bash
python manage.py runserver
```

2. 登录系统：`http://127.0.0.1:8000`

---

## 测试场景

### 场景 1：正常退货（未超过可退货数量）

**前置条件：**
- 创建采购订单，订单数量：10个
- 创建收货单，收货数量：10个
- 已退货数量：0个
- 可退货数量：10个

**测试步骤：**
1. 访问订单详情页
2. 点击"创建退货单"
3. 在退货明细中输入退货数量：3个
4. 观察前端验证提示

**预期结果：**
- ✅ 前端验证通过
- ✅ 无弹窗提示
- ✅ 小计金额正确计算：¥300.00
- ✅ 提交后退货单创建成功

---

### 场景 2：超额退货（超过可退货数量）

**前置条件：**
- 订单数量：10个
- 已收货数量：10个
- 已创建并审核过第一笔退货单：5个
- 可退货数量：10 - 5 = 5个

**测试步骤：**
1. 创建第一笔退货单（5个）并审核通过
2. 创建第二笔退货单，输入退货数量：6个
3. 输入框失去焦点（触发 onchange 事件）

**预期结果：**
- ❌ 前端阻止：弹出提示
  ```
  退货数量不能超过可退货数量5（已收货10 - 已退货5）
  ```
- ❌ 输入框自动重置为0
- ❌ 小计金额归零

**后端验证（绕过前端）：**
如果直接修改 HTML 或使用 API 提交超额退货：
- ❌ 后端返回错误：
  ```
  产品 XXX 的退货数量(6)不能超过可退货数量(5。已收货10 - 已退货5)
  ```

---

### 场景 3：边界测试

**前置条件：**
- 订单数量：10个
- 已收货数量：10个
- 已退货数量：5个
- 可退货数量：5个

**测试步骤：**

| 测试用例 | 输入值 | 预期结果 |
|---------|-------|---------|
| 退货0个 | 0 | ✅ 允许（不创建退货明细） |
| 退货5个（刚好等于可退货） | 5 | ✅ 允许 |
| 退货6个（超过可退货1个） | 6 | ❌ 阻止，弹出提示 |

---

### 场景 4：多次退货累积

**前置条件：**
- 订单数量：10个
- 已收货数量：10个

**测试步骤：**

| 次数 | 退货数量 | 剩余可退货 | 预期结果 |
|-----|---------|-----------|---------|
| 第1次 | 3个 | 7个 | ✅ 成功 |
| 第2次 | 4个 | 3个 | ✅ 成功 |
| 第3次 | 3个 | 0个 | ✅ 成功 |
| 第4次 | 1个 | 0个 | ❌ 阻止（可退货为0） |

---

## 验证代码位置

### 前端验证
**文件**: `templates/modules/purchase/return_form.html`

**关键代码**:
```javascript
// 第227-234行
if (qty > returnableQty) {
    const returned = maxQty - returnableQty;
    alert(`退货数量不能超过可退货数量 ${returnableQty}（已收货${receivedQty} - 已退货${returned}）`);
    input.value = 0;
    updateSubtotal(input);
    return;
}
```

### 后端验证
**文件**: `apps/purchase/views.py`

**关键代码** (第1486-1502行):
```python
# 验证2: 退货数量不能超过可退货数量
from django.db.models import Sum
returned_quantity = PurchaseReturnItem.objects.filter(
    order_item=order_item,
    purchase_return__purchase_order=order,
    purchase_return__is_deleted=False,
    purchase_return__status__in=['approved', 'returned', 'completed']
).aggregate(total=Sum('quantity'))['total'] or 0

returnable_quantity = order_item.received_quantity - returned_quantity

if return_quantity > returnable_quantity:
    raise ValueError(
        f'产品 {order_item.product.name} 的退货数量 ({return_quantity}) '
        f'不能超过可退货数量 ({returnable_quantity}。'
        f'已收货{order_item.received_quantity} - 已退货{returned_quantity})'
    )
```

---

## 可退货数量计算公式

```
可退货数量 = 已收货数量 - 已退货数量
```

### 已退货数量统计范围

**包含的状态：**
- ✅ `approved` - 已审核
- ✅ `returned` - 已退货
- ✅ `completed` - 已完成

**排除的状态：**
- ❌ `pending` - 待审核（未生效）
- ❌ `cancelled` - 已取消（已作废）

---

## 预期效果

1. ✅ **前端实时反馈** - 用户输入时立即提示是否超过可退货数量
2. ✅ **后端严格验证** - 即使绕过前端，后端也会拦截超额退货
3. ✅ **清晰的错误提示** - 明确告知用户可退货数量的计算过程
4. ✅ **数据一致性** - 确保退货数量永远不会超过实际可退货数量
