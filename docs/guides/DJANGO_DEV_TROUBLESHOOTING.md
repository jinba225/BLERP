# Django 开发问题解决方案

## 问题1: 为什么每次更改都要重启服务器？

### 根本原因

Django的 `DEBUG` 设置默认为 `False`，导致模板被缓存。

### ✅ 解决方案

#### 方案A: 启用DEBUG模式（推荐开发环境使用）

**检查配置文件**:
```bash
# 查看当前DEBUG设置
grep -n "DEBUG" django_erp/settings.py
```

**临时启用**（仅用于开发）:
```bash
# 启动服务器时显式设置DEBUG
python manage.py runserver --settings=django_erp.settings --debug
```

**永久启用**（在 `.env` 文件中）:
```bash
# 在项目根目录创建或编辑 .env 文件
echo "DEBUG=True" >> .env
```

#### 方案B: 清除模板缓存（如果必须保持DEBUG=False）

```bash
# 查找并删除Python缓存文件
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
```

#### 方案C: 使用开发服务器自动重载

```bash
# Django开发服务器默认会检测文件变化并自动重载
python manage.py runserver

# 但某些情况下需要手动重启
# Ctrl+C 停止服务器，然后重新运行
```

---

## 问题2: 为什么经常出现模板错误？

### 常见原因

1. **模板语法错误** - 标签不匹配或拼写错误
2. **CSS冲突** - Bootstrap vs Tailwind CSS类冲突
3. **模板继承问题** - block/endblock不匹配
4. **静态文件未加载** - CSS/JS文件路径错误

### ✅ 解决方案

#### 1. 使用模板验证命令

```bash
# 检查模板语法
python manage.py check --deploy  # 包含模板检查
```

#### 2. 验证模板结构

确保block标签正确匹配：
```django
{% extends "layouts/base.html" %}

{% block extra_css %}
<style>
/* 自定义CSS */
</style>
{% endblock %}  <!-- ✅ 正确：每个block都有对应的endblock -->

{% block content %}
<!-- 内容 -->
{% endblock %}

{% block extra_js %}
<script>
/* JavaScript */
</script>
{% endblock %}
```

#### 3. 避免CSS框架冲突

本项目使用 **Tailwind CSS**，避免混用Bootstrap类：

```html
<!-- ✅ 正确：使用Tailwind -->
<div class="bg-white p-6 shadow">
  <h2 class="text-xl font-bold">标题</h2>
</div>

<!-- ❌ 错误：混用Bootstrap -->
<div class="container card">
  <h2 class="text-xl">标题</h2>
</div>
```

#### 4. 内联关键样式（推荐）

对于关键样式，直接使用内联style：

```html
<div style="background: white; padding: 1.5rem; border-radius: 0.5rem;">
  <!-- 内容 -->
</div>
```

---

## 🚀 推荐的开发工作流

### 1. 启动开发服务器

```bash
# 方式1: 使用DEBUG模式（推荐）
python manage.py runserver 0.0.0.0:8000

# 方式2: 显式启用DEBUG
DEBUG=True python manage.py runserver
```

### 2. 修改模板文件

```bash
# 编辑模板
vim templates/index.html

# 保存后，Django会自动重载（DEBUG=True时）
# 如果没有自动重载，手动重启服务器：
# Ctrl+C → 重新运行上面的命令
```

### 3. 验证更改

```bash
# 访问浏览器，刷新页面
# 使用 Ctrl+Shift+R 强制刷新（清除缓存）
open http://127.0.0.1:8000/
```

---

## 🛠️ 常用调试技巧

### 查看Django日志

```bash
# 查看详细错误信息
python manage.py runserver --verbosity=2
```

### 验证模板语法

```bash
# Django模板调试
python manage.py check

# 包含模板检查
python manage.py check --deploy
```

### 浏览器调试

1. **打开开发者工具**: F12
2. **查看Network标签**: 检查静态文件是否加载
3. **查看Console标签**: 查看JavaScript错误
4. **强制刷新**: Ctrl+Shift+R (Chrome/Firefox)

---

## 📝 模板开发最佳实践

### 1. 渐进式开发

```bash
# 步骤1: 先创建最简单的版本
# 步骤2: 逐步添加功能
# 步骤3: 每次修改后立即测试
```

### 2. 使用模板注释

```django
{# 这是统计卡片 #}
<div class="stat-card">
  <!-- 内容 -->
</div>
```

### 3. 保持模板简洁

```django
<!-- ✅ 好：内联关键样式 -->
<div style="background: white; padding: 1rem;">
  内容
</div>

<!-- ❌ 避免：复杂的嵌套和过多的模板继承 -->
{% if condition %}
  {% if another_condition %}
    {% if yet_another %}
      <!-- 太多嵌套 -->
    {% endif %}
  {% endif %}
{% endif %}
```

### 4. 验证HTML结构

```bash
# 在线HTML验证器
# https://validator.w3.org/

# 或使用浏览器扩展
# HTML Validator Extension
```

---

## 🔍 快速问题诊断

### 问题：修改后没反应

**检查清单**:
1. ✅ 确认保存了文件
2. ✅ 确认DEBUG=True
3. ✅ 查看终端是否有重载信息
4. ✅ 浏览器强制刷新 (Ctrl+Shift+R)
5. ✅ 清除浏览器缓存

### 问题：出现模板错误

**检查清单**:
1. ✅ 运行 `python manage.py check`
2. ✅ 检查block/endblock是否配对
3. ✅ 检查模板继承路径
4. ✅ 查看完整的错误信息

### 问题：样式不生效

**检查清单**:
1. ✅ 确认CSS框架一致（只用Tailwind）
2. ✅ 检查静态文件路径
3. ✅ 使用浏览器开发者工具检查元素
4. ✅ 查看Network标签确认CSS加载

---

## 📚 相关文档

- [Django模板语言](https://docs.djangoproject.com/en/5.0/ref/templates/language/)
- [Django静态文件管理](https://docs.djangoproject.com/en/5.0/howto/static-files/)
- [Tailwind CSS文档](https://tailwindcss.com/docs)

---

**最后更新**: 2026年2月5日
**适用版本**: Django 5.0+ / Python 3.13+
