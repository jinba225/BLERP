# 报价单模块部署指南

## ✅ 已完成的工作

### 1. 数据模型 ✅
- **文件**: `apps/sales/models.py`
- Quote 模型（支持国内/海外报价，汇率自动转换）
- QuoteItem 模型（报价单明细）
- 自动计算总金额功能
- 报价单转订单功能

### 2. 单据号生成器 ✅
- **文件**:
  - `apps/core/utils/document_number.py`
  - `apps/core/models.py` (DocumentNumberSequence)
- 统一格式：前缀 + YYYYMMDD + 4位流水号
- 支持所有单据类型
- 并发安全

### 3. 表单 ✅
- **文件**: `apps/sales/forms.py`
- QuoteForm（报价单主表单）
- QuoteItemForm（明细行表单）
- QuoteItemFormSet（明细行表单集）
- QuoteSearchForm（搜索筛选表单）
- ConvertToOrderForm（转订单表单）

### 4. 视图 ✅
- **文件**: `apps/sales/views.py`
- 报价单列表（支持搜索、筛选、分页）
- 报价单详情
- 创建报价单
- 编辑报价单
- 删除报价单（软删除）
- 报价单转订单
- 更改报价单状态
- 打印报价单
- 复制报价单

### 5. URL 配置 ✅
- **文件**: `apps/sales/urls.py`
- 所有报价单相关路由已配置

### 6. Admin 后台 ✅
- **文件**: `apps/sales/admin.py`
- Quote、SalesOrder、Delivery、SalesReturn 的后台管理
- 支持内联编辑明细

---

## 🚀 部署步骤

### 步骤 1: 设置 Python 环境

```bash
cd /Users/janjung/Code_Projects/BLBS_ERP/django_erp

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境 (macOS/Linux)
source venv/bin/activate

# Windows 用户使用:
# venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 如果缺少某些包，可能需要单独安装
pip install django djangorestframework django-mptt pillow python-dateutil
```

### 步骤 2: 配置数据库

检查 `better_laser_erp/settings.py` 中的数据库配置：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # 开发环境用 SQLite
        'NAME': BASE_DIR / 'db.sqlite3',
        # 生产环境改为 MySQL:
        # 'ENGINE': 'django.db.backends.mysql',
        # 'NAME': 'better_laser_erp',
        # 'USER': 'your_username',
        # 'PASSWORD': 'your_password',
        # 'HOST': 'localhost',
        # 'PORT': '3306',
    }
}
```

### 步骤 3: 运行数据库迁移

```bash
# 创建迁移文件
python manage.py makemigrations

# 应该看到输出:
# Migrations for 'core':
#   apps/core/migrations/0001_initial.py
#     - Create model DocumentNumberSequence
#     - ...
# Migrations for 'sales':
#   apps/sales/migrations/0001_initial.py
#     - Create model Quote
#     - Create model QuoteItem
#     - ...

# 执行迁移
python manage.py migrate

# 应该看到:
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   Applying core.0001_initial... OK
#   Applying sales.0001_initial... OK
#   ...
```

### 步骤 4: 创建超级用户

```bash
python manage.py createsuperuser

# 按提示输入:
# Username: admin
# Email: admin@example.com
# Password: (输入密码，至少8位)
# Password (again): (再次输入)
```

### 步骤 5: 收集静态文件（生产环境）

```bash
# 开发环境可以跳过这一步
python manage.py collectstatic
```

### 步骤 6: 启动开发服务器

```bash
python manage.py runserver

# 服务器启动在 http://127.0.0.1:8000/
```

---

## 📋 测试功能

### 1. 访问 Admin 后台

```
URL: http://127.0.0.1:8000/admin/
用户名: admin
密码: (你刚才设置的密码)
```

**测试内容**:
- 进入 "Sales" -> "Quotes"
- 点击 "Add Quote" 创建测试报价单
- 添加报价单明细
- 检查报价单号是否自动生成（格式：QT20251105XXXX）
- 检查总金额是否自动计算

### 2. 访问报价单列表页

```
URL: http://127.0.0.1:8000/sales/quotes/
```

**注意**: 目前还没有创建模板文件，所以会显示 TemplateDoesNotExist 错误。这是正常的！

### 3. 使用 Django Shell 测试

```bash
python manage.py shell
```

```python
# 在 Shell 中测试单据号生成器
from apps.core.utils import DocumentNumberGenerator

# 生成报价单号
quote_number = DocumentNumberGenerator.generate('QT')
print(quote_number)  # 输出: QT20251105000 1

# 生成订单号
order_number = DocumentNumberGenerator.generate('SO')
print(order_number)  # 输出: SO202511050001

# 创建测试报价单
from apps.sales.models import Quote
from apps.customers.models import Customer
from django.utils import timezone

# 假设你已经在 Admin 中创建了一个客户
customer = Customer.objects.first()
if customer:
    quote = Quote.objects.create(
        quote_number=DocumentNumberGenerator.generate('QT'),
        customer=customer,
        quote_date=timezone.now().date(),
        valid_until=timezone.now().date() + timezone.timedelta(days=30),
        currency='CNY',
        tax_rate=13.00,
    )
    print(f"创建报价单成功: {quote.quote_number}")
else:
    print("请先在 Admin 中创建一个客户")
```

---

## ⚠️ 下一步工作

### 还需要创建的内容：

1. **HTML 模板** (templates)
   - quote_list.html（报价单列表）
   - quote_detail.html（报价单详情）
   - quote_form.html（创建/编辑表单）
   - quote_confirm_delete.html（删除确认）
   - quote_convert.html（转订单）
   - quote_print.html（打印）

2. **静态文件** (CSS/JavaScript)
   - 表单动态添加明细行的 JS
   - 自动计算金额的 JS
   - 样式文件

3. **测试数据**
   - 创建测试客户
   - 创建测试产品
   - 创建测试报价单

---

## 🐛 常见问题

### 问题 1: ModuleNotFoundError: No module named 'django'
**解决**: 确保已激活虚拟环境并安装了依赖
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 问题 2: django.db.utils.OperationalError: no such table
**解决**: 运行数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

### 问题 3: TemplateDoesNotExist
**这是正常的！** 我们还没有创建 HTML 模板。可以先通过 Admin 后台测试功能。

### 问题 4: 外键关联错误（Customer、Product等不存在）
**解决**: 在测试报价单功能前，需要先在 Admin 后台创建：
1. 客户（Customers）
2. 产品（Products）
3. 用户（作为销售代表）

---

## 📊 代码统计

```
新增文件:
- apps/core/utils/document_number.py      (180 行)
- apps/core/utils/__init__.py             (5 行)
- apps/sales/forms.py                     (300 行)
- apps/sales/views.py                     (350 行)
- apps/sales/admin.py                     (180 行)

修改文件:
- apps/core/models.py                     (+30 行, DocumentNumberSequence)
- apps/sales/models.py                    (+80 行, 改进 Quote 模型)
- apps/sales/urls.py                      (+15 行, 添加路由)

总计: ~1140 行代码
```

---

## ✅ 功能清单

| 功能 | 状态 | 说明 |
|-----|------|------|
| 报价单模型 | ✅ | 支持国内/海外，汇率转换 |
| 报价单明细 | ✅ | 支持多行明细 |
| 单据号生成 | ✅ | 自动生成唯一单据号 |
| 创建报价单 | ✅ | 后端逻辑完成 |
| 编辑报价单 | ✅ | 只能编辑草稿 |
| 删除报价单 | ✅ | 软删除 |
| 查看详情 | ✅ | 后端逻辑完成 |
| 列表查询 | ✅ | 支持搜索和筛选 |
| 转换订单 | ✅ | 自动转换为销售订单 |
| 状态管理 | ✅ | 草稿→已发送→已接受等 |
| 打印功能 | ✅ | 后端逻辑完成 |
| 复制报价单 | ✅ | 快速创建副本 |
| 金额计算 | ✅ | 自动计算小计、税额、折扣 |
| 汇率转换 | ✅ | 自动转换为人民币 |
| Admin 后台 | ✅ | 完整的后台管理 |
| HTML 模板 | ⏭️ | 待创建 |
| 前端交互 | ⏭️ | 待创建 |

---

## 📞 需要帮助？

如果遇到任何问题：
1. 检查虚拟环境是否已激活
2. 检查数据库迁移是否成功
3. 查看 Django 错误日志
4. 在 Django Shell 中测试功能

**准备好了吗？运行 `python manage.py runserver` 开始测试！** 🚀
