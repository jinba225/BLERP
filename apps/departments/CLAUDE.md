[根目录](../../../CLAUDE.md) > [django_erp](../../) > [apps](../) > **departments**

# Departments模块文档

## 模块职责

Departments模块负责组织架构和部门管理。主要职责包括：
- **部门管理**: 部门信息的创建、编辑、删除
- **组织架构**: 层级化的部门结构管理
- **人员关联**: 部门与员工的关联关系

## 核心模型
```python
class Department(BaseModel):
    name = CharField('部门名称', max_length=100)
    code = CharField('部门代码', max_length=50, unique=True)  
    parent = ForeignKey('self', on_delete=SET_NULL, null=True) # 上级部门
    manager = ForeignKey(User, verbose_name='部门经理')
    description = TextField('部门描述', blank=True)
    is_active = BooleanField('是否启用', default=True)
```

## 主要功能
- ✅ 部门基础信息管理
- ✅ 层级部门结构
- ✅ 部门经理分配
- ⚠️ 需要完善组织架构可视化

## 文件清单
- `models.py` - 部门模型
- `apps.py` - 应用配置
- `urls.py` - URL路由

## 测试与质量

### 测试文件位置
```bash
apps/departments/tests/
├── __init__.py
└── test_models.py  # 部门模型测试
```

### 测试覆盖情况
✅ **测试完成度: 100%** (21/21 测试通过)

#### Department模型测试 (9个测试)
- ✅ `test_department_creation` - 部门创建
- ✅ `test_department_unique_code` - 部门代码唯一性
- ✅ `test_department_hierarchy` - 层级关系
- ✅ `test_department_full_name` - 完整路径名称
- ✅ `test_department_get_employee_count` - 员工数量统计
- ✅ `test_department_employee_count_with_subdepartments` - 包含子部门员工数
- ✅ `test_department_soft_delete` - 软删除功能
- ✅ `test_department_ordering` - 排序规则
- ✅ `test_department_str_representation` - 字符串表示

#### Position模型测试 (6个测试)
- ✅ `test_position_creation` - 职位创建
- ✅ `test_position_unique_together` - 唯一性约束
- ✅ `test_position_levels` - 所有职级验证
- ✅ `test_position_ordering` - 按级别排序
- ✅ `test_position_str_representation` - 字符串表示
- ✅ `test_position_level_choices` - 职级选项完整性

#### DepartmentBudget模型测试 (6个测试)
- ✅ `test_budget_creation` - 预算创建
- ✅ `test_budget_total_budget` - 总预算计算
- ✅ `test_budget_total_actual` - 实际支出计算
- ✅ `test_budget_variance` - 预算差异计算
- ✅ `test_budget_variance_percentage` - 差异百分比
- ✅ `test_budget_str_representation` - 字符串表示

### 测试要点
- **MPTT层级**: 部门的树形结构管理和查询
- **计算属性**: full_name、get_employee_count等方法
- **预算计算**: 总预算、实际支出、差异、百分比等财务指标
- **唯一性约束**: 部门代码、职位+部门组合的唯一性
- **排序规则**: 树形排序和职级排序
- **软删除**: BaseModel的软删除功能继承

## 变更记录
### 2025-11-13
- **测试完成**: 添加21个单元测试，覆盖3个核心模型
- **测试通过率**: 100% (21/21)
- **测试内容**: Department(含MPTT)、Position、DepartmentBudget

### 2025-11-08 23:26:47
- 文档初始化，识别基础部门管理功能