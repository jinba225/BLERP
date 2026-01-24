# 自定义打印表格字段指南

## 📋 当前表格字段

更新后的表格现在包含以下列：

| 列名 | 字段 | 宽度 | 对齐 | 说明 |
|------|------|------|------|------|
| 序号 | (自动编号) | 40px | 居中 | 自动生成 1, 2, 3... |
| 产品编码 | `product_code` | 100px | 左对齐 | 产品SKU/编码 |
| 产品名称 | `product_name` | 自适应 | 左对齐 | 产品完整名称 |
| 数量 | `quantity` | 60px | 右对齐 | 订购数量 |
| 单价 | `unit_price` | 80px | 右对齐 | 单个产品价格 |
| **折扣率** | `discount_rate` | 60px | 居中 | 显示为百分比 |
| 小计 | `subtotal` | 90px | 右对齐 | **加粗显示** |
| **交货期** | `lead_time` | 80px | 居中 | 预计交货时间 |

### 新增功能
- ✅ **合计行**：自动计算所有明细的总金额，显示为红色粗体
- ✅ **更紧凑的布局**：字体从 12px 缩小到 11px，适应更多列
- ✅ **默认值处理**：空值显示为 '-' 或 '0'

## 🎨 如何自定义字段

### 文件位置
`templates/sales/quote_print_hiprint.html` - `generateItemsTable()` 函数

### 添加新列

#### 步骤 1: 修改表头

在第 439-448 行附近，添加新的 `<th>` 标签：

```javascript
// 表头 - 可根据需要调整列
html += '<thead><tr>';
html += '<th style="' + thStyle + ' width: 40px;">序号</th>';
html += '<th style="' + thStyle + ' width: 100px;">产品编码</th>';
html += '<th style="' + thStyle + '">产品名称</th>';
html += '<th style="' + thStyle + ' width: 60px;">数量</th>';
html += '<th style="' + thStyle + ' width: 80px;">单价</th>';
html += '<th style="' + thStyle + ' width: 60px;">折扣率</th>';
html += '<th style="' + thStyle + ' width: 90px;">小计</th>';
html += '<th style="' + thStyle + ' width: 80px;">交货期</th>';

// 🆕 添加新列 - 例如"备注"
html += '<th style="' + thStyle + ' width: 150px;">备注</th>';

html += '</tr></thead>';
```

#### 步骤 2: 修改表体

在第 452-463 行附近，添加对应的 `<td>` 标签：

```javascript
items.forEach(function(item, index) {
    html += '<tr>';
    html += '<td style="' + tdStyle + ' text-align: center;">' + (index + 1) + '</td>';
    html += '<td style="' + tdStyle + '">' + (item.product_code || '') + '</td>';
    html += '<td style="' + tdStyle + '">' + (item.product_name || '') + '</td>';
    html += '<td style="' + tdStyle + ' text-align: right;">' + (item.quantity || '0') + '</td>';
    html += '<td style="' + tdStyle + ' text-align: right;">' + (item.unit_price || '0.00') + '</td>';
    html += '<td style="' + tdStyle + ' text-align: center;">' + (item.discount_rate ? item.discount_rate + '%' : '-') + '</td>';
    html += '<td style="' + tdStyle + ' text-align: right; font-weight: bold;">' + (item.subtotal || '0.00') + '</td>';
    html += '<td style="' + tdStyle + ' text-align: center;">' + (item.lead_time || '-') + '</td>';

    // 🆕 添加备注列
    html += '<td style="' + tdStyle + ' font-size: 10px;">' + (item.notes || '') + '</td>';

    html += '</tr>';
});
```

#### 步骤 3: 调整合计行（如果需要）

在第 467-480 行附近，调整 `colspan` 以匹配新的列数：

```javascript
// 如果增加了1列，需要将 colspan="6" 改为 colspan="7"
html += '<td colspan="7" style="' + tdStyle + ' text-align: right;">合计：</td>';
```

### 删除列

只需：
1. 删除表头中对应的 `<th>` 标签
2. 删除表体中对应的 `<td>` 标签
3. 调整合计行的 `colspan` 值

### 调整列宽

修改 `width` 属性：

```javascript
// 窄列
html += '<th style="' + thStyle + ' width: 50px;">序号</th>';

// 中等列
html += '<th style="' + thStyle + ' width: 120px;">产品编码</th>';

// 宽列
html += '<th style="' + thStyle + ' width: 200px;">备注</th>';

// 自适应宽度（不设置 width）
html += '<th style="' + thStyle + '">产品名称</th>';
```

## 📊 可用的数据字段

报价单明细项（`item`）包含以下字段：

```javascript
{
    index: 1,                    // 序号（自动生成）
    product_code: 'BL-001',     // 产品编码
    product_name: '激光器A',     // 产品名称
    quantity: '10',             // 数量
    unit_price: '1000.00',      // 单价
    discount_rate: '5',         // 折扣率（百分比）
    subtotal: '9500.00',        // 小计
    lead_time: '30天',          // 交货期
    notes: '特殊要求...'         // 备注
}
```

### 访问字段

```javascript
item.product_code    // 直接访问
item.notes || ''     // 带默认值（空字符串）
item.quantity || '0' // 带默认值（0）
```

## 🎨 样式自定义

### 改变字体大小

```javascript
var tableStyle = `
    font-size: 12px;  // 改为 10px, 11px, 12px, 13px 等
`;
```

### 改变边框样式

```javascript
var thStyle = `
    border: 2px solid #000;  // 粗边框
    border: 1px dashed #ccc; // 虚线边框
    border: none;            // 无边框
`;
```

### 改变表头背景色

```javascript
var thStyle = `
    background: #3b82f6;  // 蓝色
    background: #10b981;  // 绿色
    background: #f3f4f6;  // 灰色（当前）
    color: white;         // 白色文字
`;
```

### 斑马纹效果

修改表体循环：

```javascript
items.forEach(function(item, index) {
    var rowStyle = index % 2 === 0 ? 'background: #f9fafb;' : '';
    html += '<tr style="' + rowStyle + '">';
    // ... 单元格内容
    html += '</tr>';
});
```

## 💡 常见自定义场景

### 1. 添加"规格型号"列

```javascript
// 表头
html += '<th style="' + thStyle + ' width: 120px;">规格型号</th>';

// 表体（假设数据字段为 specification）
html += '<td style="' + tdStyle + '">' + (item.specification || '-') + '</td>';
```

### 2. 添加"单位"列

```javascript
// 表头
html += '<th style="' + thStyle + ' width: 50px;">单位</th>';

// 表体（假设数据字段为 unit）
html += '<td style="' + tdStyle + ' text-align: center;">' + (item.unit || '个') + '</td>';
```

### 3. 合并"数量"和"单位"

```javascript
// 表头
html += '<th style="' + thStyle + ' width: 80px;">数量/单位</th>';

// 表体
html += '<td style="' + tdStyle + ' text-align: center;">' +
        (item.quantity || '0') + ' ' + (item.unit || '个') +
        '</td>';
```

### 4. 高亮显示金额

```javascript
// 小计列加颜色
html += '<td style="' + tdStyle + ' text-align: right; font-weight: bold; color: #ef4444;">' +
        (item.subtotal || '0.00') +
        '</td>';
```

### 5. 添加图标

```javascript
// 需要确保 Font Awesome 已加载
html += '<td style="' + tdStyle + '">' +
        '<i class="fas fa-box" style="color: #9ca3af; margin-right: 4px;"></i>' +
        (item.product_name || '') +
        '</td>';
```

## 🔧 数据来源

表格数据来自打印页面的 `quoteData.items` 数组，该数组在第 266-280 行定义：

```javascript
items: [
    {% for item in items %}
    {
        index: {{ forloop.counter }},
        product_code: '{{ item.product.code }}',
        product_name: '{{ item.product.name }}',
        quantity: '{{ item.quantity }}',
        unit_price: '{{ item.unit_price }}',
        discount_rate: '{{ item.discount_rate }}',
        subtotal: '{{ item.subtotal }}',
        lead_time: '{{ item.lead_time|default:"" }}',
        notes: '{{ item.notes|default:"" }}'
    }{% if not forloop.last %},{% endif %}
    {% endfor %}
]
```

### 添加新数据字段

如果你的 Django 模型有新字段，在上面的代码中添加：

```javascript
specification: '{{ item.specification|default:"" }}',
unit: '{{ item.unit|default:"个" }}',
```

## 📐 布局建议

### A4 纸张宽度
- 可打印宽度约 **700-750px**
- 建议表格宽度 **550-650px**

### 列宽分配
- 固定列（序号、数量等）：40-80px
- 中等列（编码、单价等）：80-120px
- 宽列（名称、备注等）：自适应或 150-200px

### 字体大小
- 表头：11-12px
- 表体：10-11px
- 合计行：11-12px（加粗）

## 🧪 测试步骤

1. 修改 `generateItemsTable()` 函数
2. 保存文件
3. 刷新打印预览页面（`Ctrl + F5`）
4. 查看表格变化
5. 测试打印效果

## 📝 注意事项

⚠️ **修改后需要测试**：
- 确保列对齐正确
- 检查宽度在 A4 纸张内
- 验证空值处理
- 测试多行数据显示
- 检查打印预览效果

⚠️ **不要修改**：
- `replaceTablePlaceholders()` 函数的逻辑
- 占位符文本 "【明细表格区域】"
- 表格查找和替换的核心代码

---

**更新日期**: 2025-01-07
**版本**: v1.1 - 增强版（含折扣率、交货期、合计行）
