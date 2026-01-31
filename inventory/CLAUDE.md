[根目录](../../../CLAUDE.md) > [django_erp](../../) > [apps](../) > **inventory**

# Inventory模块文档

## 模块职责

Inventory模块负责库存管理，是ERP系统的核心业务模块之一。主要职责包括：
- **库存跟踪**: 实时库存数量和状态管理
- **仓库管理**: 多仓库、多库位的库存管理
- **出入库管理**: 出入库单据和流程控制
- **库存事务**: 库存变动的事务性记录

## 核心模型

### Warehouse (仓库)
```python
class Warehouse(BaseModel):
    name = CharField('仓库名称', max_length=100)
    code = CharField('仓库代码', max_length=50, unique=True)
    address = TextField('仓库地址')
    manager = ForeignKey(User, verbose_name='仓库管理员')
    is_active = BooleanField('是否启用', default=True)
```

### Stock (库存)
```python  
class Stock(BaseModel):
    product = ForeignKey('products.Product')              # 产品
    warehouse = ForeignKey(Warehouse)                     # 仓库
    quantity_available = DecimalField('可用数量')          # 可用库存
    quantity_reserved = DecimalField('预留数量')           # 预留库存
    quantity_on_order = DecimalField('在途数量')           # 在途库存
```

### StockMovement (库存变动)
```python
class StockMovement(BaseModel):
    MOVEMENT_TYPES = [
        ('in', '入库'),
        ('out', '出库'), 
        ('transfer', '调拨'),
        ('adjustment', '调整'),
    ]
    
    product = ForeignKey('products.Product')
    warehouse = ForeignKey(Warehouse)
    movement_type = CharField('变动类型', choices=MOVEMENT_TYPES)
    quantity = DecimalField('数量')
    reference_number = CharField('参考单号')
```

## 主要功能
- ✅ 多仓库库存管理
- ✅ 库存实时跟踪
- ✅ 库存变动记录
- ✅ 出入库单据管理
- ✅ 库存预留机制

## 页面模板
- `warehouse_list.html` - 仓库列表
- `warehouse_detail.html` - 仓库详情
- `stock_list.html` - 库存列表  
- `stock_detail.html` - 库存详情
- `transaction_list.html` - 库存事务

## 集成关系
- **Products**: 产品库存基础数据
- **Sales**: 销售出库和库存预留
- **Purchase**: 采购入库处理
- **Core**: 库存变动审计日志

## 测试与质量

### 测试文件位置
```bash
apps/inventory/tests/
├── __init__.py
├── test_models.py           # 库存模型测试
├── test_business_logic.py   # 业务逻辑测试
└── test_services.py         # 服务层测试 (新增)
```

### 测试覆盖情况
✅ **测试完成度: 100%** (60/60 测试通过)

#### 模型层测试 (47个测试)
- ✅ `test_warehouse_creation` - 仓库创建
- ✅ `test_warehouse_unique_code` - 仓库代码唯一性
- ✅ `test_warehouse_soft_delete` - 软删除功能
- ✅ `test_warehouse_ordering` - 排序规则
- ✅ `test_warehouse_str_representation` - 字符串表示

#### Stock模型测试 (9个测试)
- ✅ `test_stock_creation` - 库存记录创建
- ✅ `test_stock_unique_together` - 产品+仓库唯一性约束
- ✅ `test_stock_available_quantity` - 可用数量计算
- ✅ `test_stock_reserved_quantity` - 预留数量管理
- ✅ `test_stock_on_order_quantity` - 在途数量追踪
- ✅ `test_stock_is_low_stock` - 低库存判断
- ✅ `test_stock_is_out_of_stock` - 缺货判断
- ✅ `test_stock_ordering` - 排序规则
- ✅ `test_stock_str_representation` - 字符串表示

#### StockMovement模型测试 (7个测试)
- ✅ `test_movement_creation` - 库存变动记录创建
- ✅ `test_movement_types` - 所有变动类型验证
- ✅ `test_movement_in_stock` - 入库操作
- ✅ `test_movement_out_stock` - 出库操作
- ✅ `test_movement_transfer` - 调拨操作
- ✅ `test_movement_ordering` - 按变动日期倒序
- ✅ `test_movement_str_representation` - 字符串表示

#### StockIn模型测试 (6个测试)
- ✅ `test_stock_in_creation` - 入库单创建
- ✅ `test_stock_in_unique_number` - 入库单号唯一性
- ✅ `test_stock_in_status_choices` - 入库单状态验证
- ✅ `test_stock_in_approval` - 审批流程
- ✅ `test_stock_in_ordering` - 按入库日期倒序
- ✅ `test_stock_in_str_representation` - 字符串表示

#### StockInItem模型测试 (3个测试)
- ✅ `test_stock_in_item_creation` - 入库明细创建
- ✅ `test_stock_in_item_quantity` - 数量验证
- ✅ `test_stock_in_item_str_representation` - 字符串表示

#### StockOut模型测试 (6个测试)
- ✅ `test_stock_out_creation` - 出库单创建
- ✅ `test_stock_out_unique_number` - 出库单号唯一性
- ✅ `test_stock_out_status_choices` - 出库单状态验证
- ✅ `test_stock_out_approval` - 审批流程
- ✅ `test_stock_out_ordering` - 按出库日期倒序
- ✅ `test_stock_out_str_representation` - 字符串表示

#### StockOutItem模型测试 (3个测试)
- ✅ `test_stock_out_item_creation` - 出库明细创建
- ✅ `test_stock_out_item_quantity` - 数量验证
- ✅ `test_stock_out_item_str_representation` - 字符串表示

#### StockTransfer模型测试 (5个测试)
- ✅ `test_transfer_creation` - 调拨单创建
- ✅ `test_transfer_unique_number` - 调拨单号唯一性
- ✅ `test_transfer_status_choices` - 调拨单状态验证
- ✅ `test_transfer_ordering` - 按调拨日期倒序
- ✅ `test_transfer_str_representation` - 字符串表示

#### StockAdjustment模型测试 (3个测试)
- ✅ `test_adjustment_creation` - 调整单创建
- ✅ `test_adjustment_unique_number` - 调整单号唯一性
- ✅ `test_adjustment_reasons` - 调整原因验证

#### 服务层测试 (13个测试)

##### StockAdjustmentService测试 (4个测试)
- ✅ `test_create_adjustment_basic` - 基础库存调整创建
- ✅ `test_create_adjustment_with_custom_number` - 自定义单据号
- ✅ `test_approve_adjustment_increase` - 审核增加库存的调整单
- ✅ `test_approve_adjustment_decrease` - 审核减少库存的调整单

##### StockTransferService测试 (4个测试)
- ✅ `test_create_transfer_basic` - 基础库存调拨创建
- ✅ `test_update_transfer_basic` - 更新调拨单和明细
- ✅ `test_ship_transfer` - 调拨单发货（扣减源仓库库存）
- ✅ `test_receive_transfer` - 调拨单收货（增加目标仓库库存）

##### StockCountService测试 (3个测试)
- ✅ `test_create_count_basic` - 基础库存盘点创建
- ✅ `test_create_count_with_counters` - 创建盘点单并指定盘点人
- ✅ `test_update_count_basic` - 更新盘点单和明细

##### InboundOrderService测试 (2个测试)
- ✅ `test_create_inbound_basic` - 基础入库单创建
- ✅ `test_create_inbound_with_custom_number` - 自定义单据号

### 测试要点
- **仓库管理**: 仓库代码唯一性、启用状态管理
- **库存跟踪**: 可用数量、预留数量、在途数量的计算
- **库存判断**: 低库存、缺货的自动判断逻辑
- **库存变动**: 入库、出库、调拨、调整四种类型的操作
- **单据管理**: 入库单、出库单、调拨单、调整单的完整流程
- **审批流程**: 单据的审批状态流转
- **唯一性约束**: 产品+仓库的组合唯一性
- **排序规则**: 按日期倒序排列
- **软删除**: BaseModel的软删除功能
- **服务层测试**: StockAdjustmentService, StockTransferService, StockCountService, InboundOrderService业务逻辑
- **库存事务**: InventoryTransaction.update_stock()自动更新库存机制
- **调拨流程**: 发货扣减源仓库、收货增加目标仓库的双向事务
- **事务原子性**: @transaction.atomic装饰器确保数据一致性
- **Decimal精度**: 所有数量字段使用4位小数精度

### 已修复的Bug
- **调整单逻辑**: 修复StockAdjustment模型的数量计算逻辑，确保调整前后数量正确
- **库存事务类型**: 修复服务层使用错误的transaction_type（'transfer_out'/'transfer_in' → 'out'/'in'）
- **发货数量符号**: 修复发货时quantity使用负数的问题（update_stock()自动处理减法）

## 变更记录
### 2026-01-06 (服务层测试)
- **服务层测试完成**: 添加13个单元测试，覆盖4个核心服务类
- **测试通过率**: 100% (60/60，含47个模型层测试 + 13个服务层测试)
- **测试内容**:
  - StockAdjustmentService：创建、审核增加/减少库存
  - StockTransferService：创建、更新、发货、收货完整流程
  - StockCountService：创建、更新、盘点人管理
  - InboundOrderService：创建、自定义单据号
- **Bug修复**:
  - 修复库存调拨的transaction_type错误（'transfer_out'/'transfer_in' → 'out'/'in'）
  - 修复发货数量使用负数的问题（quantity应为正数）

### 2025-11-13
- **测试完成**: 添加47个单元测试，覆盖9个核心模型
- **测试通过率**: 100% (47/47)
- **测试内容**: Warehouse、Stock、StockMovement、StockIn、StockInItem、StockOut、StockOutItem、StockTransfer、StockAdjustment
- **Bug修复**: StockAdjustment调整逻辑修正

### 2025-11-08 23:26:47
- 文档初始化，识别核心库存管理功能