# Django ERP 图标使用规范

> **版本**: 1.0.0
> **更新日期**: 2025-01-20
> **维护者**: BetterLaser ERP Team

---

## 📋 概述

本项目统一使用 **Heroicons (Outline 24px)** 作为标准图标库，确保所有图标渲染正确、风格一致、永不乱码。

---

## 🎯 图标库选择

### 官方图标库
- **名称**: Heroicons
- **版本**: Outline 24px
- **官方网站**: https://heroicons.com/
- **开源协议**: MIT

### 为什么选择 Heroicons？
1. ✅ 由 Tailwind CSS 官方维护
2. ✅ 路径完整可靠，无乱码问题
3. ✅ 文档齐全，易于维护
4. ✅ 与项目技术栈完美匹配
5. ✅ 开源免费，无版权问题

---

## 📂 图标资源文件

### 1. 图标库文件
**位置**: `/static/js/heroicons-icons.js`

包含所有常用 Heroicons 图标的 SVG 代码，支持以下功能：
- `getIcon(name, sizeClass)` - 获取图标代码
- `getAllIconNames()` - 获取所有图标名称
- `getIconsByCategory()` - 按分类获取图标

### 2. 使用示例

#### 方式 A: 直接复制 SVG 代码（推荐）
```html
<!-- 从 heroicons-icons.js 复制 -->
<svg class="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
</svg>
```

#### 方式 B: 使用 JavaScript 动态生成
```javascript
// 在模板中引用
<script src="/static/js/heroicons-icons.js"></script>

// 使用函数获取图标
const userIcon = getIcon('user', 'icon');
document.getElementById('user-icon-container').innerHTML = userIcon;
```

---

## 📐 图标尺寸规范

### 尺寸分类

| 类名 | 尺寸 | 使用场景 | CSS 定义 |
|------|------|----------|----------|
| `icon-sm` | 16px × 16px | 徽章、小按钮、表单标签 | `width: 1rem; height: 1rem;` |
| `icon` | 20px × 20px | 标准图标（默认） | `width: 1.25rem; height: 1.25rem;` |
| `icon-lg` | 24px × 24px | 大按钮、重要操作 | `width: 1.5rem; height: 1.5rem;` |

### 使用示例

```html
<!-- 小图标（徽章） -->
<span class="inline-flex items-center px-2 py-1 rounded">
  <svg class="icon-sm mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
  </svg>
  已完成
</span>

<!-- 标准图标 -->
<button class="btn">
  <svg class="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
  </svg>
  新建
</button>

<!-- 大图标 -->
<div class="text-center">
  <svg class="icon-lg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
</div>
```

---

## 🎨 图标样式规范

### 标准属性配置

所有 SVG 图标必须包含以下核心属性：

```html
<svg
  class="[icon|icon-sm|icon-lg]"      <!-- 必需：尺寸类 -->
  fill="none"                         <!-- 必需：填充方式 -->
  viewBox="0 0 24 24"                 <!-- 必需：视口定义 -->
  stroke="currentColor"               <!-- 必需：描边颜色 -->
>
  <path
    stroke-linecap="round"            <!-- 必需：线条端点样式 -->
    stroke-linejoin="round"           <!-- 必需：线条连接样式 -->
    stroke-width="2"                  <!-- 必需：线条宽度 -->
    d="[完整路径数据]"                <!-- 必需：路径定义 -->
  />
</svg>
```

### 填充型图标（Solid Icons）

某些图标（如星星）使用填充而非描边：

```html
<svg
  class="icon"
  fill="currentColor"                 <!-- 注意：使用 fill 而非 stroke -->
  viewBox="0 0 24 24"
>
  <path d="[填充路径数据]" />
</svg>
```

**常用填充型图标**：
- ⭐ `star` - 星星/超级管理员
- 📁 `folder` - 文件夹（描边版也可用）

### 颜色定制

使用 Tailwind 的颜色类：

```html
<!-- 主题色 -->
<svg class="icon text-theme-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  ...
</svg>

<!-- 红色（警告、删除） -->
<svg class="icon text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  ...
</svg>

<!-- 绿色（成功、启用） -->
<svg class="icon text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  ...
</svg>
```

---

## ⚠️ 常见问题及解决方案

### 问题 1: 图标显示为乱码或残缺

**原因**：
- ❌ 路径数据不完整或错误
- ❌ 超出 viewBox 范围的坐标（如 "1211"）
- ❌ 路径字符串过长（>200字符）导致解析错误

**解决方案**：
```html
<!-- ❌ 错误：路径坐标超出范围 -->
<svg class="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  <path d="M5 1211l11-11 11 11" />
</svg>

<!-- ✅ 正确：从 heroicons-icons.js 复制标准路径 -->
<svg class="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
</svg>
```

### 问题 2: 图标大小不一致

**原因**：
- ❌ 未添加 `class="icon"` 或 `class="icon-sm"`
- ❌ 使用了不同的尺寸类

**解决方案**：
```html
<!-- ❌ 错误：缺少尺寸类 -->
<svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
  <path d="..." />
</svg>

<!-- ✅ 正确：添加标准尺寸类 -->
<svg class="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  <path d="..." />
</svg>
```

### 问题 3: 图标颜色不跟随文字

**原因**：
- ❌ 使用了硬编码颜色（如 `stroke="#000000"`）
- ❌ 缺少 `text-[color]` 类

**解决方案**：
```html
<!-- ❌ 错误：硬编码颜色 -->
<svg class="icon" fill="none" viewBox="0 0 24 24" stroke="#000000">
  <path d="..." />
</svg>

<!-- ✅ 正确：使用 currentColor -->
<svg class="icon text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  <path d="..." />
</svg>
```

### 问题 4: 使用了 emoji 替代 SVG

**原因**：
- ❌ 为了方便直接使用 emoji（👤、⭐等）

**解决方案**：
```html
<!-- ❌ 错误：使用 emoji -->
<span>👤 客户信息</span>

<!-- ✅ 正确：使用 Heroicons SVG -->
<span class="inline-flex items-center">
  <svg class="icon mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
  客户信息
</span>
```

---

## 🔧 常用图标速查表

### 用户相关
| 图标 | 代码 | 使用场景 |
|------|------|----------|
| 👤 用户 | `user` | 用户头像、用户信息 |
| 👥 用户组 | `user-group` | 团队、部门 |
| ➕ 添加用户 | `user-add` | 新建用户按钮 |
| ✅ 管理员 | `shield-check` | 管理员标识 |
| ⭐ 超级管理员 | `star` | 超级管理员标识 |

### 操作相关
| 图标 | 代码 | 使用场景 |
|------|------|----------|
| 👁️ 查看 | `eye` | 查看详情按钮 |
| ✏️ 编辑 | `pencil` | 编辑按钮 |
| 🗑️ 删除 | `trash` | 删除按钮 |
| ➕ 新建 | `plus` | 新建按钮 |
| ✔️ 确认 | `check-circle` | 成功、启用状态 |
| ❌ 取消 | `x-circle` | 错误、停用状态 |

### 导航相关
| 图标 | 代码 | 使用场景 |
|------|------|----------|
| 🏠 首页 | `home` | 首页链接 |
| ☰ 菜单 | `menu` | 汉堡菜单 |
| 📋 列表 | `view-list` | 列表视图 |
| ⊞ 网格 | `view-grid` | 网格视图 |
| ⬇️ 展开 | `chevron-down` | 下拉菜单 |
| ⬆️ 收起 | `chevron-up` | 折叠菜单 |

### 业务相关
| 图标 | 代码 | 使用场景 |
|------|------|----------|
| 🛒 采购 | `shopping-cart` | 采购订单 |
| 📦 产品 | `cube` | 产品管理 |
| 💰 金额 | `currency-yuan` | 金额、价格 |
| 📊 统计 | `chart-bar` | 报表、统计 |

### 状态相关
| 图标 | 代码 | 使用场景 |
|------|------|----------|
| ℹ️ 信息 | `information-circle` | 提示信息 |
| ⚠️ 警告 | `exclamation-circle` | 警告提示 |
| ❓ 帮助 | `question-mark-circle` | 帮助文档 |

---

## ✅ 图标使用检查清单

在添加或修改图标时，请确保：

- [ ] 从 `heroicons-icons.js` 复制标准路径
- [ ] 添加正确的尺寸类（`icon`、`icon-sm` 或 `icon-lg`）
- [ ] 保留所有必要属性（`viewBox`、`fill`、`stroke`）
- [ ] 使用 `stroke="currentColor"` 而非硬编码颜色
- [ ] 验证图标在浏览器中正确显示
- [ ] 确认图标在不同尺寸下清晰可见
- [ ] 避免使用 emoji 替代 SVG

---

## 📚 参考资源

### 官方文档
- [Heroicons 官网](https://heroicons.com/)
- [Tailwind CSS 图标最佳实践](https://tailwindcss.com/docs/adding-custom-styles#using-css-directives)

### 项目资源
- 图标库文件: `/static/js/heroicons-icons.js`
- 本文档: `/docs/icon-guidelines.md`

### 相关文档
- [项目编码规范](/docs/coding-standards.md)
- [前端组件库文档](/docs/component-library.md)

---

## 🔄 版本历史

| 版本 | 日期 | 更新内容 | 维护者 |
|------|------|----------|--------|
| 1.0.0 | 2025-01-20 | 初始版本，定义图标使用规范 | Claude |

---

## 💡 最佳实践

1. **一致性优先**：始终使用 Heroicons 图标，保持风格统一
2. **性能优化**：避免在列表中重复渲染大量复杂图标
3. **可访问性**：为图标添加 `aria-label` 属性
4. **响应式设计**：根据屏幕大小选择合适的图标尺寸
5. **定期审查**：定期检查项目中是否有不符合规范的图标

---

## 🤝 贡献指南

发现新的图标需求或改进建议？

1. 检查 `heroicons-icons.js` 是否已包含所需图标
2. 如果没有，访问 [Heroicons 官网](https://heroicons.com/) 获取标准 SVG 代码
3. 添加到 `heroicons-icons.js` 并更新本文档的速查表
4. 提交 Pull Request 并说明图标用途

---

**Happy Coding! 🎉**

如有疑问，请联系项目维护者或查阅相关文档。
