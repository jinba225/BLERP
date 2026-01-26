# BetterLaser ERP 系统

> 专为激光设备制造企业设计的全功能 ERP 系统
> 基于 Django 5.0 + Django REST Framework 3.15 + Tailwind CSS 3.4

BetterLaser ERP 是一个功能完备的现代化企业资源规划(ERP)系统，专为激光设备制造企业设计。系统采用模块化架构，实现了从销售、采购、库存到财务的完整业务闭环，并集成了 AI 智能助手，显著提升工作效率。

---

## 🌟 核心亮点

- ✅ **12 个业务模块** - 覆盖企业完整业务流程
- ✅ **AI 智能助手** - 多渠道 AI 集成（钉钉、微信、Telegram）
- ✅ **主题切换** - 三套主题（蓝色、黄色、红色）
- ✅ **打印模板** - 可视化模板设计器，支持 PDF 导出
- ✅ **财务闭环** - 完整的应收应付管理
- ✅ **借用单管理** - 采购借用特色功能
- ✅ **含税价格体系** - 符合中国税务实务

---

## 🏢 核心业务模块

### 1. **AI 智能助手** (apps/ai_assistant/)
- ✅ **多渠道支持**：钉钉、微信、Telegram
- ✅ **自然语言查询**：支持中文自然语言提问
- ✅ **智能检索**：自动搜索产品、客户、供应商等信息
- ✅ **工具集成**：库存查询、采购查询、销售查询、报表生成
- ✅ **对话管理**：保存历史对话，支持上下文记忆

### 2. **认证授权** (apps/authentication/)
- ✅ **JWT 认证**：基于 JWT Token 的无状态认证
- ✅ **Session 认证**：传统 Cookie 认证支持
- ✅ **权限控制**：基于角色的访问控制(RBAC)
- ✅ **双因素认证**：支持 2FA（可选）

### 3. **用户管理** (apps/users/)
- ✅ **用户管理**：创建、编辑、删除、禁用用户
- ✅ **角色管理**：自定义角色和权限
- ✅ **部门管理**：组织架构管理
- ✅ **操作日志**：完整的用户操作记录和审计追踪

### 4. **客户管理** (apps/customers/)
- ✅ **客户信息**：客户基本信息、联系方式、地址
- ✅ **联系人管理**：支持每个客户多个联系人
- ✅ **价格表**：按客户设定产品价格
- ✅ **往来账务**：完整的客户应收账款管理

### 5. **供应商管理** (apps/suppliers/)
- ✅ **供应商信息**：供应商基本信息、联系方式
- ✅ **产品目录**：供应商提供的产品和价格
- ✅ **评估体系**：供应商评级和评估
- ✅ **往来账务**：完整的供应商应付账款管理

### 6. **产品管理** (apps/products/)
- ✅ **产品信息**：产品名称、编码、条形码、规格
- ✅ **产品分类**：多级分类体系
- ✅ **品牌管理**：品牌信息管理
- ✅ **计量单位**：基本单位、采购单位、销售单位
- ✅ **BOM 管理**：物料清单管理
- ✅ **价格体系**：成本价、销售价、建议价
- ✅ **库存跟踪**：库存上下限预警

### 7. **库存管理** (apps/inventory/)
- ✅ **仓库管理**：多仓库支持
- ✅ **入库管理**：采购入库、生产入库、其他入库
- ✅ **出库管理**：销售出库、领料出库、其他出库
- ✅ **调拨管理**：仓库间库存调拨
- ✅ **盘点管理**：定期盘点、差异调整
- ✅ **库存调整**：手动调整库存
- ✅ **实时库存**：准确的库存实时查询
- ✅ **库存流水**：完整的库存变动记录

### 8. **销售管理** (apps/sales/) ⭐ 核心业务
- ✅ **报价单**：创建、编辑、发送报价单
- ✅ **销售订单**：订单审核、订单变更、订单取消
- ✅ **发货单**：发货确认、部分发货、发货单打印
- ✅ **销售退货**：退货单创建、退货入库
- ✅ **审批流程**：订单审核、发货审核
- ✅ **自动业务**：审核订单自动生成发货单和应收账款

### 9. **采购管理** (apps/purchase/) ⭐ 核心业务
- ✅ **采购申请**：内部采购需求申请
- ✅ **采购订单**：订单审核、订单变更
- ✅ **收货单**：收货确认、部分收货、质检
- ✅ **采购退货**：退货单创建、退款处理
- ✅ **借用单**：采购借用、归还、转采购订单 ⭐ 特色功能
- ✅ **审批流程**：申请审核、订单审核、收货审核
- ✅ **自动业务**：审核订单自动生成收货单和应付账款

### 10. **财务管理** (apps/finance/)
- ✅ **应收账款**：客户应收账款管理、收款登记
- ✅ **应付账款**：供应商应付账款管理、付款登记
- ✅ **收款单**：收款确认、部分收款、预收款
- ✅ **付款单**：付款确认、部分付款、预付款
- ✅ **核销管理**：应收应付核销、支持多对多核销
- ✅ **预收款/预付款**：预收款和预付款管理
- ✅ **报表统计**：应收应付账龄分析、回款预测

### 11. **基础配置** (apps/core/)
- ✅ **系统配置**：基础参数、业务参数
- ✅ **打印模板**：可视化模板设计器、默认模板管理
- ✅ **单据号生成**：自动生成规则、支持自定义前缀
- ✅ **通知管理**：系统通知、消息推送
- ✅ **附件管理**：文件上传、下载、预览

### 12. **部门管理** (apps/departments/)
- ✅ **部门管理**：创建、编辑、删除部门
- ✅ **人员管理**：部门人员分配

---

## 🎨 前端特性

- ✅ **主题切换**：支持蓝色、黄色、红色三套主题
- ✅ **响应式设计**：基于 Tailwind CSS 的完全响应式布局
- ✅ **现代化 UI**：简洁、专业的界面设计
- ✅ **表单验证**：实时表单验证和错误提示
- ✅ **动态交互**：基于 Alpine.js 的轻量级交互
- ✅ **统一焦点样式**：所有输入框焦点边框统一使用主题色

---

## 🏗️ 技术栈

### 后端技术栈

- **Python**: 3.8+
- **Django**: 5.0.9 (主框架)
- **Django REST Framework**: 3.15.2 (API 框架)
- **Celery**: 5.3.4 (异步任务队列)
- **Redis**: 6.0+ (缓存和消息队列)

### 数据库技术栈

- **开发环境**: SQLite 3.36+
- **生产环境**: MySQL 8.0+
- **ORM**: Django ORM + django-mptt 0.15.0 (树形结构)

### 前端技术栈

- **Tailwind CSS**: 3.4.18 (CSS 框架)
- **Alpine.js**: 3.14.3 (轻量级 JavaScript 框架)
- **Vanilla JavaScript**: 原生 JavaScript
- **jQuery**: 3.6.0 (DOM 操作)
- **HiPrint**: (打印引擎)

### 其他关键库

- **认证**: PyJWT 2.8.0
- **文档生成**: reportlab 4.0.7 (PDF)
- **Excel 处理**: openpyxl 3.1.2
- **数据导入导出**: django-import-export 4.0.0
- **图片处理**: Pillow 10.4.0

### Web 服务器

- **Nginx**: 1.25+ (反向代理和静态文件服务)
- **Gunicorn**: 21.2.0 (WSGI HTTP 服务器)
- **Docker**: 24.0+ (容器化部署)
- **Docker Compose**: 2.23+ (多容器编排)

---

## 🚀 快速开始

### 环境要求

#### 开发环境
- Python 3.8+
- Node.js 16+
- SQLite (开发环境)
- Git 2.0+

#### 生产环境
- Python 3.8+
- MySQL 8.0+
- Redis 6.0+
- Nginx 1.25+
- Docker 24.0+

### 安装步骤

#### 方式一：本地开发（推荐新手）

**1. 克隆项目**
```bash
git clone https://github.com/jinba225/BLERP.git
cd django_erp
```

**2. 创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

**3. 安装依赖**
```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
npm install
```

**4. 配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和其他设置
```

**5. 数据库迁移**
```bash
# 查看待迁移的更改
python manage.py makemigrations

# 应用迁移
python manage.py migrate
```

**6. 创建超级用户**
```bash
python manage.py createsuperuser
```

**7. 构建前端资源**
```bash
# 开发模式（监听 CSS 变更）
npm run dev

# 生产构建（压缩 CSS）
npm run build
```

**8. 启动开发服务器**
```bash
python manage.py runserver
```

**9. 访问系统**
- 开发服务器：http://127.0.0.1:8000
- 登录页面：http://127.0.0.1:8000/login/

#### 方式二：Docker 部署（推荐生产环境）

**1. 使用 Docker Compose 启动**
```bash
docker-compose up -d
```

**2. 初始化数据库**
```bash
# 运行迁移
docker-compose exec web python manage.py migrate

# 创建超级用户
docker-compose exec web python manage.py createsuperuser
```

**3. 访问系统**
- 开发环境：http://127.0.0.1:8000
- 生产环境：http://your-domain.com

---

## 📁 项目结构

```
django_erp/
├── better_laser_erp/          # Django 项目配置
│   ├── __init__.py
│   ├── settings.py            # 项目配置
│   ├── urls.py               # 根 URL 路由
│   ├── wsgi.py               # WSGI 入口
│   └── celery.py             # Celery 配置
├── apps/                      # 应用模块（12 个）
│   ├── ai_assistant/          # AI 智能助手
│   │   ├── models.py         # AI 对话、工具执行日志
│   │   ├── views.py         # Webhook 视图
│   │   ├── services/        # AI 服务
│   │   ├── providers/       # AI 提供商（OpenAI、Anthropic、百度）
│   │   ├── channels/        # 多渠道支持（钉钉、微信、Telegram）
│   │   └── tools/          # 工具集成
│   ├── authentication/       # 认证授权
│   │   ├── models.py        # 用户、角色、权限
│   │   ├── authentication.py # JWT/Session 认证
│   │   ├── serializers.py   # API 序列化器
│   │   └── tests/          # 认证测试
│   ├── core/                # 核心基础设施
│   │   ├── models.py        # BaseModel、打印模板、通知
│   │   ├── models_choice.py # 选项数据
│   │   ├── utils/          # 工具类
│   │   └── services/       # 业务服务
│   ├── customers/           # 客户管理
│   │   ├── models.py        # 客户、联系人
│   │   └── views.py        # 客户视图
│   ├── departments/         # 部门管理
│   ├── finance/             # 财务管理
│   │   ├── models.py        # 应收应付、收款付款
│   │   └── views.py        # 财务视图
│   ├── inventory/           # 库存管理
│   │   ├── models.py        # 入库、出库、调拨、盘点
│   │   └── views.py        # 库存视图
│   ├── products/            # 产品管理
│   │   ├── models.py        # 产品、分类、品牌、单位
│   │   └── views.py        # 产品视图
│   ├── purchase/            # 采购管理（含借用单）
│   │   ├── models.py        # 申请、订单、收货、借用
│   │   └── views.py        # 采购视图
│   ├── sales/               # 销售管理
│   │   ├── models.py        # 报价、订单、发货、退货
│   │   └── views.py        # 销售视图
│   ├── suppliers/           # 供应商管理
│   │   ├── models.py        # 供应商、产品目录
│   │   └── views.py        # 供应商视图
│   └── users/               # 用户管理
│       ├── models.py        # 用户、部门
│       └── views.py        # 用户视图
├── templates/                 # Django 模板（237 个文件）
│   ├── core/                # 核心页面（登录、数据库管理）
│   ├── customers/           # 客户模板
│   ├── sales/               # 销售模板
│   ├── purchase/            # 采购模板
│   ├── inventory/           # 库存模板
│   ├── finance/             # 财务模板
│   └── base.html            # 基础模板
├── static/                    # 静态资源
│   ├── css/                 # Tailwind CSS（编译后）
│   ├── js/                  # JavaScript 文件
│   └── libs/                # 第三方库
├── media/                     # 用户上传文件
├── docs/                      # 项目文档
│   ├── index.md             # 文档索引
│   ├── project-overview.md   # 项目概览
│   ├── architecture.md       # 系统架构
│   ├── development-guide.md  # 开发指南
│   ├── API_ENDPOINTS_CATALOG.md # API 目录
│   ├── DATABASE_SCHEMA_ANALYSIS.md # 数据库分析
│   └── DJANGO_ERP_TECHNICAL_ANALYSIS.md # 技术分析
├── scripts/                   # 实用脚本
│   ├── archive/             # 归档脚本
│   ├── backup.sh            # 数据库备份
│   ├── restore.sh           # 数据库恢复
│   └── quick_start.sh       # 快速启动
├── requirements.txt           # Python 依赖
├── package.json              # Node.js 依赖
├── tailwind.config.js        # Tailwind 配置
├── manage.py                # Django 管理脚本
├── AGENTS.md                # AI 编码代理指南
├── CLAUDE.md                # Claude AI 开发指导文档
└── README.md                # 本文件
```

### 核心数据流

```
销售流程：
  报价单 → 销售订单 → 审核订单 → 发货单 → 收款单 → 核销应收

采购流程：
  采购申请 → 采购订单 → 审核订单 → 收货单 → 付款单 → 核销应付

库存流程：
  入库单 → 实时库存 → 出库单 → 调拨单 → 盘点单 → 库存调整

借用流程（特色）：
  借用单 → 归还单 → 转采购订单（可选）
```

---

## 📖 开发指南

### 代码规范

#### Python 代码规范
- 遵循 PEP 8 Python 代码规范
- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 编写单元测试和文档字符串
- 参见 [AGENTS.md](AGENTS.md) 获取完整编码指南

#### 前端代码规范
- 使用 Tailwind CSS 进行样式开发
- 遵循 4 空格缩进
- 使用语义化的 HTML 标签
- JavaScript 使用小驼峰命名
- 参见 [AGENTS.md](AGENTS.md) 获取前端开发指南

### 测试规范

#### 运行测试
```bash
# 运行所有测试
python manage.py test

# 运行特定模块测试
python manage.py test apps.sales
python manage.py test apps.core

# 运行特定测试文件
python manage.py test apps.sales.tests.test_models

# 运行单个测试类
python manage.py test apps.sales.tests.test_models.SalesOrderModelTest

# 运行单个测试方法
python manage.py test apps.sales.tests.test_models.SalesOrderModelTest.test_order_creation

# 详细输出
python manage.py test -v 2

# 保留测试数据库（用于调试）
python manage.py test --keepdb
```

#### 代码覆盖率
```bash
# 运行测试并生成覆盖率报告
coverage run --source='.' manage.py test
coverage report

# 生成 HTML 覆盖率报告
coverage html  # 查看 htmlcov/index.html
```

### 调试技巧

#### 开发模式
```bash
# 启动开发服务器
python manage.py runserver

# 启动 Celery worker
celery -A better_laser_erp worker -l info

# 启动 Celery beat
celery -A better_laser_erp beat -l info
```

#### 日志查看
```bash
# 查看应用日志
tail -f logs/django.log

# 查看 Celery 日志
tail -f logs/celery.log
```

---

## 🎨 主题切换

系统支持三套主题，可在登录页面和用户设置中切换：

### 可用主题
- 🔵 **蓝色主题**（默认）- 专业的蓝色调
- 🟡 **黄色主题** - 温暖的黄色调
- 🔴 **红色主题** - 稳重的红色调

### 主题切换方式
- 登录页面右上角的主题切换按钮
- 用户设置中的主题配置
- 所有页面自动应用当前主题

### 技术实现
- 基于 CSS 变量（`--theme-*`）
- 使用 Tailwind CSS 的 `theme-*` 颜色类
- JavaScript 动态切换 CSS 变量值

---

## 🤖 AI 智能助手

系统集成了多渠道 AI 智能助手，支持自然语言查询和智能检索。

### 支持的渠道
- **钉钉**：企业内部沟通
- **微信**：微信企业号/公众号
- **Telegram**：国际沟通

### 核心功能
- **自然语言查询**：支持中文自然语言提问
- **智能检索**：自动搜索产品、客户、供应商等信息
- **工具集成**：库存查询、采购查询、销售查询、报表生成
- **对话管理**：保存历史对话，支持上下文记忆
- **权限控制**：基于角色的工具访问控制

### 使用示例
```
用户：查询产品 A001 的库存数量
AI：产品 A001 当前库存为 500 件，已分配订单 200 件，可用库存 300 件

用户：生成上个月的销售报表
AI：正在生成销售报表...请稍候
AI：已生成销售报表，总计订单 50 笔，总金额 500,000 元
```

---

## 🖨️ 打印模板

系统提供灵活的打印模板管理功能，支持可视化模板设计。

### 功能特性
- **可视化设计器**：拖拽式模板设计
- **多模板类型**：支持报价单、订单、发货单、单据等
- **默认模板**：预置专业的默认模板
- **模板变量**：支持丰富的模板变量（单据号、客户信息、产品明细等）
- **批量打印**：支持批量打印单据
- **导出 PDF**：支持导出 PDF 格式

### 技术实现
- 基于 HiPrint 打印引擎
- 支持自定义 CSS 样式
- 支持模板继承和复用

---

## 🌐 部署指南

### Docker 部署

#### 1. 构建镜像
```bash
docker-compose build
```

#### 2. 启动服务
```bash
docker-compose up -d
```

#### 3. 环境变量配置
创建 `.env` 文件，配置以下变量：
- `DJANGO_SECRET_KEY`: Django 密钥
- `DATABASE_URL`: MySQL 连接字符串
- `REDIS_URL`: Redis 连接字符串
- `ALLOWED_HOSTS`: 允许的主机列表

### 生产环境部署

详细的生产环境部署指南请参考 [docs/deployment.md](docs/deployment.md)。

---

## 📚 支持资源

### 项目文档
- [项目文档索引](docs/index.md) - 完整的项目文档体系
- [技术分析报告](DJANGO_ERP_TECHNICAL_ANALYSIS.md) - 全面的技术分析报告
- [API 目录](API_ENDPOINTS_CATALOG.md) - REST API 完整清单
- [数据库分析](DATABASE_SCHEMA_ANALYSIS.md) - 数据模型设计
- [开发指南](docs/development-guide.md) - 开发环境设置
- [AI 编码指南](AGENTS.md) - AI 编码代理操作指南
- [Claude 配置](CLAUDE.md) - Claude AI 开发指导文档

### 官方文档
- [Django 官方文档](https://docs.djangoproject.com/)
- [Django REST Framework 文档](https://www.django-rest-framework.org/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
- [Alpine.js 文档](https://alpinejs.dev/)

### 项目相关
- **GitHub 仓库**: https://github.com/jinba225/BLERP
- **问题反馈**: GitHub Issues
- **技术支持**: 查看项目文档或联系开发团队

---

## 📝 更新日志

详细的版本更新记录请参考：
- [CHANGELOG.md](CHANGELOG.md) - 版本变更历史
- [Git 提交历史](https://github.com/jinba225/BLERP/commits/main) - 详细的提交记录

### 最近更新
- **2026-01-25**: 统一表单元素焦点样式，配置 @tailwindcss/forms 插件，移除蓝色 box-shadow
- **2026-01-24**: 清理项目代码，归档临时脚本，添加技术文档
- **2026-01-18**: 更新 Claude AI 配置文档，优化开发指南
- **2026-01-07**: 添加技术指南文档，完善项目文档体系

---

## 📊 项目规模

| 类别 | 数量 |
|------|------|
| **核心业务代码** | 63,325 行 Python 代码 |
| **模型代码** | 6,325 行数据模型 |
| **业务模块** | 12 个独立应用 |
| **数据模型** | 80+ 个数据表 |
| **模板文件** | 237 个 HTML 模板 |
| **测试文件** | 27 个测试文件 |
| **API 接口** | 350+ 个 REST 接口 |

---

## 🎯 快速开始

### 新用户
1. 阅读 [项目概览](docs/project-overview.md) 了解系统
2. 按照 [安装指南](docs/development-guide.md) 设置环境
3. 参考 [用户指南](docs/user-guide.md) 学习使用

### 开发者
1. 阅读 [开发指南](docs/development-guide.md) 设置开发环境
2. 查看 [系统架构](docs/architecture.md) 理解设计
3. 学习 [源代码树分析](docs/source-tree-analysis.md) 了解代码组织

### 运维人员
1. 参考 [部署指南](docs/deployment.md) 进行部署
2. 配置监控和日志
3. 设置备份策略

---

**本 README 持续更新中，如有问题请及时反馈。**
