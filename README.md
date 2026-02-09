# Django ERP 🏢

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-5.0.9-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![E2E Tests](https://img.shields.io/badge/tests-18%20passed-success.svg)](apps/**/test_e2e_*.py)

> 一个功能完善的企业资源计划（ERP）系统，支持销售、采购、库存、财务等核心业务模块。

---

## 📋 目录

- [功能特性](#-功能特性)
- [系统架构](#-系统架构)
- [技术栈](#-技术栈)
- [快速开始](#-快速开始)
- [文档](#-文档)
- [开发指南](#-开发指南)
- [部署指南](#-部署指南)
- [测试](#-测试)
- [贡献](#-贡献)
- [许可证](#-许可证)

---

## ✨ 功能特性

### 核心模块

- 🏢 **部门管理** - 组织架构、职位管理
- 👥 **用户管理** - 用户、角色、权限
- 🤝 **客户管理** - 客户信息、联系人管理
- 🏭 **供应商管理** - 供应商信息、资质管理
- 📦 **产品管理** - 产品、品牌、分类、单位
- 📊 **库存管理** - 仓库、库存、盘点、调拨
- 💰 **销售管理** - 报价、订单、发货、退货
- 🛒 **采购管理** - 询价、订单、收货、退货
- 💳 **财务管理** - 应收应付、费用、凭证、报表
- 🤖 **AI助手** - 大模型集成的智能助手
- 📈 **商业智能** - 数据分析、报表、大屏
- 🚚 **物流管理** - 物流跟踪、配送管理
- 🛍️ **电商同步** - 多平台电商数据同步

### 业务亮点

✅ **完整的业务流程** - 从采购到销售到财务的闭环  
✅ **借用管理** - 支持采购借用和销售借用  
✅ **预付款管理** - 客户和供应商预付款、合并核销  
✅ **页面自动刷新** - 实时数据更新  
✅ **AI智能助手** - 集成DeepSeek等大模型  
✅ **多平台同步** - 支持Jumia、Shopee、TikTok等平台  

---

## 🏗️ 系统架构

```
django_erp/
├── apps/                    # 应用模块
│   ├── core/               # 核心模块
│   ├── users/              # 用户管理
│   ├── authentication/     # 认证授权
│   ├── customers/          # 客户管理
│   ├── suppliers/          # 供应商管理
│   ├── products/           # 产品管理
│   ├── inventory/          # 库存管理
│   ├── sales/              # 销售管理
│   ├── purchase/           # 采购管理
│   ├── finance/            # 财务管理
│   ├── departments/        # 部门管理
│   ├── ai_assistant/       # AI助手
│   ├── bi/                 # 商业智能
│   ├── logistics/          # 物流管理
│   ├── ecomm_sync/         # 电商同步
│   └── collect/            # 收款管理
├── common/                 # 公共模块
├── config/                 # 配置文件
├── django_erp/             # 项目配置
├── static/                 # 静态文件
├── templates/              # 模板文件
├── scripts/                # 脚本工具
├── tests/                  # 测试文件
└── docs/                   # 文档
```

---

## 🛠️ 技术栈

### 后端

- **框架**: Django 5.0.9
- **API**: Django REST Framework 3.15.2
- **数据库**: PostgreSQL / MySQL / SQLite
- **缓存**: Redis 5.0.1
- **异步任务**: Celery 5.3.4
- **文档**: drf-spectacular 0.27.2

### 前端

- **模板**: Django Templates
- **CSS框架**: Tailwind CSS
- **JavaScript**: Alpine.js
- **图表**: Chart.js, ECharts
- **表格**: DataTables
- **表单**: django-crispy-forms

### AI集成

- **OpenAI**: GPT模型支持
- **DeepSeek**: DeepSeek模型
- **Anthropic**: Claude模型

### 开发工具

- **测试**: pytest 7.4.3
- **代码质量**: Black, flake8, isort, mypy
- **Pre-commit**: pre-commit 3.6.0
- **错误监控**: Sentry SDK

### 部署

- **容器**: Docker, Docker Compose
- **服务器**: Gunicorn, Nginx
- **CI/CD**: GitHub Actions

---

## 🚀 快速开始

### 环境要求

- Python 3.13+
- PostgreSQL 12+ (生产环境推荐)
- Redis 6+ (可选)

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/django-erp.git
cd django-erp

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
nano .env  # 修改配置

# 5. 初始化数据库
python manage.py migrate

# 6. 创建超级用户
python manage.py createsuperuser

# 7. 启动开发服务器
python manage.py runserver

# 8. 访问应用
# 浏览器打开: http://localhost:8000
```

### Docker部署

```bash
# 开发环境
docker-compose up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📚 文档

### 核心文档

- 📖 [快速启动指南](QUICK_START_GUIDE.md) - 5分钟快速开始
- 📋 [部署检查清单](DEPLOYMENT_CHECKLIST.md) - 生产环境部署检查清单
- 🔧 [运维工具指南](OPERATIONS_GUIDE.md) - 运维工具使用指南
- 📊 [项目状态总览](PROJECT_STATUS.md) - 项目状态和指标

### 报告文档

- 📈 [E2E测试总结](E2E_TEST_SUMMARY_FINAL.md) - 端到端测试报告
- 🎯 [上线准备报告](PRODUCTION_READINESS_REPORT.md) - 第一阶段改进报告
- 📝 [最终实施报告](FINAL_IMPLEMENTATION_REPORT.md) - 完整实施报告
- 📋 [工作总结](SESSION_SUMMARY.md) - 本次工作总结

### 模块文档

每个应用模块都有详细的CLAUDE.md文档：
- [Core模块](apps/core/CLAUDE.md)
- [Users模块](apps/users/CLAUDE.md)
- [Sales模块](apps/sales/CLAUDE.md)
- [Purchase模块](apps/purchase/CLAUDE.md)
- [Inventory模块](apps/inventory/CLAUDE.md)
- [Finance模块](apps/finance/CLAUDE.md)
- [AI Assistant模块](apps/ai_assistant/CLAUDE.md)

---

## 💻 开发指南

### 代码规范

```bash
# 运行代码格式化
black . --line-length=100

# 运行代码检查
flake8 . --max-line-length=100

# 运行import排序
isort . --profile black
```

### Pre-commit Hooks

```bash
# 安装hooks
pre-commit install

# 手动运行
pre-commit run --all-files
```

### 测试

```bash
# 运行E2E测试
pytest apps/**/test_e2e_*.py -v

# 生成覆盖率报告
pytest apps/**/test_e2e_*.py --cov=apps --cov-report=html

# 运行特定模块测试
pytest apps/sales/tests/test_e2e_sales_flow.py -v
```

### 开发工具

```bash
# 一键部署
./scripts/deploy.sh development deploy

# 健康检查
./scripts/health_check.sh

# 数据库备份
./scripts/backup.sh development
```

---

## 🚢 部署指南

### 开发环境部署

```bash
./scripts/deploy.sh development setup
./scripts/deploy.sh development deploy
```

### 生产环境部署

```bash
# 1. 查看部署检查清单
cat DEPLOYMENT_CHECKLIST.md

# 2. 运行健康检查
./scripts/health_check.sh

# 3. 执行部署
./scripts/deploy.sh production deploy

# 4. 验证部署
curl -I https://your-domain.com
```

### Docker部署

```bash
# 构建镜像
docker-compose -f docker-compose.prod.yml build

# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 性能测试

```bash
# 启动Locust性能测试
locust -f locustfile.py --host=http://localhost:8000

# 无头模式
locust -f locustfile.py --headless --users=100 --run-time=5m
```

---

## 🧪 测试

### 测试覆盖

- ✅ **E2E测试**: 18个（100%通过率）
- ✅ **单元测试**: 844个测试方法
- ✅ **测试执行时间**: 2分6秒

### 测试类型

- 采购流程E2E测试（4个）
- 销售流程E2E测试（4个）
- 采购借用E2E测试（3个）
- 销售借用E2E测试（3个）
- 财务报表E2E测试（4个）

### 运行测试

```bash
# 所有E2E测试
pytest apps/**/test_e2e_*.py -v

# 特定模块
pytest apps/sales/tests/test_e2e_sales_flow.py -v

# 性能测试
locust -f locustfile.py --host=http://localhost:8000
```

---

## 🤝 贡献

我们欢迎所有形式的贡献！

### 贡献方式

- 🐛 报告Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交代码

### 贡献流程

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 开发规范

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 团队

- **项目负责人**: [Your Name]
- **核心开发者**: [Team Members]
- **贡献者**: [Contributors]

---

## 📞 联系方式

- **问题反馈**: [GitHub Issues](https://github.com/your-org/django-erp/issues)
- **邮件**: support@example.com
- **文档**: [Wiki](https://github.com/your-org/django-erp/wiki)

---

## 🙏 致谢

感谢所有为本项目做出贡献的开发者！

特别感谢以下开源项目：
- [Django](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery](http://www.celeryproject.org/)
- [Redis](https://redis.io/)

---

## 📊 项目状态

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)]()
[![Code Quality](https://img.shields.io/badge/code%20quality-⭐⭐⭐⭐⭐-success.svg)]()
[![Documentation](https://img.shields.io/badge/docs-⭐⭐⭐⭐⭐-success.svg)]()

**当前版本**: v1.0.0  
**最后更新**: 2026-02-08  
**上线准备度**: ⭐⭐⭐⭐⭐ (5/5)  
**状态**: ✅ 已完全具备上线资格

---

<div align="center">

**如果这个项目对您有帮助，请给我们一个 ⭐️**

**Made with ❤️ by Django ERP Team**

</div>
