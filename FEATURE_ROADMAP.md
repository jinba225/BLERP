# BetterLaser ERP 功能完善路线图

## 文档说明

本文档详细规划了 Django Web ERP 系统的功能完善计划，参考 Windows 桌面端功能，确保所有业务单据都具备完整的增删改查（CRUD）功能。

---

## 当前状态总结

### ✅ 已完成的模块（8个）

| 模块 | 完成度 | 说明 |
|-----|--------|------|
| 客户管理 (customers) | 100% | 客户、联系人、地址、价格表 |
| 供应商管理 (suppliers) | 100% | 供应商、联系人、产品目录 |
| 产品管理 (products) | 100% | 产品、分类、BOM、属性 |
| 库存管理 (inventory) | 80% | 仓库、库位、库存；缺少调拨和盘点的视图 |
| 销售管理 (sales) | 70% | 销售订单；缺少报价单、发货单、退货单 |
| 采购管理 (purchase) | 70% | 采购订单；缺少询价单、收货单、退货单 |
| 财务管理 (finance) | 60% | 科目、凭证；缺少收付款单、发票管理 |
| 用户/部门 (users/depts) | 100% | 完整的用户和部门管理 |

### ❌ 缺失的模块（3个）

1. **生产管理 (production)** - 完全缺失
2. **合同管理 (contracts)** - 完全缺失
3. **报表中心 (reports)** - 完全缺失

---

## 第一阶段：关键业务单据（优先级：🔥🔥🔥）

**预计时间**: 2-3周
**目标**: 补全核心业务流程中缺失的单据类型

### 1.1 销售报价单管理

**文件位置**: `apps/sales/`

**需要创建的模型**:
```python
# models.py
class Quotation(BaseModel):
    """销售报价单"""
    - quotation_number (报价单号，自动生成)
    - quotation_type (报价类型: 国内/海外)
    - customer (客户)
    - contact_person (联系人)
    - quotation_date (报价日期)
    - valid_until (有效期至)
    - status (状态: 草稿/已发送/已确认/已失效/已转订单)
    - currency (币种)
    - exchange_rate (汇率)
    - payment_terms (付款条件)
    - delivery_terms (交货条件)
    - notes (备注)
    - total_amount (总金额)

class QuotationItem(BaseModel):
    """报价单明细"""
    - quotation (报价单)
    - product (产品)
    - description (产品描述)
    - quantity (数量)
    - unit_price (单价)
    - discount_rate (折扣率)
    - tax_rate (税率)
    - amount (金额)
```

**需要创建的视图和表单**:
- `views/quotation_list.py` - 报价单列表（查询、筛选）
- `views/quotation_create.py` - 创建报价单
- `views/quotation_detail.py` - 报价单详情
- `views/quotation_update.py` - 编辑报价单
- `views/quotation_delete.py` - 删除报价单（软删除）
- `forms/quotation_form.py` - 报价单表单
- `templates/sales/quotation_*.html` - 模板文件

**业务功能**:
- ✅ 自动生成报价单号（格式：QT202511050001）
- ✅ 支持国内/海外两种报价类型
- ✅ 报价单转销售订单功能
- ✅ 报价单打印/导出PDF
- ✅ 报价单状态流转管理

### 1.2 采购询价单管理

**文件位置**: `apps/purchase/`

**需要创建的模型**:
```python
# models.py
class PurchaseInquiry(BaseModel):
    """采购询价单"""
    - inquiry_number (询价单号)
    - supplier (供应商)
    - inquiry_date (询价日期)
    - required_date (要求报价日期)
    - status (状态: 草稿/已发送/已回复/已比价/已转订单)
    - notes (备注)

class PurchaseInquiryItem(BaseModel):
    """询价单明细"""
    - inquiry (询价单)
    - product (产品)
    - quantity (数量)
    - target_price (目标价格)
    - quoted_price (供应商报价)
    - delivery_time (交货时间)
```

**需要创建的视图和表单**:
- 完整的 CRUD 视图
- 询价单对比功能（多个供应商报价对比）
- 询价单转采购订单

### 1.3 销售发货单管理

**文件位置**: `apps/sales/`

**需要创建的模型**:
```python
# models.py
class SalesDelivery(BaseModel):
    """销售发货单"""
    - delivery_number (发货单号)
    - sales_order (销售订单)
    - customer (客户)
    - delivery_date (发货日期)
    - delivery_address (发货地址)
    - logistics_company (物流公司)
    - tracking_number (物流单号)
    - status (状态: 待发货/已发货/运输中/已签收)

class SalesDeliveryItem(BaseModel):
    """发货单明细"""
    - delivery (发货单)
    - order_item (订单明细)
    - product (产品)
    - quantity (发货数量)
    - warehouse (出货仓库)
```

### 1.4 采购收货单管理

**文件位置**: `apps/purchase/`

**需要创建的模型**:
```python
# models.py
class PurchaseReceipt(BaseModel):
    """采购收货单"""
    - receipt_number (收货单号)
    - purchase_order (采购订单)
    - supplier (供应商)
    - receipt_date (收货日期)
    - warehouse (收货仓库)
    - status (状态: 待收货/部分收货/已收货/待质检/已入库)

class PurchaseReceiptItem(BaseModel):
    """收货单明细"""
    - receipt (收货单)
    - order_item (订单明细)
    - product (产品)
    - ordered_quantity (订单数量)
    - received_quantity (收货数量)
    - qualified_quantity (合格数量)
    - rejected_quantity (不合格数量)
```

### 1.5 库存入库单/出库单

**文件位置**: `apps/inventory/`

**需要创建的模型**:
```python
# models.py
class StockIn(BaseModel):
    """入库单"""
    - stock_in_number (入库单号)
    - stock_in_type (入库类型: 采购入库/生产入库/退货入库/其他入库)
    - warehouse (仓库)
    - stock_in_date (入库日期)
    - source_document (源单据号)
    - status (状态: 草稿/待审核/已审核/已入库)

class StockInItem(BaseModel):
    """入库单明细"""
    - stock_in (入库单)
    - product (产品)
    - quantity (数量)
    - location (库位)
    - batch_number (批次号)

class StockOut(BaseModel):
    """出库单"""
    - stock_out_number (出库单号)
    - stock_out_type (出库类型: 销售出库/生产领料/调拨出库/其他出库)
    - warehouse (仓库)
    - stock_out_date (出库日期)
    - destination_document (目标单据号)
    - status (状态: 草稿/待审核/已审核/已出库)

class StockOutItem(BaseModel):
    """出库单明细"""
    - stock_out (出库单)
    - product (产品)
    - quantity (数量)
    - location (库位)
    - batch_number (批次号)
```

### 1.6 质检单管理

**文件位置**: `apps/inventory/`

**需要创建的模型**:
```python
# models.py
class QualityInspection(BaseModel):
    """质检单"""
    - inspection_number (质检单号)
    - inspection_type (质检类型: 进货质检/成品质检/过程质检)
    - source_document (源单据号)
    - product (产品)
    - quantity (检验数量)
    - inspection_date (检验日期)
    - inspector (检验员)
    - status (状态: 待检验/检验中/已通过/不合格)
    - result (检验结果)
    - qualified_quantity (合格数量)
    - rejected_quantity (不合格数量)
    - notes (备注)
```

---

## 第二阶段：合同管理模块（优先级：🔥🔥）

**预计时间**: 1-2周
**目标**: 实现完整的合同管理功能

### 2.1 销售合同管理

**文件位置**: `apps/contracts/`

**需要创建的模型**:
```python
# models.py
class SalesContract(BaseModel):
    """销售合同"""
    - contract_number (合同号)
    - contract_name (合同名称)
    - customer (客户)
    - contract_date (签订日期)
    - start_date (开始日期)
    - end_date (结束日期)
    - contract_amount (合同金额)
    - payment_terms (付款条件)
    - delivery_terms (交货条款)
    - status (状态: 草稿/审核中/已签订/履行中/已完成/已终止)
    - attachment (附件)

class SalesContractItem(BaseModel):
    """合同明细"""
    - contract (合同)
    - product (产品)
    - quantity (数量)
    - unit_price (单价)
    - amount (金额)
```

### 2.2 采购合同管理

**文件位置**: `apps/contracts/`

**需要创建的模型**:
```python
# models.py
class PurchaseContract(BaseModel):
    """采购合同"""
    - contract_number (合同号)
    - contract_name (合同名称)
    - supplier (供应商)
    - contract_date (签订日期)
    - start_date (开始日期)
    - end_date (结束日期)
    - contract_amount (合同金额)
    - payment_terms (付款条件)
    - delivery_terms (交货条款)
    - status (状态: 草稿/审核中/已签订/履行中/已完成/已终止)
    - attachment (附件)
```

### 2.3 借用合同管理

**文件位置**: `apps/contracts/`

**需要创建的模型**:
```python
# models.py
class LoanContract(BaseModel):
    """借用合同"""
    - contract_number (合同号)
    - loan_type (借用类型: 设备借用/物料借用)
    - borrower (借用方)
    - loan_date (借出日期)
    - expected_return_date (预计归还日期)
    - actual_return_date (实际归还日期)
    - status (状态: 借出中/已归还/已逾期/已损坏)

class LoanContractItem(BaseModel):
    """借用合同明细"""
    - contract (合同)
    - equipment_or_material (设备或物料)
    - quantity (数量)
    - condition_out (借出状态)
    - condition_return (归还状态)
```

---

## 第三阶段：生产管理模块（优先级：🔥）

**预计时间**: 2-3周
**目标**: 实现完整的生产管理功能

### 3.1 生产计划管理

**文件位置**: `apps/production/`

**需要创建的模型**:
```python
# models.py
class ProductionPlan(BaseModel):
    """生产计划"""
    - plan_number (计划单号)
    - plan_name (计划名称)
    - plan_date (计划日期)
    - start_date (开始日期)
    - end_date (结束日期)
    - status (状态: 草稿/已下达/生产中/已完成/已取消)

class ProductionPlanItem(BaseModel):
    """生产计划明细"""
    - plan (生产计划)
    - product (产品)
    - quantity (计划数量)
    - completed_quantity (完成数量)
```

### 3.2 生产工单管理

**文件位置**: `apps/production/`

**需要创建的模型**:
```python
# models.py
class ProductionOrder(BaseModel):
    """生产工单"""
    - order_number (工单号)
    - plan (生产计划)
    - product (产品)
    - quantity (生产数量)
    - workshop (车间)
    - production_line (生产线)
    - start_date (开始日期)
    - end_date (结束日期)
    - status (状态: 待开工/生产中/已完工/已入库)

class ProductionOrderOperation(BaseModel):
    """工单工序"""
    - order (工单)
    - operation (工序)
    - status (状态: 未开始/进行中/已完成)
    - start_time (开始时间)
    - end_time (结束时间)
```

### 3.3 工艺路线管理

**文件位置**: `apps/production/`

**需要创建的模型**:
```python
# models.py
class ProcessRoute(BaseModel):
    """工艺路线"""
    - route_number (路线编号)
    - route_name (路线名称)
    - product (产品)
    - version (版本)
    - status (状态: 草稿/已生效/已失效)

class ProcessRouteOperation(BaseModel):
    """工艺工序"""
    - route (工艺路线)
    - sequence (工序顺序)
    - operation_name (工序名称)
    - work_center (工作中心)
    - standard_time (标准工时)
```

### 3.4 领料单/退料单管理

**文件位置**: `apps/production/`

**需要创建的模型**:
```python
# models.py
class MaterialRequisition(BaseModel):
    """领料单"""
    - requisition_number (领料单号)
    - production_order (生产工单)
    - requisition_date (领料日期)
    - warehouse (仓库)
    - status (状态: 草稿/已审核/已出库)

class MaterialRequisitionItem(BaseModel):
    """领料单明细"""
    - requisition (领料单)
    - material (物料)
    - required_quantity (需求数量)
    - issued_quantity (发料数量)

class MaterialReturn(BaseModel):
    """退料单"""
    - return_number (退料单号)
    - production_order (生产工单)
    - return_date (退料日期)
    - warehouse (仓库)
    - status (状态: 草稿/已审核/已入库)
```

---

## 第四阶段：财务完善和报表（优先级：⚠️）

**预计时间**: 1-2周
**目标**: 完善财务单据和报表系统

### 4.1 收款单/付款单视图

**文件位置**: `apps/finance/`

**现状**: 模型已存在，需要添加视图和表单

**需要创建**:
- `views/payment_*.py` - 收款单/付款单的完整 CRUD 视图
- `forms/payment_form.py` - 收付款表单
- `templates/finance/payment_*.html` - 模板文件

### 4.2 发票管理

**文件位置**: `apps/finance/`

**需要创建的模型**:
```python
# models.py
class Invoice(BaseModel):
    """发票"""
    - invoice_number (发票号)
    - invoice_type (发票类型: 销售发票/采购发票)
    - related_document (关联单据)
    - invoice_date (开票日期)
    - amount (发票金额)
    - tax_amount (税额)
    - status (状态: 未开票/已开票/已作废)
```

### 4.3 费用报销单

**文件位置**: `apps/finance/`

**需要创建的模型**:
```python
# models.py
class ExpenseClaim(BaseModel):
    """费用报销单"""
    - claim_number (报销单号)
    - employee (员工)
    - claim_date (报销日期)
    - total_amount (总金额)
    - status (状态: 草稿/待审批/已审批/已支付)

class ExpenseClaimItem(BaseModel):
    """报销明细"""
    - claim (报销单)
    - expense_type (费用类型)
    - amount (金额)
    - description (说明)
    - attachment (附件)
```

### 4.4 业务报表

**文件位置**: `apps/reports/`

**需要实现的报表**:
1. **销售报表**
   - 销售订单明细表
   - 销售统计分析表
   - 客户销售排行榜
   - 产品销售排行榜

2. **采购报表**
   - 采购订单明细表
   - 采购统计分析表
   - 供应商采购排行榜

3. **库存报表**
   - 库存状态表
   - 出入库明细表
   - 库存预警表
   - 库存周转率分析

4. **财务报表**
   - 应收账款账龄分析
   - 应付账款账龄分析
   - 收支明细表

---

## 第五阶段：完善 CRUD 功能（优先级：✅）

**预计时间**: 1周
**目标**: 确保每个单据都有完整的功能

### 5.1 通用功能清单

每个单据模块必须包含以下功能：

✅ **列表页 (List View)**
- 数据表格展示
- 多条件查询
- 字段筛选
- 排序
- 分页
- 批量操作
- 导出 Excel/CSV

✅ **创建页 (Create View)**
- 表单验证
- 单据号自动生成
- 关联数据选择（Select2）
- 明细行动态添加
- 保存草稿功能

✅ **详情页 (Detail View)**
- 完整信息展示
- 操作历史记录
- 关联单据查看
- 打印预览

✅ **编辑页 (Update View)**
- 草稿状态可编辑
- 已审核状态不可编辑
- 修改历史记录

✅ **删除功能 (Delete)**
- 软删除（is_deleted=True）
- 权限验证
- 删除前关联检查

### 5.2 单据编号生成器

**文件位置**: `apps/core/utils/document_number.py`

```python
class DocumentNumberGenerator:
    """统一的单据号生成器"""

    @staticmethod
    def generate(prefix, date=None):
        """
        生成格式：前缀 + YYYYMMDD + 4位流水号
        例如：QT20251105000 1
        """
        pass
```

**单据号前缀规范**:
- QT: 报价单 (Quotation)
- SO: 销售订单 (Sales Order)
- SD: 销售发货单 (Sales Delivery)
- PI: 采购询价单 (Purchase Inquiry)
- PO: 采购订单 (Purchase Order)
- PR: 采购收货单 (Purchase Receipt)
- SI: 入库单 (Stock In)
- SO: 出库单 (Stock Out)
- QI: 质检单 (Quality Inspection)
- SC: 销售合同 (Sales Contract)
- PC: 采购合同 (Purchase Contract)
- LC: 借用合同 (Loan Contract)
- PP: 生产计划 (Production Plan)
- WO: 生产工单 (Work Order)
- MR: 领料单 (Material Requisition)
- MT: 退料单 (Material Return)

### 5.3 审批流程

**文件位置**: `apps/core/models/workflow.py`

```python
class ApprovalFlow(BaseModel):
    """审批流程"""
    - document_type (单据类型)
    - document_id (单据ID)
    - status (状态: 待审批/已审批/已拒绝)
    - approver (审批人)
    - approval_date (审批日期)
    - comments (审批意见)
```

---

## 实施计划时间表

| 阶段 | 内容 | 预计时间 | 累计时间 |
|-----|------|----------|---------|
| 第一阶段 | 关键业务单据 | 2-3周 | 3周 |
| 第二阶段 | 合同管理 | 1-2周 | 5周 |
| 第三阶段 | 生产管理 | 2-3周 | 8周 |
| 第四阶段 | 财务和报表 | 1-2周 | 10周 |
| 第五阶段 | CRUD 完善 | 1周 | 11周 |
| **总计** | | **约 2.5-3 个月** | |

---

## 技术规范

### 代码风格
- 遵循 PEP 8
- 使用 Black 格式化
- 使用 isort 排序导入
- 所有函数和类添加文档字符串

### 数据库规范
- 所有表继承 `BaseModel`（包含时间戳和软删除）
- 外键使用 `on_delete=models.CASCADE` 或 `SET_NULL`
- 添加适当的索引（`db_index=True`）
- 字段命名使用下划线命名法

### 前端规范
- 使用 Tailwind CSS 样式
- 遵循 Django 模板最佳实践
- 表单使用 CSRF 保护
- 实现响应式设计

### 测试要求
- 每个模型编写单元测试
- 每个视图编写集成测试
- 测试覆盖率 > 80%

---

## 下一步行动

1. ✅ 删除无用的 Spring Boot + React 技术栈 ✓
2. ✅ 更新 CLAUDE.md 文档 ✓
3. ⏭️ 开始实施第一阶段：报价单管理
4. ⏭️ 逐步完成其他模块

---

**文档版本**: v1.0
**创建日期**: 2025-11-05
**最后更新**: 2025-11-05
