# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 项目概览

**BetterLaser ERP** 是一个基于 Django + Tailwind CSS 的现代化企业资源规划(ERP)系统，专为激光设备制造企业设计。系统采用模块化架构，提供从销售、采购、库存到财务的完整业务流程管理。

### 关键特点
- **技术栈**: Django 4.2 + DRF + Tailwind CSS + SQLite(开发) / MySQL(生产)
- **模块化设计**: 12个独立业务模块，松耦合高内聚
- **含税价格体系**: 系统全局采用含税价格，税额反推计算
- **单据号系统**: 统一的可配置单据编号生成器
- **打印模板**: 集成 HiPrint 打印引擎，支持可视化模板设计

---

## 快速开始

### 开发环境启动

```bash
# 1. 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate    # Windows

# 2. 安装依赖（首次运行）
pip install -r requirements.txt
npm install

# 3. 数据库迁移
python manage.py migrate

# 4. 创建超级用户（首次运行）
python manage.py createsuperuser

# 5. 构建前端资源
npm run build  # 生产构建
# npm run dev  # 开发模式（监听CSS变更）

# 6. 启动开发服务器
python manage.py runserver
```

### 测试运行

```bash
# 运行所有测试
python manage.py test

# 运行特定模块测试
python manage.py test apps.core
python manage.py test apps.sales
python manage.py test apps.customers

# 带覆盖率报告
coverage run --source='.' manage.py test
coverage report
```

### 数据库管理

```bash
# 创建迁移文件
python manage.py makemigrations

# 查看迁移状态
python manage.py showmigrations

# 应用迁移
python manage.py migrate

# 回滚迁移
python manage.py migrate app_name migration_name

# 重置数据库（开发环境）
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

---

## 项目架构

### 目录结构

```
django_erp/
├── better_laser_erp/          # Django 项目配置
│   ├── settings.py            # 核心配置（环境检测、安全配置）
│   ├── urls.py                # 主路由配置
│   ├── wsgi.py / asgi.py      # 服务器入口
│   └── celery.py.bak          # Celery 配置（生产环境）
├── apps/                      # 业务模块（12个独立应用）
│   ├── core/                  # 核心基础模块
│   ├── authentication/        # 认证系统（JWT）
│   ├── users/                 # 用户管理
│   ├── departments/           # 部门管理
│   ├── customers/             # 客户管理
│   ├── suppliers/             # 供应商管理
│   ├── products/              # 产品管理
│   ├── inventory/             # 库存管理
│   ├── sales/                 # 销售管理（核心业务）
│   ├── purchase/              # 采购管理
│   ├── finance/               # 财务管理
│   ├── reports/               # 报表中心
│   └── contracts/             # 合同管理
├── templates/                 # Django 模板文件
├── static/                    # 静态资源
│   ├── css/                   # Tailwind CSS 输出
│   └── js/                    # JavaScript 文件
├── media/                     # 用户上传文件
├── logs/                      # 日志文件
├── fixtures/                  # 初始数据
├── scripts/                   # 运维脚本（备份/恢复）
├── docs/                      # 项目文档
├── requirements.txt           # Python 依赖
├── package.json               # Node.js 依赖（Tailwind）
├── tailwind.config.js         # Tailwind 配置
├── manage.py                  # Django 管理脚本
└── db.sqlite3                 # SQLite 数据库（开发环境）
```

### 核心模块架构

#### 1. Core 模块（apps/core/）
**职责**: 提供所有模块共享的基础功能

- **基础模型抽象** (`models.py`):
  - `TimeStampedModel`: 自动时间戳（created_at, updated_at）
  - `SoftDeleteModel`: 软删除支持（is_deleted, deleted_at）
  - `BaseModel`: 完整基类（时间戳 + 软删除 + 创建人）

- **核心业务模型**:
  - `Company`: 企业信息管理
  - `SystemConfig`: 系统配置（键值对存储）
  - `Attachment`: 通用附件管理（Generic Foreign Key）
  - `AuditLog`: 审计日志（操作追踪）
  - `DocumentNumberSequence`: 单据号序列（并发安全）
  - `Notification`: 系统通知
  - `PrintTemplate`: 打印模板（HiPrint）
  - `DefaultTemplateMapping`: 模板映射配置

- **工具类** (`utils/`):
  - `DocumentNumberGenerator`: 单据号生成器（支持配置化前缀、日期格式、序号位数）

- **中间件** (`middleware.py`):
  - `TimezoneMiddleware`: 时区处理中间件

#### 2. Sales 模块（apps/sales/）
**职责**: 完整的销售流程管理

- **核心模型**:
  - `Quote`: 报价单（报价 → 转订单）
  - `QuoteItem`: 报价明细
  - `SalesOrder`: 销售订单（订单 → 发货 → 完成）
  - `SalesOrderItem`: 订单明细（支持部分交付）
  - `Delivery`: 发货单（支持多次部分发货）
  - `DeliveryItem`: 发货明细
  - `SalesReturn`: 退货单（退货申请 → 审核 → 处理）
  - `SalesReturnItem`: 退货明细

- **业务特性**:
  - ✅ 报价单一键转订单
  - ✅ 订单审核自动生成发货单和应收账款
  - ✅ 支持部分发货（多次发货）
  - ✅ 退货流程管理（审核、库存回补、通知系统）
  - ✅ 含税价格体系（税额反推计算）

- **视图组织**:
  - `views.py`: 主要业务视图（报价、订单、发货、退货）
  - `views_template.py`: 打印模板相关视图

#### 3. Authentication 模块（apps/authentication/）
**职责**: JWT 认证和授权

- `JWTAuthentication`: 自定义 JWT 认证类
- Token 生成和验证
- 用户登录/登出接口

---

## 数据库设计要点

### 1. 含税价格体系

**系统全局采用含税价格**，这是一个核心设计原则：

```python
# 所有单价和金额字段都是含税的
unit_price = DecimalField('含税单价', help_text='含税单价')
line_total = DecimalField('含税小计', help_text='含税金额')
total_amount = DecimalField('含税总金额', help_text='客户实际支付金额（含税）')

# 税额字段是反推计算的（用于财务核算）
tax_amount = DecimalField('税额', help_text='从含税价格反推得出')

# 税额计算公式
# tax_amount = total_with_tax / (1 + tax_rate) × tax_rate
# 例如：含税价113元，税率13%，税额 = 113 / 1.13 × 0.13 = 13元
```

### 2. 部分交付支持

销售订单支持多次部分发货：

```python
class SalesOrderItem:
    quantity = DecimalField('订单数量')
    delivered_quantity = DecimalField('已交付数量', default=0)

    @property
    def remaining_quantity(self):
        """剩余待发货数量"""
        return self.quantity - self.delivered_quantity
```

### 3. 单据号生成系统

使用 `DocumentNumberGenerator` 统一管理所有单据编号：

```python
# 格式: PREFIX + YYYYMMDD + 序号
# 例如: SO20251108001

# 可配置项（SystemConfig）：
# - document_prefix_sales_order: 'SO'     # 前缀
# - document_number_date_format: 'YYMMDD'  # 日期格式（YYYYMMDD/YYMMDD/YYMM）
# - document_number_sequence_digits: 3     # 序号位数

# 使用方式
from apps.core.utils import DocumentNumberGenerator

order_number = DocumentNumberGenerator.generate('sales_order')
# 或使用旧前缀（向后兼容）
order_number = DocumentNumberGenerator.generate('SO')
```

### 4. 软删除机制

所有业务模型继承 `BaseModel`，支持软删除：

```python
# 软删除（标记为删除，数据仍保留）
object.delete()  # 调用 BaseModel.delete()

# 硬删除（物理删除）
object.hard_delete()

# 查询时需要过滤已删除记录
objects.filter(is_deleted=False)
```

---

## 开发规范

### 模型开发

```python
from apps.core.models import BaseModel
from django.db import models

class YourModel(BaseModel):
    """
    模型文档字符串（必需）
    """
    name = models.CharField('名称', max_length=200)

    class Meta:
        verbose_name = '显示名称'
        verbose_name_plural = '显示名称复数'
        db_table = 'your_table_name'  # 明确指定表名
        ordering = ['-created_at']     # 默认排序

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # 自定义保存逻辑
        super().save(*args, **kwargs)
```

### 视图开发

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

@login_required
def your_view(request, pk):
    """视图文档字符串"""
    obj = get_object_or_404(YourModel, pk=pk, is_deleted=False)

    if request.method == 'POST':
        # 处理表单提交
        try:
            # 业务逻辑
            messages.success(request, '操作成功')
            return redirect('app:view_name')
        except Exception as e:
            messages.error(request, f'操作失败: {str(e)}')

    context = {
        'object': obj,
    }
    return render(request, 'app/template.html', context)
```

### API 开发

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class YourViewSet(viewsets.ModelViewSet):
    """ViewSet 文档字符串"""
    queryset = YourModel.objects.filter(is_deleted=False)
    serializer_class = YourSerializer
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

### 测试开发

```python
from django.test import TestCase
from apps.yourapp.models import YourModel

class YourModelTestCase(TestCase):
    """测试用例文档字符串"""

    def setUp(self):
        """测试前准备"""
        self.obj = YourModel.objects.create(
            name='Test Object'
        )

    def test_model_creation(self):
        """测试模型创建"""
        self.assertEqual(self.obj.name, 'Test Object')
        self.assertIsNotNone(self.obj.created_at)

    def test_soft_delete(self):
        """测试软删除"""
        self.obj.delete()
        self.assertTrue(self.obj.is_deleted)
        self.assertIsNotNone(self.obj.deleted_at)
```

---

## 业务流程

### 销售流程

```
报价单创建
    ↓
报价单发送给客户
    ↓
客户接受报价 → 报价单转销售订单
    ↓
订单审核 → 自动生成：
    - Delivery (发货单)
    - CustomerAccount (应收账款)
    ↓
发货单确认发货 → 更新库存
    ↓
客户确认收货 → 订单完成
    ↓
收款记录 → 应收账款核销
```

### 退货流程

```
客户申请退货 → 创建 SalesReturn
    ↓
审核退货申请
    ↓
审核通过 → 创建通知 → 客户收到通知
    ↓
收到退货 → 更新状态为 'received'
    ↓
处理退货 → 库存回补 + 退款处理
    ↓
完成退货 → 更新状态为 'processed'
```

### 订单审核业务逻辑

```python
# apps/sales/models.py - SalesOrder.approve_order()

def approve_order(self, approved_by_user, warehouse=None):
    """
    订单审核流程：
    1. 验证订单状态（未审核）
    2. 验证订单明细（有明细）
    3. 更新订单状态为 'confirmed'
    4. 自动创建发货单（Delivery）
    5. 创建应收账款（CustomerAccount）
    6. 返回创建的发货单和应收账款对象
    """
```

---

## 配置管理

### 环境变量（.env）

```bash
# 安全配置
DEBUG=True                              # 开发模式
SECRET_KEY=your-secret-key-here         # Django 密钥
ALLOWED_HOSTS=localhost,127.0.0.1       # 允许的主机

# 数据库配置
DB_ENGINE=django.db.backends.sqlite3    # 开发：SQLite
# DB_ENGINE=django.db.backends.mysql    # 生产：MySQL
DB_NAME=django_erp
DB_USER=django_user
DB_PASSWORD=django_password
DB_HOST=localhost
DB_PORT=3306

# Redis 配置（可选，生产环境）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Celery 配置（可选，生产环境）
CELERY_BROKER_URL=redis://localhost:6379/0

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret-key
```

### SystemConfig 配置项

系统通过 `SystemConfig` 模型管理动态配置：

```python
# 单据号前缀配置
document_prefix_sales_order = 'SO'        # 销售订单前缀
document_prefix_quotation = 'SQ'          # 报价单前缀
document_prefix_delivery = 'OUT'          # 发货单前缀
document_prefix_sales_return = 'SR'       # 销售退货前缀
document_prefix_purchase_request = 'PR'   # 采购申请前缀

# 单据号格式配置
document_number_date_format = 'YYMMDD'    # 日期格式：YYYYMMDD/YYMMDD/YYMM
document_number_sequence_digits = 3       # 序号位数：1-5

# 业务配置
sales_auto_create_delivery_on_approve = 'true'  # 审核订单时自动生成发货单
purchase_auto_create_order_on_approve = 'true'  # 审核采购申请时自动生成采购订单
```

---

## 常见任务

### 添加新的业务模块

1. 在 `apps/` 下创建新应用：
   ```bash
   python manage.py startapp your_module apps/your_module
   ```

2. 在 `settings.py` 的 `LOCAL_APPS` 中注册：
   ```python
   LOCAL_APPS = [
       # ...
       'apps.your_module',
   ]
   ```

3. 创建模型（继承 `BaseModel`）：
   ```python
   from apps.core.models import BaseModel

   class YourModel(BaseModel):
       # 字段定义
       pass
   ```

4. 创建迁移并应用：
   ```bash
   python manage.py makemigrations your_module
   python manage.py migrate
   ```

5. 注册到 Admin（可选）：
   ```python
   # apps/your_module/admin.py
   from django.contrib import admin
   from .models import YourModel

   @admin.register(YourModel)
   class YourModelAdmin(admin.ModelAdmin):
       list_display = ['name', 'created_at', 'is_deleted']
       list_filter = ['is_deleted', 'created_at']
       search_fields = ['name']
   ```

### 添加新的单据类型

1. 在 `DocumentNumberGenerator` 的 `PREFIX_CONFIG_MAP` 中添加映射：
   ```python
   PREFIX_CONFIG_MAP = {
       # ...
       'your_document': 'document_prefix_your_document',
   }
   ```

2. 在数据库中添加配置记录：
   ```python
   from apps.core.models import SystemConfig

   SystemConfig.objects.create(
       key='document_prefix_your_document',
       value='YD',  # 前缀
       config_type='business',
       description='Your Document 前缀',
       is_active=True
   )
   ```

3. 在模型中使用：
   ```python
   from apps.core.utils import DocumentNumberGenerator

   class YourDocument(BaseModel):
       document_number = models.CharField(max_length=100, unique=True)

       def save(self, *args, **kwargs):
           if not self.document_number:
               self.document_number = DocumentNumberGenerator.generate('your_document')
           super().save(*args, **kwargs)
   ```

### 添加打印模板

1. 访问模板管理页面：
   ```
   /sales/templates/
   ```

2. 创建新模板或导入现有模板（JSON 格式）

3. 使用 HiPrint 可视化编辑器设计模板

4. 在模型中关联模板：
   ```python
   from apps.core.models import PrintTemplate

   # 获取模板
   template = PrintTemplate.objects.get(
       document_type='sales_order',
       is_default=True
   )
   ```

---

## 故障排查

### 数据库迁移冲突

```bash
# 查看迁移状态
python manage.py showmigrations

# 回滚到指定迁移
python manage.py migrate app_name migration_name

# 清除所有迁移记录（谨慎使用）
python manage.py migrate app_name zero

# 伪造迁移（标记为已应用但不执行）
python manage.py migrate --fake app_name migration_name
```

### 静态文件问题

```bash
# 重新收集静态文件
python manage.py collectstatic --clear --noinput

# 重新构建 Tailwind CSS
npm run build
```

### 权限问题

```bash
# 检查文件权限
ls -la media/ logs/ staticfiles/

# 修复权限（Unix/Linux）
chmod -R 755 media/ logs/ staticfiles/
chown -R www-data:www-data media/ logs/ staticfiles/
```

### 日志查看

```bash
# 开发环境日志（终端输出）
python manage.py runserver

# 生产环境日志文件
tail -f logs/django.log

# 数据库查询日志（settings.py 中配置）
# 'loggers': {'django.db.backends': {'level': 'DEBUG'}}
```

---

## 生产环境部署

### 部署前检查

1. **环境变量检查**:
   ```bash
   DEBUG=False
   SECRET_KEY=<强随机密钥>
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

2. **数据库配置**:
   - 切换到 MySQL
   - 配置连接池
   - 启用 SSL（可选）

3. **静态文件**:
   ```bash
   python manage.py collectstatic --noinput
   npm run build
   ```

4. **安全检查**:
   ```bash
   python manage.py check --deploy
   ```

### Gunicorn + Nginx 部署

```bash
# 1. 启动 Gunicorn
gunicorn better_laser_erp.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --daemon

# 2. 配置 Nginx（nginx.conf 已提供）
sudo systemctl start nginx
sudo systemctl enable nginx

# 3. 配置 Celery（可选，异步任务）
celery -A better_laser_erp worker -l info --detach
celery -A better_laser_erp beat -l info --detach
```

### 备份和恢复

```bash
# 数据库备份
./scripts/backup.sh

# 数据库恢复
./scripts/restore.sh backup_file.sql

# 媒体文件备份
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/
```

---

## 技术债务和待改进项

### 测试覆盖

- ✅ Core 模块: 100% (34/34 测试通过)
- ✅ Sales 模块: 100% (45/45 测试通过)
- ⚠️ 其他模块: 需要添加完整测试

### 性能优化

- [ ] 添加数据库索引优化
- [ ] 实现查询结果缓存
- [ ] 优化 N+1 查询问题
- [ ] 添加异步任务处理（Celery）

### 安全加固

- [x] HTTPS 配置（生产环境）
- [x] CSRF 保护
- [x] SQL 注入防护（Django ORM）
- [ ] XSS 防护增强
- [ ] 接口限流

### 功能扩展

- [ ] 生产管理模块完善
- [ ] 报表中心增强
- [ ] 移动端适配
- [ ] 多语言支持
- [ ] 数据导入导出增强

---

## 相关文档

- **部署指南**: `docs/deployment.md`
- **安装指南**: `docs/installation.md`
- **用户指南**: `docs/user-guide.md`
- **快速开始**: `QUICKSTART.md`
- **更新日志**: `CHANGELOG.md`

---

## 联系和支持

- **项目维护**: BetterLaser ERP Team
- **问题反馈**: 在项目 Issues 中提交
- **文档更新**: 2025-12-18

---

**注意**: 本文档会随项目演进持续更新。开发时请确保遵循上述规范，保持代码一致性和可维护性。
