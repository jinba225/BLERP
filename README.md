# BetterLaser ERP 系统

> 专为激光设备制造企业设计的全功能 ERP 系统
> 基于 Django 5.0 + Django REST Framework 3.15 + Tailwind CSS 3.4

BetterLaser ERP 是一个功能完备的现代化企业资源规划(ERP)系统，专为激光设备制造企业设计。系统采用模块化架构，实现了从销售、采购、库存到财务的完整业务闭环，并集成了 AI 智能助手和电商平台数据采集功能，显著提升工作效率。

---

## 🌟 核心亮点

- ✅ **14 个业务模块** - 覆盖企业完整业务流程，含电商数据采集
- ✅ **AI 智能助手** - 多渠道 AI 集成（钉钉、微信、Telegram）
- ✅ **电商平台对接** - 支持6大主流电商平台（淘宝、京东、拼多多、抖音、快手、1688）
- ✅ **数据采集管理** - 统一的电商平台数据采集和管理
- ✅ **主题切换** - 三套主题（蓝色、黄色、红色）
- ✅ **打印模板** - 可视化模板设计器，支持 PDF 导出
- ✅ **财务闭环** - 完整的应收应付管理
- ✅ **借用单管理** - 采购借用特色功能
- ✅ **含税价格体系** - 符合中国税务实务
- ✅ **统一交互体验** - 所有输入框焦点样式统一，主题色高亮

---

## 🏢 核心业务模块

### 1. **AI 智能助手** (ai_assistant/)
- ✅ **多渠道支持**：钉钉、微信、Telegram
- ✅ **自然语言查询**：支持中文自然语言提问
- ✅ **智能检索**：自动搜索产品、客户、供应商等信息
- ✅ **工具集成**：库存查询、采购查询、销售查询、报表生成
- ✅ **对话管理**：保存历史对话，支持上下文记忆

### 2. **认证授权** (authentication/)
- ✅ **JWT 认证**：基于 JWT Token 的无状态认证
- ✅ **Session 认证**：传统 Cookie 认证支持
- ✅ **权限控制**：基于角色的访问控制(RBAC)
- ✅ **双因素认证**：支持 2FA（可选）
- ✅ **API 文档**：集成 drf-spectacular 自动生成 OpenAPI 文档

### 3. **用户管理** (users/)
- ✅ **用户管理**：创建、编辑、删除、禁用用户
- ✅ **角色管理**：自定义角色和权限
- ✅ **部门管理**：组织架构管理
- ✅ **操作日志**：完整的用户操作记录和审计追踪
- ✅ **权限系统**：细粒度权限控制（users/permissions.py）

### 4. **客户管理** (customers/)
- ✅ **客户信息**：客户基本信息、联系方式、地址
- ✅ **联系人管理**：支持每个客户多个联系人
- ✅ **价格表**：按客户设定产品价格
- ✅ **往来账务**：完整的客户应收账款管理
- ✅ **数据导出**：支持客户数据导出（django-import-export）

### 5. **供应商管理** (suppliers/)
- ✅ **供应商信息**：供应商基本信息、联系方式
- ✅ **产品目录**：供应商提供的产品和价格
- ✅ **评估体系**：供应商评级和评估
- ✅ **往来账务**：完整的供应商应付账款管理

### 6. **产品管理** (products/)
- ✅ **产品信息**：产品名称、编码、条形码、规格
- ✅ **产品分类**：多级分类体系
- ✅ **品牌管理**：品牌信息管理
- ✅ **计量单位**：基本单位、采购单位、销售单位
- ✅ **BOM 管理**：物料清单管理
- ✅ **价格体系**：成本价、销售价、建议价
- ✅ **库存跟踪**：库存上下限预警

### 7. **库存管理** (inventory/)
- ✅ **仓库管理**：多仓库支持
- ✅ **入库管理**：采购入库、生产入库、其他入库
- ✅ **出库管理**：销售出库、领料出库、其他出库
- ✅ **调拨管理**：仓库间库存调拨
- ✅ **盘点管理**：定期盘点、差异调整
- ✅ **库存调整**：手动调整库存
- ✅ **实时库存**：准确的库存实时查询
- ✅ **库存流水**：完整的库存变动记录
- ✅ **资源导出**：支持库存数据导出（inventory/resources.py）

### 8. **销售管理** (sales/) ⭐ 核心业务
- ✅ **报价单**：创建、编辑、发送报价单
- ✅ **销售订单**：订单审核、订单变更、订单取消
- ✅ **发货单**：发货确认、部分发货、发货单打印
- ✅ **销售退货**：退货单创建、退货入库
- ✅ **审批流程**：订单审核、发货审核
- ✅ **自动业务**：审核订单自动生成发货单和应收账款
- ✅ **打印模板**：可视化模板编辑器（hiprint）

### 9. **采购管理** (purchase/) ⭐ 核心业务
- ✅ **采购申请**：内部采购需求申请
- ✅ **采购订单**：订单审核、订单变更
- ✅ **收货单**：收货确认、部分收货、质检
- ✅ **采购退货**：退货单创建、退款处理
- ✅ **借用单**：采购借用、归还、转采购订单 ⭐ 特色功能
- ✅ **审批流程**：申请审核、订单审核、收货审核
- ✅ **自动业务**：审核订单自动生成收货单和应付账款
- ✅ **供应商检索**：支持供应商名称和编码搜索

### 10. **财务管理** (finance/)
- ✅ **应收账款**：客户应收账款管理、收款登记
- ✅ **应付账款**：供应商应付账款管理、付款登记
- ✅ **收款单**：收款确认、部分收款、预收款
- ✅ **付款单**：付款确认、部分付款、预付款
- ✅ **核销管理**：应收应付核销、支持多对多核销
- ✅ **预收款/预付款**：预收款和预付款管理
- ✅ **报表统计**：应收应付账龄分析、回款预测
- ✅ **发票管理**：开票登记、发票打印

### 11. **基础配置** (core/)
- ✅ **系统配置**：基础参数、业务参数
- ✅ **打印模板**：可视化模板设计器、默认模板管理
- ✅ **单据号生成**：自动生成规则、支持自定义前缀
- ✅ **通知管理**：系统通知、消息推送
- ✅ **附件管理**：文件上传、下载、预览
- ✅ **序列化管理**：核心工具类和服务（core/utils/managers/）

### 12. **部门管理** (departments/)
- ✅ **部门管理**：创建、编辑、删除部门
- ✅ **人员管理**：部门人员分配

### 13. **采集管理** (collect/) 🆕
- ✅ **统一平台**：统一的电商数据采集管理界面
- ✅ **配置管理**：采集任务配置和管理
- ✅ **数据同步**：与电商平台数据同步
- ✅ **中文名称**：Admin界面显示为"采集"

### 14. **电商同步** (ecomm_sync/) 🆕
- ✅ **多平台适配**：支持6大主流电商平台
  - 淘宝 (Taobao)
  - 京东 (JD)
  - 拼多多 (Pinduoduo)
  - 抖音 (Douyin)
  - 快手 (Kuaishou)
  - 1688 (阿里巴巴)
- ✅ **Listing管理**：商品信息统一管理
- ✅ **订单同步**：自动同步电商订单
- ✅ **库存同步**：实时库存同步到电商平台
- ✅ **平台管理**：统一平台账号和配置管理
- ✅ **适配器模式**：可扩展的电商平台适配器架构

---

## 🎨 前端特性

- ✅ **主题切换**：支持蓝色、黄色、红色三套主题
- ✅ **响应式设计**：基于 Tailwind CSS 的完全响应式布局
- ✅ **现代化 UI**：简洁、专业的界面设计
- ✅ **表单验证**：实时表单验证和错误提示
- ✅ **动态交互**：基于 Alpine.js 的轻量级交互
- ✅ **统一焦点样式**：所有输入框焦点边框统一使用主题色（focus:border-theme-500）
- ✅ **流畅过渡动画**：输入框焦点状态平滑过渡（transition-colors）
- ✅ **用户体验优化**：
  - 借用单供应商下拉菜单支持编码搜索
  - 表单输入框聚焦时边框高亮提示
  - 表格行内输入框统一样式

---

## 🏗️ 技术栈

### 后端技术栈

- **Python**: 3.13.5
- **Django**: 5.0.9 (主框架)
- **Django REST Framework**: 3.15.2 (API 框架)
- **drf-spectacular**: 0.27.2 (OpenAPI 3.0 文档生成)
- **Celery**: 5.3.4 (异步任务队列)
- **Redis**: 6.0+ (缓存和消息队列)

### 数据库技术栈

- **开发环境**: SQLite 3.36+
- **生产环境**: MySQL 8.0+
- **ORM**: Django ORM + django-mptt 0.15.0 (树形结构)

### 前端技术栈

- **Tailwind CSS**: 3.4.18 (CSS 框架)
- **@tailwindcss/forms**: 0.5.7 (表单插件)
- **Alpine.js**: 3.14.3 (轻量级 JavaScript 框架)
- **Vanilla JavaScript**: 原生 JavaScript
- **jQuery**: 3.6.0 (DOM 操作)
- **HiPrint**: (打印引擎)

### 其他关键库

- **认证**: PyJWT 2.8.0, djangorestframework-simplejwt 5.3.1
- **文档生成**: reportlab 4.0.7 (PDF)
- **Excel 处理**: openpyxl 3.1.2
- **数据导入导出**: django-import-export 4.0.0
- **图片处理**: Pillow 10.4.0
- **API 文档**: drf-spectacular 0.27.2
- **过滤和分页**: django-filter 24.3

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
- API 文档：http://127.0.0.1:8000/api/schema/

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

> **注意**：本项目已于 2026-02-03 进行深度目录结构重组（方案 C）。详见 [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

```
django_erp/
├── django_erp/                # Django 项目配置
│   ├── __init__.py
│   ├── settings.py           # 项目配置（已更新：支持 apps/ 和 common/）
│   ├── urls.py               # 根 URL 路由
│   ├── wsgi.py               # WSGI 入口
│   └── celery.py             # Celery 配置
│
├── apps/                      # 🆕 所有 Django 应用（16 个）
│   ├── ai_assistant/          # AI 智能助手
│   ├── ai_assistant/          # AI 智能助手
│   │   ├── models.py         # AI 对话、工具执行日志
│   │   ├── views.py         # Webhook 视图
│   │   ├── services/        # AI 服务
│   │   ├── providers/       # AI 提供商（OpenAI、Anthropic、百度）
│   │   ├── channels/        # 多渠道支持（钉钉、微信、Telegram）
│   │   ├── tools/          # 工具集成
│   │   └── tests/          # AI 测试
│   ├── authentication/       # 认证授权
│   │   ├── models.py        # 用户、角色、权限
│   │   ├── authentication.py # JWT/Session 认证
│   │   ├── serializers.py   # API 序列化器
│   │   ├── permissions.py  # 权限配置
│   │   └── spectacular.py  # API 文档配置
│   ├── collect/              # 采集管理 🆕
│   │   ├── models.py        # 采集任务模型
│   │   ├── admin.py         # Admin 配置
│   │   └── apps.py          # 应用配置（verbose_name="采集"）
│   ├── core/                 # 核心基础设施
│   │   ├── models.py        # BaseModel、打印模板、通知
│   │   ├── models_choice.py # 选项数据
│   │   ├── utils/           # 工具类
│   │   │   └── managers/    # 序列化管理器 🆕
│   │   └── services/        # 业务服务
│   ├── customers/            # 客户管理
│   │   ├── models.py        # 客户、联系人
│   │   ├── views.py        # 客户视图
│   │   └── resources.py    # 数据导出
│   ├── departments/          # 部门管理
│   │   └── models.py       # 部门模型
│   ├── ecomm_sync/           # 电商同步 🆕
│   │   ├── models.py        # Listing、平台、订单同步
│   │   ├── admin.py         # Admin 配置
│   │   ├── adapters/        # 电商平台适配器
│   │   │   ├── base.py      # 基础适配器
│   │   │   ├── taobao.py    # 淘宝适配器
│   │   │   ├── jd.py        # 京东适配器
│   │   │   ├── pinduoduo.py # 拼多多适配器
│   │   │   ├── douyin.py    # 抖音适配器
│   │   │   ├── kuaishou.py  # 快手适配器
│   │   │   └── alibaba1688.py # 1688适配器
│   │   ├── services/        # 同步服务
│   │   └── tests/          # 电商同步测试
│   ├── finance/              # 财务管理
│   │   ├── models.py        # 应收应付、收款付款
│   │   ├── views.py        # 财务视图
│   │   └── forms.py        # 财务表单
│   ├── inventory/            # 库存管理
│   │   ├── models.py        # 入库、出库、调拨、盘点
│   │   ├── views.py        # 库存视图
│   │   └── resources.py    # 数据导出
│   ├── products/             # 产品管理
│   │   ├── models.py        # 产品、分类、品牌、单位
│   │   └── views.py        # 产品视图
│   ├── purchase/             # 采购管理（含借用单）
│   │   ├── models.py        # 申请、订单、收货、借用
│   │   └── views.py        # 采购视图
│   ├── sales/                # 销售管理
│   │   ├── models.py        # 报价、订单、发货、退货
│   │   ├── views.py        # 销售视图
│   │   └── template_editor_*.html # 打印模板编辑器
│   ├── suppliers/            # 供应商管理
│   │   ├── models.py        # 供应商、产品目录
│   │   └── views.py        # 供应商视图
│   └── users/                # 用户管理
│       ├── models.py        # 用户、部门
│       ├── serializers.py   # 用户序列化器
│       ├── permissions.py  # 权限定义
│       └── views.py        # 用户视图
├── templates/                 # 🆕 Django 模板（重组后）
│   ├── layouts/             # 布局模板（base.html, dashboard.html）
│   ├── components/          # 可重用组件（预留）
│   └── modules/             # 模块模板
│       ├── core/            # 核心页面（登录、数据库管理）
│       ├── customers/       # 客户模板
│       ├── sales/           # 销售模板
│       ├── purchase/        # 采购模板（含借用单）
│       ├── inventory/       # 库存模板
│       ├── finance/         # 财务模板
│       └── ...              # 其他模块模板
│
├── static/                    # 🆕 静态资源（重组后）
│   ├── css/
│   │   ├── components/      # 组件样式
│   │   ├── layouts/         # 布局样式
│   │   └── modules/         # 模块样式（预留）
│   └── js/
│       ├── components/      # 组件脚本
│       ├── layouts/         # 布局脚本
│       ├── libs/            # 🆕 第三方库（已从根目录移入）
│       └── modules/         # 模块脚本（预留）
│
├── common/                    # 🆕 共享代码
│   ├── utils/               # 通用工具函数
│   │   ├── database_helper.py
│   │   ├── document_number.py
│   │   ├── cache.py
│   │   ├── encryption.py
│   │   ├── logger.py
│   │   └── ...
│   ├── mixins/              # Django 模型 mixins
│   ├── decorators/          # 装饰器
│   ├── exceptions/          # 自定义异常
│   ├── constants/           # 常量定义
│   ├── middleware/          # 中间件
│   └── validators/          # 验证器
│
├── config/                    # 配置文件
│   ├── environment/         # 🆕 环境配置
│   │   ├── .env
│   │   └── .env.example
│   ├── docker/              # Docker 配置
│   ├── nginx/               # Nginx 配置
│   └── gunicorn/            # Gunicorn 配置
│
├── scripts/                   # 🆕 所有脚本统一管理
│   ├── start_server.sh      # 启动脚本（已从根目录移入）
│   ├── backup.sh            # 备份脚本
│   ├── restore.sh           # 恢复脚本
│   └── ...                  # 其他工具脚本
│
├── docs/                      # 项目文档
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
├── postcss.config.js         # PostCSS 配置 🆕
├── manage.py                # Django 管理脚本
├── AGENTS.md                # AI 编码代理指南
├── CLAUDE.md                # Claude AI 开发指导文档
├── COLLECT_IMPLEMENTATION_COMPLETE.md # 采集模块实现文档 🆕
├── FINAL_IMPLEMENTATION_SUMMARY.md # 最终实现总结 🆕
├── OPTIMIZATION_SUMMARY.md   # 优化总结 🆕
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

电商同步流程 🆕：
  电商平台 → Listing同步 → 订单同步 → 库存同步 → ERP系统
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
- 所有输入框必须包含统一的焦点样式：
  ```html
  class="... focus:outline-none focus:border-theme-500 transition-colors"
  ```
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
celery -A django_erp worker -l info

# 启动 Celery beat
celery -A django_erp beat -l info
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

## 🛒 电商平台对接 🆕

系统集成了6大主流电商平台的数据采集和同步功能，实现电商业务与ERP系统的无缝对接。

### 支持的电商平台

| 平台 | 适配器 | 支持功能 |
|------|--------|----------|
| **淘宝** | TaobaoAdapter | Listing同步、订单同步、库存同步 |
| **京东** | JDAdapter | Listing同步、订单同步、库存同步 |
| **拼多多** | PinduoduoAdapter | Listing同步、订单同步、库存同步 |
| **抖音** | DouyinAdapter | Listing同步、订单同步、库存同步 |
| **快手** | KuaishouAdapter | Listing同步、订单同步、库存同步 |
| **1688** | Alibaba1688Adapter | Listing同步、订单同步、库存同步 |

### 核心功能

#### 1. Listing 管理
- ✅ 统一的商品信息管理
- ✅ 多平台商品映射
- ✅ 自动同步商品数据
- ✅ 商品状态管理

#### 2. 订单同步
- ✅ 自动拉取电商平台订单
- ✅ 订单状态实时更新
- ✅ 订单信息自动归档
- ✅ 支持批量订单处理

#### 3. 库存同步
- ✅ ERP库存自动同步到电商平台
- ✅ 库存变化实时推送
- ✅ 多平台库存统一管理
- ✅ 防止超卖机制

#### 4. 平台管理
- ✅ 多平台账号管理
- ✅ API密钥配置
- ✅ 同步任务调度
- ✅ 同步日志记录

### 技术架构
- **适配器模式**：可扩展的电商平台适配器架构
- **异步处理**：基于Celery的异步任务处理
- **错误重试**：自动重试机制保证数据一致性
- **日志追踪**：完整的同步日志记录

---

## 📊 数据采集管理 🆕

系统提供统一的电商数据采集管理功能，支持多种数据采集场景。

### 核心功能
- ✅ **统一管理界面**：Admin界面显示为"采集"
- ✅ **任务配置**：灵活的采集任务配置
- ✅ **调度管理**：定时任务调度
- ✅ **数据同步**：与电商平台数据同步
- ✅ **日志监控**：采集过程日志记录

### 管理界面
- Django Admin集成
- 简洁直观的操作界面
- 支持批量操作
- 实时状态监控

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
- **Hiprint引擎**：基于HiPrint的强大打印能力

### 技术实现
- 基于 HiPrint 打印引擎
- 支持自定义 CSS 样式
- 支持模板继承和复用
- 提供standalone版本和集成版本

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
- [采集模块实现](COLLECT_IMPLEMENTATION_COMPLETE.md) - 采集模块完整实现 🆕
- [实现总结](FINAL_IMPLEMENTATION_SUMMARY.md) - 最终实现总结 🆕
- [优化总结](OPTIMIZATION_SUMMARY.md) - 优化总结 🆕

### 官方文档
- [Django 官方文档](https://docs.djangoproject.com/)
- [Django REST Framework 文档](https://www.django-rest-framework.org/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
- [Alpine.js 文档](https://alpinejs.dev/)
- [drf-spectacular 文档](https://drf-spectacular.readthedocs.io/)

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
- **2026-01-31**: 统一表单输入框聚焦样式，修复借用单供应商下拉菜单 🎨
  - 为22个输入框添加主题色聚焦边框
  - 修复purchase模块供应商查询，添加code字段
  - 统一采购、销售、财务模块表单交互体验
  - 更新collect模块verbose_name为"采集"

- **2026-01-30**: 完成电商平台适配器和同步服务开发 🛒
  - 实现6大电商平台适配器（淘宝、京东、拼多多、抖音、快手、1688）
  - 完成Listing管理服务
  - 实现订单和库存同步功能
  - 添加平台管理和适配器配置

- **2026-01-25**: 统一表单元素焦点样式，配置 @tailwindcss/forms 插件
  - 移除蓝色 box-shadow
  - 配置表单插件优化样式

- **2026-01-24**: 清理项目代码，归档临时脚本，添加技术文档

- **2026-01-18**: 更新 Claude AI 配置文档，优化开发指南

- **2026-01-07**: 添加技术指南文档，完善项目文档体系

---

## 📊 项目规模

| 类别 | 数量 |
|------|------|
| **核心业务代码** | 74,190 行 Python 代码 |
| **模型代码** | 8,000+ 行数据模型 |
| **业务模块** | 14 个独立应用 |
| **电商平台** | 6 大主流平台对接 |
| **数据模型** | 100+ 个数据表 |
| **模板文件** | 241 个 HTML 模板 |
| **测试文件** | 30+ 个测试文件 |
| **API 接口** | 400+ 个 REST 接口 |

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

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

请确保：
- 代码符合项目规范
- 添加必要的测试
- 更新相关文档
- 提交信息清晰明确

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

感谢所有为本项目做出贡献的开发者！

---

**本 README 持续更新中，如有问题请及时反馈。**
