# Tom Select 使用指南

## 📋 概述

**Tom Select** 是项目中使用的增强型下拉框组件，提供智能搜索、键盘导航和流畅的用户体验。它是 Selectize.js 的轻量级分支（~16kb gzipped），具有框架无关性。

### 核心特性

- ✅ **智能搜索**：实时过滤选项，支持模糊搜索
- ✅ **键盘导航**：完整的键盘支持（方向键、Enter、Esc、Tab）
- ✅ **单选/多选**：支持单选和多选模式
- ✅ **主题适配**：完美集成 Tailwind CSS 主题系统
- ✅ **可定制**：支持自定义配置和渲染模板

---

## 🚀 快速开始

### 1. 自动初始化（推荐）

在模板中，只需给 `<select>` 元素添加 `data-tom-select` 属性：

```django
<select name="customer" data-tom-select required>
    <option value="">请选择客户</option>
    {% for customer in customers %}
    <option value="{{ customer.id }}">{{ customer.name }}</option>
    {% endfor %}
</select>
```

**优势**：页面加载时自动初始化，无需编写 JavaScript 代码。

### 2. 排除初始化

如果某些下拉框不需要使用 Tom Select，添加 `data-disable-tom-select` 属性：

```django
<select name="currency" data-disable-tom-select>
    <option value="CNY">CNY (人民币)</option>
    <option value="USD">USD (美元)</option>
</select>
```

**使用场景**：选项很少（< 5 个）的下拉框，原生 select 更合适。

### 3. 自定义配置

使用 `data-tom-select-config` 属性传递 JSON 配置：

```django
<select name="product"
        data-tom-select
        data-tom-select-config='{"placeholder": "搜索产品...", "maxOptions": 50}'>
    <option value="">请选择产品</option>
    {% for product in products %}
    <option value="{{ product.id }}">{{ product.name }}</option>
    {% endfor %}
</select>
```

---

## ⚙️ 配置选项

### 基础配置（全局默认）

项目在 `templates/base.html` 中定义了以下默认配置：

```javascript
{
    // 搜索和交互
    openOnFocus: true,           // 聚焦时打开下拉
    selectOnTab: true,           // Tab 键选择
    hideSelected: false,         // 保持已选项在下拉列表中可见

    // 数据配置
    allowEmptyOption: true,      // 允许空选项
    create: false,               // 禁止创建新选项
    maxOptions: null,            // 不限制显示的选项数量

    // 渲染模板（见下方说明）
    render: { ... }
}
```

### 常用配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `placeholder` | string | '' | 占位符文本 |
| `maxOptions` | number | null | 最多显示的选项数量 |
| `maxItems` | number | null | 最多选择的数量（1 = 单选） |
| `create` | boolean | false | 是否允许创建新选项 |
| `openOnFocus` | boolean | true | 聚焦时是否打开下拉 |
| `hideSelected` | boolean | false | 是否隐藏已选项 |
| `searchField` | array | ['text'] | 搜索字段 |

### 自定义配置示例

```django
<!-- 带占位符 -->
<select data-tom-select-config='{"placeholder": "请选择..."}'>
    ...
</select>

<!-- 限制显示数量 -->
<select data-tom-select-config='{"maxOptions": 100}'>
    ...
</select>

<!-- 多选模式 -->
<select multiple data-tom-select-config='{"maxItems": 3}'>
    ...
</select>
```

---

## 🎨 渲染模板

### 默认渲染模板

项目定义了以下渲染模板：

```javascript
render: {
    option: function(data, escape) {
        return '<div class="px-3 py-2 cursor-pointer hover:bg-gray-50">' +
               escape(data.text) +
               '</div>';
    },
    item: function(data, escape) {
        return '<div class="text-gray-900">' + escape(data.text) + '</div>';
    },
    no_results: function(data, escape) {
        return '<div class="px-3 py-2 text-gray-400 text-sm">未找到匹配项</div>';
    }
}
```

### 自定义渲染模板

如果需要自定义渲染，可以通过 `data-tom-select-config` 传递：

```django
<select data-tom-select
        data-tom-select-config='{
            "render": {
                "option": "function(data, escape) { return '<strong>' + escape(data.text) + '</strong>'; }"
            }
        }'>
    ...
</select>
```

**注意**：由于 HTML 属性限制，复杂的自定义渲染建议在 JavaScript 中手动初始化。

---

## 📝 完整示例

### 示例 1：客户选择下拉框

```django
<div class="mb-4">
    <label class="block text-sm font-medium text-gray-700 mb-2">客户 *</label>
    <select name="customer" data-tom-select class="w-full" required>
        <option value="">请选择客户</option>
        {% for customer in customers %}
        <option value="{{ customer.id }}"
                {% if form.customer.value == customer.id|stringformat:"s" %}selected{% endif %}>
            {{ customer.code }} - {{ customer.name }}
        </option>
        {% endfor %}
    </select>
</div>
```

### 示例 2：带初始值的编辑表单

```django
<div class="mb-4">
    <label class="block text-sm font-medium text-gray-700 mb-2">销售代表</label>
    <select name="sales_rep" data-tom-select class="w-full">
        <option value="">请选择</option>
        {% for user in users %}
        <option value="{{ user.id }}"
                {% if order.sales_rep_id == user.id %}selected{% endif %}>
            {{ user.get_full_name|default:user.username }}
        </option>
        {% endfor %}
    </select>
</div>
```

### 示例 3：使用 Django 表单

```python
# forms.py
from django import forms

class OrderForm(forms.ModelForm):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_approved=True),
        widget=forms.Select(attrs={
            'data-tom-select': '',  # 启用 Tom Select
            'class': 'w-full'
        })
    )
```

---

## 🔧 高级用法

### 手动初始化（特殊情况）

如果需要在 JavaScript 中手动初始化（例如动态加载的表单）：

```javascript
// 等待 DOM 加载
document.addEventListener('DOMContentLoaded', function() {
    // 初始化特定元素
    var select = document.querySelector('#my-select');
    if (select && !select.tomselect) {
        new TomSelect(select, {
            placeholder: '请选择...',
            maxOptions: 100
        });
    }
});
```

### 动态更新选项

```javascript
// 获取 Tom Select 实例
var instance = select.tomselect;

// 清空所有选项
instance.clearOptions();

// 添加新选项
instance.addOption([
    {value: '1', text: '选项 1'},
    {value: '2', text: '选项 2'}
]);

// 刷新下拉列表
instance.refreshOptions();
```

### 监听事件

```javascript
var instance = new TomSelect('#my-select', {
    onChange: function(value) {
        console.log('选择了:', value);
    },
    onDropdownOpen: function() {
        console.log('下拉框已打开');
    },
    onDropdownClose: function() {
        console.log('下拉框已关闭');
    }
});
```

---

## 🐛 常见问题

### Q1: 下拉框点击无反应？

**原因**：可能是 Tom Select 未正确初始化。

**解决方案**：
1. 检查控制台是否有 JavaScript 错误
2. 确认 CDN 资源已正确加载
3. 检查 select 元素是否有 `data-disable-tom-select` 属性

### Q2: 样式错乱或高度不对？

**原因**：CSS 样式冲突或未正确应用。

**解决方案**：
1. 确保页面已引入 Tailwind CSS
2. 检查是否有其他 CSS 规则覆盖了 Tom Select 样式
3. 尝试清除浏览器缓存

### Q3: 搜索功能不工作？

**原因**：可能是配置问题或数据格式问题。

**解决方案**：
1. 确认选项有 `value` 和 `text` 属性
2. 检查 `searchField` 配置
3. 查看控制台是否有错误信息

### Q4: 如何禁用 Tom Select？

**解决方案**：给 select 元素添加 `data-disable-tom-select` 属性。

```django
<select name="simple_choice" data-disable-tom-select>
    <option value="1">选项 1</option>
    <option value="2">选项 2</option>
</select>
```

### Q5: 动态加载的表单如何初始化？

**解决方案**：在加载完成后手动初始化。

```javascript
// 例如：通过 AJAX 加载表单后
fetch('/form-url/')
    .then(response => response.text())
    .then(html => {
        document.getElementById('form-container').innerHTML = html;
        // 手动初始化 Tom Select
        const newSelects = document.querySelectorAll('#form-container select:not(.tomselected)');
        newSelects.forEach(function(select) {
            if (!select.tomselect) {
                new TomSelect(select);
            }
        });
    });
```

---

## 📚 相关资源

### 官方文档

- **Tom Select 官网**: https://tom-select.js.org/
- **GitHub 仓库**: https://github.com/orchidjs/tom-select
- **API 文档**: https://tom-select.js.org/docs/

### 项目配置

- **初始化代码**: `templates/base.html` (第 1048-1147 行)
- **CSS 样式**: `templates/base.html` (第 190-332 行)
- **CDN 资源**:
  - CSS: https://cdn.jsdelivr.net/npm/tom-select@2.3.1/dist/css/tom-select.css
  - JS: https://cdn.jsdelivr.net/npm/tom-select@2.3.1/dist/js/tom-select.complete.min.js

### 相关文档

- **DAL 使用指南**: `/docs/DAL_USAGE_GUIDE.md`
- **前端开发规范**: `/CLAUDE.md`

---

## 🔄 版本历史

### v1.5.0 (2025-01-18) - 简化版本 ⭐

**回到原点**：移除所有自定义逻辑，使用 Tom Select 原生行为

**背景**：
- 之前尝试了多种自定义方案（CSS 隐藏、事件处理、clear/setValue 等）
- 都没有完全解决问题，反而越来越复杂
- **应该相信 Tom Select 自己的默认行为**

**最终决定**：
- ✅ 移除所有自定义 CSS 样式
- ✅ 移除所有自定义事件处理逻辑
- ✅ 移除所有自定义 render 函数
- ✅ 让 Tom Select 使用默认配置

**核心配置**：
```javascript
const baseConfig = {
    // 只保留基础配置
    hidePlaceholder: true,  // 关键！让 Tom Select 自动隐藏 placeholder
    openOnFocus: true,
    selectOnTab: true,
    hideSelected: false,
    allowEmptyOption: true,
    create: false,
    maxOptions: null

    // 移除所有自定义 render 函数
    // 移除所有自定义事件处理
};
```

**效果**：
- ✅ 使用 Tom Select 原生 placeholder 管理
- ✅ 单选模式下自动隐藏 placeholder
- ✅ 选择后只显示选中的值
- ✅ 无闪烁，无视觉干扰
- ✅ 代码简洁，易于维护

### v1.4.5 (2025-01-18)

**重大发现**：找到闪烁的真正原因并彻底解决！

**真正的问题**：
- ❌ 不是 CSS 的问题
- ❌ 不是选择器优先级的问题
- ✅ **是 `clear()` 方法导致的！**

**问题根源**：
```javascript
// v1.4.4 的代码（有问题）
baseConfig.onDropdownOpen = function() {
    // 保存原值
    originalValue = this.getValue();
    // ❌ 使用 clear() 清空值
    this.clear(false); // 这会触发 placeholder 闪烁！
}
```

**`clear()` 的问题**：
1. `clear()` 会清空当前的值
2. Tom Select 内部会临时显示 placeholder
3. 瞄间出现 placeholder 闪烁

**解决方案**：
```javascript
// v1.4.5 的代码（正确）
baseConfig.onDropdownOpen = function() {
    // 保存原值
    originalValue = this.getValue();
    // ✅ 使用 setValue() 直接设置空值
    this.setValue('', false); // 不会触发 placeholder 闪烁
}
```

**核心改进**：
1. ✅ 不再使用 `clear()` 方法
2. ✅ 使用 `setValue('', false)` 直接设置空值
3. ✅ 避免中间状态，直接设置空值
4. ✅ 没有 placeholder 闪烁

**CSS 优化**（配套改进）：
```css
/* 当有选项时：隐藏所有 input 元素（包括动态创建的） */
.ts_wrapper.single.has_items .ts_control input {
    display: none !important;
}
```

**效果**：
- ✅ 选择后完全看不到任何 placeholder
- ✅ 不会显示在选项末尾
- ✅ 无闪烁，视觉稳定
- ✅ 用户体验完美

### v1.4.4 (2025-01-18) - 最新版本 ⭐

**最终方案**：使用 `display: none` 彻底解决 placeholder 闪烁问题

**问题描述**：
- ⚠️ 选择选项后，输入框中一直有 placeholder 闪烁
- ⚠️ 提示符甚至显示在选项末尾
- ❌ 视觉干扰，用户体验极差

**尝试过的方案**：
1. ❌ `color: transparent` - 仍然闪烁
2. ❌ `opacity: 0` - 仍然占据空间，可能被聚焦
3. ❌ `visibility: hidden` - 有时还会显示，不完全可靠
4. ✅ `display: none` - **完全移除元素，彻底解决**

**最终方案**：
```css
/* 当有选项时：input 完全隐藏（包括 placeholder） */
.ts-wrapper.single.has-items .ts-control input {
    display: none !important;
}

/* 当有选项且聚焦时：显示 input，可以搜索 */
.ts-wrapper.single.has-items.focus .ts-control input {
    display: block !important;
    position: absolute !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    z-index: 10 !important;
    background: transparent !important;
}
```

**核心原理**：
- `display: none` 从 DOM 渲染树中移除元素
- 不占据任何空间，不会被意外聚焦
- 彻底解决闪烁问题

**技术对比**：
| 属性 | 效果 | 占据空间 | 可聚焦 | 会闪烁 | 推荐度 |
|------|------|---------|--------|--------|---------|
| `color: transparent` | 透明 | ✅ 是 | ✅ | ❌ 会闪烁 | ❌ 不推荐 |
| `opacity: 0` | 透明 | ✅ 是 | ✅ | ❌ 会闪烁 | ❌ 不推荐 |
| `visibility: hidden` | 隐藏 | ❌ 否 | ❌ 否 | ⚠️ 有时还会显示 | ⚠️ 可用但不完美 |
| `display: none` | 移除 | ❌ 否 | ❌ 否 | ✅ 完全不会闪烁 | ✅ **强烈推荐** |

**效果**：
- ✅ 选择后完全看不到任何 placeholder
- ✅ 不会显示在选项末尾
- ✅ 界面稳定，无任何视觉干扰
- ✅ 用户体验最佳

### v1.4.5 (2025-01-18) - 最新版本 ⭐

**重大发现**：找到闪烁的真正原因并彻底解决！

**真正的问题**：
- ❌ 不是 CSS 的问题
- ❌ 不是选择器优先级的问题
- ✅ **是 `clear()` 方法导致的！**

**问题根源**：
```javascript
// v1.4.4 的代码（有问题）
baseConfig.onDropdownOpen = function() {
    // 保存原值
    originalValue = this.getValue();
    // ❌ 使用 clear() 清空值
    this.clear(false); // 这会触发 placeholder 闪烁！
}
```

**`clear()` 的问题**：
1. `clear()` 会清空当前的值
2. Tom Select 内部会临时显示 placeholder
3. 然后重新渲染 item
4. 在这个过程中，用户会看到 placeholder 闪烁

**解决方案**：
```javascript
// v1.4.5 的代码（正确）
baseConfig.onDropdownOpen = function() {
    // 保存原值
    originalValue = this.getValue();
    // ✅ 使用 setValue() 直接设置空值
    this.setValue('', false); // 不会触发 placeholder 闪烁
}
```

**核心改进**：
1. ✅ 不再使用 `clear()` 方法
2. ✅ 使用 `setValue('', false)` 直接设置空值
3. ✅ 避免中间状态，直接设置空值
4. ✅ 没有 placeholder 闪烁

**CSS 优化**（配套改进）：
```css
/* 当有选项时：隐藏所有 input 元素（包括动态创建的） */
.ts_wrapper.single.has-items .ts-control input,
.ts-wrapper.single.has-items .ts-control > input,
.ts-wrapper.single.has-items .ts-control > * > input {
    display: none !important;
    visibility: hidden !important;
}
```

**效果**：
- ✅ 选择后完全看不到任何 placeholder
- ✅ 不会显示在选项末尾
- ✅ 无闪烁，视觉稳定
- ✅ 用户体验完美

### v1.4.3 (2025-01-18)

**关键修复**：解决选择选项后 placeholder 闪烁的问题

**问题描述**：
- ⚠️ 选择选项后，输入框中一直有 placeholder 闪烁
- ❌ 即使设置了 `color: transparent`，仍然有闪烁
- ❌ 视觉干扰，影响用户体验

**根本原因**：
- 使用 `opacity: 0` 只是让 input 透明
- 但 input 仍然占据空间，可以被聚焦
- 导致 placeholder 不稳定地显示/隐藏

**解决方案**：
1. ✅ 改用 `visibility: hidden` 完全隐藏 input
2. ✅ `visibility: hidden` 不会占据空间，真正隐藏元素
3. ✅ 聚焦时再设置为 `visibility: visible`

**核心 CSS**：
```css
/* 当有选项时：完全隐藏 input（避免 placeholder 闪烁） */
.ts-wrapper.single.has-items .ts-control input {
    visibility: hidden !important;
    position: absolute !important;
}

/* 当有选项且聚焦时：显示 input，可以搜索 */
.ts-wrapper.single.has-items.focus .ts-control input {
    visibility: visible !important;
    position: relative !important;
    width: 100% !important;
    left: 0 !important;
    z-index: 10 !important;
}
```

**技术对比**：
| 属性 | `opacity: 0` | `visibility: hidden` |
|------|---------------|-------------------|
| 效果 | 透明但占据空间 | 完全隐藏，不占据空间 |
| 可以聚焦 | ✅ | ❌ |
| 会闪烁 | ⚠️ 可能 | ❌ 不会 |
| 推荐使用 | ❌ | ✅ |

**效果**：
- ✅ 选择后完全看不到 placeholder
- ✅ 没有任何闪烁
- 界面稳定专业

### v1.4.2 (2025-01-18)

**UI 优化**：隐藏已选项的输入提示符，界面更清爽

**问题描述**：
- ⚠️ 选择选项后，仍然可以看到 placeholder 提示符
- ❌ 界面显示混乱，用户体验不好

**改进方案**：
- ✅ 当有选项时（has-items），隐藏 placeholder
- ✅ 无论是否聚焦，只要有值就隐藏提示符
- ✅ 聚焦搜索时，只显示输入框，不显示 placeholder

### v1.4.1 (2025-01-18)

**关键修复**：解决点击时有时能清除已选项，有时清除不了的问题

**问题描述**：
- ⚠️ 点击下拉框时，有时能清除已选项，有时清除不了
- ❌ 时序不稳定，用户体验不一致

**根本原因**：
- 在 `onFocus` 中清除值可能太早
- Tom Select 内部状态可能还没完全准备好
- 事件触发顺序不一致

**解决方案**：
1. ✅ 将清除逻辑移到 `onDropdownOpen` 事件
2. ✅ `onDropdownOpen` 在下拉框打开时触发，时机更准确
3. ✅ `onFocus` 只负责添加 focus 类（用于 CSS 控制）
4. ✅ 确保每次下拉框打开时都会清除已选项

### v1.4.0 (2025-01-18)

**功能增强**：点击时自动清除已选项，方便搜索

**新功能**：
- ✅ 点击已选择的下拉框时，自动清除当前值
- ✅ 下拉框显示所有可选选项
- ✅ 用户可以搜索和选择新选项
- ✅ 如果没有选择就离开，自动恢复之前的值

### v1.3.1 (2025-01-18)

**关键修复**：确保输入检索功能正常工作

**问题描述**：
- ✅ 可以下拉选择
- ❌ 不能输入检索（focus 类没有正确添加）

**解决方案**：
1. ✅ 添加 `onFocus` 事件，手动添加 `focus` 类到 wrapper
2. ✅ 添加 `onBlur` 事件，移除 `focus` 类
3. ✅ 优化 CSS 选择器，确保聚焦时 input 正确显示
4. ✅ 添加平滑过渡动画

### v1.3.0 (2025-01-18)

**重大重构**：彻底简化 Tom Select 单选模式，使用纯 CSS 解决显示问题

**设计理念**：
- 不再使用 JavaScript 手动控制显示/隐藏逻辑
- 让 Tom Select 自己处理状态管理
- 只用 CSS 控制外观和显示优先级

**核心改进**：
```javascript
// 单选模式：完全移除复杂的事件处理
if (isSingleSelect) {
    // 不再需要任何自定义事件！
    // Tom Select 会自动处理一切
}
```

**为什么这个方案更好？**
1. **CSS 控制显示**：利用 `has-items` 和 `focus` 类，Tom Select 自动管理
2. **无 JavaScript 冲突**：不依赖事件顺序，没有时序问题
3. **性能更好**：不需要 setTimeout 或手动 DOM 操作
4. **代码更少**：从 40+ 行减少到最少

### v1.2.0 (2025-01-18)

**关键修复**：彻底解决选择后不立即显示值的问题

**问题根源**：
- 事件触发顺序：`onItemAdd` → `onChange` → `onDropdownClose`
- 之前在 `onDropdownClose` 中移除 `input-active` 类，但可能与 `onChange` 冲突
- CSS 状态切换时机不对，导致 item 没有立即显示

**解决方案**：
1. ✅ 使用 `onItemAdd` 事件代替 `onChange`（更准确的时机）
2. ✅ 使用 `setTimeout(..., 0)` 确保在下一个事件循环中执行
3. ✅ 移除 `onDropdownClose` 中的逻辑，避免事件冲突
4. ✅ 优化 `onFocus` 逻辑，只在下拉未打开时进入搜索模式

**核心代码**：
```javascript
// 单选模式下的事件处理
baseConfig.onItemAdd = function(value, item) {
    // item 被添加到 DOM 后立即触发
    // 使用 setTimeout 确保在下一个事件循环中执行
    setTimeout(function() {
        var control = this.wrapper.querySelector('.ts-control');
        if (control) {
            // 移除搜索状态，让 item 显示
            control.classList.remove('input-active');
        }
    }.bind(this), 0);
};

baseConfig.onDropdownOpen = function() {
    var control = this.wrapper.querySelector('.ts-control');
    if (control) {
        control.classList.add('input-active');
        var input = control.querySelector('input');
        if (input) {
            input.focus();
        }
    }
};

baseConfig.onFocus = function() {
    var control = this.wrapper.querySelector('.ts-control');
    if (control && !this.isOpen) {
        // 只有当下拉框未打开时才进入搜索模式
        control.classList.add('input-active');
        var input = control.querySelector('input');
        if (input) {
            input.focus();
        }
    }
};
```

**效果**：
- ✅ 选择选项后**立即**显示值（无需移除焦点）
- ✅ 点击控件进入搜索模式
- ✅ 支持输入检索
- ✅ 多次选择同一选项时正常显示
- ✅ 完美支持键盘操作

### v1.1.0 (2025-01-18)

**修复内容**：
- ✅ 修复单选模式下选择选项后不显示的问题
- ✅ 优化焦点处理逻辑，确保选择后立即显示值
- ✅ 添加 `onFocus` 事件处理，支持点击进入搜索模式
- ✅ 改进事件触发顺序，解决显示延迟问题

**核心改进**：
```javascript
// 单选模式下的事件处理逻辑
onFocus: function() {
    // 点击控件时，进入搜索模式（显示 input）
    control.classList.add('input-active');
},
onDropdownOpen: function() {
    // 下拉打开时，进入搜索模式
    control.classList.add('input-active');
},
onDropdownClose: function() {
    // 下拉关闭时，退出搜索模式，显示选中的值
    control.classList.remove('input-active');
},
onChange: function(value) {
    // 值变化时，确保退出搜索模式
    control.classList.remove('input-active');
}
```

**解决的问题**：
- ❌ 选择选项后不显示，需要移除焦点才显示
- ✅ 选择后立即显示选中的值
- ✅ 点击控件可以进入搜索模式
- ✅ 支持输入检索和下拉选择两种方式
- ✅ 多次选择同一选项时正确显示值

### v1.0.0 (2025-01-18)

**重构内容**：
- ✅ 简化初始化代码（从 95 行减少到 79 行）
- ✅ 移除不必要的状态管理（currentValue, previousValue, isRestoring）
- ✅ 添加 `data-tom-select` 和 `data-disable-tom-select` 属性支持
- ✅ 添加 `data-tom-select-config` 自定义配置支持
- ✅ 优化 CSS 样式，添加清晰的注释分组
- ✅ 改进错误处理和日志输出
- ✅ 基于官方文档的最佳实践

**解决的问题**：
- 重复选择已选项时的值处理问题
- 复杂的状态管理导致的维护困难
- 缺乏灵活的配置方式

---

## ✅ 最佳实践

### 1. 何时使用 Tom Select？

**推荐使用**：
- 选项数量 > 10 个
- 需要搜索功能
- 需要更好的用户体验

**不推荐使用**（使用原生 select）：
- 选项数量 < 5 个
- 简单的是/否选择
- 性能敏感场景

### 2. 性能优化

- 限制 `maxOptions` 数量（建议 50-100）
- 避免在单个页面初始化过多 Tom Select 实例
- 对于大数据量，考虑使用虚拟滚动插件

### 3. 可访问性

- 始终提供 `<label>` 标签
- 确保 `placeholder` 或默认选项有意义
- 支持键盘导航（Tom Select 默认支持）

### 4. 代码规范

```django
<!-- ✅ 推荐 -->
<select name="customer" data-tom-select class="w-full" required>
    <option value="">请选择客户</option>
    ...
</select>

<!-- ❌ 不推荐 -->
<select name="customer" class="w-full">
    ...
</select>
```

---

**维护者**: 浮浮酱 (幽浮喵)
**最后更新**: 2025-01-18
**版本**: v1.5.0 - 简化版本

**版本说明**：回到 Tom Select 原生行为，移除所有自定义逻辑，让 Tom Select 自己处理 placeholder 显示
