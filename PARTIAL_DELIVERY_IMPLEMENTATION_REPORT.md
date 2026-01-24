# 销售订单分批发货功能实现报告

## 实现时间
2025年11月8日

## 需求概述
根据用户要求，实现了以下两个核心功能：

1. **分批发货支持**：允许销售订单分多批次发货，精确跟踪每个产品的已发货数量和剩余待发数量
2. **可配置的自动发货单生成**：通过系统配置控制订单审核后是否自动生成发货单

## 功能实现详情

### 1. 系统配置模块

**文件**: `init_sales_config.py`

创建了系统配置项 `sales_auto_create_delivery_on_approve`：
- 配置类型：business（业务配置）
- 默认值：true（自动生成发货单）
- 可通过后台 `/admin/core/systemconfig/` 修改

**使用方法**：
```bash
python init_sales_config.py
```

### 2. 数据模型优化

**文件**: `apps/sales/models.py`

#### 发现已有字段
`SalesOrderItem` 模型中已经包含了支持分批发货的字段：
- `delivered_quantity`：已交付数量
- `remaining_quantity`（属性方法）：计算剩余待发货数量

#### 修改的方法
**`SalesOrder.approve_order()`** (lines 167-267)
- 添加了 `auto_create_delivery` 参数（可选）
- 如果参数为 None，则检查系统配置 `sales_auto_create_delivery_on_approve`
- 仅在配置为 true 时自动创建发货单
- 创建发货单时使用 `remaining_quantity` 而非 `quantity`，支持部分发货场景
- 返回值：`(delivery, customer_account)`，其中 delivery 可能为 None

### 3. 视图层实现

**文件**: `apps/sales/views.py`

#### 新增视图函数
**`delivery_create(order_pk)`** (lines 983-1070)
- 功能：从订单手动创建发货单，支持选择部分产品和数量
- 权限：需要登录
- 事务：使用 `@transaction.atomic` 确保数据一致性
- 验证：
  - 订单必须已审核
  - 必须有剩余待发货的产品
  - 发货数量不能超过剩余数量
- 特性：
  - 支持选择仓库
  - 支持选择特定产品和数量
  - 从 JSON 数据接收明细信息
  - 自动生成发货单号

**修改的视图函数**

**`order_detail(pk)`** (lines 536-559)
- 添加 `can_create_delivery` 上下文变量
- 逻辑：订单已审核 且 存在剩余待发货的产品

**`delivery_ship(pk)`** (lines 1089-1132)
- 增强发货逻辑以支持部分发货：
  - 发货时更新每个 `order_item.delivered_quantity`
  - 检查是否所有产品完全发货 (`all_items_delivered`)
  - 检查是否有产品部分发货 (`any_items_delivered`)
  - 根据发货进度更新订单状态：
    - 全部发货 → `shipped`（已发货）
    - 部分发货 → `ready_to_ship`（待发货）

### 4. URL 路由

**文件**: `apps/sales/urls.py`

添加了新路由：
```python
path('orders/<int:order_pk>/delivery/create/', views.delivery_create, name='delivery_create'),
```

### 5. 前端模板

#### 新建模板：发货单创建表单
**文件**: `templates/sales/delivery_form.html`

**特性**：
- 使用 Alpine.js 实现动态表单
- 显示订单信息和发货信息
- 动态明细表格，显示：
  - 订购数量
  - 已发货数量
  - 剩余待发数量
  - 本次发货数量（可输入）
- 客户端验证：
  - 至少选择一项产品
  - 发货数量不能超过剩余数量
- 默认预填剩余数量
- JSON 序列化提交数据

**Alpine.js 核心逻辑**：
```javascript
function deliveryForm() {
    return {
        items: [...],  // 产品明细数组
        itemsJSON: '[]',

        get totalItems() {
            return this.items.filter(item => parseFloat(item.quantity) > 0).length;
        },

        prepareSubmit(e) {
            // 验证并序列化数据
            const validItems = this.items.filter(item => parseFloat(item.quantity) > 0);
            if (validItems.length === 0) {
                e.preventDefault();
                alert('请至少选择一项产品发货');
                return false;
            }

            // 检查数量是否超过剩余
            for (let item of validItems) {
                if (parseFloat(item.quantity) > parseFloat(item.remaining_quantity)) {
                    e.preventDefault();
                    alert(`产品 ${item.product_name} 的发货数量超过剩余数量`);
                    return false;
                }
            }

            this.itemsJSON = JSON.stringify(validItems);
        }
    }
}
```

#### 修改模板：订单详情页
**文件**: `templates/sales/order_detail.html`

**修改1：添加"创建发货单"按钮** (lines 60-65)
```html
{% if can_create_delivery %}
<a href="{% url 'sales:delivery_create' order.pk %}"
   class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
    <i class="fas fa-truck mr-2"></i>创建发货单
</a>
{% endif %}
```

**修改2：订单明细表格增加发货进度列** (lines 155-199)
- 对于已审核的订单，增加两列：
  - **已发货**：显示已发货数量
  - **剩余待发**：显示剩余数量（使用颜色区分：橙色=有剩余，绿色=已全部发货）

表格结构：
```
# | 产品编码 | 产品名称 | 订购数量 | 已发货 | 剩余待发 | 单价 | 折扣率 | 行总计
```

### 6. 测试验证

**文件**: `test_partial_delivery.py`

**测试场景**：
1. **场景1**：创建订单并审核（自动生成发货单）
   - ✅ 配置为 true 时，审核后自动生成发货单
   - ✅ 发货单包含所有订单明细

2. **场景2**：撤销审核并重新审核（关闭自动生成）
   - ✅ 撤销审核正确删除相关发货单（软删除）
   - ✅ 配置为 false 时，审核后不自动生成发货单

3. **场景3**：手动创建第一批发货单（部分产品）
   - ✅ 成功创建发货单
   - ✅ 只包含选定的产品和数量

4. **场景4**：确认第一批发货并检查订单状态
   - ✅ 发货后 `delivered_quantity` 正确更新
   - ✅ `remaining_quantity` 正确计算
   - ✅ 订单状态更新为"待发货"（部分发货）

5. **场景5**：创建第二批发货单（剩余产品）
   - ✅ 成功创建第二批发货单
   - ✅ 包含所有剩余待发的产品

6. **场景6**：确认第二批发货并检查订单状态
   - ✅ 所有产品的 `remaining_quantity` 为 0
   - ✅ 订单状态更新为"已发货"（全部发货）

**测试结果**：
```
✅ 所有测试通过！分批发货功能正常工作
```

## 核心业务流程

### 流程1：订单审核自动生成发货单
```
1. 用户审核订单
2. 系统检查配置 sales_auto_create_delivery_on_approve
3. 如果配置为 true：
   - 自动创建发货单
   - 发货单包含所有订单明细
   - 数量为各产品的 remaining_quantity
4. 如果配置为 false：
   - 不创建发货单
   - 用户需手动创建
```

### 流程2：手动创建部分发货单
```
1. 用户在订单详情页点击"创建发货单"
2. 系统显示发货单创建表单
   - 列出所有有剩余数量的产品
   - 显示订购/已发货/剩余数量
3. 用户选择：
   - 仓库
   - 要发货的产品及数量
   - 发货日期和备注
4. 提交后系统验证：
   - 至少选择一项产品
   - 数量不超过剩余数量
5. 创建发货单
```

### 流程3：确认发货更新订单状态
```
1. 用户在发货单详情页点击"标记为已发货"
2. 系统更新：
   - delivery.status = 'shipped'
   - delivery.actual_date = 当前日期
   - delivery.shipped_by = 当前用户
3. 更新订单明细：
   - order_item.delivered_quantity += delivery_item.quantity
4. 检查订单发货进度：
   - 如果所有产品完全发货：order.status = 'shipped'
   - 如果部分产品发货：order.status = 'ready_to_ship'
   - 如果未发货：order.status = 'confirmed'
```

## 技术亮点

### 1. 数据完整性保护
- 使用 `@transaction.atomic` 确保发货单创建的原子性
- 软删除模式（`is_deleted`）保留历史数据
- 撤销审核时级联删除相关记录

### 2. 灵活的配置系统
- 系统配置热更新，无需重启服务
- 可通过后台界面修改，方便业务调整
- 支持审核方法级别的配置覆盖

### 3. 前端交互体验
- Alpine.js 实现轻量级响应式表单
- 实时计算统计信息
- 客户端 + 服务器端双重验证
- 颜色标识区分状态（橙色=待发货，绿色=已完成）

### 4. 精确的数量跟踪
- `delivered_quantity`：累积已发货数量
- `remaining_quantity`：动态计算剩余数量
- 支持小数精度（decimal_places=4）适应各种计量单位

## 使用说明

### 系统配置
```bash
# 初始化配置
cd django_erp
python init_sales_config.py

# 或通过后台修改
访问：http://localhost:8000/admin/core/systemconfig/
查找：sales_auto_create_delivery_on_approve
修改：value 字段为 'true' 或 'false'
```

### 分批发货操作步骤
1. 创建并审核销售订单
2. 在订单详情页点击"创建发货单"
3. 选择仓库和要发货的产品及数量
4. 提交创建发货单
5. 在发货单详情页点击"标记为已发货"
6. 重复步骤2-5直到所有产品发货完成

### 订单状态说明
- **已确认** (`confirmed`)：订单已审核，未开始发货
- **待发货** (`ready_to_ship`)：至少有一个产品已部分发货
- **已发货** (`shipped`)：所有产品已完全发货

## 相关文件清单

### 后端文件
- `init_sales_config.py` - 系统配置初始化脚本
- `apps/sales/models.py` - 数据模型（SalesOrder, SalesOrderItem, Delivery, DeliveryItem）
- `apps/sales/views.py` - 视图逻辑（order_detail, delivery_create, delivery_ship）
- `apps/sales/urls.py` - URL 路由配置

### 前端文件
- `templates/sales/delivery_form.html` - 发货单创建表单（新建）
- `templates/sales/order_detail.html` - 订单详情页（修改）

### 测试文件
- `test_partial_delivery.py` - 功能测试脚本

## 数据库影响

**无需数据库迁移**

所有必需字段已存在于数据模型中：
- `SalesOrderItem.delivered_quantity`（已存在）
- `SalesOrderItem.remaining_quantity`（计算属性，无需数据库字段）

## 已知限制和注意事项

1. **库存扣减**：当前实现未自动扣减库存，需要配合库存管理模块使用
2. **撤销发货**：已发货的发货单不支持撤销，需要通过退货流程处理
3. **并发控制**：多用户同时创建发货单时，建议在应用层加锁或使用数据库行锁
4. **权限控制**：当前仅检查登录状态，未实现细粒度权限控制

## 后续优化建议

1. **库存集成**：发货时自动扣减库存，撤销时恢复库存
2. **发货提醒**：逾期未发货的订单自动提醒
3. **批量发货**：支持一次为多个订单创建发货单
4. **发货单模板打印**：支持打印发货单和物流标签
5. **物流跟踪**：集成物流公司 API 实时跟踪物流状态

## 总结

本次实现完整地实现了销售订单分批发货功能，包括：

✅ 系统配置控制自动发货单生成
✅ 手动创建发货单，支持选择部分产品和数量
✅ 精确跟踪已发货和剩余数量
✅ 根据发货进度自动更新订单状态
✅ 完整的前后端实现
✅ 全面的测试验证

所有功能经过测试验证，可以投入生产使用。
