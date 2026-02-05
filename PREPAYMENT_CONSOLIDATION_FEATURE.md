# 预付款/预收款合并功能

## 功能概述

实现供应商预付款和客户预收款的合并功能，解决同一供应商/客户多次预付（收）导致金额分散，核销时无法充分利用的问题。

## 业务场景

**问题场景：**
- 供应商丙分两次预付了100,000元（50,000 + 50,000）
- 相关订单应付78,000元
- 旧逻辑：只能选择单笔预付款，最多使用50,000元，还需现金支付28,000元
- 新逻辑：合并为100,000元一笔预付款，核销时全部使用预付款，无需现金支付

## 实现内容

### 1. 模型更新（apps/finance/models.py）

#### SupplierPrepayment 模型新增字段：
```python
PREPAYMENT_STATUS = [
    ('active', '活跃'),
    ('merged', '已合并'),
    ('exhausted', '已用完'),
]

status = models.CharField('状态', max_length=20, choices=PREPAYMENT_STATUS, default='active')
merged_into = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='merged_from', verbose_name='合并到')
is_consolidated = models.BooleanField('是否合并记录', default=False)
```

#### CustomerPrepayment 模型新增字段：
同上（客户预收款）

### 2. 视图更新（apps/finance/views.py）

#### 列表视图更新：
- `supplier_prepayment_list`: 只显示活跃的预付款，按供应商统计
- `customer_prepayment_list`: 只显示活跃的预收款，按客户统计

#### 新增合并视图：
- `supplier_prepayment_consolidate`: 供应商预付款合并页面
- `customer_prepayment_consolidate`: 客户预收款合并页面

#### 核销视图更新：
- `supplier_account_writeoff`: 只显示活跃的预付款
- `customer_account_writeoff`: 只显示活跃的预收款

### 3. URL路由（apps/finance/urls.py）

```python
path('prepayments/customer/<int:customer_id>/consolidate/',
      views.customer_prepayment_consolidate,
      name='customer_prepayment_consolidate'),
path('prepayments/supplier/<int:supplier_id>/consolidate/',
      views.supplier_prepayment_consolidate,
      name='supplier_prepayment_consolidate'),
```

### 4. 模板文件

#### 列表模板（带统计和合并按钮）：
- `templates/modules/finance/supplier_prepayment_list.html`
- `templates/modules/finance/customer_prepayment_list.html`

#### 合并页面模板：
- `templates/modules/finance/supplier_prepayment_consolidate.html`
- `templates/modules/finance/customer_prepayment_consolidate.html`

### 5. 数据库迁移

```bash
# 创建迁移文件
python3 manage.py makemigrations finance --name add_prepayment_consolidation_fields

# 应用迁移
python3 manage.py migrate finance
```

迁移文件：`apps/finance/migrations/0012_add_prepayment_consolidation_fields.py`

## 使用方法

### 供应商预付款合并

1. **访问预付款列表页**
   ```
   http://127.0.0.1:8000/finance/prepayments/supplier/
   ```

2. **查看统计信息**
   - 在"供应商预付款统计"区域，查看每个供应商的预付款笔数
   - 如果某供应商有2笔或以上预付款，会显示"合并"按钮

3. **执行合并操作**
   - 点击"合并"按钮进入合并页面
   - 勾选要合并的预付款（至少2笔）
   - 查看实时统计信息（选中的笔数和总余额）
   - 点击"合并预付款"按钮提交

4. **合并后的效果**
   - 生成一条新的预付款记录，余额为所有选中记录的余额之和
   - 原记录被标记为"已合并"（status='merged'），不再在列表中显示
   - 核销时只会显示合并后的记录

### 客户预收款合并

操作同上，访问地址：
```
http://127.0.0.1:8000/finance/prepayments/customer/
```

## 业务优势

1. **解决预付金额浪费问题**
   - 避免多次预付金额远超应付，却只能使用单次预付的问题
   - 合并后可一次性使用所有预付款余额

2. **简化核销操作**
   - 多笔预付款合并为一笔，核销时选择更简单
   - 减少操作步骤，提高工作效率

3. **提高财务管理效率**
   - 清晰的预付款状态管理（活跃/已合并/已用完）
   - 统计信息一目了然

## 技术特点

1. **状态管理**
   - 使用 `status` 字段管理预付款状态
   - `is_consolidated` 标识是否为合并记录
   - `merged_into` 外键关联到合并后的记录

2. **数据完整性**
   - 原记录标记为"已合并"而不是物理删除
   - 可追溯合并历史
   - 软删除机制确保数据安全

3. **用户体验**
   - 实时统计选中的预付款笔数和余额
   - 全选/取消全选功能
   - 至少选择2笔才能提交，防止误操作

## 测试验证

### 测试脚本
- `test_prepayment_consolidation.py`: 测试合并功能
- `undo_consolidation.py`: 撤销测试合并，恢复数据

### 测试场景
- ✅ 供应商丙2笔预付款（50,000 + 50,000）合并为1笔（100,000）
- ✅ 合并后原记录状态变为"merged"
- ✅ 合并后记录状态为"active"，标记为合并记录
- ✅ 核销时只显示合并后的记录

## 相关修复

此功能与之前的预付款核销逻辑修复配合使用：

**之前的修复：**
- 修复核销逻辑，优先使用预付款
- 计算公式从 `effective_prepay = min(prepay.balance, max_use)` 改为 `effective_prepay = min(prepay.balance, amount)`

**现在的增强：**
- 允许合并多笔预付款为一笔
- 核销时可使用所有预付款余额
- 完全解决预付金额远超应付却无法充分利用的问题

## 后续建议

1. **批量操作**
   - 可考虑添加"全部合并"按钮，一键合并某供应商/客户的所有预付款

2. **自动合并**
   - 创建预付款时，可提示用户是否与现有预付款合并

3. **拆分功能**
   - 如需要，可添加拆分功能，将合并的记录拆分回原记录

## 文件清单

### 修改的文件
- `apps/finance/models.py`: 添加合并相关字段
- `apps/finance/views.py`: 添加合并视图，更新列表和核销视图
- `apps/finance/urls.py`: 添加合并路由
- `templates/modules/finance/supplier_prepayment_list.html`: 添加统计和合并按钮
- `templates/modules/finance/customer_prepayment_list.html`: 添加统计和合并按钮

### 新增的文件
- `apps/finance/migrations/0012_add_prepayment_consolidation_fields.py`: 数据库迁移
- `templates/modules/finance/supplier_prepayment_consolidate.html`: 供应商合并页面
- `templates/modules/finance/customer_prepayment_consolidate.html`: 客户合并页面
- `test_prepayment_consolidation.py`: 测试脚本
- `undo_consolidation.py`: 撤销脚本
- `PREPAYMENT_CONSOLIDATION_FEATURE.md`: 本文档

## 总结

预付款/预收款合并功能完整实现了用户需求，解决了多次预付（收）导致金额分散无法充分利用的问题。通过状态管理、合并操作和界面优化，提供了一个高效、易用的财务工具。
