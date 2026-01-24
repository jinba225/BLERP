# Font Awesome 到 Tailwind SVG 替换示例

## 示例 1：基础图标替换

### 替换前
```html
<i class="fas fa-trash"></i>
```

### 替换后
```html
<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
</svg>
```

---

## 示例 2：带 Tailwind 样式的图标

### 替换前
```html
<i class="fas fa-phone mr-1 text-gray-400"></i>
<i class="fas fa-mobile-alt mr-1 text-gray-400"></i>
<i class="fas fa-address-book text-4xl mb-4"></i>
```

### 替换后
```html
<svg class="w-5 h-5 mr-1 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
</svg>

<svg class="w-5 h-5 mr-1 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
</svg>

<svg class="text-4xl mb-4 w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
</svg>
```

---

## 示例 3：Alpine.js 动态绑定

### 替换前
```html
<i class="fas" :class="section.expanded ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
```

### 替换后
```html
<svg class="w-5 h-5 transition-transform duration-200" 
     :class="{ 'rotate-180': section.expanded }" 
     fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
</svg>
```

---

## 示例 4：Django 模板条件图标

### 替换前
```html
<i class="fas fa-{% if user.is_active %}check-circle{% else %}times-circle{% endif %} 
   text-{% if user.is_active %}green{% else %}red{% endif %}-600"></i>
```

### 替换后
```html
{% if user.is_active %}
<svg class="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
</svg>
{% else %}
<svg class="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
</svg>
{% endif %}
```

---

## 示例 5：JavaScript 动态切换

### 替换前
```html
<i id="eyeIcon" class="fas fa-eye"></i>

<script>
document.getElementById('toggleBtn').addEventListener('click', function() {
    const icon = document.getElementById('eyeIcon');
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
});
</script>
```

### 替换后
```html
<svg id="eyeIcon" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
</svg>

<script>
document.getElementById('toggleBtn').addEventListener('click', function() {
    const icon = document.getElementById('eyeIcon');
    if (input.type === 'password') {
        input.type = 'text';
        // 切换到 eye-slash 图标
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />';
    } else {
        input.type = 'password';
        // 切换回 eye 图标
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />';
    }
});
</script>
```

---

## 示例 6：JavaScript 模板字符串

### 替换前
```javascript
messageDiv.innerHTML = `
    <div class="flex items-center space-x-2">
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
    </div>
`;
```

### 替换后
```javascript
messageDiv.innerHTML = `
    <div class="flex items-center space-x-2">
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            ${type === 'success'
                ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />'
                : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />'}
        </svg>
        <span>${message}</span>
    </div>
`;
```

---

## 关键要点

### 1. 统一的 SVG 结构
所有 SVG 图标使用相同的结构：
```html
<svg class="[尺寸] [颜色] [其他Tailwind类]" 
     fill="none" 
     viewBox="0 0 24 24" 
     stroke="currentColor">
    <path stroke-linecap="round" 
          stroke-linejoin="round" 
          stroke-width="2" 
          d="[路径数据]" />
</svg>
```

### 2. 保留原有样式
- **尺寸类**：`w-4 h-4`, `w-5 h-5`, `w-6 h-6`, `text-xl` 等
- **颜色类**：`text-red-600`, `text-green-500`, `text-theme-600` 等  
- **布局类**：`mr-2`, `ml-3`, `mb-4` 等

### 3. 动态图标处理
- **切换类名** → **切换 SVG innerHTML**
- **切换类名** → **CSS transform (rotate-180)**
- **条件类名** → **条件渲染不同 SVG**

### 4. 优势
✅ 零外部依赖（不需要 Font Awesome CSS/字体文件）
✅ 更小的页面体积（SVG 比 Web Font 小）
✅ 更快的渲染速度（无需等待字体加载）
✅ 完全可定制（Tailwind CSS 类控制样式）
✅ 无 FOUC（Flash of Unstyled Content）问题

