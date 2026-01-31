# AGENTS.md

本文件为编码智能代理（AI Coding Agents）提供 BetterLaser ERP 项目的操作指南。

---

## 构建与测试命令

### Python 测试
```bash
# 运行所有测试
python manage.py test

# 运行特定模块的测试
python manage.py test apps.core
python manage.py test apps.sales
python manage.py test apps.customers

# 运行特定测试文件
python manage.py test apps.sales.tests.test_models

# 运行单个测试类
python manage.py test apps.sales.tests.test_models.SalesOrderModelTest

# 运行单个测试方法
python manage.py test apps.sales.tests.test_models.SalesOrderModelTest.test_order_creation

# 带详细输出
python manage.py test -v 2

# 保留测试数据库（用于调试）
python manage.py test --keepdb
```

### 代码覆盖率
```bash
# 运行测试并生成覆盖率报告
coverage run --source='.' manage.py test
coverage report

# 生成 HTML 覆盖率报告
coverage html  # 查看 htmlcov/index.html
```

### 前端构建
```bash
# 开发模式（监听 CSS 变更）
npm run dev

# 生产构建（压缩 CSS）
npm run build
```

### 数据库操作
```bash
# 创建迁移
python manage.py makemigrations

# 应用迁移
python manage.py migrate

# 查看迁移状态
python manage.py showmigrations

# 回滚迁移
python manage.py migrate app_name migration_name
```

### 静态文件
```bash
# 收集静态文件
python manage.py collectstatic --noinput

# 清除后重新收集
python manage.py collectstatic --clear --noinput
```

### Linting（当前项目未配置，可选）
```bash
# 如需启用代码检查，可安装并使用：
# pip install flake8 black isort
# flake8 apps/
# black apps/
# isort apps/
```

---

## 代码风格指南

### 导入顺序
遵循标准 PEP 8 导入顺序：
1. 标准库导入
2. 第三方库导入
3. Django 相关导入
4. 本地应用导入

```python
import json
from decimal import Decimal
from datetime import timedelta

from django.db import models
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404

from apps.core.models import BaseModel
from apps.sales.models import SalesOrder
```

### 模型开发规范

所有业务模型必须继承 `BaseModel`（自动提供时间戳、软删除、创建人）：

```python
from apps.core.models import BaseModel
from django.db import models

class YourModel(BaseModel):
    """模型文档字符串（必需，中文）"""

    # 字段定义
    name = models.CharField('名称', max_length=200, help_text='字段的中文说明')
    code = models.CharField('代码', max_length=50, unique=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='draft')

    # 金额字段使用 DecimalField，含税价格体系
    amount = models.DecimalField('含税金额', max_digits=12, decimal_places=2, default=0, help_text='含税金额')

    class Meta:
        verbose_name = '显示名称'
        verbose_name_plural = '显示名称复数'
        db_table = 'your_table_name'  # 必须明确指定表名
        ordering = ['-created_at']     # 默认按创建时间倒序
        indexes = [models.Index(fields=['code'])]  # 为常用查询字段添加索引

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # 自定义保存逻辑
        super().save(*args, **kwargs)
```

### 视图开发规范

函数式视图必须使用 `@login_required` 装饰器：

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction

@login_required
def your_view(request, pk):
    """视图文档字符串（必需）"""
    obj = get_object_or_404(YourModel, pk=pk, is_deleted=False)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 业务逻辑
                obj.save()
            messages.success(request, '操作成功')
            return redirect('app:view_name')
        except Exception as e:
            messages.error(request, f'操作失败: {str(e)}')

    context = {
        'object': obj,
    }
    return render(request, 'app/template.html', context)
```

### API 开发规范

使用 Django REST Framework ViewSet：

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class YourViewSet(viewsets.ModelViewSet):
    """ViewSet 文档字符串（必需）"""
    queryset = YourModel.objects.filter(is_deleted=False)
    serializer_class = YourSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['field1', 'field2']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        """自定义动作文档字符串"""
        obj = self.get_object()
        # 业务逻辑
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
```

### 测试开发规范

使用 Django TestCase，所有测试必须包含文档字符串：

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.yourapp.models import YourModel

User = get_user_model()

class YourModelTestCase(TestCase):
    """测试用例文档字符串（必需）"""

    def setUp(self):
        """测试前准备数据"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        self.obj = YourModel.objects.create(
            name='Test Object',
            created_by=self.user
        )

    def test_model_creation(self):
        """测试模型创建"""
        self.assertEqual(self.obj.name, 'Test Object')
        self.assertIsNotNone(self.obj.created_at)
        self.assertFalse(self.obj.is_deleted)

    def test_soft_delete(self):
        """测试软删除功能"""
        self.obj.delete()
        self.assertTrue(self.obj.is_deleted)
        self.assertIsNotNone(self.obj.deleted_at)
```

### 命名约定

- **模型类**: PascalCase (SalesOrder, Quote, Customer)
- **视图函数**: snake_case (quote_list, order_detail)
- **ViewSet 类**: PascalCase + 'ViewSet' (SalesOrderViewSet)
- **测试类**: PascalCase + 'Test' (SalesOrderModelTest)
- **测试方法**: test_ 前缀，snake_case (test_order_creation)
- **数据库表名**: snake_case，明确指定 db_table
- **常量**: UPPER_CASE (ORDER_STATUS, PAYMENT_STATUS)

### 错误处理

```python
# 在视图中使用 messages 框架
try:
    # 业务逻辑
    messages.success(request, '操作成功')
except ValidationError as e:
    messages.error(request, f'验证失败: {str(e)}')
except Exception as e:
    messages.error(request, f'操作失败: {str(e)}')
```

### 类型与字段

- **金额字段**: 使用 `DecimalField(max_digits=12, decimal_places=2)`
- **价格字段**: 全局采用含税价格，使用 help_text 说明
- **状态字段**: 使用 `choices` 参数定义选项
- **布尔字段**: 使用 `BooleanField(default=False)`
- **日期时间**: `DateTimeField(auto_now_add=True)` 或 `auto_now=True`
- **外键**: 使用 `on_delete=models.SET_NULL, null=True, blank=True` 允许软删除

### 软删除机制

所有查询必须过滤已删除记录：

```python
# 正确：过滤已删除记录
YourModel.objects.filter(is_deleted=False)
YourModel.objects.filter(status='active', is_deleted=False)

# 错误：未过滤已删除记录
YourModel.objects.all()

# 软删除
obj.delete()  # 标记为删除，不物理删除

# 硬删除（谨慎使用）
obj.hard_delete()
```

### 文档字符串

所有类、函数、方法必须包含中文文档字符串：

```python
def your_function(param1, param2):
    """函数的简短说明（必需）

    详细说明（可选）：
    - param1: 参数1说明
    - param2: 参数2说明

    Returns:
        返回值说明
    """
    pass
```

### 业务流程关键点

1. **含税价格体系**: 所有价格字段为含税价格，税额反推计算
2. **单据号生成**: 使用 `DocumentNumberGenerator.generate('document_type')`
3. **部分交付**: 使用 `delivered_quantity` 字段追踪已交付数量
4. **订单审核**: 调用 `approve_order()` 自动生成发货单和应收账款
5. **软删除**: 所有业务模型支持软删除，查询时必须过滤 `is_deleted=False`

### 数据库迁移规范

```bash
# 创建迁移前先检查
python manage.py makemigrations --dry-run

# 创建迁移
python manage.py makemigrations

# 查看迁移 SQL（调试）
python manage.py sqlmigrate app_name migration_name
```

---

## 项目架构关键点

- **模块化设计**: 12 个独立业务模块在 `apps/` 目录下
- **基础模块**: `apps/core/` 提供共享功能（BaseModel, DocumentNumberGenerator）
- **认证系统**: `apps/authentication/` 提供 JWT 认证
- **核心业务**: `apps/sales/` 处理完整销售流程
- **静态资源**: `static/` 目录使用 Tailwind CSS
- **模板文件**: `templates/` 目录使用 Django 模板

---

## 快速检查清单

在提交代码前，确保：
- [ ] 所有模型继承 BaseModel
- [ ] 所有查询过滤 `is_deleted=False`
- [ ] 所有金额字段使用 DecimalField
- [ ] 所有视图使用 @login_required
- [ ] 所有类/函数包含中文文档字符串
- [ ] 所有测试通过 (`python manage.py test`)
- [ ] 金额字段包含 help_text 说明含税
- [ ] 运行 `python manage.py makemigrations` 检查是否有待迁移的更改

---

## 常见问题

**Q: 如何运行单个测试？**
A: `python manage.py test apps.sales.tests.test_models.SalesOrderModelTest.test_order_creation`

**Q: 如何生成单据号？**
A: `from apps.core.utils import DocumentNumberGenerator; doc_num = DocumentNumberGenerator.generate('sales_order')`

**Q: 如何软删除对象？**
A: `obj.delete()` - BaseModel 覆写了 delete() 方法实现软删除

**Q: 如何硬删除对象？**
A: `obj.hard_delete()` - 物理删除（谨慎使用）

---

本文件由 AGENTS.md 自动生成，为 AI 编码代理提供项目特定指南。
