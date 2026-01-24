# Django ERP 快速启动指南

## ✅ 已优化配置

### 1. 简化依赖包
- ✅ 移除了 mysqlclient（改用 SQLite）
- ✅ 移除了 redis、celery（生产环境才需要）
- ✅ 移除了 django-taggit、gunicorn 等非必须包
- ✅ 保留核心开发依赖（Django、DRF、Pillow 等）

### 2. 数据库配置
- ✅ 开发环境：使用 SQLite（无需安装和配置）
- ✅ 生产环境：可切换到 MySQL（配置已注释）

### 3. 缓存配置
- ✅ 开发环境：使用本地内存缓存
- ✅ 生产环境：可切换到 Redis（配置已注释）

---

## 🚀 快速启动（5分钟）

### 步骤 1: 创建虚拟环境

```bash
cd /Users/janjung/Code_Projects/BLBS_ERP/django_erp

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# Windows: venv\Scripts\activate
```

### 步骤 2: 安装依赖

```bash
# 安装所有依赖（约需 1-2 分钟）
pip install -r requirements.txt

# 如果遇到 Pillow 安装问题，macOS 用户可能需要：
# brew install libjpeg
```

### 步骤 3: 配置环境变量（可选）

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env（可选，使用默认值即可）
# nano .env
```

**注意**: 开发环境无需配置 .env 文件，Django 会使用默认配置。

### 步骤 4: 初始化数据库

```bash
# 创建数据库表
python manage.py makemigrations
python manage.py migrate

# 应该看到类似输出:
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   Applying core.0001_initial... OK
#   Applying sales.0001_initial... OK
#   ...
```

### 步骤 5: 创建管理员账号

```bash
python manage.py createsuperuser

# 按提示输入:
# Username: admin
# Email: admin@example.com
# Password: ******** (至少8位)
# Password (again): ********
```

### 步骤 6: 启动开发服务器

```bash
python manage.py runserver

# 看到以下输出表示成功:
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CONTROL-C.
```

---

## 🎯 测试功能

### 1. 访问 Admin 后台

```
URL: http://127.0.0.1:8000/admin/
用户名: admin
密码: (你刚才设置的密码)
```

### 2. 测试报价单功能

**在 Admin 后台操作**:

1. 先创建测试数据:
   - **Customers** → **Add Customer** → 创建一个客户（如：测试公司）
   - **Products** → **Add Product** → 创建一个产品（如：激光切割机）

2. 创建报价单:
   - **Sales** → **Quotes** → **Add Quote**
   - 选择客户
   - 单据号会自动生成（QT20251105XXXX）
   - 添加报价单明细
   - 保存

3. 验证功能:
   - ✅ 单据号自动生成
   - ✅ 总金额自动计算
   - ✅ 汇率转换（如果选择外币）

### 3. 使用 Django Shell 测试

```bash
python manage.py shell
```

```python
# 测试单据号生成器
from apps.core.utils import DocumentNumberGenerator

# 生成报价单号
quote_no = DocumentNumberGenerator.generate('QT')
print(f"报价单号: {quote_no}")

# 生成销售订单号
order_no = DocumentNumberGenerator.generate('SO')
print(f"订单号: {order_no}")

# 查看所有报价单
from apps.sales.models import Quote
quotes = Quote.objects.all()
print(f"报价单数量: {quotes.count()}")
for q in quotes:
    print(f"  - {q.quote_number}: {q.customer.name}, {q.total_amount} {q.currency}")

# 测试报价单转订单
if quotes.exists():
    quote = quotes.first()
    order = quote.convert_to_order()
    print(f"报价单 {quote.quote_number} 已转换为订单 {order.order_number}")
```

---

## 📁 项目结构

```
django_erp/
├── apps/                      # 应用模块
│   ├── core/                  # 核心功能
│   │   └── utils/             # 工具类（单据号生成器等）
│   ├── sales/                 # 销售管理（报价单已完成）
│   ├── purchase/              # 采购管理
│   ├── inventory/             # 库存管理
│   ├── customers/             # 客户管理
│   ├── products/              # 产品管理
│   └── ...
├── better_laser_erp/          # Django 项目配置
│   ├── settings.py            # 配置文件（已优化）
│   └── urls.py                # 路由配置
├── db.sqlite3                 # SQLite 数据库（自动生成）
├── manage.py                  # Django 管理脚本
├── requirements.txt           # 依赖列表（已精简）
├── .env.example               # 配置模板（已更新）
└── QUOTATION_DEPLOYMENT.md    # 报价单部署指南
```

---

## ❓ 常见问题

### Q1: pip install 太慢怎么办？

使用国内镜像源:

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2: Pillow 安装失败

**macOS**:
```bash
brew install libjpeg
pip install Pillow
```

**Ubuntu/Debian**:
```bash
sudo apt-get install libjpeg-dev zlib1g-dev
pip install Pillow
```

### Q3: ImportError: No module named 'apps'

确保在项目根目录运行命令:
```bash
cd /Users/janjung/Code_Projects/BLBS_ERP/django_erp
python manage.py runserver
```

### Q4: django.core.exceptions.ImproperlyConfigured: mysqlclient

这个错误不应该出现了，因为我们已经改用 SQLite。如果还有这个错误，说明 settings.py 没有正确修改。

### Q5: 如何重置数据库？

```bash
# 删除数据库文件
rm db.sqlite3

# 重新创建
python manage.py migrate
python manage.py createsuperuser
```

---

## 🔧 开发工具推荐

### 1. VS Code 插件
- Python
- Django
- SQLite Viewer
- Tailwind CSS IntelliSense

### 2. 数据库工具
- **DB Browser for SQLite** (免费，可视化查看 SQLite)
- 下载: https://sqlitebrowser.org/

### 3. API 测试工具
- **Postman** 或 **Insomnia**
- 测试 REST API 接口

---

## 📊 依赖包说明

| 包名 | 版本 | 用途 |
|-----|------|------|
| Django | 4.2.7 | Web 框架 |
| djangorestframework | 3.14.0 | REST API |
| django-mptt | 0.15.0 | 树形结构（部门、分类）|
| django-crispy-forms | 2.1 | 表单渲染 |
| crispy-tailwind | 0.5.0 | Tailwind CSS 样式 |
| django-filter | 23.3 | 数据过滤 |
| Pillow | 10.4.0 | 图片处理 |
| openpyxl | 3.1.2 | Excel 导入导出 |
| reportlab | 4.0.7 | PDF 生成 |
| python-decouple | 3.8 | 配置管理 |
| whitenoise | 6.6.0 | 静态文件服务 |
| django-cors-headers | 4.3.1 | CORS 跨域 |
| PyJWT | 2.8.0 | JWT 认证 |
| cryptography | 41.0.7 | 加密支持 |

**总大小**: 约 150 MB

---

## 🎉 下一步

1. ✅ **完成**: 环境搭建和基础配置
2. ✅ **完成**: 报价单模块后端开发
3. ⏭️ **待办**: 创建报价单 HTML 模板
4. ⏭️ **待办**: 完成其他单据模块（采购询价、发货单等）

---

## 📚 参考文档

- Django 官方文档: https://docs.djangoproject.com/zh-hans/4.2/
- DRF 文档: https://www.django-rest-framework.org/
- Tailwind CSS: https://tailwindcss.com/docs

---

## 💬 需要帮助？

如果遇到任何问题：
1. 检查虚拟环境是否激活
2. 确认在正确的目录（django_erp/）
3. 查看错误信息的详细堆栈
4. 参考上面的"常见问题"部分

**准备好了吗？运行命令开始开发！** 🚀

```bash
cd /Users/janjung/Code_Projects/BLBS_ERP/django_erp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
