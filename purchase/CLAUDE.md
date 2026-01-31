[根目录](../../../CLAUDE.md) > [django_erp](../../) > [apps](../) > **purchase**

# Purchase模块文档

## 模块职责

Purchase模块负责采购管理流程。主要职责包括：
- **采购订单**: 采购订单的创建、审核、跟踪
- **供应商集成**: 与供应商模块深度集成
- **库存集成**: 采购入库自动更新库存
- **财务集成**: 采购付款和应付账款管理

## 核心模型
```python
class PurchaseOrder(BaseModel):
    order_number = CharField('采购订单号', max_length=100, unique=True)
    supplier = ForeignKey('suppliers.Supplier')
    status = CharField('状态', max_length=20, choices=ORDER_STATUS)
    order_date = DateField('订单日期')
    expected_date = DateField('预计到货日期')
    total_amount = DecimalField('总金额', max_digits=12, decimal_places=2)
    
class PurchaseOrderItem(BaseModel):
    purchase_order = ForeignKey(PurchaseOrder)
    product = ForeignKey('products.Product')
    quantity = DecimalField('数量', max_digits=10, decimal_places=3)
    unit_price = DecimalField('单价', max_digits=10, decimal_places=2)
```

## 主要功能
- ✅ 采购订单管理
- ✅ 订单状态跟踪
- ✅ 采购询价管理（RFQ）
- ✅ 供应商报价管理
- ✅ 报价对比与选择
- ✅ 询价单转采购订单
- ✅ 收货流程管理
- ✅ 退货流程管理
- ✅ 质检流程管理（完整）
- ✅ 质检模板管理
- ✅ 不合格品处理（NCP）
- ✅ 质检统计分析
- ⚠️ 需要完善付款管理

## 页面模板

### 采购订单
- `order_list.html` - 采购订单列表
- `order_form.html` - 采购订单表单
- `order_detail.html` - 采购订单详情
- `order_confirm_delete.html` - 删除确认

### 采购询价
- `inquiry_list.html` - 询价单列表
- `inquiry_detail.html` - 询价单详情
- `inquiry_confirm_delete.html` - 删除确认
- `inquiry_send.html` - 发送给供应商
- `inquiry_confirm_create_order.html` - 创建订单确认

### 供应商报价
- `quotation_list.html` - 报价单列表
- `quotation_detail.html` - 报价单详情
- `quotation_compare.html` - 报价对比
- `quotation_confirm_select.html` - 选定报价确认

### 收货管理
- `receipt_list.html` - 收货单列表
- `receipt_detail.html` - 收货单详情
- `receipt_form.html` - 收货单表单

### 退货管理
- `return_list.html` - 退货单列表
- `return_detail.html` - 退货单详情
- `return_form.html` - 退货单表单
- `return_statistics.html` - 退货统计

### 质检管理
- `inspection_list.html` - 质检单列表
- `inspection_detail.html` - 质检单详情
- `inspection_form.html` - 质检单表单
- `inspection_execute.html` - 质检执行页面
- `inspection_confirm_approve.html` - 质检审批确认
- `inspection_confirm_delete.html` - 删除确认

### 质检模板
- `template_list.html` - 质检模板列表
- `template_detail.html` - 质检模板详情
- `template_form.html` - 质检模板表单（支持动态添加检验项目）
- `template_confirm_delete.html` - 删除确认

### 不合格品处理（NCP）
- `ncp_list.html` - 不合格品列表
- `ncp_detail.html` - 不合格品详情
- `ncp_handle.html` - 不合格品处理页面

### 质检统计
- `quality_statistics.html` - 质检统计分析报表

## 集成关系
- **Suppliers**: 供应商信息、报价管理
- **Products**: 采购产品信息
- **Inventory**: 采购入库处理、库存更新
- **Finance**: 应付账款管理、付款记录

## 测试与质量

### 测试文件位置
```bash
apps/purchase/tests/
├── __init__.py
├── test_models.py     # 采购模型测试
└── test_services.py   # 采购服务层测试 (新增)
```

### 测试覆盖情况
✅ **测试完成度: 100%** (36/36 测试通过)

#### 模型层测试 (27个测试)

##### PurchaseOrder模型测试 (6个测试)
- ✅ `test_purchase_order_creation` - 采购订单创建
- ✅ `test_order_unique_number` - 订单号唯一性
- ✅ `test_order_status_choices` - 所有订单状态验证
- ✅ `test_order_total_amount` - 总金额计算
- ✅ `test_order_soft_delete` - 软删除功能
- ✅ `test_order_str_representation` - 字符串表示

#### PurchaseOrderItem模型测试 (3个测试)
- ✅ `test_order_item_creation` - 订单明细创建
- ✅ `test_order_item_subtotal` - 小计金额计算
- ✅ `test_order_item_str_representation` - 字符串表示

#### PurchaseReceipt模型测试 (5个测试)
- ✅ `test_receipt_creation` - 收货单创建
- ✅ `test_receipt_unique_number` - 收货单号唯一性
- ✅ `test_receipt_status_choices` - 收货状态验证
- ✅ `test_receipt_ordering` - 按收货日期倒序
- ✅ `test_receipt_str_representation` - 字符串表示

#### PurchaseReturn模型测试 (6个测试)
- ✅ `test_return_creation` - 退货单创建
- ✅ `test_return_unique_number` - 退货单号唯一性
- ✅ `test_return_reasons` - 退货原因验证
- ✅ `test_return_status_choices` - 退货状态验证
- ✅ `test_return_ordering` - 按退货日期倒序
- ✅ `test_return_str_representation` - 字符串表示

#### QualityInspection模型测试 (7个测试)
- ✅ `test_inspection_creation` - 质检单创建
- ✅ `test_inspection_unique_number` - 质检单号唯一性
- ✅ `test_inspection_result_choices` - 质检结果验证
- ✅ `test_inspection_status_choices` - 质检状态验证
- ✅ `test_inspection_pass_rate_calculation` - 合格率计算
- ✅ `test_inspection_ordering` - 按检验日期倒序
- ✅ `test_inspection_str_representation` - 字符串表示

#### 服务层测试 (9个测试)

##### PurchaseOrderService测试 (5个测试)
- ✅ `test_create_order_basic` - 基础采购订单创建
- ✅ `test_create_order_with_custom_number` - 自定义单据号
- ✅ `test_create_order_filter_empty_items` - 过滤空明细
- ✅ `test_update_order_basic` - 更新订单和明细
- ✅ `test_update_order_keep_items_when_none` - 仅更新主单不修改明细

##### PurchaseRequestService测试 (4个测试)
- ✅ `test_create_request_basic` - 基础采购申请创建
- ✅ `test_update_request_basic` - 更新采购申请
- ✅ `test_convert_request_to_order_basic` - 采购申请转订单
- ✅ `test_convert_request_to_order_with_notes` - 转换时生成详细备注

### 测试要点
- **订单管理**: 订单号唯一性、状态流转、总金额计算
- **收货流程**: 收货单号生成、收货状态管理
- **退货流程**: 退货原因分类、退货状态跟踪
- **质检流程**: 合格率计算、质检结果判定、状态流转
- **服务层测试**: PurchaseOrderService和PurchaseRequestService业务逻辑
- **申请转订单**: 采购申请到采购订单的完整转换流程
- **明细过滤**: 同时支持product对象和product_id的过滤逻辑
- **事务原子性**: @transaction.atomic装饰器确保数据一致性
- **Decimal精度**: 价格和数量字段的精确计算
- **排序规则**: 按日期倒序排列
- **软删除**: BaseModel的软删除功能

### 已修复的Bug
- **质检合格率计算**: 确保pass_rate属性正确计算合格率百分比
- **Python缓存问题**: 清理__pycache__目录解决旧代码缓存问题
- **服务层skip_calculate参数**: 移除不支持的save()参数
- **明细过滤逻辑**: 同时检查product_id和product，支持两种传参方式

## 变更记录

### 2026-01-14 (询价单转订单优化)
- **供应商可选**: 修改 `PurchaseOrder.supplier` 字段为可空（`null=True, blank=True`）
- **灵活转换**: 询价单转采购订单支持两种模式：
  1. **有报价模式**: 选定供应商报价后转订单，自动填充供应商、价格等信息
  2. **无报价模式**: 未选定报价也可直接转订单，供应商为空，价格使用目标价或0
- **视图优化**:
  - 修改 `inquiry_create_order()` 视图，移除必须选定报价的限制
  - 支持从询价明细创建订单明细（价格为0或目标价）
- **模板优化**:
  - `inquiry_detail.html`: "创建采购订单"按钮不再限制必须选定报价
  - `inquiry_confirm_create_order.html`: 支持显示有报价和无报价两种情况
- **数据库迁移**: apps/purchase/migrations/0010_allow_null_supplier_in_order.py
- **业务价值**: 提高采购流程灵活性，支持无报价情况下快速创建订单框架

### 2026-01-06 (服务层测试)
- **服务层测试完成**: 添加9个单元测试，覆盖PurchaseOrderService和PurchaseRequestService
- **测试通过率**: 100% (36/36，含27个模型层测试 + 9个服务层测试)
- **测试内容**:
  - PurchaseOrderService：创建、更新、明细过滤
  - PurchaseRequestService：创建、更新、申请转订单
- **Bug修复**:
  - 移除save()方法中不支持的skip_calculate参数
  - 修复明细过滤逻辑，同时支持product对象和product_id

### 2025-11-11 (任务1.8 - 质检流程)
- **质检完整流程实现**（3个阶段完成）

  **阶段1：核心功能（2025-11-11 15:30）**
  - 新增4个模型：QualityInspection, QualityInspectionItem, QualityInspectionTemplate, NonConformingProduct
  - 质检单CRUD：创建、编辑、删除、查看
  - 质检执行功能：逐项录入检验结果，自动计算合格率
  - 质检审批功能：审批通过后触发后续流程
  - 质检模板CRUD：支持动态添加/删除检验项目
  - 自动创建NCP：质检失败自动生成不合格品记录
  - 状态流转：pending → in_progress → passed/failed/conditional → approved
  - 添加7个视图函数和9个页面模板

  **阶段2：业务集成（2025-11-11 18:00）**
  - 收货确认自动创建质检单：支持质检模板智能应用
  - 质检审批自动更新收货单状态：合格验收/不合格拒收
  - 质检审批自动更新入库单状态：合格自动审批入库
  - NCP完整工作流：列表、详情、处理功能
  - NCP处理方式：退货、返工、报废、让步接收
  - NCP状态流转：pending → in_progress → completed
  - 添加3个视图函数和3个页面模板

  **阶段3：统计分析（2025-11-11 19:30）**
  - 质检统计报表：总体质检数据统计
  - 供应商质量对比：Top 10供应商排名和质量评级
  - 产品分类统计：按分类统计质检合格率
  - 不合格品分析：处理方式占比、成本分析
  - 月度趋势分析：质检数量和合格率变化趋势
  - 数据可视化：统计卡片、进度条、评级徽章
  - 日期范围筛选：支持自定义时间段分析
  - 添加1个视图函数和1个页面模板

- **数据库迁移**: apps/purchase/migrations/0005
- **代码统计**: 新增约600行Python代码，约1200行HTML模板代码

### 2025-11-11 (任务1.5)
- **新增采购询价管理完整功能**
  - 新增4个模型：PurchaseInquiry, PurchaseInquiryItem, SupplierQuotation, SupplierQuotationItem
  - 实现询价单CRUD：创建、编辑、删除、查看
  - 实现询价单发送功能：支持多供应商批量发送
  - 实现供应商报价管理：待报价、已提交、已选定、已拒绝
  - 实现报价对比功能：多供应商横向对比价格、交货期、付款条款
  - 实现报价选定功能：选定后自动拒绝其他报价
  - 实现询价转订单：根据选定报价自动生成采购订单
  - 添加11个视图函数和9个页面模板
  - 完整的状态流转：draft → sent → quoted → selected → ordered
  - 数据库迁移：apps/purchase/migrations/0004

### 2025-11-08 23:26:47
- 文档初始化，识别基础采购管理功能