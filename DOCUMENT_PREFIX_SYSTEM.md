# 单号前缀配置系统

## 功能概述

系统现已支持可配置的单号前缀，参考 Odoo 标准实现。管理员可以通过后台界面修改各类单据的单号前缀，无需修改代码。

## 实现内容

### 1. 系统配置（26个单号前缀）

参考 Odoo 标准，支持以下单据类型的前缀配置：

| 配置键名 | 默认前缀 | 说明 | Odoo 标准 |
|---------|---------|------|-----------|
| document_prefix_quotation | **SQ** | 报价单 | Sales Quotation |
| document_prefix_sales_order | **SO** | 销售订单 | Sales Order |
| document_prefix_delivery | **OUT** | 发货单 | Delivery/Outbound |
| document_prefix_sales_return | SR | 销售退货 | Sales Return |
| document_prefix_purchase_request | **PR** | 采购申请 | Purchase Request |
| document_prefix_purchase_inquiry | RFQ | 采购询价 | Request for Quotation |
| document_prefix_purchase_order | **PO** | 采购订单 | Purchase Order |
| document_prefix_receipt | **IN** | 收货单/入库单 | Receipt/Inbound |
| document_prefix_purchase_return | ROUT | 采购退货 | Return Outbound |
| document_prefix_stock_in | **IN** | 库存入库 | Stock In |
| document_prefix_stock_out | **OUT** | 库存出库 | Stock Out |
| document_prefix_stock_transfer | INT | 库存调拨 | Internal Transfer |
| document_prefix_stock_picking | PICK | 库存盘点 | Picking/Inventory |
| document_prefix_stock_adjustment | ADJ | 库存调整 | Adjustment |
| document_prefix_quality_inspection | QC | 质检单 | Quality Control |
| document_prefix_sales_contract | SC | 销售合同 | Sales Contract |
| document_prefix_purchase_contract | PC | 采购合同 | Purchase Contract |
| document_prefix_loan_contract | LC | 借用合同 | Loan Contract |
| document_prefix_production_plan | PP | 生产计划 | Production Plan |
| document_prefix_work_order | MO | 生产工单 | Manufacturing Order |
| document_prefix_material_requisition | MR | 领料单 | Material Requisition |
| document_prefix_material_return | MTR | 退料单 | Material Return |
| document_prefix_payment_receipt | PAY | 收款单 | Payment Receipt |
| document_prefix_payment | BILL | 付款单 | Bill Payment |
| document_prefix_invoice | INV | 发票 | Invoice |
| document_prefix_refund | RINV | 退款单 | Refund Invoice |
| document_prefix_expense | EXP | 报销单 | Expense |

**粗体标记**为用户特别要求或重点配置的前缀：SQ (报价单)、SO (销售订单)、PR (采购申请)、PO (采购订单)、IN (入库单)、OUT (出库单)

### 2. 单号格式（可配置）

**默认格式**（推荐）：
```
前缀 + YYMMDD + 3位序号

示例：
- SO251108001  (销售订单)
- PO251108001  (采购订单)
- IN251108001  (入库单)
- OUT251108001 (出库单)
```

**日期格式选项**（可通过 `document_number_date_format` 配置）：
- `YYMMDD` - 6位日期，例如：251108 (2025年11月8日) **[推荐]**
- `YYYYMMDD` - 8位日期，例如：20251108 (2025年11月8日)
- `YYMM` - 4位年月，例如：2511 (2025年11月)

**流水号位数选项**（可通过 `document_number_sequence_digits` 配置）：
- `3` - 三位流水号 001-999 **[推荐]**
- `4` - 四位流水号 0001-9999
- `5` - 五位流水号 00001-99999

**不同配置示例**：
- `SO251108001` - 前缀 + YYMMDD + 3位流水号 (默认/推荐)
- `SO20251108001` - 前缀 + YYYYMMDD + 3位流水号
- `SO2511001` - 前缀 + YYMM + 3位流水号
- `SO202511080001` - 前缀 + YYYYMMDD + 4位流水号

### 3. 向后兼容

系统完全兼容旧的前缀代码，以下用法都支持：

```python
# 新用法（推荐）- 使用配置键名
DocumentNumberGenerator.generate('sales_order')

# 旧用法（兼容）- 直接使用前缀字符串
DocumentNumberGenerator.generate('SO')
```

## 使用方法

### 初始化配置

**1. 初始化单号前缀配置**（26个前缀）

```bash
cd django_erp
python init_document_prefixes.py
```

这将创建所有26个单号前缀配置。

**2. 初始化单号格式规则配置**（日期格式 + 流水号位数）

```bash
cd django_erp
python init_document_number_rules.py
```

这将创建单号日期格式和流水号位数的配置：
- `document_number_date_format`: 默认为 `YYMMDD`
- `document_number_sequence_digits`: 默认为 `3`

### 修改单号前缀

有两种方式修改单号前缀：

#### 方式1：Django Admin 后台

1. 访问：http://localhost:8000/admin/core/systemconfig/
2. 找到要修改的前缀配置（例如：`document_prefix_sales_order`）
3. 修改 `value` 字段为新的前缀
4. 保存

#### 方式2：代码中使用

```python
from apps.core.models import SystemConfig

# 修改销售订单前缀
config = SystemConfig.objects.get(key='document_prefix_sales_order')
config.value = 'XS'  # 改为自定义前缀
config.save()
```

### 修改单号格式规则

有两种方式修改单号格式规则（日期格式和流水号位数）：

#### 方式1：Django Admin 后台

1. 访问：http://localhost:8000/admin/core/systemconfig/
2. 找到单号格式配置：
   - `document_number_date_format` - 日期格式
   - `document_number_sequence_digits` - 流水号位数
3. 修改 `value` 字段
4. 保存（修改立即生效）

**示例配置组合**：
- 默认推荐：`YYMMDD` + `3` → `SO251108001`
- 完整日期：`YYYYMMDD` + `3` → `SO20251108001`
- 年月简化：`YYMM` + `3` → `SO2511001`
- 大流水号：`YYMMDD` + `4` → `SO2511080001`

#### 方式2：代码中使用

```python
from apps.core.models import SystemConfig

# 修改日期格式
date_config = SystemConfig.objects.get(key='document_number_date_format')
date_config.value = 'YYYYMMDD'  # 改为8位日期
date_config.save()

# 修改流水号位数
seq_config = SystemConfig.objects.get(key='document_number_sequence_digits')
seq_config.value = '4'  # 改为4位流水号
seq_config.save()
```

### 代码中生成单号

```python
from apps.core.utils import DocumentNumberGenerator

# 推荐用法 - 使用配置键名
quote_number = DocumentNumberGenerator.generate('quotation')
order_number = DocumentNumberGenerator.generate('sales_order')
delivery_number = DocumentNumberGenerator.generate('delivery')

# 兼容用法 - 直接使用前缀
order_number = DocumentNumberGenerator.generate('SO')  # 仍然有效
```

## 技术实现

### 文件清单

1. **配置初始化脚本**
   - `init_document_prefixes.py` - 创建26个单号前缀配置
   - `init_document_number_rules.py` - 创建日期格式和流水号位数配置

2. **核心工具类**
   - `apps/core/utils/document_number.py` - 单号生成器
   - 新增 `get_prefix()` 方法：从系统配置获取前缀
   - 新增 `get_date_format()` 方法：从系统配置获取日期格式
   - 新增 `get_sequence_digits()` 方法：从系统配置获取流水号位数
   - 新增 `format_date()` 方法：根据配置格式化日期
   - 修改 `generate()` 方法：支持配置键名、可配置日期格式和流水号位数
   - 修改 `validate_number()` 方法：灵活验证不同格式的单号
   - 修改 `parse_number()` 方法：支持解析不同格式的单号

3. **测试脚本**
   - `test_document_prefix.py` - 测试前缀配置功能
   - `test_document_number_rules.py` - 测试日期格式和流水号位数配置

4. **后台管理**
   - `apps/core/admin.py` - SystemConfigAdmin 改进
   - 添加了 fieldsets 分组
   - 添加了 display_value 方法（高亮显示单号前缀）
   - 按 config_type 和 key 排序

5. **更新的视图文件**
   - `apps/sales/views.py` - 所有单号生成改用配置键名
   - `apps/sales/models.py` - Quote.convert_to_order() 方法

### 兼容性映射

系统维护了两个映射表：

1. **PREFIX_CONFIG_MAP**: 配置键名 → 配置 key
2. **LEGACY_PREFIX_MAP**: 旧前缀 → 配置键名

查找优先级：
1. 如果是配置键名（如 'sales_order'），直接查数据库
2. 如果是旧前缀（如 'SO'），先映射到配置键名，再查数据库
3. 如果都不是，当作自定义前缀直接使用

## 管理建议

### 修改前缀的注意事项

1. **不影响历史单据**：修改前缀只影响新创建的单据，历史单据编号保持不变

2. **避免重复**：确保新前缀与其他单据类型不重复

3. **简短明确**：建议使用 2-4 个字母，便于识别

4. **大写规范**：建议使用大写字母，与国际惯例一致

### 修改格式规则的注意事项

1. **配置立即生效**：修改日期格式或流水号位数后，下一个生成的单号立即采用新规则

2. **历史单据不变**：修改配置只影响新创建的单据，历史单据编号保持不变

3. **同一天不同格式**：如果在同一天内修改了日期格式，新旧格式的单号流水号独立计数

4. **推荐配置**：
   - 日期格式：`YYMMDD` (简洁明了，适合大多数场景)
   - 流水号位数：`3` (支持每天999个单号，满足绝大多数需求)

### 常用前缀参考（Odoo 标准）

- **销售相关**：QT, SO, OUT, SR
- **采购相关**：RFQ, PO, IN, ROUT
- **库存相关**：IN, OUT, INT, PICK, ADJ
- **生产相关**：PP, MO, MR, MTR
- **财务相关**：PAY, BILL, INV, RINV, EXP

## 测试验证

### 测试前缀配置

```bash
cd django_erp
python test_document_prefix.py
```

```python
# 测试前缀获取
from apps.core.utils import DocumentNumberGenerator

# 测试新用法
prefix = DocumentNumberGenerator.get_prefix('sales_order')
print(prefix)  # 输出: SO

# 测试旧用法兼容性
prefix = DocumentNumberGenerator.get_prefix('SO')
print(prefix)  # 输出: SO

# 测试单号生成
number = DocumentNumberGenerator.generate('sales_order')
print(number)  # 输出: SO251108001 (默认 YYMMDD + 3位)
```

### 测试格式规则配置

```bash
cd django_erp
python test_document_number_rules.py
```

这将测试：
- 默认配置 (YYMMDD + 3位流水号)
- YYYYMMDD + 4位流水号
- YYMM + 3位流水号
- 不同格式的单号解析
- 配置修改立即生效

## 未来扩展

可以在此基础上扩展更多功能：

1. **分公司前缀**：支持多公司环境下的前缀区分
2. **前缀模板**：支持更复杂的单号模板，如 {PREFIX}-{YEAR}-{MONTH}-{SEQ}
3. **自定义分隔符**：支持在前缀、日期、流水号之间添加分隔符（如 SO-251108-001）
4. **重置规则**：支持按年、按月、按日自动重置流水号（当前按日重置）

## 总结

本次实现完成了：

✅ 26个单号前缀的系统配置
✅ 单号日期格式可配置（YYYYMMDD/YYMMDD/YYMM）
✅ 单号流水号位数可配置（3/4/5位）
✅ 单号生成器支持从配置读取前缀和格式规则
✅ 后台管理界面优化
✅ 完全向后兼容旧代码
✅ 参考 Odoo 标准设置默认前缀
✅ 支持用户自定义修改
✅ 配置修改立即生效
✅ 完整的测试验证

**默认单号格式**：`前缀 + YYMMDD + 3位流水号`
**示例**：`SO251108001` (SO + 251108 + 001)

系统现在完全支持可配置的单号前缀和格式规则，与 Odoo 标准对齐。管理员可以随时通过后台修改配置，无需修改任何代码。
