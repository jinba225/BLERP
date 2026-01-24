# BetterLaser ERP 系统

基于 Django + Tailwind CSS 的现代化企业资源规划(ERP)系统，专为激光设备制造企业设计。

## 功能特性

### 核心模块

- **用户管理** - 用户账户、角色权限、部门管理
- **客户管理** - 客户信息、联系人、地址、价格表
- **供应商管理** - 供应商信息、产品目录、评估体系
- **产品管理** - 产品信息、分类、BOM、属性管理
- **库存管理** - 仓库管理、库存跟踪、调拨、盘点
- **销售管理** - 销售订单、报价、发货、退货
- **采购管理** - 采购订单、申请、收货、退货
- **财务管理** - 会计科目、凭证、应收应付、预算
- **生产管理** - 生产计划、工单、工艺路线
- **报表中心** - 各类业务报表和分析

### 技术特性

- **现代化界面** - 基于 Tailwind CSS 的响应式设计
- **RESTful API** - 完整的 REST API 支持
- **权限控制** - 基于角色的访问控制(RBAC)
- **审计日志** - 完整的操作记录和追踪
- **多语言支持** - 国际化和本地化支持
- **缓存优化** - Redis 缓存提升性能
- **异步任务** - Celery 异步任务处理

## 技术栈

- **后端**: Django 4.2, Django REST Framework
- **前端**: Tailwind CSS, Alpine.js
- **数据库**: MySQL 8.0
- **缓存**: Redis
- **任务队列**: Celery
- **Web服务器**: Nginx + Gunicorn

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Redis 6.0+

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd django_erp
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
npm install
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和其他设置
```

5. **数据库迁移**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **创建超级用户**
```bash
python manage.py createsuperuser
```

7. **构建前端资源**
```bash
npm run build
```

8. **启动开发服务器**
```bash
python manage.py runserver
```

访问 http://localhost:8000 查看系统。

## 项目结构

```
django_erp/
├── better_laser_erp/          # Django 项目配置
├── apps/                      # 应用模块
│   ├── core/                  # 核心模块
│   ├── users/                 # 用户管理
│   ├── customers/             # 客户管理
│   ├── suppliers/             # 供应商管理
│   ├── products/              # 产品管理
│   ├── inventory/             # 库存管理
│   ├── sales/                 # 销售管理
│   ├── purchase/              # 采购管理
│   ├── finance/               # 财务管理
│   ├── production/            # 生产管理
│   └── reports/               # 报表中心
├── templates/                 # 模板文件
├── static/                    # 静态资源
├── media/                     # 媒体文件
└── requirements.txt           # Python 依赖
```

## 数据库设计

系统采用模块化的数据库设计，主要包括：

- **用户模块**: 用户、角色、权限、部门
- **基础数据**: 客户、供应商、产品、仓库
- **业务流程**: 销售、采购、库存、财务
- **系统管理**: 配置、日志、附件

详细的数据库设计文档请参考 `docs/database.md`。

## API 文档

系统提供完整的 RESTful API，支持：

- 认证和授权
- CRUD 操作
- 批量操作
- 搜索和过滤
- 分页和排序

API 文档访问地址：http://localhost:8000/api/docs/

## 部署指南

### Docker 部署

1. **构建镜像**
```bash
docker-compose build
```

2. **启动服务**
```bash
docker-compose up -d
```

### 生产环境部署

详细的生产环境部署指南请参考 `docs/deployment.md`。

## 开发指南

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 编写单元测试和文档

### 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证，详情请参考 [LICENSE](LICENSE) 文件。

## 支持

如有问题或建议，请：

1. 查看文档
2. 搜索已有 Issues
3. 创建新的 Issue
4. 联系开发团队

## 更新日志

详细的更新日志请参考 [CHANGELOG.md](CHANGELOG.md)。