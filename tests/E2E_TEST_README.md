# Django ERP 端到端测试指南

## 概述

Django ERP E2E测试系统提供了全面的业务流程验证，确保跨模块数据一致性和业务逻辑正确性。

## 测试架构

```
tests/
├── __init__.py
├── conftest.py                 # 全局pytest fixtures
├── e2e/                        # 端到端测试
│   └── test_e2e_data_consistency.py
├── helpers/                    # 测试辅助工具
│   └── auto_fixer.py          # 自动修复器
└── scanners/                   # 数据扫描器
    └── scanner_data_integrity.py

apps/
├── core/tests/
│   └── test_fixtures.py       # 测试数据工厂
├── purchase/tests/
│   ├── test_e2e_purchase_flow.py
│   └── test_e2e_borrow_flow.py
├── sales/tests/
│   ├── test_e2e_sales_flow.py
│   └── test_e2e_loan_flow.py
└── finance/tests/
    └── test_e2e_financial_reports.py
```

## 快速开始

### 1. 安装依赖

```bash
pip install pytest==7.4.3 pytest-django==4.7.0 pytest-cov==4.1.0 pytest-xdist==3.5.0 factory-boy==3.3.0 freezegun==1.4.0
```

### 2. 运行所有E2E测试

```bash
# 运行所有E2E测试
pytest -v

# 运行特定模块E2E测试
pytest apps/purchase/tests/test_e2e_purchase_flow.py -v
pytest apps/sales/tests/test_e2e_sales_flow.py -v
pytest apps/finance/tests/test_e2e_financial_reports.py -v

# 并行执行（加速）
pytest -n auto
```

### 3. 生成覆盖率报告

```bash
# 生成HTML覆盖率报告
pytest --cov=apps --cov-report=html

# 查看报告
open htmlcov/index.html
```

## 测试用例说明

### 采购流程E2E测试

**文件**: `apps/purchase/tests/test_e2e_purchase_flow.py`

#### 测试用例

1. **test_complete_purchase_flow_single_receipt**
   - 场景: 一次性收货完整流程
   - 验证: 订单→收货→库存→应付→付款→核销

2. **test_complete_purchase_flow_batch_receipt**
   - 场景: 分批收货完整流程
   - 验证: 分批状态更新、累计收货数量

3. **test_purchase_with_return_flow**
   - 场景: 收货后退货流程
   - 验证: 库存减少、应付退款

4. **test_purchase_edge_cases**
   - 场景: 边界条件
   - 验证: 超量收货、超量退货、重复付款

### 销售流程E2E测试

**文件**: `apps/sales/tests/test_e2e_sales_flow.py`

#### 测试用例

1. **test_complete_sales_flow_single_delivery**
   - 场景: 一次性发货完整流程
   - 验证: 订单→发货→库存→应收→收款→核销

2. **test_complete_sales_flow_batch_delivery**
   - 场景: 分批发货完整流程
   - 验证: 分批状态更新、累计发货数量

3. **test_sales_with_return_flow**
   - 场景: 发货后退货流程
   - 验证: 库存恢复、应收退款

4. **test_sales_edge_cases**
   - 场景: 边界条件
   - 验证: 超量发货、超量退货、重复收款

### 借用流程E2E测试

**文件**:
- `apps/purchase/tests/test_e2e_borrow_flow.py`
- `apps/sales/tests/test_e2e_loan_flow.py`

#### 测试用例

1. **test_borrow_and_return_flow**
   - 场景: 借用后归还
   - 验证: 借用仓库存变动

2. **test_borrow_convert_to_purchase**
   - 场景: 借用转采购
   - 验证: 生成正式采购订单

3. **test_borrow_partial_operations**
   - 场景: 部分归还+部分转采购
   - 验证: 混合操作处理

### 财务报表E2E测试

**文件**: `apps/finance/tests/test_e2e_financial_reports.py`

#### 测试用例

1. **test_balance_sheet_generation**
   - 验证: 资产总计 = 负债总计 + 权益总计

2. **test_income_statement_generation**
   - 验证: 收入 - 成本 - 费用 = 利润

3. **test_cash_flow_statement_generation**
   - 验证: 现金净增加额 = 期末现金 - 期初现金

4. **test_report_data_consistency**
   - 验证: 报表数据与明细账一致性

### 数据一致性验证

**文件**: `tests/e2e/test_e2e_data_consistency.py`

#### 验证规则

1. **采购订单与库存一致性**
   - 订单收货数量 = 库存交易入库数量

2. **应付账款与收货单一致性**
   - 应付金额 = 收货单汇总 - 退货单汇总

3. **销售订单与发货一致性**
   - 订单发货数量 = 库存交易出库数量

4. **应收账款与发货单一致性**
   - 应收金额 = 发货单汇总 - 退货单汇总

## 自动修复工具

### AutoFixer类

**文件**: `tests/helpers/auto_fixer.py`

#### 使用方法

```python
from tests.helpers.auto_fixer import AutoFixer

# 创建修复器
fixer = AutoFixer()

# 修复单个对象
fixer.fix_purchase_order_totals(order)
fixer.fix_supplier_account_aggregation(account)
fixer.fix_inventory_stock_quantity(stock)

# 批量修复
fixer.fix_all_purchase_orders()
fixer.fix_all_supplier_accounts()
fixer.fix_all_inventory_stocks()

# 查看修复记录
for fix in fixer.get_fixes_applied():
    print(f"{fix['model']}: {fix['description']}")
```

#### 修复能力

1. **金额计算错误**: 调用 `calculate_totals()`
2. **数量汇总不一致**: 重新从明细汇总
3. **应付/应收归集错误**: 调用 `aggregate_from_details()`
4. **库存数量偏差**: 重新从交易记录汇总

## 数据扫描器

### ModelFieldScanner类

**文件**: `tests/scanners/scanner_data_integrity.py`

#### 使用方法

```python
from tests.scanners.scanner_data_integrity import ModelFieldScanner

# 创建扫描器
scanner = ModelFieldScanner()

# 运行所有扫描
issues = scanner.scan_all()

# 打印报告
scanner.print_report(issues)
```

#### 扫描规则

1. **Decimal字段精度**: 金额字段精度检查
2. **外键级联删除**: 核心业务数据保护检查
3. **状态流转完整性**: 状态字段choices检查
4. **计算方法正确性**: calculate_totals()方法检查
5. **索引优化**: 常用查询字段索引检查

## Fixtures使用

### 全局Fixtures

**文件**: `tests/conftest.py`

```python
def test_example(test_users, test_supplier, test_customer, test_products, test_warehouse):
    """
    test_users: 包含5种角色的用户
    test_supplier: 测试供应商
    test_customer: 测试客户
    test_products: 3个测试产品
    test_warehouse: (主仓库, 借用仓)
    """
    admin = test_users['admin']
    pass
```

### FixtureFactory

**文件**: `apps/core/tests/test_fixtures.py`

```python
from apps.core.tests.test_fixtures import FixtureFactory

# 创建产品
product = FixtureFactory.create_product(
    code='PROD001',
    name='测试产品',
    cost_price=Decimal('100.00'),
    selling_price=Decimal('150.00')
)

# 创建采购订单
order = FixtureFactory.create_purchase_order(
    user=admin,
    supplier=supplier,
    items_data=[
        {'product': product1, 'quantity': 100, 'unit_price': 10},
        {'product': product2, 'quantity': 50, 'unit_price': 15}
    ]
)

# 创建销售订单
order = FixtureFactory.create_sales_order(
    user=admin,
    customer=customer,
    items_data=[
        {'product': product1, 'quantity': 100, 'unit_price': 15}
    ]
)
```

## 最佳实践

### 1. 测试隔离

每个测试应该独立运行，不依赖其他测试的状态：

```python
@pytest.mark.django_db
def test_something(test_users):
    # 每个测试都创建自己的数据
    order = create_order(test_users['admin'])
    # 不要依赖其他测试创建的数据
```

### 2. 使用Fixtures

优先使用全局fixtures和FixtureFactory，避免重复代码：

```python
# ✅ 好的做法
def test_purchase(test_users, test_supplier, test_products):
    admin = test_users['admin']
    order = FixtureFactory.create_purchase_order(...)

# ❌ 不好的做法
def test_purchase():
    user = User.objects.create_user(...)
    supplier = Supplier.objects.create(...)
    product = Product.objects.create(...)
```

### 3. 明确断言

使用清晰的断言消息，便于调试：

```python
# ✅ 好的做法
assert order.status == 'confirmed', f"订单状态应该是confirmed，实际是{order.status}"

# ❌ 不好的做法
assert order.status == 'confirmed'
```

### 4. 验证副作用

不仅验证主要结果，还要验证副作用（库存、应收应付等）：

```python
# 不仅要验证订单状态
assert order.status == 'fully_received'

# 还要验证库存和应付
stock = InventoryStock.objects.get(product=product)
assert stock.quantity == expected_quantity

account = SupplierAccount.objects.get(purchase_order=order)
assert account.outstanding_amount == expected_amount
```

## 持续集成

### GitHub Actions示例

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run E2E tests
        run: |
          pytest -v --cov=apps --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 故障排查

### 常见问题

1. **数据库错误**
   ```
   django.db.utils.OperationalError: no such table
   ```
   解决: 确保使用 `@pytest.mark.django_db` 装饰器

2. **外键约束错误**
   ```
   django.db.utils.IntegrityError: FOREIGN KEY constraint failed
   ```
   解决: 检查是否正确创建了关联对象

3. **时间敏感测试失败**
   ```
   AssertionError: assert datetime.datetime(2026, 2, 8, 0, 0) == datetime.datetime(2026, 2, 7, 16, 30, 21)
   ```
   解决: 使用 `freezegun.freeze_time()` 冻结时间

### 调试技巧

```python
# 1. 使用pytest的pdb调试
pytest -vv --pdb

# 2. 只运行失败的测试
pytest --lf

# 3. 先运行上次失败的测试
pytest --ff

# 4. 打印详细输出
pytest -vv -s
```

## 性能优化

### 并行执行

```bash
# 使用所有CPU核心
pytest -n auto

# 指定工作进程数
pytest -n 4
```

### 选择性运行

```bash
# 只运行E2E测试
pytest -m e2e

# 只运行快速测试
pytest -m "not slow"

# 只运行特定模块
pytest apps/purchase/tests/test_e2e_purchase_flow.py
```

## 总结

Django ERP E2E测试系统提供：

- ✅ 21个端到端测试用例
- ✅ 跨模块数据一致性验证
- ✅ 自动修复工具
- ✅ 代码质量扫描器
- ✅ 全面的测试fixtures

通过这些测试，可以确保：
- 业务流程端到端正确性
- 跨模块数据一致性
- 财务报表准确性
- 及时发现和修复问题
