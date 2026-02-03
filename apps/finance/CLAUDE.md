[根目录](../../../CLAUDE.md) > [django_erp](../../) > [apps](../) > **finance**

# Finance模块文档

## 模块职责

Finance模块负责财务管理功能。主要职责包括：
- **应收应付管理**: 客户应收款和供应商应付款
- **收付款记录**: 收款和付款流水管理
- **费用管理**: 费用报销申请、审批、支付流程
- **会计核算**: 会计科目、凭证、分录管理
- **财务报表**: 资产负债表、利润表、现金流量表、科目余额表

## 核心模型
```python
class Expense(BaseModel):
    """费用报销单模型"""
    EXPENSE_STATUS = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('approved', '已审批'),
        ('rejected', '已拒绝'),
        ('paid', '已支付'),
        ('cancelled', '已取消'),
    ]

    EXPENSE_CATEGORY = [
        ('travel', '差旅费'),
        ('transportation', '交通费'),
        ('meal', '餐饮费'),
        ('office', '办公费'),
        ('communication', '通讯费'),
        ('utilities', '水电费'),
        ('entertainment', '业务招待费'),
        ('training', '培训费'),
        ('maintenance', '维修费'),
        ('advertising', '广告费'),
        ('other', '其他费用'),
    ]

    expense_number = CharField('费用单号', max_length=100, unique=True)
    expense_date = DateField('费用日期')
    applicant = ForeignKey(User, verbose_name='申请人')
    department = ForeignKey('departments.Department', verbose_name='申请部门')
    category = CharField('费用类别', choices=EXPENSE_CATEGORY)
    amount = DecimalField('费用金额', max_digits=12, decimal_places=2)
    status = CharField('状态', choices=EXPENSE_STATUS, default='draft')

    # 审批信息
    approved_by = ForeignKey(User, verbose_name='审批人')
    approved_at = DateTimeField('审批时间')

    # 支付信息
    paid_by = ForeignKey(User, verbose_name='支付人')
    payment_account = ForeignKey(Account, verbose_name='支付科目')
    journal = ForeignKey(Journal, verbose_name='关联凭证')

    def submit(self, user=None): ...
    def approve(self, approved_by_user): ...
    def reject(self, rejected_by_user, reason): ...
    def mark_paid(self, paid_by_user, payment_account=None, auto_create_journal=True): ...

class Account(BaseModel):
    """会计科目"""
    code = CharField('科目代码', max_length=20, unique=True)
    name = CharField('科目名称', max_length=100)
    account_type = CharField('科目类型', choices=ACCOUNT_TYPES)

class Journal(BaseModel):
    """会计凭证"""
    journal_number = CharField('凭证号', max_length=50, unique=True)
    journal_type = CharField('凭证类型', choices=JOURNAL_TYPES)
    status = CharField('状态', choices=JOURNAL_STATUS, default='draft')
    total_debit = DecimalField('借方合计')
    total_credit = DecimalField('贷方合计')
```

## 主要功能

### ✅ 费用管理（完整实现）
- **费用创建**: 草稿状态的费用单创建和编辑
- **费用提交**: 提交费用单进入审批流程
- **费用审批**: 审批通过或拒绝（需填写拒绝原因）
- **费用支付**: 审批通过后可支付费用，自动生成会计凭证
- **状态流转**: draft → submitted → approved/rejected → paid
- **自动记账**: 支付时自动生成会计凭证（借：费用科目，贷：支付科目）
- **费用分类**: 11种费用类别，自动映射到会计科目（6601销售费用/6602管理费用）

### ✅ 会计核算
- **会计科目**: 科目代码、名称、类型、层级关系管理
- **会计凭证**: 凭证创建、分录管理、借贷平衡验证
- **自动凭证**: 费用支付自动生成凭证，确保账务一致

### ✅ 财务报表
- **资产负债表**: 资产、负债、所有者权益自动汇总
- **利润表**: 收入、成本、费用自动计算净利润（含费用数据）
- **现金流量表**: 现金类科目变动统计
- **科目余额表**: 所有科目期初、发生额、期末余额
- **报表集成**: 费用数据通过会计凭证自动集成到利润表

### ⚠️ 规划中功能
- 需要完善收付款流程

## 文件清单
- `models.py` - 财务模型（Expense、Account、Journal、JournalEntry等）
- `views_expense.py` - 费用管理视图（10个视图函数）
- `report_generator.py` - 财务报表生成器（自动集成费用数据）
- `admin.py` - Django Admin配置
- `urls.py` - URL路由配置
- `apps.py` - 应用配置

## 测试与质量

### 测试文件位置
```bash
apps/finance/tests/
├── __init__.py
└── test_models.py  # 财务模型测试
```

### 测试覆盖情况
✅ **测试完成度: 100%** (24/24 测试通过)

#### PaymentRecord模型测试 (7个测试)
- ✅ `test_payment_record_creation` - 收付款记录创建
- ✅ `test_payment_types` - 所有付款类型验证
- ✅ `test_payment_status_choices` - 所有状态验证
- ✅ `test_payment_methods` - 所有付款方式验证
- ✅ `test_payment_ordering` - 按付款日期倒序
- ✅ `test_payment_soft_delete` - 软删除功能
- ✅ `test_payment_str_representation` - 字符串表示

#### Invoice模型测试 (8个测试)
- ✅ `test_invoice_creation` - 发票创建
- ✅ `test_invoice_unique_number` - 发票号唯一性
- ✅ `test_invoice_types` - 发票类型验证
- ✅ `test_invoice_status_choices` - 发票状态验证
- ✅ `test_invoice_total_calculation` - 总金额计算
- ✅ `test_invoice_paid_amount_tracking` - 已付金额追踪
- ✅ `test_invoice_ordering` - 按发票日期倒序
- ✅ `test_invoice_str_representation` - 字符串表示

#### Expense模型测试 (6个测试)
- ✅ `test_expense_creation` - 费用记录创建
- ✅ `test_expense_categories` - 费用分类验证
- ✅ `test_expense_status_choices` - 审批状态验证
- ✅ `test_expense_with_department` - 部门关联
- ✅ `test_expense_ordering` - 按费用日期倒序
- ✅ `test_expense_str_representation` - 字符串表示

#### AccountBalance模型测试 (3个测试)
- ✅ `test_account_balance_creation` - 账户余额创建
- ✅ `test_account_balance_unique_date` - 日期唯一性
- ✅ `test_account_balance_str_representation` - 字符串表示

### 测试要点
- **付款类型**: 应收款、应付款的完整验证
- **状态管理**: 待付款、部分付款、已付款、已取消等状态流转
- **付款方式**: 现金、银行转账、支票、承兑汇票等
- **发票管理**: 唯一发票号、总金额计算、已付金额追踪
- **费用管理**: 费用分类、审批流程、部门关联
- **账户余额**: 日期唯一性约束
- **软删除**: BaseModel的软删除功能

## 变更记录

### 2026-01-11（费用管理模块完整实现）
- **Expense模型**: 创建完整的费用报销单模型，包含11种费用类别
- **数据库迁移**: 创建并应用migration 0009_expense.py
- **Admin配置**: 添加ExpenseAdmin，支持自动生成费用单号
- **视图层实现**: 创建10个视图函数（CRUD + 工作流）
  - expense_list - 费用列表（搜索、过滤、分页、统计）
  - expense_create - 创建费用
  - expense_detail - 费用详情
  - expense_edit - 编辑费用（仅草稿状态）
  - expense_delete - 删除费用（软删除）
  - expense_submit - 提交审批
  - expense_approve - 审批通过
  - expense_reject - 审批拒绝（需填写原因）
  - expense_pay - 支付费用（自动生成会计凭证）
- **URL路由**: 配置9个费用管理路由
- **模板实现**: 创建8个完整模板
  - expense_list.html - 费用列表
  - expense_form.html - 费用表单（创建/编辑）
  - expense_detail.html - 费用详情
  - expense_confirm_delete.html - 删除确认
  - expense_confirm_submit.html - 提交确认
  - expense_confirm_approve.html - 审批确认
  - expense_confirm_reject.html - 拒绝确认
  - expense_pay.html - 支付表单
- **自动记账**: 费用支付自动生成会计凭证（借：费用科目，贷：支付科目）
- **费用科目映射**:
  - 销售费用(6601): 差旅费、交通费、餐饮费、业务招待费、广告费
  - 管理费用(6602): 办公费、通讯费、水电费、培训费、维修费、其他
- **报表集成**: 费用数据通过会计凭证自动集成到利润表，无需修改报表生成器
- **工作流程**: 完整的费用报销流程（创建→提交→审批→支付）

### 2025-11-13
- **测试完成**: 添加24个单元测试，覆盖4个核心模型
- **测试通过率**: 100% (24/24)
- **测试内容**: PaymentRecord、Invoice、Expense、AccountBalance

### 2025-11-08 23:26:47
- 文档初始化，模块处于规划阶段