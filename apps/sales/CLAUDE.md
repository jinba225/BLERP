[根目录](../../../CLAUDE.md) > [django_erp](../../) > [apps](../) > **sales**

# Sales模块文档

## 模块职责

Sales模块是ERP系统的核心业务模块，负责完整的销售流程管理。主要职责包括：

- **报价管理**: 客户询价、报价单生成、报价转订单
- **销售订单**: 订单创建、审核、状态跟踪、部分交付支持
- **发货管理**: 发货单生成、物流跟踪、发货确认
- **退货处理**: 退货申请、审核流程、退货统计
- **模板系统**: 支持HiPrint打印模板的设计和使用
- **业务集成**: 与客户、产品、库存等模块深度集成

## 入口与启动

### 模型文件
- **主文件**: `models.py`
- **核心模型**: 
  - `Quote` - 报价单
  - `SalesOrder` - 销售订单  
  - `Delivery` - 发货单
  - `SalesReturn` - 退货单

### 视图入口
- **前端视图**: `views.py` - Django模板视图
- **模板视图**: `views_template.py` - 打印模板相关视图

### URL配置
- **路由文件**: `urls.py`
- **命名空间**: `sales`

## 对外接口

### 前端页面路由

#### 报价单管理
```python
path('quotes/', views.quote_list, name='quote_list')                    # 报价单列表
path('quotes/create/', views.quote_create, name='quote_create')         # 创建报价单
path('quotes/<int:pk>/', views.quote_detail, name='quote_detail')       # 报价单详情
path('quotes/<int:pk>/edit/', views.quote_update, name='quote_update')  # 编辑报价单
path('quotes/<int:pk>/convert/', views.quote_convert_to_order)           # 转为订单
path('quotes/<int:pk>/print/', views.quote_print)                       # 打印报价单
```

#### 销售订单管理
```python
path('orders/', views.order_list, name='order_list')                    # 订单列表
path('orders/create/', views.order_create, name='order_create')         # 创建订单
path('orders/<int:pk>/', views.order_detail, name='order_detail')       # 订单详情
path('orders/<int:pk>/approve/', views.order_approve)                   # 审核订单
path('orders/<int:pk>/unapprove/', views.order_unapprove)               # 撤销审核
```

#### 发货管理
```python
path('deliveries/', views.delivery_list, name='delivery_list')          # 发货单列表
path('orders/<int:order_pk>/delivery/create/', views.delivery_create)   # 创建发货单
path('deliveries/<int:pk>/ship/', views.delivery_ship)                  # 确认发货
```

#### 退货管理
```python
path('returns/', views.return_list, name='return_list')                 # 退货单列表
path('returns/statistics/', views.return_statistics)                    # 退货统计
path('orders/<int:order_pk>/return/create/', views.return_create)       # 创建退货单
path('returns/<int:pk>/approve/', views.return_approve)                 # 审核退货
```

### API接口
```python
path('api/customers/<int:customer_id>/info/', views.get_customer_info)  # 客户信息API
path('api/products/<int:product_id>/info/', views.get_product_info)     # 产品信息API
```

## 关键依赖与配置

### 内部模块依赖
```python
from apps.core.models import BaseModel                    # 基础模型
from apps.core.utils import DocumentNumberGenerator       # 单据号生成器
from apps.core.models import Notification                 # 通知系统
from apps.customers.models import Customer                # 客户信息
from apps.products.models import Product                  # 产品信息
from apps.inventory.models import Warehouse, StockMovement # 库存管理
```

### 外部依赖
```python
from decimal import Decimal                               # 精确计算
from django.db import transaction                        # 数据库事务
from django.core.paginator import Paginator              # 分页功能
```

### 配置项
销售模块使用以下系统配置：
- 单据号前缀（报价单、订单、发货单、退货单）
- 默认税率
- 发货方式选项
- 退货原因选项

## 数据模型

### Quote (报价单)
```python
class Quote(BaseModel):
    quote_number = CharField(max_length=100, unique=True)     # 报价单号
    customer = ForeignKey('customers.Customer')              # 客户
    status = CharField(max_length=20, choices=QUOTE_STATUS)   # 状态
    quote_date = DateField()                                  # 报价日期
    valid_until = DateField()                                 # 有效期
    subtotal = DecimalField(max_digits=12, decimal_places=2)  # 小计
    tax_amount = DecimalField(max_digits=12, decimal_places=2) # 税额
    total_amount = DecimalField(max_digits=12, decimal_places=2) # 总额
```

**状态流转**: draft → sent → accepted/rejected/expired

### SalesOrder (销售订单)
```python
class SalesOrder(BaseModel):
    order_number = CharField(max_length=100, unique=True)     # 订单号
    customer = ForeignKey('customers.Customer')              # 客户
    status = CharField(max_length=20, choices=ORDER_STATUS)   # 状态
    payment_status = CharField(max_length=20, choices=PAYMENT_STATUS) # 付款状态
    order_date = DateField()                                  # 订单日期
    required_date = DateField()                               # 要求交期
    promised_date = DateField()                               # 承诺交期
```

**状态流转**: draft → pending → confirmed → in_production → ready_to_ship → shipped → delivered → completed

### Delivery (发货单)
```python
class Delivery(BaseModel):
    delivery_number = CharField(max_length=100, unique=True)  # 发货单号
    sales_order = ForeignKey(SalesOrder)                     # 关联订单
    delivery_date = DateField()                              # 发货日期
    tracking_number = CharField(max_length=100)              # 快递单号
    shipping_address = TextField()                           # 收货地址
    status = CharField(max_length=20, choices=DELIVERY_STATUS) # 状态
```

**支持功能**: 部分发货、多次发货、物流跟踪

### SalesReturn (退货单)
```python
class SalesReturn(BaseModel):
    return_number = CharField(max_length=100, unique=True)    # 退货单号
    sales_order = ForeignKey(SalesOrder)                     # 关联订单
    return_reason = CharField(max_length=20, choices=RETURN_REASONS) # 退货原因
    status = CharField(max_length=20, choices=RETURN_STATUS)  # 状态
    request_date = DateField()                               # 申请日期
    approved_date = DateField(null=True, blank=True)         # 审核日期
```

**状态流转**: pending → approved/rejected → received → processed

### 明细表设计
每个主单据都有对应的明细表：
- `QuoteItem` - 报价明细
- `SalesOrderItem` - 订单明细
- `DeliveryItem` - 发货明细
- `SalesReturnItem` - 退货明细

## 业务特性

### 1. 报价转订单
- 一键转换功能
- 支持选择性转换明细
- 自动生成订单号
- 保持关联关系

### 2. 部分交付支持
- 支持多次部分发货
- 自动更新订单状态
- 库存数量实时扣减
- 交付进度跟踪

### 3. 退货流程管理
- 多级审核流程
- 退货原因分类
- 库存自动回补
- 通知系统集成

### 4. 打印模板系统
- 集成HiPrint打印引擎
- 支持自定义模板设计
- 报价单/订单打印
- 模板导入导出

### 5. 通知机制
```python
def _create_return_notification(sales_return, action, recipient):
    # 自动创建业务通知
    # 支持多种通知类型：创建、审核、收货、处理、拒绝
```

## 测试与质量

### 测试文件位置
```bash
apps/sales/tests/  # 测试目录 (需要创建)
```

### 测试覆盖缺口
- ❌ 缺少模型测试
- ❌ 缺少视图测试
- ❌ 缺少业务流程测试
- ❌ 缺少API测试

### 建议测试重点
1. **报价转订单**: 数据完整性和关联关系
2. **订单状态流转**: 状态机逻辑正确性
3. **部分交付**: 数量计算和库存变动
4. **退货流程**: 审核流程和状态变更
5. **金额计算**: 税费、折扣、总额计算精度

## 模板文件

### 页面模板
```
templates/sales/
├── quote_list.html          # 报价单列表
├── quote_form.html          # 报价单编辑
├── quote_detail.html        # 报价单详情  
├── quote_print.html         # 报价单打印
├── order_list.html          # 订单列表
├── order_form.html          # 订单编辑
├── order_detail.html        # 订单详情
├── delivery_list.html       # 发货单列表
├── return_list.html         # 退货单列表
└── return_statistics.html   # 退货统计
```

### 打印模板
```
templates/sales/
├── template_editor.html              # 模板编辑器
├── template_editor_hiprint.html      # HiPrint编辑器
├── template_list.html                # 模板列表
└── quote_print_hiprint.html          # HiPrint打印页面
```

## 常见问题 (FAQ)

### Q: 如何处理报价单过期？
A: 系统会自动检查 `valid_until` 字段，过期的报价单状态会变为 `expired`。

### Q: 订单可以部分发货吗？
A: 支持。每次发货会创建新的 `Delivery` 记录，系统自动跟踪剩余待发货数量。

### Q: 如何处理退货的库存问题？
A: 退货审核通过后，系统会自动创建库存入库记录，恢复相应产品的库存数量。

### Q: 报价单能重复转换为订单吗？
A: 不能。每个报价单只能转换一次，转换后状态会标记为 `converted`。

### Q: 如何自定义打印模板？
A: 通过 `template_editor_hiprint.html` 页面，使用HiPrint可视化编辑器设计模板。

## 相关文件清单

### 核心文件
- `__init__.py` - 包初始化
- `apps.py` - Django应用配置
- `models.py` - 数据模型定义 (完整的销售业务模型)
- `views.py` - 业务视图逻辑 (约2000+行)
- `views_template.py` - 打印模板相关视图
- `urls.py` - URL路由配置 (50+个路由)
- `admin.py` - Admin后台配置

### 表单和序列化
- `forms.py` - Django表单定义
- `serializers.py` - DRF序列化器 (如果有)

### 数据库迁移
- `migrations/` - 数据库迁移文件
  - `0001_initial.py` - 初始迁移
  - `0002_initial.py` - 补充迁移

### 模板文件
- `templates/sales/` - 约25个HTML模板文件

### 静态资源
- HiPrint打印组件相关JS文件
- 自定义业务逻辑JS文件

## 测试与质量

### 测试文件位置
```bash
apps/sales/tests/
├── __init__.py
└── test_models.py  # 销售模型测试
```

### 测试覆盖情况
✅ **测试完成度: 100%** (45/45 测试通过)

#### Quotation模型测试 (6个测试)
- ✅ `test_quotation_creation` - 报价单创建
- ✅ `test_quotation_unique_number` - 报价单号唯一性
- ✅ `test_quotation_status_choices` - 报价单状态验证
- ✅ `test_quotation_total_amount` - 总金额计算
- ✅ `test_quotation_soft_delete` - 软删除功能
- ✅ `test_quotation_str_representation` - 字符串表示

#### QuotationItem模型测试 (3个测试)
- ✅ `test_quotation_item_creation` - 报价明细创建
- ✅ `test_quotation_item_subtotal` - 小计金额计算
- ✅ `test_quotation_item_str_representation` - 字符串表示

#### SalesOrder模型测试 (10个测试)
- ✅ `test_sales_order_creation` - 销售订单创建
- ✅ `test_order_unique_number` - 订单号唯一性
- ✅ `test_order_status_choices` - 订单状态验证
- ✅ `test_order_total_amount` - 总金额计算
- ✅ `test_order_paid_amount` - 已付金额追踪
- ✅ `test_order_payment_status` - 付款状态计算
- ✅ `test_order_delivery_status` - 发货状态判断
- ✅ `test_order_soft_delete` - 软删除功能
- ✅ `test_order_ordering` - 排序规则
- ✅ `test_order_str_representation` - 字符串表示

#### SalesOrderItem模型测试 (6个测试)
- ✅ `test_order_item_creation` - 订单明细创建
- ✅ `test_order_item_subtotal` - 小计金额计算
- ✅ `test_order_item_delivered_quantity` - 已发货数量追踪
- ✅ `test_order_item_remaining_quantity` - 剩余数量计算
- ✅ `test_order_item_delivery_status` - 发货状态判断
- ✅ `test_order_item_str_representation` - 字符串表示

#### Delivery模型测试 (6个测试)
- ✅ `test_delivery_creation` - 发货单创建
- ✅ `test_delivery_unique_number` - 发货单号唯一性
- ✅ `test_delivery_status_choices` - 发货状态验证
- ✅ `test_delivery_soft_delete` - 软删除功能
- ✅ `test_delivery_ordering` - 按发货日期倒序
- ✅ `test_delivery_str_representation` - 字符串表示

#### DeliveryItem模型测试 (3个测试)
- ✅ `test_delivery_item_creation` - 发货明细创建
- ✅ `test_delivery_item_quantity` - 发货数量验证
- ✅ `test_delivery_item_str_representation` - 字符串表示

#### SalesReturn模型测试 (7个测试)
- ✅ `test_return_creation` - 退货单创建
- ✅ `test_return_unique_number` - 退货单号唯一性
- ✅ `test_return_reasons` - 退货原因验证
- ✅ `test_return_status_choices` - 退货状态验证
- ✅ `test_return_refund_amount` - 退款金额计算
- ✅ `test_return_ordering` - 按退货日期倒序
- ✅ `test_return_str_representation` - 字符串表示

#### SalesReturnItem模型测试 (4个测试)
- ✅ `test_return_item_creation` - 退货明细创建
- ✅ `test_return_item_refund_amount` - 退款金额计算
- ✅ `test_return_item_with_delivery` - 发货单关联
- ✅ `test_return_item_str_representation` - 字符串表示

### 测试要点
- **报价管理**: 报价单号唯一性、状态流转、金额计算
- **订单管理**: 订单号唯一性、付款状态、发货状态判断
- **发货流程**: 分批发货、已发货数量追踪、剩余数量计算
- **退货流程**: 退货原因分类、退款金额计算、状态管理
- **金额计算**: DecimalField精度处理、小计和总计计算
- **状态判断**: 部分发货、全部发货、部分付款、全额付款
- **排序规则**: 按日期倒序排列
- **软删除**: BaseModel的软删除功能

### 已修复的Bug
- **Inventory调整逻辑**: 修复库存调整单的数量计算逻辑
- **分批发货状态**: 确保订单发货状态正确反映部分/全部发货情况

## 变更记录 (Changelog)

### 2025-11-13
- **测试完成**: 添加45个单元测试，覆盖8个核心模型
- **测试通过率**: 100% (45/45)
- **测试内容**: Quotation、QuotationItem、SalesOrder、SalesOrderItem、Delivery、DeliveryItem、SalesReturn、SalesReturnItem

### 2025-11-08 23:26:47
- **文档初始化**: 创建Sales模块完整文档
- **业务分析**: 详细梳理了4个核心业务流程
- **接口整理**: 汇总了50+个URL路由和对外接口
- **模型分析**: 分析了销售业务的完整数据模型设计
- **特性识别**: 识别了部分交付、退货流程等关键业务特性