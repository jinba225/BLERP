# HiPrint 明细数据显示问题 - 诊断指南

## 🔍 问题描述

**症状 1**：设计模板时，拖入的明细项元素显示不正确
**症状 2**：预览时明细数据不显示

---

## 📋 快速诊断步骤

### 步骤 1：清除缓存（必须！）

```
Ctrl + Shift + R (Windows)
Cmd + Shift + R (Mac)

或者：
1. F12 打开开发者工具
2. Network 标签 → 勾选 "Disable cache"
3. 刷新页面
```

### 步骤 2：打开模板编辑器并打开开发者工具

```
URL: http://127.0.0.1:8000/sales/templates/1/edit/
按 F12 打开开发者工具
切换到 Console 标签
```

### 步骤 3：检查元素提供器是否加载

在 Console 中输入：

```javascript
// 检查 QuoteElementProvider 是否存在
typeof QuoteElementProvider

// 应该显示: "function"
```

如果显示 `"undefined"`，说明元素提供器没有加载，需要检查文件路径。

### 步骤 4：检查元素库是否正常渲染

在页面左侧应该看到元素库，包含：
- 📝 基础元素
- ━ 线条元素
- ▦ 条码元素
- 🔖 基本信息
- 👤 客户信息
- 💰 金额信息
- 📋 条款信息
- 🏢 公司信息
- 📦 明细项字段 ⭐

如果看不到，在 Console 中输入：

```javascript
// 重新初始化元素提供器
initElementProvider()
```

### 步骤 5：测试拖拽明细项字段

1. 从 "📦 明细项字段" 分组中拖拽 "产品名称" 到画布
2. 观察画布上显示的内容

**预期结果**：
```
应该显示: "激光器A" （testData）
```

**如果显示错误**：
- 显示 "items.#.product_name" → testData 没有生效
- 显示空白 → 元素没有正确创建
- 显示其他内容 → 数据绑定错误

### 步骤 6：在 Console 中调试

```javascript
// 1. 检查模板对象
console.log(hiprintTemplate);

// 2. 检查画布上的元素
var json = hiprintTemplate.getJson();
console.log('元素列表:', json.panels[0].printElements);

// 3. 检查特定元素的配置
var elem = json.panels[0].printElements[0];
console.log('第一个元素:', elem);
console.log('字段名:', elem.options.field);
console.log('测试数据:', elem.options.testData);

// 4. 检查测试数据
var testData = getSampleData();
console.log('测试数据:', testData);
console.log('明细项数量:', testData.items.length);
console.log('第一条明细:', testData.items[0]);
```

### 步骤 7：测试预览功能

1. 点击工具栏的 "预览" 按钮
2. 查看 Console 日志

**预期日志**：
```javascript
✅ 预览完成
```

**如果出错**：
```javascript
❌ 可能的错误信息：
- "items is undefined"
- "Cannot read property 'length' of undefined"
- "Field not found: items.#.product_name"
```

---

## 🔧 常见问题和解决方法

### 问题 1：拖入元素后显示字段名而不是 testData

**原因**：testData 没有正确设置或 HiPrint 没有读取到

**解决方法**：

在 Console 中手动测试：

```javascript
// 创建一个测试元素
var panel = hiprintTemplate.printPanels[0];
panel.addPrintText({
    left: 100,
    top: 100,
    width: 150,
    height: 20,
    field: 'items.#.product_name',
    testData: '测试产品名称',
    title: '产品名称',
    hideTitle: true
});

// 应该在画布上看到 "测试产品名称"
```

### 问题 2：预览时明细数据不显示

**原因 1**：数据格式不正确

检查数据格式：

```javascript
var testData = getSampleData();

// 检查 items 是否是数组
console.log('items 是数组吗?', Array.isArray(testData.items));

// 检查 items 是否有数据
console.log('items 数量:', testData.items.length);

// 检查字段名是否正确
console.log('第一条明细的字段:', Object.keys(testData.items[0]));
```

**原因 2**：HiPrint 版本不支持明细项循环

检查 HiPrint 版本：

```javascript
console.log('HiPrint 版本:', hiprint.version || '未知');
```

如果版本低于 0.0.40，可能不支持 `items.#.` 语法。

**解决方法**：

尝试使用旧版语法：

```javascript
// 方案 A: 使用 hiprint 的表格元素（推荐）
// 但这需要重新设计模板

// 方案 B: 手动处理明细项（临时方案）
// 在预览时手动展开明细项
```

### 问题 3：明细项字段无法拖拽

**原因**：元素提供器注册失败

**解决方法**：

```javascript
// 1. 检查元素是否注册
console.log(hiprint.PrintElementTypeManager);

// 2. 重新初始化
initElementProvider();

// 3. 手动注册（如果上述方法无效）
var provider = new QuoteElementProvider();
hiprint.init({
    providers: [provider]
});
hiprint.PrintElementTypeManager.buildByHtml($('.ep-draggable-item'));
```

---

## 🎯 完整的调试脚本

复制以下代码到 Console 中运行：

```javascript
(function() {
    console.log('=== HiPrint 诊断开始 ===');

    // 1. 检查依赖
    console.log('1. 依赖检查:');
    console.log('  jQuery:', typeof $ !== 'undefined' ? '✅' : '❌');
    console.log('  HiPrint:', typeof hiprint !== 'undefined' ? '✅' : '❌');
    console.log('  QuoteElementProvider:', typeof QuoteElementProvider !== 'undefined' ? '✅' : '❌');

    // 2. 检查模板
    console.log('\n2. 模板检查:');
    console.log('  hiprintTemplate:', hiprintTemplate ? '✅' : '❌');
    if (hiprintTemplate) {
        var json = hiprintTemplate.getJson();
        console.log('  画布数量:', json.panels ? json.panels.length : 0);
        if (json.panels && json.panels[0]) {
            console.log('  元素数量:', json.panels[0].printElements ? json.panels[0].printElements.length : 0);

            // 检查明细项字段
            var itemFields = json.panels[0].printElements.filter(function(elem) {
                return elem.options && elem.options.field && elem.options.field.startsWith('items.#.');
            });
            console.log('  明细项字段数量:', itemFields.length);

            if (itemFields.length > 0) {
                console.log('\n  明细项字段列表:');
                itemFields.forEach(function(field, index) {
                    console.log('    ' + (index + 1) + '. ' + field.options.field +
                               ' (testData: ' + field.options.testData + ')');
                });
            }
        }
    }

    // 3. 检查测试数据
    console.log('\n3. 测试数据检查:');
    if (typeof getSampleData === 'function') {
        var testData = getSampleData();
        console.log('  getSampleData:', '✅');
        console.log('  items 是数组:', Array.isArray(testData.items) ? '✅' : '❌');
        console.log('  items 数量:', testData.items ? testData.items.length : 0);

        if (testData.items && testData.items.length > 0) {
            console.log('\n  第一条明细数据:');
            var firstItem = testData.items[0];
            Object.keys(firstItem).forEach(function(key) {
                console.log('    ' + key + ': ' + firstItem[key]);
            });
        }
    } else {
        console.log('  getSampleData: ❌ 函数未定义');
    }

    // 4. 检查元素库
    console.log('\n4. 元素库检查:');
    var $elements = $('.ep-draggable-item');
    console.log('  可拖拽元素数量:', $elements.length);

    var $itemFields = $elements.filter(function() {
        var tid = $(this).attr('tid');
        return tid && tid.indexOf('.itemField.') > -1;
    });
    console.log('  明细项字段数量:', $itemFields.length);

    console.log('\n=== HiPrint 诊断完成 ===');
    console.log('\n💡 如果发现问题，请将以上日志截图发送给开发人员');
})();
```

---

## 📸 问题报告模板

如果问题仍未解决，请提供以下信息：

### 1. 浏览器信息
- 浏览器类型和版本：_________
- 操作系统：_________

### 2. Console 日志
```
（复制完整的诊断脚本输出）
```

### 3. 截图
- [ ] 模板编辑器整体界面
- [ ] 拖入明细项字段后的效果
- [ ] 预览时的效果
- [ ] Console 中的错误信息（如果有）

### 4. 操作步骤
1. 清除缓存
2. 打开模板编辑器
3. 拖拽"产品名称"字段到画布
4. 结果：_________（描述看到的内容）
5. 点击"预览"
6. 结果：_________（描述看到的内容）

---

## 🚀 临时解决方案

如果以上方法都无效，可以使用以下临时方案：

### 方案 A：使用固定行数

不使用明细项循环，而是手动添加固定行数的字段：

```javascript
// 添加第 1 行
panel.addPrintText({ left: 50, top: 200, field: 'items[0].product_name' });

// 添加第 2 行
panel.addPrintText({ left: 50, top: 220, field: 'items[1].product_name' });

// 添加第 3 行
panel.addPrintText({ left: 50, top: 240, field: 'items[2].product_name' });
```

**缺点**：行数固定，不能自动扩展

### 方案 B：使用表格元素

使用 HiPrint 的原生表格元素（如果支持）：

```javascript
panel.addPrintTable({
    left: 50,
    top: 200,
    width: 700,
    height: 200,
    field: 'items',
    columns: [
        { title: '产品名称', field: 'product_name', width: 200 },
        { title: '数量', field: 'quantity', width: 100 },
        { title: '单价', field: 'unit_price', width: 100 }
    ]
});
```

**缺点**：需要重新设计模板

### 方案 C：后端生成 HTML 表格

在后端将明细数据渲染成 HTML 表格，然后作为一个字段传递：

```python
# views.py
items_html = render_to_string('sales/items_table.html', {'items': items})
context['items_html'] = items_html
```

```javascript
// 在模板中使用
panel.addPrintHtml({
    left: 50,
    top: 200,
    width: 700,
    height: 200,
    field: 'items_html'
});
```

---

## 📞 需要帮助？

如果以上步骤都无法解决问题，请：

1. 运行完整的诊断脚本
2. 截图所有相关界面
3. 复制 Console 日志
4. 描述详细的操作步骤和预期结果

这样可以更快地定位和解决问题。
