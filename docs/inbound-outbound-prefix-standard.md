# 入库/出库单据前缀统一规范

## 📋 设计原则

**统一前缀，通过关联单据区分业务类型**

- ✅ 所有**入库单据**统一使用 `IN` 前缀
- ✅ 所有**出库单据**统一使用 `OUT` 前缀
- ✅ 通过单据中的 `transaction_type` 或 `reference_type` 字段区分具体业务类型

## 📦 入库单据（IN 前缀）

| 业务类型 | 单据名称 | 配置键 | 关联字段 | 说明 |
|---------|---------|--------|---------|------|
| 采购收货 | PurchaseReceipt | `document_prefix_receipt` | `reference_type='purchase_receipt'` | 采购订单收货入库 |
| 销售退货 | SalesReturn | `document_prefix_sales_return` | `reference_type='sales_return'` | 客户退货入库 |
| 生产入库 | StockIn | `document_prefix_stock_in` | `transaction_type='in'` | 生产完成入库 |
| 退料入库 | MaterialReturn | `document_prefix_material_return` | `reference_type='material_return'` | 生产退料入库 |

### 入库单据编号示例

```
IN20250115001 - 采购收货单
IN20250115002 - 销售退货单
IN20250115003 - 生产入库单
IN20250115004 - 退料单
```

**如何区分：**
```python
# 方法1：通过 reference_type 字段
if receipt.reference_type == 'purchase_receipt':
    # 这是采购收货单
elif receipt.reference_type == 'sales_return':
    # 这是销售退货单

# 方法2：通过关联对象查询
from apps.purchase.models import PurchaseReceipt
from apps.sales.models import SalesReturn

if hasattr(receipt, 'purchase_receipt'):
    # 这是采购收货单
elif hasattr(receipt, 'sales_return'):
    # 这是销售退货单
```

## 📤 出库单据（OUT 前缀）

| 业务类型 | 单据名称 | 配置键 | 关联字段 | 说明 |
|---------|---------|--------|---------|------|
| 销售发货 | Delivery | `document_prefix_delivery` | `reference_type='sales_delivery'` | 销售订单发货出库 |
| 采购退货 | PurchaseReturn | `document_prefix_purchase_return` | `reference_type='purchase_return'` | 退货给供应商 |
| 生产出库 | StockOut | `document_prefix_stock_out` | `transaction_type='out'` | 生产领料出库 |
| 领料出库 | MaterialRequisition | `document_prefix_material_requisition` | `reference_type='material_requisition'` | 生产领料单 |

### 出库单据编号示例

```
OUT20250115001 - 销售发货单
OUT20250115002 - 采购退货单
OUT20250115003 - 生产出库单
OUT20250115004 - 领料单
```

**如何区分：**
```python
# 方法1：通过 reference_type 字段
if delivery.reference_type == 'sales_delivery':
    # 这是销售发货单
elif delivery.reference_type == 'purchase_return':
    # 这是采购退货单

# 方法2：通过关联对象查询
from apps.sales.models import Delivery
from apps.purchase.models import PurchaseReturn

if hasattr(delivery, 'sales_delivery'):
    # 这是销售发货单
elif hasattr(delivery, 'purchase_return'):
    # 这是采购退货单
```

## 🔍 使用示例

### 生成入库单据编号

```python
from apps.core.utils import DocumentNumberGenerator

# 采购收货单
receipt_number = DocumentNumberGenerator.generate('receipt')
# 结果：IN20250115001

# 销售退货单
sales_return_number = DocumentNumberGenerator.generate('sales_return')
# 结果：IN20250115002
```

### 生成出库单据编号

```python
from apps.core.utils import DocumentNumberGenerator

# 销售发货单
delivery_number = DocumentNumberGenerator.generate('delivery')
# 结果：OUT20250115001

# 采购退货单
purchase_return_number = DocumentNumberGenerator.generate('purchase_return')
# 结果：OUT20250115002
```

### 查询特定类型的入库单据

```python
from apps.inventory.models import InventoryTransaction

# 查询所有采购收货入库
purchase_receipts = InventoryTransaction.objects.filter(
    transaction_type='in',
    reference_type='purchase_receipt'
)

# 查询所有销售退货入库
sales_returns = InventoryTransaction.objects.filter(
    transaction_type='in',
    reference_type='sales_return'
)

# 查询所有入库记录
all_inbound = InventoryTransaction.objects.filter(transaction_type='in')
# 然后通过 reference_type 区分具体类型
```

### 统计入库/出库总量

```python
from apps.inventory.models import InventoryTransaction
from django.db.models import Sum

# 统计总入库量
total_inbound = InventoryTransaction.objects.filter(
    transaction_type='in'
).aggregate(total_qty=Sum('quantity'))['total_qty']

# 统计总出库量
total_outbound = InventoryTransaction.objects.filter(
    transaction_type='out'
).aggregate(total_qty=Sum('quantity'))['total_qty']

# 按业务类型统计入库
inbound_by_type = InventoryTransaction.objects.filter(
    transaction_type='in'
).values('reference_type').annotate(
    total_qty=Sum('quantity')
)
```

## 📊 报表展示

在报表中展示入库/出库单据时，建议格式：

```
单据编号        | 业务类型      | 日期        | 数量
---------------|-------------|------------|------
IN20250115001  | 采购收货     | 2025-01-15 | 100
IN20250115002  | 销售退货     | 2025-01-15 | 50
OUT20250115001 | 销售发货     | 2025-01-15 | 200
OUT20250115002 | 采购退货     | 2025-01-15 | 30
```

## ⚙️ 系统配置

在数据库中配置（SystemConfig 表）：

```python
# 入库单据配置
SystemConfig.objects.create(
    key='document_prefix_receipt',
    value='IN',
    config_type='business',
    description='采购收货单前缀（入库）',
    is_active=True
)

# 出库单据配置
SystemConfig.objects.create(
    key='document_prefix_delivery',
    value='OUT',
    config_type='business',
    description='销售发货单前缀（出库）',
    is_active=True
)
```

## 🎯 设计优势

1. **简洁明了**：只需记住 IN（入库）和 OUT（出库）两个前缀
2. **易于识别**：看到单据编号就能知道是入库还是出库
3. **灵活扩展**：新增业务类型无需新增前缀，只需添加关联类型
4. **查询方便**：通过前缀快速筛选入库/出库单据
5. **报表清晰**：入库和出库一目了然

## 🔄 迁移说明

如果系统中有旧的单据使用了不同的前缀，可以运行数据迁移：

```bash
python manage.py migrate core
```

迁移脚本会自动将所有入库单据的前缀统一为 IN，所有出库单据的前缀统一为 OUT。

## 📝 注意事项

1. **兼容性**：旧的前缀（如 SR、ROUT、MR、MTR 等）仍然兼容，但新单据必须使用统一前缀
2. **配置管理**：不要修改 SystemConfig 中的统一前缀配置，除非有特殊业务需求
3. **关联字段**：创建单据时必须正确设置 `reference_type` 或 `transaction_type` 字段
4. **测试覆盖**：所有入库/出库相关测试都已更新为统一前缀

---

**文档版本**: v1.0
**创建日期**: 2025-01-15
**维护人员**: BetterLaser ERP Team
