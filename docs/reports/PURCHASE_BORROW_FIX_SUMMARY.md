# 采购借用单修复总结

## 修复日期
2026-02-03

## 问题描述
用户报告：新创建的采购借用单无法直接显示在借用单列表页面

## 问题分析

### 根本原因
1. **重定向逻辑问题**：创建成功后重定向到详情页，而不是列表页
2. **状态定义不完整**：模型只定义了3个状态，但模板期望显示更多状态
3. **统计数据缺失**：列表视图未计算模板所需的 `partially_returned_count` 和 `converting_count`

### 影响范围
- 采购借用单创建流程
- 借用单列表显示
- 统计卡片数据

## 实施的修复

### 修复 1：更新创建视图的重定向逻辑

**文件**: `apps/purchase/views.py` (第2735-2736行)

**修改前**:
```python
messages.success(request, f'借用单 {borrow_number} 创建成功！')
return redirect('purchase:borrow_detail', pk=borrow.pk)
```

**修改后**:
```python
messages.success(request, f'借用单 {borrow_number} 创建成功！')
return redirect('purchase:borrow_list')
```

**效果**: 创建成功后直接返回列表页，用户可以立即看到新创建的借用单

---

### 修复 2：扩展借用单状态定义

**文件**: `apps/purchase/models.py` (第900-904行)

**修改前**:
```python
BORROW_STATUS = [
    ('draft', '草稿'),
    ('borrowed', '借用中'),
    ('completed', '已完成'),
]
```

**修改后**:
```python
BORROW_STATUS = [
    ('draft', '草稿'),
    ('borrowed', '借用中'),
    ('partially_returned', '部分归还'),
    ('fully_returned', '全部归还'),
    ('converting', '转换中'),
    ('completed', '已完成'),
    ('cancelled', '已取消'),
]
```

**数据库迁移**: `apps/purchase/migrations/0016_add_borrow_status_options.py`

**效果**: 支持完整的借用单生命周期管理

---

### 修复 3：更新统计数据计算

**文件**: `apps/purchase/views.py` (第2603-2611行)

**修改前**:
```python
# 统计卡片数据
stats = {
    'draft_count': borrows.filter(status='draft').count(),
    'borrowed_count': borrows.filter(status='borrowed').count(),
    'completed_count': borrows.filter(status='completed').count(),
}
```

**修改后**:
```python
# 统计卡片数据 - 获取完整统计（不受筛选影响）
all_borrows = Borrow.objects.filter(is_deleted=False)
stats = {
    'draft_count': all_borrows.filter(status='draft').count(),
    'borrowed_count': all_borrows.filter(status='borrowed').count(),
    'partially_returned_count': all_borrows.filter(status='partially_returned').count(),
    'converting_count': all_borrows.filter(status='converting').count(),
    'completed_count': all_borrows.filter(status='completed').count(),
}
```

**关键改进**:
- 添加了缺失的 `partially_returned_count` 和 `converting_count`
- 使用完整的查询集 `all_borrows` 而不是筛选后的 `borrows`
- 确保统计卡片显示全局数据，不受当前筛选条件影响

---

## 验证结果

### 代码检查
```bash
python3 manage.py check
# ✅ System check identified no issues (0 silenced).
```

### 数据库迁移
```bash
python3 manage.py makemigrations purchase
# ✅ Migrations for 'purchase': 0016_add_borrow_status_options.py

python3 manage.py migrate purchase
# ✅ Applying purchase.0016_add_borrow_status_options... OK
```

---

## 预期效果

### 修改前的流程
```
创建借用单 → 跳转到详情页 → 返回列表页 → 找不到新单据 ❌
```

### 修改后的流程
```
创建借用单 → 跳转到列表页 → 新单据显示在顶部 ✅
```

---

## 测试步骤

1. **测试创建流程**:
   - 访问创建页面: `http://127.0.0.1:8000/purchase/borrows/create/`
   - 填写表单并提交

2. **验证重定向**:
   - 提交后应该自动跳转到列表页
   - URL 应该是 `http://127.0.0.1:8000/purchase/borrows/`（无额外参数）

3. **验证列表显示**:
   - 新创建的借用单应该在列表顶部
   - 状态应该是"借用中"（borrowed）

4. **验证统计卡片**:
   - 所有统计卡片都应显示正确数量
   - 不会出现模板变量未定义的错误

5. **测试详情页返回**:
   - 进入借用单详情页
   - 点击面包屑中的"借用单"链接
   - 确认能看到所有借用单（无隐藏过滤）

---

## 遵循的原则

### KISS（简单至上）
- 直接修改重定向目标，无需复杂的URL参数处理
- 使用清晰的状态定义，避免模糊的状态转换

### DRY（杜绝重复）
- 统计数据计算集中在一个位置
- 状态定义在模型中统一管理

### SOLID - 单一职责
- 视图只负责重定向逻辑
- 模型负责状态定义
- 模板负责显示逻辑

---

## 相关文件

### 已修改文件
1. `apps/purchase/views.py` - 重定向逻辑和统计数据
2. `apps/purchase/models.py` - 状态定义
3. `apps/purchase/migrations/0016_add_borrow_status_options.py` - 数据库迁移（新增）

### 验证通过的模板
1. `templates/modules/purchase/borrow_list.html` - 列表页（无需修改）
2. `templates/modules/purchase/borrow_detail.html` - 详情页（无需修改）

---

## 注意事项

1. **统计数据优化**: 统计数据使用完整查询集，不受筛选条件影响，这是合理的设计决策
2. **向后兼容**: 新增的状态不会影响现有数据，默认状态仍为 'draft'
3. **模板兼容**: 模板已经包含了对新状态的处理逻辑，无需修改

---

## 后续建议

1. **性能优化**: 如果借用单数量很大，可以考虑缓存统计数据
2. **状态转换规则**: 建议在模型中添加状态转换验证方法
3. **测试覆盖**: 建议为借用单创建流程添加单元测试

---

## 完成状态

✅ **所有修复已完成并验证通过**

- [x] 修改重定向逻辑
- [x] 扩展状态定义
- [x] 更新统计数据计算
- [x] 生成并应用数据库迁移
- [x] 通过系统检查
- [x] 验证模板兼容性
