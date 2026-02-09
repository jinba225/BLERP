# 核销逻辑修复说明

## 问题描述

用户反馈：测试供应商丙合计预付了100,000元，在核销时全部使用预付款，提示"核销总额无效"。

## 根本原因

**旧的核销逻辑有严重的逻辑错误：**

```python
# 旧逻辑（错误）
amount = 用户填写的"付款金额"（现金）
effective_prepay_amount = min(prepay.balance, amount)
total_offset = effective_prepay_amount + amount  # ❌ 重复计算！

# 示例：
# 应付账款余额：¥78,000
# 预付款余额：¥100,000
# 用户填写付款金额：¥78,000（想全部用预付）
#
# 计算：
# effective_prepay_amount = min(100000, 78000) = 78000
# total_offset = 78000 + 78000 = 156000 ❌
#
# 验证：156000 > 78000 → 核销总额无效 ❌
```

**问题分析：**
1. 表单字段叫"付款金额"，但实际含义不清晰
2. 用户理解：我要核销78,000，全部用预付款，所以付款金额=0
3. 旧逻辑理解：付款金额=78,000是现金，预付款再使用78,000，总共156,000
4. 结果：重复计算导致核销总额超出应付余额

## 修复方案

### 1. **修改表单字段含义**

**修改前：**
```
付款金额：_____
说明：如选择预付款，最终抵扣=预付款 + 付款金额
```

**修改后：**
```
核销总金额：_____ （默认填写应付余额）
说明：系统将优先使用预付款，剩余部分使用现金支付
```

### 2. **修改核销逻辑**

```python
# 新逻辑（正确）
writeoff_amount = 用户填写的"核销总金额"

# 计算预付款和现金的分配
effective_prepay_amount = Decimal('0')
cash_amount = Decimal('0')

if prepay_id:
    # 优先使用预付款：最多使用核销金额这么多
    effective_prepay_amount = min(prepay.balance, writeoff_amount)
    cash_amount = writeoff_amount - effective_prepay_amount
else:
    # 没有选择预付款，全部用现金
    cash_amount = writeoff_amount

total_offset = writeoff_amount  # ✅ 直接使用核销金额

# 示例：
# 应付账款余额：¥78,000
# 预付款余额：¥100,000
# 用户填写核销总金额：¥78,000
#
# 计算：
# effective_prepay_amount = min(100000, 78000) = 78000
# cash_amount = 78000 - 78000 = 0
# total_offset = 78000 ✅
#
# 验证：78000 <= 78000 → 通过 ✅
```

## 修复的文件

### 1. 视图逻辑（apps/finance/views.py）

#### 供应商核销（supplier_account_writeoff）
```python
# 修改前：
amount = Decimal(request.POST.get('amount', '0') or '0'))
effective_prepay_amount = min(prepay.balance, amount)
total_offset = (effective_prepay_amount + amount)

# 修改后：
writeoff_amount = Decimal(request.POST.get('amount', '0') or '0'))
effective_prepay_amount = min(prepay.balance, writeoff_amount)
cash_amount = writeoff_amount - effective_prepay_amount
total_offset = writeoff_amount
```

#### 客户核销（customer_account_writeoff）
- 同样的修改

### 2. 模板文件

#### 供应商核销表单（supplier_account_writeoff.html）
```html
<!-- 修改前 -->
<label>付款金额</label>
<input name="amount" placeholder="0.00">
<p>如选择预付款，最终抵扣=预付款 + 付款金额</p>

<!-- 修改后 -->
<label>核销总金额</label>
<input name="amount" value="{{ account.balance }}">
<p>系统将优先使用预付款，剩余部分使用现金支付</p>
```

#### 客户核销表单（customer_account_writeoff.html）
- 同样的修改

## 业务场景验证

### 场景1：全部使用预付款

**数据：**
- 应付账款余额：¥78,000
- 预付款余额：¥100,000

**操作：**
1. 核销总金额：¥78,000（自动填充应付余额）
2. 选择预付款：100,000余额的预付款
3. 点击"确认核销"

**计算：**
- 使用预付款：min(100,000, 78,000) = 78,000
- 使用现金：78,000 - 78,000 = 0
- 总核销：78,000

**结果：**
- ✅ 应付账款结清
- ✅ 预付款剩余：22,000
- ✅ 无需现金支付

### 场景2：预付款不足

**数据：**
- 应付账款余额：¥100,000
- 预付款余额：¥30,000

**操作：**
1. 核销总金额：¥100,000
2. 选择预付款：30,000余额的预付款

**计算：**
- 使用预付款：min(30,000, 100,000) = 30,000
- 使用现金：100,000 - 30,000 = 70,000
- 总核销：100,000

**结果：**
- ✅ 应付账款核销100,000
- ✅ 预付款用完
- ✅ 现金支付70,000

### 场景3：不使用预付款

**数据：**
- 应付账款余额：¥50,000
- 预付款余额：¥100,000

**操作：**
1. 核销总金额：¥50,000
2. 不选择预付款

**计算：**
- 使用预付款：0
- 使用现金：50,000
- 总核销：50,000

**结果：**
- ✅ 应付账款核销50,000
- ✅ 预付款不动
- ✅ 现金支付50,000

## 用户体验改进

### 1. **更清晰的表单标签**
- 从"付款金额"改为"核销总金额"
- 用户明确知道要填写什么

### 2. **智能默认值**
- 核销总金额默认填充应付账款余额
- 用户通常不需要修改，直接点确认

### 3. **清晰的说明文字**
- "系统将优先使用预付款，剩余部分使用现金支付"
- 用户明确知道系统会自动计算

### 4. **更好的错误提示**
```python
# 修改前：
messages.error(request, '核销总额无效')

# 修改后：
messages.error(request, f'核销金额（¥{writeoff_amount}）不能超过应付余额（¥{account.balance}）')
```

## 测试验证

### 测试脚本
创建了 `test_writeoff_logic.py` 验证修复效果。

### 测试结果
```
✅ 修复后的逻辑:
  核销总金额: ¥78,000
  预付款使用: ¥78,000
  现金需求: ¥0
  验证: 通过 ✅

❌ 修复前的逻辑:
  付款金额: ¥78,000
  预付款使用: ¥78,000
  总核销: ¥156,000
  验证: 失败 ❌（超出了！）
```

## 使用方法

### 核销操作步骤：

1. **访问核销页面**
   ```
   http://127.0.0.1:8000/finance/supplier-accounts/1/writeoff/
   ```

2. **填写核销信息**
   - **核销总金额**：默认已填写应付账款余额（如78,000）
   - **选择预付款**：从下拉框选择（如"2026-02-04 - 余额 ¥100,000.00"）
   - **付款日期**：默认当天
   - **付款方式**：如果需要现金支付，选择方式

3. **确认核销**
   - 点击"确认核销"按钮
   - 系统自动计算预付款和现金的分配
   - 完成核销

### 关键点：
- ✅ **核销总金额** = 您要核销的应付/应收金额
- ✅ 系统自动优先使用预付款
- ✅ 剩余部分才需要现金支付
- ✅ 预付款不足时，自动补充现金

## 技术细节

### 逻辑变更对比

| 项目 | 旧逻辑 | 新逻辑 |
|------|--------|--------|
| 表单字段 | "付款金额" | "核销总金额" |
| 用户理解 | 现金支付金额 | 要核销的总金额 |
| 预付款计算 | min(预付款, 付款金额) | min(预付款, 核销金额) |
| 现金计算 | 用户填写 | 核销金额 - 预付款 |
| 总核销 | 预付款 + 现金（重复） | 核销金额（正确） |
| 用户体验 | ❌ 混乱，容易出错 | ✅ 清晰，自动计算 |

### 代码质量改进

1. **语义化变量名**
   ```python
   # 修改前：
   amount  # 含义不明确

   # 修改后：
   writeoff_amount  # 核销总金额
   cash_amount      # 现金金额
   ```

2. **明确的验证**
   ```python
   # 修改前：
   if total_offset <= 0 or total_offset > account.balance:
       messages.error(request, '核销总额无效')

   # 修改后：
   if writeoff_amount <= 0:
       messages.error(request, '核销金额必须大于0')
   if writeoff_amount > account.balance:
       messages.error(request, f'核销金额（¥{writeoff_amount}）不能超过应付余额（¥{account.balance}）')
   ```

3. **分离关注点**
   - 计算逻辑与验证逻辑分离
   - 更易于维护和测试

## 影响范围

### 修改的模块：
- ✅ 应付账款核销（供应商）
- ✅ 应收账款核销（客户）

### 修改的文件：
- ✅ `apps/finance/views.py`（2个视图函数）
- ✅ `templates/modules/finance/supplier_account_writeoff.html`
- ✅ `templates/modules/finance/customer_account_writeoff.html`

### 数据库影响：
- ✅ 无需数据库迁移
- ✅ 无需修改现有数据
- ✅ 仅修改业务逻辑和表单标签

## 总结

这次修复解决了核销逻辑的根本问题：

1. **明确业务语义**：从"付款金额"改为"核销总金额"
2. **优化计算逻辑**：系统自动计算预付款和现金的分配
3. **改善用户体验**：清晰的表单标签和说明文字
4. **提供详细反馈**：更明确的错误提示

现在用户可以：
- ✅ 轻松理解核销操作的含义
- ✅ 优先使用预付款，避免现金浪费
- ✅ 清楚了解预付款和现金的使用情况
- ✅ 避免"核销总额无效"的错误

核销功能现在完全符合业务需求！
