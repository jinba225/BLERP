# BLERP 开发指南

## 🚀 快速开始

### 环境要求

- **Python**: 3.8+ (推荐 3.11+)
- **Node.js**: 16+ (推荐 18+)
- **MySQL**: 8.0+ (开发环境可用 SQLite)
- **Redis**: 6.0+ (可选，用于缓存)
- **Git**: 2.0+

### 开发环境设置

#### 1. 克隆项目

```bash
git clone https://github.com/jinba225/BLERP.git django_erp
cd django_erp
```

#### 2. 创建虚拟环境

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Node.js 依赖
npm install
```

#### 4. 数据库设置

**开发环境（SQLite）**:
```bash
# 数据库会自动创建
python manage.py migrate
```

**生产环境（MySQL）**:
```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE better_laser_erp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'erp_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON better_laser_erp.* TO 'erp_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件设置数据库连接信息

# 运行迁移
python manage.py migrate
```

#### 5. 创建超级用户

```bash
python manage.py createsuperuser
```

#### 6. 构建前端资源

```bash
# 开发模式（监听 CSS 变更）
npm run dev

# 生产构建
npm run build
```

#### 7. 启动开发服务器

```bash
# 启动 Django 开发服务器
python manage.py runserver

# 访问 http://localhost:8000
# 访问管理后台 http://localhost:8000/admin/
```

## 📁 项目结构

```
django_erp/
├── better_laser_erp/          # Django 项目配置
│   ├── settings.py            # 核心配置
│   ├── urls.py                # 主路由配置
│   └── wsgi.py / asgi.py      # 服务器入口
├── apps/                      # 业务模块（12个独立应用）
│   ├── core/                  # 核心基础模块
│   ├── authentication/        # 认证系统
│   ├── users/                 # 用户管理
│   ├── departments/           # 部门管理
│   ├── customers/             # 客户管理
│   ├── suppliers/             # 供应商管理
│   ├── products/              # 产品管理
│   ├── inventory/             # 库存管理
│   ├── sales/                 # 销售管理
│   ├── purchase/              # 采购管理
│   ├── finance/               # 财务管理
│   └── ai_assistant/          # AI 助手
├── templates/                 # Django 模板文件
├── static/                    # 静态资源
├── media/                     # 用户上传文件
├── logs/                      # 日志文件
├── fixtures/                  # 初始数据
└── scripts/                   # 运维脚本
```

## 🛠️ 开发工作流

### 创建新功能

#### 1. 创建新模块

```bash
# 创建新的 Django 应用
python manage.py startapp your_module apps/your_module

# 在 settings.py 中注册
# LOCAL_APPS = [
#     # ...
#     'apps.your_module',
# ]
```

#### 2. 定义数据模型

```python
# apps/your_module/models.py
from apps.core.models import BaseModel
from django.db import models

class YourModel(BaseModel):
    """
    模型文档字符串
    """
    name = models.CharField('名称', max_length=200)
    code = models.CharField('编码', max_length=50, unique=True)

    class Meta:
        verbose_name = '显示名称'
        verbose_name_plural = '显示名称复数'
        db_table = 'your_table_name'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
```

#### 3. 创建并应用迁移

```bash
# 创建迁移文件
python manage.py makemigrations your_module

# 查看迁移状态
python manage.py showmigrations

# 应用迁移
python manage.py migrate

# 查看迁移 SQL
python manage.py sqlmigrate your_module 0001
```

#### 4. 创建视图

```python
# apps/your_module/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import YourModel

@login_required
def your_view(request, pk=None):
    """视图文档字符串"""
    if pk:
        obj = get_object_or_404(YourModel, pk=pk, is_deleted=False)
    else:
        obj = None

    if request.method == 'POST':
        # 处理表单提交
        try:
            # 业务逻辑
            messages.success(request, '操作成功')
            return redirect('your_module:view_name')
        except Exception as e:
            messages.error(request, f'操作失败: {str(e)}')

    context = {
        'object': obj,
    }
    return render(request, 'your_module/template.html', context)
```

#### 5. 配置 URL

```python
# apps/your_module/urls.py
from django.urls import path
from . import views

app_name = 'your_module'
urlpatterns = [
    path('', views.list_view, name='list'),
    path('create/', views.create_view, name='create'),
    path('<int:pk>/', views.detail_view, name='detail'),
]

# better_laser_erp/urls.py
urlpatterns = [
    # ...
    path('your-module/', include('apps.your_module.urls')),
]
```

#### 6. 创建模板

```django
<!-- templates/your_module/template.html -->
{% extends "base.html" %}

{% block title %}页面标题{% endblock %}

{% block content %}
<div class="container mx-auto px-4">
    <h1 class="text-2xl font-bold mb-4">页面标题</h1>

    {% if messages %}
        {% for message in messages %}
            <div class="alert alert-{{ message.tags }}">
                {{ message }}
            </div>
        {% endfor %}
    {% endif %}

    <!-- 页面内容 -->
</div>
{% endblock %}
```

### 测试开发

#### 创建测试用例

```python
# apps/your_module/tests.py
from django.test import TestCase
from .models import YourModel

class YourModelTestCase(TestCase):
    """测试用例文档字符串"""

    def setUp(self):
        """测试前准备"""
        self.obj = YourModel.objects.create(
            name='Test Object',
            code='TEST001'
        )

    def test_model_creation(self):
        """测试模型创建"""
        self.assertEqual(self.obj.name, 'Test Object')
        self.assertEqual(self.obj.code, 'TEST001')
        self.assertIsNotNone(self.obj.created_at)

    def test_soft_delete(self):
        """测试软删除"""
        self.obj.delete()
        self.assertTrue(self.obj.is_deleted)
        self.assertIsNotNone(self.obj.deleted_at)
```

#### 运行测试

```bash
# 运行所有测试
python manage.py test

# 运行特定模块测试
python manage.py test apps.your_module

# 运行特定测试类
python manage.py test apps.your_module.tests.YourModelTestCase

# 带覆盖率报告
coverage run --source='.' manage.py test
coverage report
coverage html  # 生成 HTML 报告
```

### API 开发

#### 创建 API ViewSet

```python
# apps/your_module/views_api.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import YourModel
from .serializers import YourModelSerializer

class YourModelViewSet(viewsets.ModelViewSet):
    """ViewSet 文档字符串"""
    queryset = YourModel.objects.filter(is_deleted=False)
    serializer_class = YourModelSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['field1', 'field2']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']

    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        """自定义动作"""
        obj = self.get_object()
        # 业务逻辑
        return Response({'status': 'success'})
```

#### 配置 API 路由

```python
# better_laser_erp/urls.py
from rest_framework.routers import DefaultRouter
from apps.your_module.views_api import YourModelViewSet

router = DefaultRouter()
router.register(r'your-models', YourModelViewSet, basename='yourmodel')

urlpatterns = [
    # ...
    path('api/', include(router.urls)),
]
```

## 🎨 前端开发

### Tailwind CSS 开发

```bash
# 开发模式（监听 CSS 变更）
npm run dev

# 生产构建（压缩 CSS）
npm run build
```

### 静态文件管理

```bash
# 收集静态文件
python manage.py collectstatic --noinput

# 清理静态文件
python manage.py collectstatic --clear --noinput
```

### 模板开发

- **基础模板**: `templates/base.html`
- **组件模板**: `templates/components/`
- **模块模板**: `templates/[module_name]/`

## 🔧 常用命令

### 数据库管理

```bash
# 创建迁移
python manage.py makemigrations

# 应用迁移
python manage.py migrate

# 查看迁移
python manage.py showmigrations

# 回滚迁移
python manage.py migrate app_name migration_name

# 数据库 shell
python manage.py dbshell

# 重置数据库（开发环境）
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### 用户管理

```bash
# 创建超级用户
python manage.py createsuperuser

# 修改用户密码
python manage.py changepassword <username>

# 启动开发服务器
python manage.py runserver
```

### 开发工具

```bash
# 启动 Django shell
python manage.py shell

# 检查配置
python manage.py check

# 收集静态文件
python manage.py collectstatic

# 查看URL配置
python manage.py show_urls
```

## 🐛 调试技巧

### Django 调试工具栏

```bash
# 安装
pip install django-debug-toolbar

# 添加到 INSTALLED_APPS
# DEBUG 模式下自动启用
```

### 日志调试

```python
# 在代码中添加日志
import logging
logger = logging.getLogger(__name__)

logger.debug('调试信息')
logger.info('普通信息')
logger.warning('警告信息')
logger.error('错误信息')
```

### 查询分析

```python
# 在 shell 中分析查询
from django.db import connection
from apps.sales.models import SalesOrder

# 执行查询
orders = SalesOrder.objects.all()

# 查看执行的 SQL
print(connection.queries)
```

## 📊 代码规范

### Python 代码规范

- **PEP 8**: 遵循 Python 代码规范
- **Black**: 自动代码格式化
- **isort**: 导入排序
- **flake8**: 代码质量检查

```bash
# 安装开发工具
pip install black isort flake8

# 格式化代码
black .
isort .

# 检查代码
flake8 .
```

### Django 规范

- 模型继承 `BaseModel`
- 视图使用 `@login_required` 装饰器
- 使用 `get_object_or_404()` 处理对象获取
- 使用 `messages` 框架显示反馈
- URL 命名使用 `app_name:view_name` 格式

### 命名规范

- **模型类**: `PascalCase` (如 `SalesOrder`)
- **函数/方法**: `snake_case` (如 `calculate_total`)
- **变量**: `snake_case` (如 `order_count`)
- **常量**: `UPPER_SNAKE_CASE` (如 `MAX_ITEMS`)
- **URL 参数**: `kebab-case` (如 `/sales-orders/`)

## 🔐 安全开发

### 常见安全问题

1. **SQL 注入**: 使用 Django ORM 防止
2. **XSS 攻击**: 模板自动转义
3. **CSRF 攻击**: 使用 `{% csrf_token %}`
4. **权限验证**: 使用装饰器和中间件

### 安全最佳实践

```python
# 始终验证用户权限
from django.contrib.auth.decorators import login_required, permission_required

@login_required
@permission_required('sales.view_salesorder')
def sensitive_view(request):
    # 业务逻辑
    pass

# 使用 get_object_or_404 防止 404 错误
from django.shortcuts import get_object_or_404

obj = get_object_or_404(MyModel, pk=pk, is_deleted=False)

# 使用参数化查询
MyModel.objects.filter(name=user_input)  # ✅ 安全
MyModel.objects.raw(f"SELECT * FROM mymodel WHERE name = '{user_input}'")  # ❌ 不安全
```

## 🚀 性能优化

### 数据库优化

```python
# 使用 select_related 减少 SQL 查询
orders = SalesOrder.objects.select_related('customer', 'created_by').all()

# 使用 prefetch_related 预加载多对多关系
products = Product.objects.prefetch_related('categories').all()

# 使用 only() 只选择需要的字段
orders = SalesOrder.objects.only('id', 'order_number', 'total_amount').all()

# 使用 values() 减少内存使用
order_data = SalesOrder.objects.values('id', 'order_number', 'total_amount')
```

### 缓存优化

```python
# 使用 Redis 缓存
from django.core.cache import cache

def get_expensive_result():
    result = cache.get('expensive_result')
    if result is None:
        result = complex_calculation()
        cache.set('expensive_result', result, 3600)  # 缓存 1 小时
    return result
```

### 静态文件优化

```bash
# 压缩静态文件
python manage.py compress

# 使用 CDN
# 在 settings.py 中配置 STATIC_URL
```

## 🧪 测试策略

### 单元测试

- 测试单个函数/方法
- 使用 Mock 对象
- 快速执行

### 集成测试

- 测试模块间交互
- 使用测试数据库
- 测试业务流程

### 功能测试

- 测试用户界面
- 使用 Selenium
- 模拟用户操作

## 📚 资源和文档

- **Django 官方文档**: https://docs.djangoproject.com/
- **DRF 文档**: https://www.django-rest-framework.org/
- **Tailwind CSS**: https://tailwindcss.com/
- **项目 CLAUDE.md**: `/Users/janjung/Code_Projects/django_erp/CLAUDE.md`
- **用户指南**: `/Users/janjung/Code_Projects/django_erp/docs/user-guide.md`

## 🆘 故障排除

### 常见问题

1. **迁移冲突**
   ```bash
   python manage.py showmigrations
   python manage.py migrate app_name migration_name
   ```

2. **静态文件无法加载**
   ```bash
   python manage.py collectstatic --noinput
   npm run build
   ```

3. **权限问题**
   ```bash
   chmod -R 755 media/ logs/ staticfiles/
   ```

4. **日志查看**
   ```bash
   tail -f logs/django.log
   ```

## 🎯 开发最佳实践

1. **版本控制**: 使用 Git 分支管理功能
2. **代码审查**: 所有代码合并前需要审查
3. **测试覆盖**: 保持高测试覆盖率
4. **文档更新**: 及时更新相关文档
5. **性能监控**: 关注查询性能和响应时间
6. **安全审查**: 定期进行安全检查

祝您开发愉快！🚀
