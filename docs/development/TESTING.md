# 测试指南

## 🧪 运行测试

由于项目目录结构重组（apps/），Django 的默认测试发现器存在问题。我们提供了自定义测试运行脚本。

### 推荐方式：使用自定义测试脚本

```bash
# 运行所有测试
python run_tests.py

# 运行特定应用的测试
python run_tests.py collect
python run_tests.py sales
python run_tests.py purchase

# 运行特定测试模块
python run_tests.py collect.tests.test_models

# 运行特定测试类
python run_tests.py collect.tests.test_models.PlatformModelTest

# 保留测试数据库（加速测试）
python run_tests.py collect -k

# 调整输出详细程度
python run_tests.py collect -v 1
python run_tests.py collect -v 2
python run_tests.py collect -v 3
```

### 传统方式（有限支持）

```bash
# 注意：以下命令可能因为测试发现器问题而失败
# 建议使用上面的自定义测试脚本

# 运行所有测试（可能失败）
python manage.py test

# 运行特定应用测试（可能失败）
python manage.py test collect
```

## 📝 测试文件位置

测试文件位于各个应用的 `tests/` 目录：

```
apps/
├── collect/
│   └── tests/
│       ├── __init__.py
│       └── test_models.py
├── sales/
│   └── tests/
│       └── test_models.py
└── ...
```

## 🔧 测试脚本说明

`run_tests.py` 是一个自定义的 Django 测试运行器，解决了以下问题：

1. **路径问题**：自动添加 `apps/` 到 Python 路径
2. **测试发现**：绕过 Django 的测试发现器问题
3. **灵活性**：支持多种测试粒度（所有测试、应用、模块、类）

## 📊 测试覆盖率

当前已实现测试的应用：

- ✅ collect（采集模块）
- 🚧 其他应用（测试待添加）

## 🐛 已知问题

### Django 测试发现器问题

**症状**：
```
ImportError: 'tests' module incorrectly imported from '/path/to/apps/collect/tests'
```

**解决方案**：
使用自定义测试脚本 `run_tests.py` 而不是 `python manage.py test`。

**原因**：
Django 的测试发现器在处理 apps/ 目录下的测试时存在问题，这与我们的目录结构重组有关。

---

**文档更新时间**: 2026-02-03
**相关变更**: 方案 C 深度重构
