# Django ERP 系统 - iFlow 上下文文档

## 项目概述

这是一个基于 Django + Tailwind CSS 的现代化企业资源规划(ERP)系统，专为激光设备制造企业设计。系统采用模块化架构，包含用户管理、客户管理、供应商管理、产品管理、库存管理、销售管理、采购管理、财务管理等核心业务模块。

### 技术栈
- **后端**: Django 4.2, Django REST Framework
- **前端**: Tailwind CSS, Alpine.js
- **数据库**: 开发环境使用 SQLite，生产环境支持 MySQL 8.0
- **缓存**: 开发环境使用本地缓存，生产环境支持 Redis
- **任务队列**: Celery (生产环境)
- **Web服务器**: Nginx + Gunicorn (生产环境)

## 项目结构

```
django_erp/
├── better_laser_erp/          # Django 项目配置
│   ├── settings.py            # 主配置文件
│   ├── urls.py               # 主路由配置
│   └── wsgi.py               # WSGI 配置
├── apps/                      # 应用模块
│   ├── authentication/       # 认证模块
│   ├── contracts/           # 合同管理
│   ├── core/                # 核心模块
│   ├── customers/           # 客户管理
│   ├── departments/         # 部门管理
│   ├── finance/             # 财务管理
│   ├── inventory/           # 库存管理
│   ├── products/            # 产品管理
│   ├── purchase/            # 采购管理
│   ├── reports/             # 报表中心
│   ├── sales/               # 销售管理
│   ├── suppliers/           # 供应商管理
│   └── users/               # 用户管理
├── templates/               # 模板文件
├── static/                  # 静态资源
├── media/                   # 媒体文件
├── requirements.txt         # Python 依赖
├── package.json            # Node.js 依赖
├── docker-compose.yml      # Docker 编排文件
├── .env.example            # 环境变量模板
└── manage.py               # Django 管理脚本
```

## 构建和运行

### 开发环境快速启动

1. **创建虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
```

2. **安装依赖**
```bash
pip install -r requirements.txt
npm install
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，保持默认配置即可（使用 SQLite）
```

4. **数据库迁移**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **创建超级用户**
```bash
python manage.py createsuperuser
```

6. **构建前端资源**
```bash
npm run build
```

7. **启动开发服务器**
```bash
python manage.py runserver
```

访问 http://localhost:8000 查看系统。

### Docker 开发环境

```bash
# 启动所有服务（数据库、Redis、Web应用）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f web

# 停止服务
docker-compose down
```

### 常用管理命令

```bash
# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 收集静态文件
python manage.py collectstatic

# Django Shell
python manage.py shell

# 查看路由
python manage.py show_urls
```

### 前端资源构建

```bash
# 开发模式（监听文件变化）
npm run dev

# 生产构建（压缩）
npm run build

# 仅构建 CSS
npm run build-css
```

## 开发约定

### 代码规范
- 遵循 PEP 8 Python 代码规范
- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 前端使用 Tailwind CSS 类名规范

### 应用结构
每个应用模块通常包含：
- `models.py` - 数据模型
- `views.py` - 视图逻辑
- `serializers.py` - API 序列化器
- `urls.py` - 路由配置
- `admin.py` - 后台管理
- `tests/` - 测试文件
- `migrations/` - 数据库迁移

### 数据库设计原则
- 使用 UUID 作为主键（可选）
- 软删除字段（deleted_at）
- 创建时间、更新时间字段
- 用户审计字段（created_by, updated_by）

### API 设计
- 使用 Django REST Framework
- 遵循 RESTful 设计原则
- 统一的响应格式
- JWT 认证机制
- API 版本控制

## 环境配置

### 开发环境
- 数据库：SQLite
- 缓存：本地内存缓存
- 调试模式：开启
- 静态文件：Django 直接服务

### 生产环境
- 数据库：MySQL 8.0
- 缓存：Redis
- 调试模式：关闭
- 静态文件：Nginx 服务
- 异步任务：Celery

### 关键环境变量

```bash
# Django 核心配置
DEBUG=True                    # 生产环境设为 False
SECRET_KEY=your-secret-key    # 必须设置
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库配置（生产环境）
DB_ENGINE=django.db.backends.mysql
DB_NAME=django_erp
DB_USER=django_user
DB_PASSWORD=your_password
DB_HOST=db
DB_PORT=3306

# Redis 配置（生产环境）
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# JWT 认证
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DELTA=86400
```

## 测试

```bash
# 运行所有测试
python manage.py test

# 运行特定应用测试
python manage.py test apps.sales

# 运行特定测试类
python manage.py test apps.sales.tests.TestOrderModel

# 生成测试覆盖率报告
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 部署

### 生产环境部署

1. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，设置生产环境配置
```

2. **使用 Docker Compose 生产配置**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. **收集静态文件**
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

4. **数据库迁移**
```bash
docker-compose exec web python manage.py migrate
```

### 备份和恢复

```bash
# 数据库备份
python manage.py dbbackup

# 数据库恢复
python manage.py dbrestore

# 媒体文件备份
tar -czf media_backup.tar.gz media/
```

## 故障排除

### 常见问题

1. **数据库连接错误**
   - 检查数据库服务是否启动
   - 验证数据库配置信息
   - 确认网络连接

2. **静态文件 404**
   - 运行 `python manage.py collectstatic`
   - 检查 STATIC_URL 和 STATIC_ROOT 配置

3. **权限错误**
   - 检查文件和目录权限
   - 确认用户和组设置

4. **依赖包冲突**
   - 使用虚拟环境
   - 更新 requirements.txt
   - 重新安装依赖

### 日志查看

```bash
# Django 日志
tail -f logs/django.log

# Gunicorn 日志（生产环境）
tail -f logs/gunicorn_access.log
tail -f logs/gunicorn_error.log

# Docker 日志
docker-compose logs -f web
docker-compose logs -f db
```

## 扩展开发

### 添加新应用模块

1. **创建应用**
```bash
python manage.py startapp new_module
```

2. **添加到 INSTALLED_APPS**
在 `better_laser_erp/settings.py` 中添加新应用

3. **配置路由**
在 `better_laser_erp/urls.py` 中包含新应用路由

4. **创建模型、视图、序列化器**
按照现有应用的结构创建相应文件

### 自定义管理命令

在应用目录下创建 `management/commands/your_command.py`

```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Your custom command description'
    
    def handle(self, *args, **options):
        # 命令逻辑
        self.stdout.write(self.style.SUCCESS('Command executed successfully'))
```

## 性能优化

### 数据库优化
- 使用 `select_related()` 和 `prefetch_related()`
- 添加适当的数据库索引
- 使用数据库连接池

### 缓存策略
- 视图缓存
- 模板片段缓存
- 查询结果缓存

### 前端优化
- 压缩 CSS 和 JavaScript
- 使用 CDN
- 图片优化

## 安全考虑

### 必须配置的安全设置
- 生产环境设置 `DEBUG=False`
- 配置正确的 `ALLOWED_HOSTS`
- 设置强密码的 `SECRET_KEY`
- 使用 HTTPS
- 配置安全头

### 数据保护
- 敏感数据加密
- 用户权限控制
- 审计日志记录
- 定期安全更新