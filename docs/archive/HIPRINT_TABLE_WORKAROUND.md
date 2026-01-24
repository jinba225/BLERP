# HiPrint 表格元素替代方案

## 问题背景

由于 hiprint 库的 i18n 兼容性问题，表格元素（`TablePrintElement`）无法正常工作。错误信息：
```
TypeError: i18n._ is not a function
```

## 解决方案：混合渲染

使用**表格占位符 + HTML 表格**的混合渲染方案：

### 工作原理

1. **设计阶段**：在 hiprint 编辑器中拖拽"明细表格占位符"元素
2. **打印阶段**：自动将占位符替换为真实的 HTML 表格，填充实际数据

### 使用步骤

#### 1. 在模板编辑器中添加占位符

1. 进入模板编辑器：`/sales/templates/<id>/edit/`
2. 从左侧元素库找到"📊 明细表格"分类
3. 拖拽"明细表格占位符"到画布
4. 调整位置和大小
5. 点击"保存模板"

#### 2. 打印预览/打印

1. 在报价单详情页点击"打印"按钮
2. 系统会自动：
   - 渲染 hiprint 固定元素（标题、编号等）
   - 查找表格占位符
   - 用真实的 HTML 表格替换占位符
   - 填充产品明细数据

### 优势

✅ **稳定可靠**：使用传统 HTML 表格，无兼容性问题
✅ **保留设计自由度**：仍可在 hiprint 编辑器中拖拽调整位置
✅ **自动数据填充**：打印时自动获取最新的产品明细
✅ **支持任意行数**：表格自动扩展，支持任意数量的明细项

### 技术细节

#### 占位符元素定义

文件：`static/js/hiprint-provider.js`

```javascript
var tablePlaceholderElement = function () {
    return {
        tid: 'tablePlaceholder.' + Date.now(),
        title: '明细表格占位符',
        type: 'text',
        field: '__table_placeholder__',
        options: {
            width: 550,
            height: 200,
            text: '【明细表格区域】\n打印时将显示产品明细',
            backgroundColor: '#f3f4f6',
            borderStyle: 'dashed'
        }
    };
};
```

#### 替换逻辑

文件：`templates/sales/quote_print_hiprint.html`

```javascript
function replaceTablePlaceholders() {
    // 查找占位符
    var $placeholders = $('*:contains("【明细表格区域】")');

    $placeholders.each(function() {
        // 生成HTML表格
        var tableHtml = generateItemsTable(quoteData.items);

        // 替换占位符
        $(this).replaceWith(tableHtml);
    });
}
```

### 表格字段配置

当前表格包含以下列：
- 序号
- 产品编码
- 产品名称
- 数量
- 单价
- 小计

如需修改表格列，编辑 `generateItemsTable()` 函数。

### 自定义表格样式

表格样式可在 `generateItemsTable()` 函数中修改：

```javascript
var thStyle = `
    border: 1px solid #d1d5db;
    padding: 8px;
    background: #f3f4f6;
    font-weight: bold;
`;
```

### 打印输出

表格会在以下场景正确显示：
- ✅ 浏览器预览打印
- ✅ 打印到 PDF
- ✅ 打印到打印机
- ✅ 导出 PDF（如果 hiprint 支持）

### 限制和注意事项

⚠️ **占位符必须包含特定文本**："【明细表格区域】"
⚠️ **每个模板只建议使用一个表格占位符**
⚠️ **表格宽度继承占位符宽度**
⚠️ **打印预览时会自动替换，但编辑器中仍显示占位符**

### 未来改进方向

如果 hiprint 官方修复 i18n 问题，或找到解决方案，可以：
1. 恢复使用原生的 `TablePrintElement`
2. 移除占位符方案
3. 迁移现有模板

### 相关文件

- `static/js/hiprint-provider.js` - 元素定义
- `templates/sales/quote_print_hiprint.html` - 打印页面
- `templates/sales/template_editor_hiprint.html` - 编辑器

---

**创建日期**：2025-01-07
**更新日期**：2025-01-07
**状态**：✅ 可用（临时方案）
