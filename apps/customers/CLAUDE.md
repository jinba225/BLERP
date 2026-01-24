[根目录](../../../CLAUDE.md) > [django_erp](../../) > [apps](../) > **customers**

# Customers模块文档

## 模块职责

Customers模块负责客户关系管理(CRM)功能，是销售业务的基础支撑模块。主要职责包括：

- **客户信息管理**: 企业客户、个人客户的基础信息维护
- **客户分类体系**: 多维度的客户分类和等级管理
- **联系人管理**: 客户多联系人信息和关系维护
- **客户档案**: 完整的客户档案和信用信息
- **销售支持**: 为销售流程提供客户数据支撑

## 入口与启动

### 模型文件
- **主文件**: `models.py`
- **核心模型**:
  - `Customer` - 客户主表
  - `CustomerCategory` - 客户分类
  - `CustomerContact` - 客户联系人

### 视图入口
- **文件**: `views.py`
- **功能**: Django模板视图和CRUD操作

### URL配置
- **路由文件**: `urls.py`
- **命名空间**: `customers`

## 对外接口

### 前端页面路由

#### 客户管理
```python
path('', views.customer_list, name='customer_list')                     # 客户列表
path('create/', views.customer_create, name='customer_create')          # 创建客户
path('<int:pk>/', views.customer_detail, name='customer_detail')        # 客户详情
path('<int:pk>/edit/', views.customer_update, name='customer_update')   # 编辑客户
path('<int:pk>/delete/', views.customer_delete, name='customer_delete') # 删除客户
```

#### 联系人管理
```python
path('contacts/', views.contact_list, name='contact_list')              # 联系人列表
path('contacts/create/', views.contact_create, name='contact_create')   # 创建联系人
path('contacts/<int:pk>/edit/', views.contact_update)                   # 编辑联系人
path('contacts/<int:pk>/delete/', views.contact_delete)                 # 删除联系人
```

### API接口
```python
path('api/', include(router.urls))  # REST API路由 (通过DRF Router)
```

## 关键依赖与配置

### 内部模块依赖
```python
from apps.core.models import BaseModel                    # 基础模型
from django.contrib.auth import get_user_model           # 用户模型
```

### 外部依赖
```python
from django.core.validators import RegexValidator         # 正则验证器
```

### 验证规则
```python
# 电话号码验证
phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$', 
    message='请输入有效的电话号码'
)
```

## 数据模型

### CustomerCategory (客户分类)
```python
class CustomerCategory(BaseModel):
    name = CharField('分类名称', max_length=100, unique=True)        # 分类名称
    code = CharField('分类代码', max_length=50, unique=True)         # 分类代码  
    description = TextField('分类描述', blank=True)                 # 描述
    discount_rate = DecimalField('默认折扣率', max_digits=5, decimal_places=2) # 折扣率
    is_active = BooleanField('是否启用', default=True)              # 状态
```

**用途**: 
- 客户分类管理（如：重要客户、普通客户、潜在客户）
- 差异化折扣政策
- 客户分析和报表

### Customer (客户主表)
```python
class Customer(BaseModel):
    # 基础信息
    name = CharField('客户名称', max_length=200)                    # 客户名称
    code = CharField('客户编码', max_length=100, unique=True)       # 客户编码
    customer_type = CharField('客户类型', max_length=20, choices=CUSTOMER_TYPES)
    customer_level = CharField('客户等级', max_length=1, choices=CUSTOMER_LEVELS)  
    status = CharField('状态', max_length=20, choices=STATUS_CHOICES)
    
    # 分类关系
    category = ForeignKey(CustomerCategory, on_delete=SET_NULL, null=True)
    
    # 联系信息
    contact_person = CharField('联系人', max_length=100, blank=True)
    phone = CharField('电话', max_length=20, blank=True, validators=[phone_validator])
    email = EmailField('邮箱', blank=True)
    website = URLField('网站', blank=True)
    
    # 地址信息
    address = TextField('地址', blank=True)
    city = CharField('城市', max_length=100, blank=True)
    province = CharField('省份', max_length=100, blank=True) 
    postal_code = CharField('邮政编码', max_length=20, blank=True)
    country = CharField('国家', max_length=100, default='中国')
    
    # 企业信息  
    legal_representative = CharField('法定代表人', max_length=100, blank=True)
    registration_number = CharField('工商注册号', max_length=100, blank=True)
    tax_number = CharField('税务登记号', max_length=100, blank=True)
    
    # 业务信息
    industry = CharField('所属行业', max_length=100, blank=True)
    credit_limit = DecimalField('信用额度', max_digits=12, decimal_places=2, default=0)
    payment_terms = CharField('付款条件', max_length=50, choices=PAYMENT_METHOD_CHOICES, blank=True)
    currency = CharField('币种', max_length=10, default='CNY')
    
    # 销售支持
    sales_rep = ForeignKey(User, on_delete=SET_NULL, null=True, verbose_name='销售代表')
```

**客户类型**:
- individual: 个人客户
- enterprise: 企业客户  
- government: 政府客户
- dealer: 经销商
- agent: 代理商

**客户等级**:
- A级客户: 重要客户
- B级客户: 主要客户
- C级客户: 普通客户
- D级客户: 小客户

**客户状态**:
- active: 正常
- inactive: 停用  
- potential: 潜在客户
- blacklist: 黑名单

### CustomerContact (客户联系人)
```python
class CustomerContact(BaseModel):
    customer = ForeignKey(Customer, on_delete=CASCADE, related_name='contacts')
    name = CharField('姓名', max_length=100)                        # 联系人姓名
    position = CharField('职位', max_length=100, blank=True)        # 职位
    department = CharField('部门', max_length=100, blank=True)      # 部门
    phone = CharField('电话', max_length=20, blank=True)            # 电话
    mobile = CharField('手机', max_length=20, blank=True)           # 手机
    email = EmailField('邮箱', blank=True)                          # 邮箱
    is_primary = BooleanField('是否主联系人', default=False)         # 主联系人标记
    notes = TextField('备注', blank=True)                           # 备注信息
```

**功能特性**:
- 支持一个客户多个联系人
- 主联系人标记（确保唯一性）
- 完整的联系方式管理
- 联系人角色和部门信息

## 业务特性

### 1. 客户编码生成
- 自动生成唯一客户编码
- 支持自定义编码规则
- 编码格式可配置

### 2. 客户等级管理
- 4级客户等级体系
- 等级与折扣政策联动
- 支持等级升降级

### 3. 信用管理
- 信用额度设置
- 超限预警机制
- 信用状态跟踪

### 4. 多联系人支持
- 一客户多联系人
- 主联系人机制
- 联系人角色管理

### 5. 销售支持集成
- 销售代表分配
- 客户付款条件
- 货币和区域设置

## 管理界面

### Admin配置
```python
# admin.py 中的配置
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'customer_type', 'customer_level', 'status']
    list_filter = ['customer_type', 'customer_level', 'status', 'category']
    search_fields = ['code', 'name', 'contact_person']
    ordering = ['code']
```

### 页面模板
```
templates/customers/
├── customer_list.html           # 客户列表页面
├── customer_form.html           # 客户编辑表单  
├── customer_detail.html         # 客户详情页面
├── customer_confirm_delete.html # 删除确认页面
├── contact_list.html            # 联系人列表
├── contact_form.html            # 联系人编辑表单
└── contact_confirm_delete.html  # 联系人删除确认
```

## 测试与质量

### 测试文件位置
```bash
apps/customers/tests/
├── __init__.py
└── test_models.py  # 客户模型测试
```

### 测试覆盖情况
✅ **测试完成度: 100%** (28/28 测试通过)

#### CustomerCategory模型测试 (4个测试)
- ✅ `test_category_creation` - 分类创建
- ✅ `test_category_unique_constraints` - 唯一性约束
- ✅ `test_category_str_representation` - 字符串表示
- ✅ `test_category_ordering` - 排序规则

#### Customer模型测试 (7个测试)
- ✅ `test_customer_creation` - 客户创建
- ✅ `test_customer_unique_code` - 客户编码唯一性
- ✅ `test_customer_types` - 所有客户类型验证
- ✅ `test_customer_levels` - 所有客户等级验证
- ✅ `test_customer_status_choices` - 所有状态验证
- ✅ `test_customer_display_name` - display_name属性
- ✅ `test_customer_str_representation` - 字符串表示

#### CustomerContact模型测试 (3个测试)
- ✅ `test_contact_creation` - 联系人创建
- ✅ `test_contact_ordering` - 排序规则
- ✅ `test_contact_str_representation` - 字符串表示

#### CustomerAddress模型测试 (5个测试)
- ✅ `test_address_creation` - 地址创建
- ✅ `test_address_types` - 所有地址类型验证
- ✅ `test_address_full_address` - 完整地址属性
- ✅ `test_address_ordering` - 排序规则
- ✅ `test_address_str_representation` - 字符串表示

#### CustomerCreditHistory模型测试 (4个测试)
- ✅ `test_credit_history_creation` - 信用历史创建
- ✅ `test_credit_history_operations` - 所有操作类型验证
- ✅ `test_credit_history_ordering` - 按时间倒序
- ✅ `test_credit_history_str_representation` - 字符串表示

#### CustomerVisit模型测试 (5个测试)
- ✅ `test_visit_creation` - 客户拜访创建
- ✅ `test_visit_types` - 所有拜访类型验证
- ✅ `test_visit_ordering` - 按拜访日期倒序
- ✅ `test_visit_str_representation` - 字符串表示
- ✅ `test_visit_with_sales_rep` - 销售代表关联

### 测试要点
- **客户类型**: 个人、企业、政府、经销商、代理商的完整验证
- **客户等级**: A/B/C/D四级客户体系
- **客户状态**: 正常、停用、潜在客户、黑名单的状态管理
- **地址管理**: 账单地址、配送地址、多地址支持
- **信用管理**: 信用额度调整历史追踪
- **拜访记录**: 销售拜访类型、目的、结果记录
- **display_name属性**: 客户显示名称逻辑
- **full_address属性**: 完整地址拼接

## 常见问题 (FAQ)

### Q: 如何设置客户的默认折扣？
A: 通过客户分类的 `discount_rate` 字段设置，客户会继承所属分类的默认折扣率。

### Q: 客户编码可以修改吗？
A: 建议客户编码在创建后不要修改，以避免影响关联的销售订单等数据。

### Q: 如何处理重复的客户信息？
A: 系统通过客户编码保证唯一性，建议在创建前先搜索检查是否已存在相似客户。

### Q: 客户联系人信息如何与销售订单关联？
A: 销售订单会自动获取客户的主联系人信息，也可以手动选择其他联系人。

### Q: 如何管理国外客户的信息？
A: 系统支持多货币和国家设置，可以在客户信息中指定对应的货币和国家。

## 相关文件清单

### 核心文件
- `__init__.py` - 包初始化
- `apps.py` - Django应用配置
- `models.py` - 数据模型定义 (约200行)
- `views.py` - 业务视图逻辑
- `urls.py` - URL路由配置
- `admin.py` - Admin后台配置

### 数据库迁移
- `migrations/` - 数据库迁移文件
  - `0001_initial.py` - 初始迁移
  - `0002_initial.py` - 补充迁移

### 模板文件
- `templates/customers/` - 7个HTML模板文件
  - 客户管理相关模板
  - 联系人管理相关模板

## 与其他模块的集成

### 销售模块 (Sales)
- 提供客户���息用于报价和订单
- 客户付款条件和折扣设置
- 销售代表关联关系

### 产品模块 (Products)  
- 客户专用价格设置（未来功能）
- 客户产品偏好分析

### 财务模块 (Finance)
- 客户信用管理
- 应收账款跟踪
- 收款记录关联

## 变更记录 (Changelog)

### 2025-11-13
- **测试完成**: 添加28个单元测试，覆盖6个核心模型
- **测试通过率**: 100% (28/28)
- **测试内容**: CustomerCategory、Customer、CustomerContact、CustomerAddress、CustomerCreditHistory、CustomerVisit

### 2025-11-08 23:26:47
- **文档初始化**: 创建Customers模块完整文档
- **模型分析**: 详细分析了3个核心模型的设计和用途
- **业务特性**: 识别了客户分类、等级管理、多联系人等关键特性
- **集成关系**: 梳理了与销售、财务等模块的集成关系