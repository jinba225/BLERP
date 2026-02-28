[根目录](../../../CLAUDE.md) > [django_erp](../../) > [apps](../) > **core**

# Core模块文档

## 模块职责

Core模块是整个ERP系统的核心基础模块，提供所有其他模块共用的基础功能和抽象模型。主要职责包括：

- **基础模型抽象**: 提供所有业务模型的基类（时间戳、软删除、创建人等）
- **审计日志系统**: 记录用户操作和数据变更历史
- **附件管理**: 统一的文件上传和管理功能
- **通知系统**: 系统内消息通知机制
- **系统配置**: 全局系统参数和配置管理
- **单据号生成**: 统一的单据编号生成规则
- **公司信息**: 企业基础信息管理

## 入口与启动

### 核心模型
- **文件**: `models.py`
- **关键类**:
  - `BaseModel`: 所有业务模型的基类
  - `TimeStampedModel`: 时间戳抽象模型
  - `SoftDeleteModel`: 软删除抽象模型

### 中间件
- **文件**: `middleware.py`
- **功能**: 时区处理中间件

### 管理命令
- **目录**: `management/commands/`
- **命令**: `migrate_legacy_data.py` - Legacy数据迁移

## 对外接口

### REST API
- **基础路由**: `/api/core/`
- **ViewSets**: `viewsets.py` 提供核心功能的API接口
- **序列化器**: `serializers.py` 定义API数据结构

### 前端视图
- **登录页面**: `login_view` - 用户登录
- **登出功能**: `logout_view` - 用户登出
- **仪表板**: `dashboard_view` - 系统主页

### URL路由
```python
# 主要路由
path('login/', core_views.login_view, name='login')
path('logout/', core_views.logout_view, name='logout')
path('', core_views.dashboard_view, name='dashboard')
```

## 关键依赖与配置

### 内部依赖
- Django核心框架
- Django REST Framework
- 用户模型 (`settings.AUTH_USER_MODEL`)

### 外部依赖
```python
# 无特殊外部依赖，使用Django内置功能
```

### 配置项
在 `settings.py` 中的相关配置：
```python
AUTH_USER_MODEL = 'users.User'  # 自定义用户模型
MIDDLEWARE = [
    'apps.core.middleware.TimezoneMiddleware',  # 时区中间件
]
```

## 数据模型

### 核心抽象模型

#### TimeStampedModel
```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.ForeignKey(User, ...)
    updated_by = models.ForeignKey(User, ...)
```

#### SoftDeleteModel
```python
class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField('是否删除', default=False)
    deleted_at = models.DateTimeField('删除时间', null=True, blank=True)
    deleted_by = models.ForeignKey(User, ...)
```

#### BaseModel
```python
class BaseModel(TimeStampedModel, SoftDeleteModel):
    # 组合了时间戳和软删除功能的完整基类
```

### 业务模型

#### Company (公司信息)
- 公司基础信息：名称、代码、法人代表
- 联系方式：地址、电话、传真、邮箱
- 企业标识：Logo、网站、描述

#### SystemConfig (系统配置)
- 配置项管理：键值对形式存储
- 配置分类：系统、业务、界面、安全
- 动态配置：支持运行时修改

#### Attachment (附件管理)
- 文件存储：支持多种文件类型
- 通用关联：可关联到任意模型实例
- 元数据管理：文件大小、类型、描述

#### AuditLog (审计日志)
- 操作记录：创建、更新、删除、查看等
- 用户追踪：记录操作用户和IP地址
- 变更详情：JSON格式存储具体变更内容

#### DocumentNumberSequence (单据号序列)
- 编号规则：支持前缀+日期+序号格式
- 序号管理：按日期自动重置
- 并发安全：保证编号唯一性

#### Notification (通知系统)
- 消息分类：信息、成功、警告、错误
- 业务分类：销售、采购、库存、财务等
- 状态管理：已读/未读状态

## 测试与质量

### 测试文件位置
```bash
apps/core/tests/
├── __init__.py
└── test_models.py  # 核心模型测试
```

### 测试覆盖情况
✅ **测试完成度: 100%** (34/34 测试通过)

#### Company模型测试 (5个测试)
- ✅ `test_company_creation` - 公司创建
- ✅ `test_company_unique_code` - 公司代码唯一性
- ✅ `test_company_soft_delete` - 软删除功能
- ✅ `test_company_hard_delete` - 硬删除功能
- ✅ `test_company_str_representation` - 字符串表示

#### SystemConfig模型测试 (4个测试)
- ✅ `test_config_creation` - 配置创建
- ✅ `test_config_unique_key` - 配置键唯一性
- ✅ `test_config_types` - 所有配置类型验证
- ✅ `test_config_str_representation` - 字符串表示

#### Attachment模型测试 (7个测试)
- ✅ `test_attachment_creation` - 附件创建
- ✅ `test_attachment_types` - 所有附件类型验证
- ✅ `test_file_size_display_bytes` - 文件大小显示(字节)
- ✅ `test_file_size_display_kb` - 文件大小显示(KB)
- ✅ `test_file_size_display_mb` - 文件大小显示(MB)
- ✅ `test_file_size_display_gb` - 文件大小显示(GB)
- ✅ `test_attachment_str_representation` - 字符串表示

#### AuditLog模型测试 (5个测试)
- ✅ `test_audit_log_creation` - 审计日志创建
- ✅ `test_audit_log_action_types` - 所有操作类型验证
- ✅ `test_audit_log_changes_json` - JSON变更记录
- ✅ `test_audit_log_ordering` - 按时间倒序排列
- ✅ `test_audit_log_str_representation` - 字符串表示

#### DocumentNumberSequence模型测试 (5个测试)
- ✅ `test_sequence_creation` - 序列创建
- ✅ `test_sequence_unique_together` - 唯一性约束
- ✅ `test_different_dates_same_prefix` - 相同前缀不同日期
- ✅ `test_different_prefixes_same_date` - 相同日期不同前缀
- ✅ `test_sequence_str_representation` - 字符串表示

#### Notification模型测试 (8个测试)
- ✅ `test_notification_creation` - 通知创建
- ✅ `test_notification_types` - 所有通知类型验证
- ✅ `test_notification_categories` - 所有业务分类验证
- ✅ `test_mark_as_read` - 标记已读功能
- ✅ `test_mark_as_read_idempotent` - 重复标记已读
- ✅ `test_create_notification_classmethod` - 类方法创建通知
- ✅ `test_notification_ordering` - 按时间倒序排列
- ✅ `test_notification_str_representation` - 字符串表示

### 测试要点
- **基础模型**: 时间戳、软删除、创建人等基础功能
- **唯一性约束**: 验证各种唯一性规则
- **字段验证**: 测试所有字段类型和选项
- **属性方法**: 测试计算属性和业务方法
- **排序规则**: 验证默认排序逻辑
- **JSON字段**: 测试JSON数据的存储和读取

## 常见问题 (FAQ)

### Q: 如何为新模型添加审计日志？
A: 继承 `BaseModel`，然后在视图或信号中调用审计日志创建方法。

### Q: 如何生成标准的单据编号？
A: 使用 `DocumentNumberSequence` 模型，通过 `DocumentNumberGenerator` 工具类生成。

### Q: 如何添加系统配置项？
A: 在 `SystemConfig` 模型中添加新记录，��通过Admin后台管理。

### Q: 附件如何关联到其他模型？
A: 使用Generic Foreign Key，通过 `content_type` 和 `object_id` 字段关联。

## 相关文件清单

### 核心文件
- `__init__.py` - 包初始化
- `apps.py` - Django应用配置
- `models.py` - 数据模型定义 (339行)
- `views.py` - 视图逻辑
- `urls.py` - URL路由配置
- `middleware.py` - 自定义中间件

### API相关
- `serializers.py` - REST API序列化器
- `viewsets.py` - REST API视图集

### 管理功能
- `management/commands/migrate_legacy_data.py` - 数据迁移命令

### 工具模块
- `utils/__init__.py` - 工具函数包
- `tasks.py` - Celery异步任务

### 数据库
- `migrations/` - 数据库迁移文件
  - `0001_initial.py` - 初始迁移
  - `0002_initial.py` - 补充迁移

## 变更记录 (Changelog)

### 2026-01-14 (单据号前缀统一)
- **前缀规范化**: 统一所有入库单据使用 `IN` 前缀，所有出库单据使用 `OUT` 前缀
- **入库单据** (IN前缀):
  - receipt (采购收货单) - 已经是IN
  - stock_in (入库单) - 已经是IN
  - sales_return (销售退货) - SR → IN
  - material_return (退料单) - MTR → IN
- **出库单据** (OUT前缀):
  - delivery (销售发货单) - 已经是OUT
  - stock_out (出库单) - 已经是OUT
  - purchase_return (采购退货) - ROUT → OUT
  - material_requisition (领料单) - MR → OUT
- **单据区分**: 通过 `transaction_type` 或 `reference_type` 字段区分具体的单据类型
- **配置更新**: 更新了4个SystemConfig配置项
- **文档更新**: 更新 `document_number.py` 中的前缀说明，按业务流程分类展示
- **脚本工具**: 创建 `scripts/unify_document_prefixes.py` 数据迁移脚本

### 2025-11-13
- **测试完成**: 添加34个单元测试，覆盖6个核心模型
- **测试通过率**: 100% (34/34)
- **测试内容**: Company、SystemConfig、Attachment、AuditLog、DocumentNumberSequence、Notification

### 2025-11-08 23:26:47
- **文档初始化**: 创建Core模块完整文档
- **模型分析**: 详细分析了8个核心模型的职责
- **API接口**: 梳理了对外提供的API和视图接口
- **测试缺口**: 识别出缺少完整的测试覆盖
