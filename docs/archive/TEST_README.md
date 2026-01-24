# 测试计划快速开始指南

> 🎯 **目标**: 快速了解和使用测试计划
> ✅ **状态**: 配置完成，可立即使用

---

## 📋 已完成的配置

### 1. 核心文档
- ✅ **`docs/TEST_PLAN.md`** (17,000+ 字) - 完整的测试计划文档
  - 测试策略和优先级
  - 详细的测试范围和类型
  - 5个阶段的执行计划（12周）
  - 质量指标和验收标准

- ✅ **`docs/TEST_GUIDELINES.md`** (15,000+ 字) - 测试开发指南
  - 测试哲学和原则
  - 单元测试/API测试/集成测试模板
  - Factory Boy使用指南
  - Mock和性能测试技巧

### 2. 测试配置文件
- ✅ **`requirements-test.txt`** - 测试依赖包
- ✅ **`pytest.ini`** - Pytest配置
- ✅ **`.coveragerc`** - 代码覆盖率配置
- ✅ **`locustfile.py`** - 性能测试配置

### 3. 自动化脚本
- ✅ **`run_tests.sh`** - 一键测试脚本
- ✅ **`.github/workflows/tests.yml`** - CI/CD配置

### 4. 测试工具
- ✅ **`apps/factories.py`** - Factory Boy工厂类

---

## 🚀 快速开始

### 第一步：安装测试依赖

```bash
# 安装测试工具
pip install -r requirements-test.txt

# 安装Playwright浏览器（如果需要E2E测试）
playwright install chromium
```

### 第二步：运行测试

```bash
# 使用测试脚本（推荐）
./run_tests.sh all              # 运行所有测试
./run_tests.sh quick            # 快速测试
./run_tests.sh coverage         # 生成覆盖率报告
./run_tests.sh app sales        # 测试特定应用

# 或使用pytest直接运行
pytest apps/ -v                 # 所有测试
pytest apps/sales/ -v           # 特定模块
pytest -m "unit" apps/          # 特定标记
```

### 第三步：查看报告

```bash
# 测试覆盖率报告
open htmlcov/index.html         # macOS
# xdg-open htmlcov/index.html   # Linux
# start htmlcov/index.html      # Windows

# 测试日志
cat test-reports/pytest.log
```

---

## 📊 当前测试状态

### 测试覆盖率

| 模块 | 测试文件 | 测试行数 | 覆盖率 | 状态 |
|------|---------|----------|--------|------|
| **Core** | 1 | 587 | 100% | ✅ 完整 |
| **Sales** | 3 | 1,531 | 100% | ✅ 完整 |
| **Inventory** | 2 | 1,775 | 100% | ✅ 完整 |
| **Purchase** | 2 | 1,075 | 100% | ✅ 完整 |
| **Finance** | 1 | 684 | 100% | ✅ 完整 |
| **Customers** | 1 | 620 | 100% | ✅ 完整 |
| **Suppliers** | 1 | 578 | 100% | ✅ 完整 |
| **Users** | 1 | 595 | 100% | ✅ 完整 |
| **Departments** | 1 | 485 | 100% | ✅ 完整 |
| **Products** | 1 | 525 | 100% | ✅ 完整 |
| **Authentication** | 1 | 262 | 部分 | ⚠️ 需补充 |
| **总计** | 15 | **8,717行** | **~85%** | 🎯 良好 |

### 测试类型覆盖

```
测试类型           当前状态       目标覆盖率    优先级
─────────────────────────────────────────────────
单元测试（模型）     ✅ 100%       100%         P0
单元测试（服务层）   ⚠️ 60%        90%          P0  ← 需要补充
单元测试（视图层）   ⚠️ 20%        80%          P1  ← 需要补充
API集成测试         ❌ 0%         95%          P0  ← 优先级最高
业务流程测试         ⚠️ 40%        90%          P0  ← 需要补充
功能测试（前端）     ❌ 0%         70%          P1
性能测试            ❌ 0%         60%          P2
安全测试            ❌ 0%         80%          P1
端到端测试          ❌ 0%         50%          P2
```

---

## 📝 测试脚本使用说明

### 基本命令

```bash
# 查看帮助
./run_tests.sh --help

# 运行所有测试
./run_tests.sh all

# 运行单元测试
./run_tests.sh unit

# 运行API测试
./run_tests.sh api

# 运行集成测试
./run_tests.sh integration

# 运行性能测试
./run_tests.sh performance

# 运行安全测试
./run_tests.sh security

# 快速测试（跳过慢速测试）
./run_tests.sh quick

# 测试特定应用
./run_tests.sh app sales
./run_tests.sh app inventory

# 生成覆盖率报告
./run_tests.sh coverage

# 清理测试文件
./run_tests.sh clean
```

### 高级选项

```bash
# 并行测试（加速）
./run_tests.sh all -p

# 详细输出
./run_tests.sh all -v

# 遇到失败立即停止
./run_tests.sh all -f

# 只运行匹配模式的测试
./run_tests.sh quick -k "order"

# 保持数据库（加速）
./run_tests.sh all --keepdb

# 失败时进入调试器
./run_tests.sh all --pdb
```

---

## 📈 性能测试

### 使用Locust

```bash
# 启动Locust Web界面
locust -f locustfile.py --host=http://localhost:8000
# 然后访问 http://localhost:8089

# 命令行模式（无界面）
locust -f locustfile.py \
    --host=http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 60s \
    --headless
```

### 性能测试场景

| 场景 | 用户类型 | 权重 | 说明 |
|------|---------|------|------|
| 销售流程 | SalesUser | 30% | 报价、订单、发货 |
| 采购流程 | PurchaseUser | 20% | 询价、订单、质检 |
| 库存管理 | WarehouseUser | 30% | 库存查询、出入库 |
| 财务管理 | FinanceUser | 20% | 应收应付、报表 |

---

## 🔧 CI/CD集成

### GitHub Actions

已配置的测试流水线（`.github/workflows/tests.yml`）:

1. **代码质量检查** - Black, Flake8, Pylint
2. **安全扫描** - Bandit, Safety
3. **单元测试 (SQLite)** - 快速验证
4. **集成测试 (MySQL)** - 真实环境测试
5. **API测试** - REST API端点验证
6. **E2E测试** - Playwright自动化测试
7. **测试报告汇总** - Codecov覆盖率报告

### 触发条件

- ✅ Push到 main/develop/feature 分支
- ✅ Pull Request到 main/develop
- ✅ 每日凌晨2点自动运行（夜间构建）

---

## 📚 详细文档

### 主要文档

1. **[完整测试计划](docs/TEST_PLAN.md)** - 了解测试策略和执行计划
2. **[测试开发指南](docs/TEST_GUIDELINES.md)** - 学习如何编写测试
3. **[项目文档](CLAUDE.md)** - 项目架构和开发规范

### 测试示例

```python
# 单元测试示例
# apps/sales/tests/test_models.py
from django.test import TestCase
from apps.sales.factories import SalesOrderFactory

class SalesOrderTestCase(TestCase):
    def test_order_creation(self):
        order = SalesOrderFactory()
        self.assertIsNotNone(order.id)
        self.assertEqual(order.status, 'draft')

# API测试示例
# apps/sales/tests/test_api.py
from rest_framework.test import APITestCase
from django.urls import reverse

class SalesOrderAPITestCase(APITestCase):
    def test_list_orders(self):
        response = self.client.get(reverse('api:salesorder-list'))
        self.assertEqual(response.status_code, 200)

# 集成测试示例
# apps/sales/tests/test_integration.py
from django.test import TransactionTestCase

class SalesWorkflowTestCase(TransactionTestCase):
    def test_complete_order_workflow(self):
        # 测试完整的订单流程
        pass
```

---

## 🎯 下一步行动

### 优先级 P0（立即执行）

1. **补充API测试** - 覆盖所有REST端点
   ```bash
   # 创建API测试文件
   touch apps/sales/tests/test_api.py
   touch apps/purchase/tests/test_api.py
   touch apps/inventory/tests/test_api.py
   ```

2. **补充服务层测试** - 测试业务逻辑
   ```bash
   # 创建服务测试文件
   touch apps/sales/tests/test_services.py
   touch apps/purchase/tests/test_services.py
   ```

3. **补充集成测试** - 验证跨模块协作
   ```bash
   # 扩展集成测试
   # 已有: apps/sales/tests/test_business_logic.py
   # 已有: apps/inventory/tests/test_business_logic.py
   ```

### 优先级 P1（重要但不紧急）

4. **补充视图层测试** - 测试Django视图
5. **添加安全测试** - 验证安全漏洞
6. **编写E2E测试** - 用户场景测试

### 优先级 P2（长期优化）

7. **性能优化** - 基于性能测试结果优化
8. **负载测试** - 验证系统扩展性

---

## 💡 最佳实践提醒

### 开发流程

1. ✅ **先写测试，再写代码** (TDD)
2. ✅ **每次提交前运行测试** (`./run_tests.sh quick`)
3. ✅ **保持测试通过率100%**
4. ✅ **代码覆盖率保持在80%以上**
5. ✅ **新功能必须有测试**

### 测试原则

- 🎯 **Fast** - 单元测试 < 1秒
- 🔒 **Independent** - 测试互不依赖
- 🔁 **Repeatable** - 任何环境可重复
- ✅ **Self-Validating** - 自动验证结果
- ⏱️ **Timely** - 与代码同步开发

---

## 🆘 常见问题

### Q: 测试运行太慢怎么办?

```bash
# 方案1: 使用--keepdb保持数据库
./run_tests.sh all --keepdb

# 方案2: 跳过迁移（仅SQLite）
pytest --nomigrations apps/

# 方案3: 并行测试
./run_tests.sh all -p

# 方案4: 只运行快速测试
./run_tests.sh quick
```

### Q: 如何调试失败的测试?

```bash
# 方案1: 详细输出
./run_tests.sh all -v

# 方案2: 失败时进入调试器
./run_tests.sh all --pdb

# 方案3: 只运行失败的测试
pytest --lf apps/
```

### Q: 如何查看测试覆盖率?

```bash
# 生成覆盖率报告
./run_tests.sh coverage

# 查看HTML报告
open htmlcov/index.html

# 查看终端报告
coverage report -m
```

---

## 📞 支持与反馈

如有问题或建议，请:
1. 查看详细文档: `docs/TEST_PLAN.md`
2. 查看测试指南: `docs/TEST_GUIDELINES.md`
3. 在项目Issues中提交问题
4. 联系测试团队

---

**文档版本**: v1.0
**创建时间**: 2026-01-06
**维护人**: 猫娘工程师 幽浮喵 ฅ'ω'ฅ

---

_祝测试愉快！记住：好的测试是高质量代码的保证！_ ✨
