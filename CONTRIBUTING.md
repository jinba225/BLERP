# 贡献指南

感谢您对Django ERP项目的关注！我们欢迎所有形式的贡献。

---

## 📋 目录

- [行为准则](#-行为准则)
- [如何贡献](#-如何贡献)
- [开发流程](#-开发流程)
- [代码规范](#-代码规范)
- [提交规范](#-提交规范)
- [Pull Request流程](#-pull-request流程)

---

## 🤝 行为准则

### 我们的承诺

为了营造开放和友好的环境，我们承诺让每个人都能参与项目，不受歧视。

### 我们的承诺

- 使用包容性语言
- 尊重不同观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

---

## 🚀 如何贡献

### 贡献方式

1. **报告Bug** 🐛
   - 在GitHub Issues中提交Bug报告
   - 详细描述问题、复现步骤、期望行为
   - 提供环境信息和日志

2. **讨论新功能** 💡
   - 在GitHub Issues中提出功能建议
   - 说明功能价值和用例
   - 讨论实现可行性

3. **提交代码** 🔧
   - Fork项目并创建特性分支
   - 遵循代码规范
   - 编写测试和文档
   - 提交Pull Request

4. **改进文档** 📖
   - 修正文档错误
   - 补充使用示例
   - 翻译文档

5. **帮助其他用户** 💬
   - 回答GitHub Issues中的问题
   - 帮助新用户上手
   - 分享使用经验

---

## 🔨 开发流程

### 1. 准备环境

```bash
# Fork并克隆仓库
git clone https://github.com/YOUR-USERNAME/django-erp.git
cd django-erp

# 添加上游仓库
git remote add upstream https://github.com/ORIGINAL-OWNER/django-erp.git

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 安装pre-commit hooks
pre-commit install
```

### 2. 创建特性分支

```bash
# 从main分支创建特性分支
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

### 3. 开发和测试

```bash
# 运行测试
pytest apps/**/test_e2e_*.py -v

# 代码质量检查
black . --line-length=100
flake8 . --max-line-length=100
isort . --profile black

# 提交前检查
pre-commit run --all-files
```

### 4. 提交更改

```bash
# 添加更改
git add .

# 提交（遵循提交规范）
git commit -m "feat: add new feature description"
```

---

## 📐 代码规范

### Python代码风格

我们遵循以下代码规范：

- **PEP 8** - Python官方代码风格指南
- **Black** - 代码格式化工具（行长度100）
- **flake8** - 代码检查工具
- **isort** - Import排序工具

### 运行代码格式化

```bash
# 自动格式化
black . --line-length=100

# 排序imports
isort . --profile black

# 检查代码质量
flake8 . --max-line-length=100 --ignore=E203,W503
```

### Django规范

#### 模型组织

```python
# ✅ 好的做法
from django.db import models
from core.models import BaseModel


class Product(BaseModel):
    """产品模型"""
    
    name = models.CharField('产品名称', max_length=200)
    quantity = models.IntegerField('数量', default=0)
    
    class Meta:
        verbose_name = '产品'
        verbose_name_plural = '产品'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # 自定义保存逻辑
        super().save(*args, **kwargs)
```

#### 视图组织

```python
# ✅ 好的做法
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product
from .forms import ProductForm


@login_required
def product_list(request):
    """产品列表视图"""
    products = Product.objects.all()
    return render(request, 'products/list.html', {'products': products})
```

### 模板规范

#### 使用注释

```html
<!-- 产品列表 -->
{% extends "base.html" %}

{% block content %}
<div class="product-list">
    <!-- 遍历产品 -->
    {% for product in products %}
    <div class="product-item">
        {{ product.name }}
    </div>
    {% endfor %}
</div>
{% endblock %}
```

### JavaScript规范

```javascript
// ✅ 好的做法
function updateProduct(productId, data) {
    fetch(`/api/products/${productId}/`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification('success', '产品更新成功');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('error', '产品更新失败');
    });
}
```

---

## 📝 提交规范

我们遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/) 规范。

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type类型

- **feat**: 新功能
- **fix**: Bug修复
- **docs**: 文档更新
- **style**: 代码格式（不影响功能）
- **refactor**: 重构（不是新功能也不是修复）
- **perf**: 性能优化
- **test**: 添加测试
- **chore**: 构建/工具链更新
- **ci**: CI/CD配置

### 示例

```bash
# 新功能
git commit -m "feat(sales): add bulk export for sales orders"

# Bug修复
git commit -m "fix(inventory): correct stock calculation after transfer"

# 文档
git commit -m "docs: update installation guide for Python 3.13"

# 重构
git commit -m "refactor(core): simplify base model logic"

# 性能
git commit -m "perf(api): optimize database query with select_related"

# 测试
git commit -m "test(purchase): add E2E tests for purchase flow"
```

### 详细格式

```bash
# 带正文和footer的提交
git commit -m "feat(finance): add automatic journal entry for expense payment

- Create journal entry when expense is marked as paid
- Debit: expense account, Credit: payment account
- Ensure debit-credit balance

Closes #123"
```

---

## 🔀 Pull Request流程

### 1. 确保代码是最新的

```bash
git checkout main
git pull upstream main
git checkout feature/your-feature
git rebase main
```

### 2. 推送到您的Fork

```bash
git push origin feature/your-feature
```

### 3. 创建Pull Request

1. 访问GitHub上的原始仓库
2. 点击"New Pull Request"
3. 填写PR模板：
   - 标题：简洁描述更改
   - 描述：详细说明变更内容和原因
   - 关联相关Issue：`Closes #123`
   - 截图：如有UI变更

### 4. PR检查清单

在提交PR前，请确认：

- [ ] 代码通过所有测试（`pytest apps/**/test_e2e_*.py -v`）
- [ ] 代码通过代码质量检查（`black .`, `flake8 .`, `isort .`）
- [ ] 新功能有相应的测试
- [ ] 文档已更新（如需要）
- [ ] 提交信息符合规范
- [ ] PR标题清晰描述变更

### 5. 代码审查

维护者会审查您的代码并提出建议。请：

- 及时响应审查意见
- 解释您的实现选择
- 按要求修改代码
- 保持友好和专业的态度

### 6. 合并

一旦PR通过审查：
- 维护者将合并您的代码
- 您的分支将被删除
- 您的贡献将被记录在CHANGELOG中

---

## 🧪 测试指南

### 编写测试

#### E2E测试示例

```python
import pytest
from decimal import Decimal
from sales.models import SalesOrder, SalesOrderItem
from core.tests.test_fixtures import FixtureFactory


@pytest.mark.django_db
class TestSalesOrderFlow:
    """销售订单流程测试"""
    
    def test_create_order(self, test_customer, test_products):
        """测试创建订单"""
        order = SalesOrder.objects.create(
            customer=test_customer,
            order_date=timezone.now().date(),
            status='draft'
        )
        
        item = SalesOrderItem.objects.create(
            order=order,
            product=test_products[0],
            quantity=Decimal('10'),
            unit_price=Decimal('100.00')
        )
        
        order.calculate_totals()
        
        assert order.items.count() == 1
        assert order.total_amount == Decimal('1000.00')
```

### 运行测试

```bash
# 运行所有测试
pytest apps/**/test_e2e_*.py -v

# 运行特定模块测试
pytest apps/sales/tests/test_e2e_sales_flow.py -v

# 生成覆盖率报告
pytest apps/**/test_e2e_*.py --cov=apps --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

---

## 📖 文档贡献

### 文档结构

- `README.md` - 项目主文档
- `QUICK_START_GUIDE.md` - 快速开始指南
- `DEPLOYMENT_CHECKLIST.md` - 部署检查清单
- `OPERATIONS_GUIDE.md` - 运维工具指南
- `apps/*/CLAUDE.md` - 模块文档

### 文档编写建议

1. **清晰简洁** - 用简单的语言解释复杂的概念
2. **示例丰富** - 提供可运行的代码示例
3. **保持更新** - 代码变更时同步更新文档
4. **结构清晰** - 使用目录、标题、列表组织内容

---

## 🐛 Bug报告

### Bug报告模板

在提交Issue时，请包含以下信息：

```markdown
### Bug描述
简短描述问题

### 复现步骤
1. 进入页面 '...'
2. 点击按钮 '....'
3. 滚动到 '....'
4. 看到错误

### 期望行为
应该发生什么

### 实际行为
实际发生了什么

### 环境信息
- OS: [e.g. macOS 13.0]
- Python: [e.g. 3.13.5]
- Django: [e.g. 5.0.9]
- 浏览器: [e.g. Chrome 120]

### 截图
如果有UI问题，请提供截图

### 附加信息
其他相关信息（日志、配置等）
```

---

## 💡 功能建议

### 功能建议模板

```markdown
### 功能描述
简短描述新功能

### 问题背景
当前的问题或限制

### 解决方案
详细描述您建议的解决方案

### 替代方案
考虑过的其他解决方案

### 附加信息
其他相关信息、参考链接等
```

---

## 📧 联系方式

- **GitHub Issues**: [项目Issues页面](https://github.com/your-org/django-erp/issues)
- **邮件**: dev@example.com
- **Discord**: [加入社区](https://discord.gg/xxx)

---

## 🎖️ 认可贡献者

我们会在以下地方认可贡献者：

- 项目README的贡献者列表
- CHANGELOG中记录贡献
- 发布公告中感谢

---

## 📄 许可证

贡献的代码将采用与项目相同的 [MIT License](LICENSE)。

---

**再次感谢您的贡献！** 🎉

---

## 相关资源

- [代码规范](#-代码规范)
- [提交规范](#-提交规范)
- [测试指南](#-测试指南)
- [文档贡献](#-文档贡献)
