[根目录](../../../CLAUDE.md) > [django_erp](../../) > [apps](../) > **users**

# Users模块文档

## 模块职责

Users模块负责用户管理和员工信息管理，基于Django的自定义用户模型。主要职责包括：
- **用户认证**: 扩展Django默认User模型，支持邮箱登录
- **员工信息**: 员工档案、部门关系、职位信息管理  
- **组织架构**: 员工层级关系和汇报结构
- **个人资料**: 头像、个人信息、联系方式管理

## 核心模型

### User (用户模型)
```python
class User(AbstractUser):
    email = EmailField('邮箱', unique=True)                    # 邮箱登录
    phone = CharField('手机号', max_length=20, blank=True)      # 手机号
    avatar = ImageField('头像', upload_to='avatars/')          # 头像
    employee_id = CharField('员工编号', max_length=50, unique=True) # 员工编号
    department = ForeignKey('departments.Department')         # 所属部门
    position = CharField('职位', max_length=100)               # 职位
    manager = ForeignKey('self', on_delete=SET_NULL)          # 直属上级
    hire_date = DateField('入职日期')                          # 入职日期
```

## 主要功能
- ✅ 自定义用户模型，支持邮箱作为用户名
- ✅ 员工基础信息管理
- ✅ 部门和职位关联
- ✅ 用户头像上传
- ✅ 层级管理关系

## 文件清单
- `models.py` - 自定义User模型 (约80行)
- `apps.py` - 应用配置
- `urls.py` - URL路由
- `serializers.py` - API序列化器
- `viewsets.py` - API视图集
- `migrations/` - 数据库迁移文件

## 集成关系
- **Authentication**: 提供用户认证基础
- **Departments**: 用户部门关联
- **Core**: 审计日志的用户关联
- **Sales**: 销售代表分配

## 测试与质量

### 测试文件位置
```bash
apps/users/tests/
├── __init__.py
└── test_models.py  # 用户和权限模型测试
```

### 测试覆盖情况
✅ **测试完成度: 100%** (32/32 测试通过)

#### User模型测试 (9个测试)
- ✅ `test_user_creation` - 用户创建
- ✅ `test_user_email_unique` - 邮箱唯一性
- ✅ `test_user_employee_id_unique` - 员工编号唯一性
- ✅ `test_user_with_department` - 部门关联
- ✅ `test_user_manager_relationship` - 上级关系
- ✅ `test_user_get_full_name` - 获取全名
- ✅ `test_user_display_name` - 显示名称属性
- ✅ `test_user_str_representation` - 字符串表示
- ✅ `test_user_ordering` - 排序规则

#### Role模型测试 (5个测试)
- ✅ `test_role_creation` - 角色创建
- ✅ `test_role_unique_name` - 角色名称唯一性
- ✅ `test_role_unique_code` - 角色代码唯一性
- ✅ `test_role_ordering` - 排序规则
- ✅ `test_role_str_representation` - 字符串表示

#### UserRole模型测试 (4个测试)
- ✅ `test_user_role_creation` - 用户角色关联
- ✅ `test_user_role_unique_together` - 唯一性约束
- ✅ `test_user_role_ordering` - 排序规则
- ✅ `test_user_role_str_representation` - 字符串表示

#### Permission模型测试 (4个测试)
- ✅ `test_permission_creation` - 权限创建
- ✅ `test_permission_unique_together` - 唯一性约束
- ✅ `test_permission_ordering` - 排序规则
- ✅ `test_permission_str_representation` - 字符串表示

#### UserProfile模型测试 (4个测试)
- ✅ `test_profile_creation` - 用户档案创建
- ✅ `test_profile_one_to_one` - 一对一关系
- ✅ `test_profile_auto_created` - 自动创建档案
- ✅ `test_profile_str_representation` - 字符串表示

#### LoginLog模型测试 (6个测试)
- ✅ `test_login_log_creation` - 登录日志创建
- ✅ `test_login_log_ordering` - 按时间倒序
- ✅ `test_login_status_choices` - 登录状态选项
- ✅ `test_login_log_session_duration` - 会话时长计算
- ✅ `test_login_log_active_session` - 活跃会话判断
- ✅ `test_login_log_str_representation` - 字符串表示

### 测试要点
- **自定义用户模型**: 邮箱登录、员工信息、层级关系
- **角色权限系统**: 角色定义、权限分配、用户角色关联
- **用户档案**: OneToOne关系、自动创建机制
- **登录日志**: 会话管理、时长计算、状态追踪
- **唯一性约束**: 邮箱、员工编号、角色名称等
- **排序规则**: 各模型的默认排序

## 变更记录
### 2025-11-13
- **测试完成**: 添加32个单元测试，覆盖6个核心模型
- **测试通过率**: 100% (32/32)
- **测试内容**: User、Role、UserRole、Permission、UserProfile、LoginLog

### 2025-11-08 23:26:47
- 文档初始化，识别核心用户管理功能