# 变更日志 (CHANGELOG)

本文档记录Django ERP项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### 待发布

---

## [1.0.0] - 2026-02-08

### 新增 (Added)

#### 核心功能
- ✨ 完整的ERP业务流程
  - 销售管理：报价、订单、发货、退货
  - 采购管理：询价、订单、收货、退货
  - 库存管理：仓库、库存、盘点、调拨
  - 财务管理：应收应付、费用、凭证、报表
  - 客户/供应商管理：完整的CRUD功能
  - 用户/权限管理：RBAC权限控制

#### 高级功能
- ✨ **借用管理系统**
  - 采购借用：样品借用、转采购订单
  - 销售借用：客户借用、转销售订单
  - 借用仓库存管理
  - 部分归还+部分转订单

- ✨ **预付款管理**
  - 客户预付款：充值、核销、合并
  - 供应商预付款：支付、核销、合并
  - 自动核销和智能匹配

- ✨ **AI智能助手**
  - 集成DeepSeek大模型
  - 支持多渠道接入（微信、钉钉）
  - ERP工具调用（查询、创建、更新）
  - 对话历史管理

- ✨ **页面自动刷新**
  - 5种刷新模式（仪表盘、列表、详情、表单、报表）
  - 智能刷新（页面可见性、用户活动检测）
  - 保留滚动位置

- ✨ **电商同步**
  - 支持Jumia、Shopee、TikTok、Temu等平台
  - 产品同步、订单同步、价格同步
  - 物流跟踪、自动补货提醒

#### 技术特性
- ✨ **测试体系**
  - 18个E2E测试（100%通过）
  - 844个单元测试方法
  - 测试覆盖率：核心业务100%

- ✨ **代码质量工具**
  - Black、flake8、isort、mypy
  - Pre-commit hooks
  - CI/CD自动化流水线

- ✨ **运维工具**
  - 一键部署脚本
  - 系统健康检查（45+检查项）
  - 数据库自动备份
  - Locust性能测试

- ✨ **监控和日志**
  - Sentry错误监控
  - 结构化日志系统
  - 日志分级和轮转

### 改进 (Changed)

#### 系统架构
- 🔄 将所有应用从根目录迁移至`apps/`目录
- 🔄 统一使用`from xxx.models import`导入路径
- 🔄 优化项目结构和代码组织

#### 业务流程
- 🔄 优化采购订单收货流程（支持分批收货）
- 🔄 优化销售订单发货流程（支持分批发货）
- 🔄 优化退货流程的库存回退机制
- 🔄 改进应收应付核销逻辑

#### 性能优化
- ⚡ 数据库连接池（10分钟连接重用）
- ⚡ Redis缓存（5分钟缓存超时）
- ⚡ 查询优化（减少N+1查询）
- ⚡ 静态文件CDN缓存

### 修复 (Fixed)

#### Bug修复
- 🐛 修复InventoryStock模型缺失字段
- 🐛 修复销售退货明细字段错误
- 🐛 修复应收应付模型字段不一致
- 🐛 修复发货模型字段（actual_date）
- 🐛 修复会计科目模型字段问题

#### 数据一致性
- 🐛 修复借用单数量追踪逻辑
- 🐛 修复预付款核销计算错误
- 🐛 修复会计科目余额计算规则

### 安全 (Security)

- 🔒 启用HTTPS/HSTS（生产环境）
- 🔒 配置CSP和XSS防护
- 🔒 启用CSRF防护
- 🔒 配置会话安全（HttpOnly、Secure、SameSite）
- 🔒 环境变量敏感信息保护
- 🔒 API Key加密存储

### 文档 (Documentation)

- 📖 **新增文档**（40+页）
  - README.md - 项目主文档
  - QUICK_START_GUIDE.md - 快速启动指南
  - DEPLOYMENT_CHECKLIST.md - 部署检查清单
  - OPERATIONS_GUIDE.md - 运维工具指南
  - PROJECT_STATUS.md - 项目状态总览
  - E2E_TEST_SUMMARY_FINAL.md - E2E测试总结
  - PRODUCTION_READINESS_REPORT.md - 上线准备报告
  - FINAL_IMPLEMENTATION_REPORT.md - 实施报告
  - SESSION_SUMMARY.md - 工作总结
  - CHANGELOG.md - 变更日志

- 📖 **模块文档**（15个模块CLAUDE.md）
  - 每个应用模块都有详细的文档说明

### 工具 (Tooling)

#### 新增脚本
- ✨ `scripts/deploy.sh` - 一键部署脚本
- ✨ `scripts/health_check.sh` - 系统健康检查
- ✨ `scripts/backup.sh` - 数据库备份脚本（增强）
- ✨ `scripts/crontab.example` - 定时任务配置示例
- ✨ `locustfile.py` - Locust性能测试脚本

#### 配置文件
- ✨ `.pre-commit-config.yaml` - Pre-commit hooks配置
- ✨ `.github/workflows/ci.yml` - GitHub Actions CI/CD
- ✨ `pytest.ini` - Pytest配置

### 依赖 (Dependencies)

#### 新增依赖
- ✨ sentry-sdk==1.38.0 - 错误监控
- ✨ black==23.12.1 - 代码格式化
- ✨ flake8==7.0.0 - 代码检查
- ✨ isort==5.13.2 - import排序
- ✨ mypy==1.8.0 - 类型检查
- ✨ pre-commit==3.6.0 - Git hooks
- ✨ locust - 性能测试

---

## [0.9.0] - 2025-11-15

### 新增
- ✨ AI助手基础功能
- ✨ 电商同步基础框架
- ✨ 商业智能模块
- ✨ 物流管理模块

### 改进
- 🔄 优化用户界面
- 🔄 改进响应速度

---

## [0.5.0] - 2025-10-20

### 新增
- ✨ 核心ERP功能
  - 销售管理
  - 采购管理
  - 库存管理
  - 财务管理
  - 客户/供应商管理
- ✨ 用户和权限管理
- ✨ 部门管理

---

## 版本命名规则

- **主版本号**：不兼容的API变更
- **次版本号**：向下兼容的功能新增
- **修订号**：向下兼容的问题修复

---

## 变更类型

- **新增 (Added)**: 新功能
- **改进 (Changed)**: 现有功能的变更
- **弃用 (Deprecated)**: 即将移除的功能
- **移除 (Removed)**: 已移除的功能
- **修复 (Fixed)**: Bug修复
- **安全 (Security)**: 安全相关的修复

---

## 贡献指南

如果您想贡献代码，请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 支持

- 📖 [文档](QUICK_START_GUIDE.md)
- 🐛 [问题反馈](https://github.com/your-org/django-erp/issues)
- 📧 [邮件](support@example.com)
