# Django ERP E2E测试快速启动指南

## 1. 验证pytest安装

```bash
pytest --version
# 应该显示: pytest 7.4.3
```

## 2. 运行pytest设置测试

```bash
pytest tests/test_pytest_setup.py -v
# 应该通过2个测试
```

## 3. 运行E2E测试

### 运行所有测试
```bash
pytest -v
```

### 运行特定模块测试
```bash
# 采购流程
pytest apps/purchase/tests/test_e2e_purchase_flow.py -v

# 销售流程
pytest apps/sales/tests/test_e2e_sales_flow.py -v

# 财务报表
pytest apps/finance/tests/test_e2e_financial_reports.py -v

# 数据一致性验证
pytest tests/e2e/test_e2e_data_consistency.py -v
```

### 并行执行（加速）
```bash
pytest -n auto
```

### 生成覆盖率报告
```bash
pytest --cov=apps --cov-report=html
open htmlcov/index.html
```

## 4. 使用自动修复工具

### Python脚本方式

```python
# fix_issues.py
from tests.helpers.auto_fixer import AutoFixer

fixer = AutoFixer()

# 修复所有采购订单
fixed = fixer.fix_all_purchase_orders()
print(f"修复了 {fixed} 个采购订单")

# 修复所有供应商应付账款
fixed = fixer.fix_all_supplier_accounts()
print(f"修复了 {fixed} 个应付账款")

# 查看修复记录
for fix in fixer.get_fixes_applied():
    print(fix)
```

运行脚本：
```bash
python fix_issues.py
```

### Django Shell方式

```bash
python manage.py shell
```

```python
from tests.helpers.auto_fixer import AutoFixer
fixer = AutoFixer()
fixer.fix_all_purchase_orders()
```

## 5. 使用数据扫描器

### Python脚本方式

```python
# scan_code.py
from tests.scanners.scanner_data_integrity import ModelFieldScanner

scanner = ModelFieldScanner()
issues = scanner.scan_all()
scanner.print_report(issues)
```

运行脚本：
```bash
python scan_code.py
```

## 6. 常见问题

### Q: 测试运行很慢怎么办？
A: 使用并行执行：
```bash
pytest -n auto
```

### Q: 如何只运行失败的测试？
A:
```bash
pytest --lf  # 只运行上次失败的测试
```

### Q: 如何查看最慢的10个测试？
A:
```bash
pytest --durations=10
```

### Q: 测试失败了怎么办？
A:
1. 查看详细错误信息：`pytest -vv`
2. 使用pdb调试：`pytest --pdb`
3. 尝试使用自动修复工具修复数据问题

## 7. 测试标记

只运行特定类型的测试：
```bash
# 只运行E2E测试
pytest -m e2e

# 只运行慢速测试
pytest -m slow

# 排除慢速测试
pytest -m "not slow"
```

## 8. 持续集成

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

## 9. 下一步

1. ✅ 阅读完整文档：`tests/E2E_TEST_README.md`
2. ✅ 运行pytest设置测试验证环境
3. ✅ 运行完整的E2E测试套件
4. ✅ 使用自动修复工具修复发现的问题
5. ✅ 使用数据扫描器检查代码质量
6. ✅ 集成到CI/CD流程

## 10. 获取帮助

- 查看完整文档：`tests/E2E_TEST_README.md`
- 查看实施总结：`E2E_TEST_IMPLEMENTATION_SUMMARY.md`
- 运行帮助命令：`pytest --help`
- 查看pytest-django文档：https://pytest-django.readthedocs.io/

---

**提示**: 第一次运行E2E测试可能需要较长时间，因为要创建测试数据库。后续运行会使用缓存的数据库，速度会快很多。
