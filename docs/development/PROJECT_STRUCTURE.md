# Django ERP 项目结构

> 最后更新：2026-02-03
> 重构方案：方案 C（深度重构）

## 📊 根目录概览

```
django_erp/
├── apps/                    # 所有 Django 应用（16个）
├── common/                  # 共享代码中心
├── config/                  # 配置文件
├── django_erp/              # Django 项目配置
├── docs/                    # 项目文档
├── scripts/                 # 所有脚本
├── static/                  # 静态资源（重组）
├── staticfiles/             # 收集的静态文件
├── templates/               # 模板文件（重组）
├── .backups/                # 统一备份目录
├── fixtures/                # 测试数据
├── logs/                    # 日志文件
├── media/                   # 用户上传文件
├── start.sh                 # 启动快捷方式
├── manage.py                # Django 管理脚本
├── requirements.txt         # Python 依赖
├── package.json             # Node.js 依赖
├── README.md                # 项目说明
├── MIGRATION_GUIDE.md       # 迁移指南
└── PROJECT_STRUCTURE.md     # 本文档
```

## 📁 详细目录结构

### apps/ - Django 应用

```
apps/
├── ai_assistant/            # AI 智能助手
├── authentication/          # 认证授权
├── bi/                      # 商业智能
├── collect/                 # 采集管理
├── core/                    # 核心基础设施
├── customers/               # 客户管理
├── departments/             # 部门管理
├── ecomm_sync/              # 电商同步
├── factories.py             # 测试工厂
├── finance/                 # 财务管理
├── inventory/               # 库存管理
├── logistics/               # 物流管理
├── products/                # 产品管理
├── purchase/                # 采购管理
├── sales/                   # 销售管理
├── suppliers/               # 供应商管理
└── users/                   # 用户管理
```

### common/ - 共享代码

```
common/
├── utils/                   # 通用工具函数
│   ├── __init__.py
│   ├── cache.py
│   ├── code_generator.py
│   ├── database_helper.py
│   ├── document_number.py
│   ├── encryption.py
│   ├── logger.py
│   ├── managers/
│   ├── permissions.py
│   └── rbac.py
├── mixins/                  # Django 模型 mixins
├── decorators/              # 装饰器
├── exceptions/              # 自定义异常
├── constants/               # 常量定义
├── middleware/              # 中间件
└── validators/              # 验证器
```

### config/ - 配置文件

```
config/
├── environment/             # 环境配置
│   ├── .env
│   └── .env.example
├── docker/                  # Docker 配置
├── nginx/                   # Nginx 配置
└── gunicorn/                # Gunicorn 配置
```

### static/ - 静态资源

```
static/
├── css/
│   ├── components/          # 组件样式
│   │   ├── input.css
│   │   └── output.css
│   ├── layouts/             # 布局样式
│   │   └── admin_overrides.css
│   └── modules/             # 模块样式（预留）
└── js/
    ├── components/          # 组件脚本
    │   ├── hiprint-provider.js
    │   └── theme.js
    ├── layouts/             # 布局脚本
    │   └── logo-responsive.js
    ├── libs/                # 第三方库
    │   ├── jquery-3.6.0.min.js
    │   ├── alpinejs.min.js
    │   └── ...
    └── modules/             # 模块脚本（预留）
```

### templates/ - 模板文件

```
templates/
├── layouts/                 # 布局模板
│   ├── base.html
│   ├── dashboard.html
│   └── index.html
├── components/              # 可重用组件（预留）
└── modules/                 # 模块模板
    ├── ai_assistant/
    ├── collect/
    ├── core/
    ├── customers/
    ├── departments/
    ├── ecomm_sync/
    ├── finance/
    ├── inventory/
    ├── listing/
    ├── products/
    ├── purchase/
    ├── sales/
    ├── suppliers/
    └── users/
```

### scripts/ - 脚本文件

```
scripts/
├── start_server.sh          # 启动脚本
├── backup.sh                # 备份脚本
├── restore.sh               # 恢复脚本
├── quick_start.sh           # 快速启动
├── check_fontawesome_coverage.py
├── check_svg_attributes.py
├── check_url_consistency.py
├── fix_payment_sequence.py
├── unify_document_prefixes.py
└── reports/                 # 报告目录
```

### .backups/ - 备份目录

```
.backups/
├── database/                # 数据库备份
├── legacy/                  # 来自旧 backups/ 目录
│   └── db_backup_20260130_193934.sqlite3
├── 20260203_git_cleanup_before/
├── pre_refactor_20260203/   # 迁移前备份
│   ├── git_status.txt
│   ├── git_recent_commits.txt
│   ├── git_branches.txt
│   ├── settings.py.backup
│   ├── .env.backup
│   └── directory_structure.txt
└── cleanup_report_20260203.md
```

## 🎯 Django 配置更新

### sys.path 更新

`django_erp/settings.py` 已添加：

```python
# 添加 apps/ 到 Python 路径
APPS_DIR = BASE_DIR / 'apps'
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

# 添加 common/ 到 Python 路径
COMMON_DIR = BASE_DIR / 'common'
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))
```

### 导入路径变更

```python
# 旧路径
from core.utils import database_helper
from ai_assistant.utils import cache
from utils import rbac

# 新路径
from common.utils import database_helper
from common.utils import cache
from common.utils import rbac
```

## 📈 重构成果

| 指标 | 重构前 | 重构后 | 改进 |
|------|--------|--------|------|
| 根目录项数 | 48 | 32 | ⬇️ 33% |
| Django 应用位置 | 根目录（分散） | apps/（集中） | ✅ |
| 共享代码目录 | 3 个分散 | 1 个统一（common/） | ✅ |
| 备份目录 | 2 个冗余 | 1 个统一（.backups/） | ✅ |
| 脚本文件 | 分散 | 集中在 scripts/ | ✅ |
| 配置文件 | 分散 | 集中在 config/ | ✅ |

## ✅ 验证状态

- [x] Django 配置检查通过
- [x] 数据库迁移成功
- [x] 静态文件收集完成
- [x] 部署检查通过
- [x] 备份已创建

## 📚 相关文档

- [README.md](README.md) - 项目概述
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 详细迁移指南
- [docs/index.md](docs/index.md) - 文档索引

---

**文档生成时间**: 2026-02-03
**重构方案**: 方案 C（深度重构）
**状态**: ✅ 已完成并验证
