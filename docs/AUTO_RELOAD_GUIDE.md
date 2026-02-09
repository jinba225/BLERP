# Django 自动重载完全指南

## 📋 问题概述

**问题**: 为什么修改装饰器后需要重启服务器才能生效？

**答案**: Python 的装饰器在模块导入时应用，Django 的自动重载机制不会重新应用装饰器。

---

## 🔍 Django 自动重载原理

### 默认行为

Django 开发服务器使用 `threading` 和 `importlib` 实现自动重载：

```python
# Django 内部逻辑（简化）
def check_changes():
    """检查文件变化"""
    for filename in watched_files:
        if file_changed(filename):
            restart_server()  # 重启服务器进程

def reload_module(module_name):
    """重新加载模块"""
    importlib.reload(module)
    # 但是！已应用的装饰器不会重新应用
```

### 为什么装饰器需要重启？

```python
# 文件: views.py

@decorator_a  # ← 装饰器在导入时执行
def my_view(request):
    pass

# 当你修改为：
@decorator_a
@decorator_b  # ← 添加新装饰器
def my_view(request):
    pass

# Django 自动重载只会 reload 这个模块
# 但 my_view 函数对象已经绑定到旧的装饰器链
# 新的 @decorator_b 不会被应用！
```

---

## 🛠️ 解决方案对比

### 方案 1: Django 默认重载（当前使用）

**启动方式**:
```bash
python3 manage.py runserver
```

**优点**:
- ✅ 无需安装额外依赖
- ✅ Django 内置功能
- ✅ 适合大多数情况

**缺点**:
- ❌ 装饰器修改需要重启
- ❌ URL 配置修改可能需要重启
- ❌ 设置文件修改需要重启

**自动重载范围**:
- ✅ 视图函数内部逻辑
- ✅ 模板文件
- ✅ 静态文件
- ❌ 装饰器
- ❌ 模型字段
- ❌ URL 配置（部分）

---

### 方案 2: watchfiles（推荐）

**安装**:
```bash
pip install watchfiles
```

**启动方式**:
```bash
# 方式 1: 使用 watchfiles 命令
watchfiles run python3 manage.py runserver

# 方式 2: 使用提供的脚本
./runserver.sh
```

**优点**:
- ✅ 更快的文件变化检测
- ✅ 更智能的重载策略
- ✅ 支持更多文件类型
- ✅ 跨平台兼容性好

**缺点**:
- ⚠️  仍然无法解决装饰器问题（需要完全重启）

---

### 方案 3: Django Extensions（功能丰富）

**安装**:
```bash
pip install django-extensions
```

**配置 settings.py**:
```python
INSTALLED_APPS = [
    # ...
    'django_extensions',
]
```

**启动方式**:
```bash
python3 manage.py runserver_plus
```

**优点**:
- ✅ 自动检测更多文件变化
- ✅ 增强的错误报告
- ✅ 调试工具集成
- ✅ Werkzeug 调试器

**缺点**:
- ⚠️  装饰器仍然需要重启
- ⚠️  额外的依赖

---

### 方案 4: 手动重载（最可靠）

**方法 1: 使用 shell 脚本**

创建 `dev.sh`:
```bash
#!/bin/bash
while true; do
    python3 manage.py runserver
    echo "🔄 服务器已停止，按 Ctrl+C 退出，或等待 3 秒自动重启..."
    sleep 3
done
```

**方法 2: 使用 Python 监控**

创建 `monitor.py`:
```python
import time
import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"\n🔄 检测到文件变化: {event.src_path}")
            print("🔄 正在重启服务器...")
            self.restart_server()

    def restart_server(self):
        # 这里实现重启逻辑
        pass

if __name__ == '__main__':
    observer = Observer()
    observer.schedule(RestartHandler(), path='.', recursive=True)
    observer.start()

    try:
        subprocess.run([sys.executable, 'manage.py', 'runserver'])
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

---

## 📊 各方案对比表

| 方案 | 自动重载 | 装饰器支持 | URL配置 | 设置文件 | 易用性 |
|------|---------|----------|---------|---------|--------|
| Django 默认 | ⭐⭐⭐ | ❌ | ⭐⭐ | ❌ | ⭐⭐⭐⭐⭐ |
| watchfiles | ⭐⭐⭐⭐ | ❌ | ⭐⭐⭐ | ❌ | ⭐⭐⭐⭐ |
| django-extensions | ⭐⭐⭐⭐ | ❌ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 手动脚本 | ⭐ | ✅ | ✅ | ✅ | ⭐⭐ |

---

## 🎯 实际建议

### 开发环境推荐配置

**1. 安装工具**:
```bash
pip install watchfiles
```

**2. 创建快捷启动脚本**:

我已经为您创建了 `runserver.sh`，使用：
```bash
./runserver.sh
```

**3. 对于装饰器修改**:

创建一个别名或函数：
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
alias rs='python3 manage.py runserver'
alias rsr='fuser -k 8000/tcp 2>/dev/null; python3 manage.py runserver'
```

使用：
- `rs` - 正常启动
- `rsr` - 强制重启（先杀死进程）

---

## 🔧 针对装饰器的特殊处理

### 为什么装饰器特殊？

```python
# Python 装饰器执行时机
def decorator(func):
    print("装饰器在导入时执行")
    return func

@decorator  # ← 这行在 import 时执行！
def my_function():
    pass

# 当你修改装饰器后：
# importlib.reload() 会重新执行模块代码
# 但 my_function 已经指向旧的装饰后的函数对象
```

### 解决装饰器重载的方案

**方案 1: 完全重启服务器**（当前推荐）
```bash
# Ctrl+C 停止
# 重新启动
python3 manage.py runserver
```

**方案 2: 使用装饰器工厂模式**
```python
# 不推荐这样：
@my_decorator
def view(request):
    pass

# 推荐这样：
def view(request):
    pass
view = my_decorator(view)  # 显式绑定

# 或者使用装饰器类
class DecoratorClass:
    def __init__(self, func):
        self.func = func
    def __call__(self, *args):
        return self.func(*args)

@DecoratorClass  # 类实例化在每次导入时重新创建
def view(request):
    pass
```

**方案 3: 分离装饰器逻辑**
```python
# decorators.py
def never_cache(func):
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        response['Cache-Control'] = 'no-cache'
        return response
    return wrapper

# views.py
from decorators import never_cache

@never_cache  # 修改装饰器文件后，重载 views.py 会重新导入
def borrow_list(request):
    pass
```

---

## 💡 最佳实践

### 1. 开发流程优化

```
修改代码 → 保存 → 等待自动重载 → 测试
                 ↓
              如果是装饰器/URL/设置
                 ↓
            Ctrl+C → 重启服务器 → 测试
```

### 2. 使用多个终端

```bash
# 终端 1: 运行服务器
./runserver.sh

# 终端 2: 运行其他命令
python3 manage.py shell
python3 manage.py test
# 等
```

### 3. Git hooks

创建 `.git/hooks/post-merge`:
```bash
#!/bin/bash
# 合并代码后自动提醒重启
echo "⚠️  代码已更新，建议重启服务器"
echo "运行: ./runserver.sh"
```

---

## 🚀 快速参考

### 启动服务器的各种方式

```bash
# 1. Django 默认（推荐日常使用）
python3 manage.py runserver

# 2. 指定端口
python3 manage.py runserver 8080

# 3. 监听所有地址（允许局域网访问）
python3 manage.py runserver 0.0.0.0:8000

# 4. 禁用自动重载（不推荐）
python3 manage.py runserver --noreload

# 5. 使用 watchfiles（需要先安装）
watchfiles run python3 manage.py runserver

# 6. 使用提供的脚本
./runserver.sh
```

### 判断何时需要重启

| 修改内容 | 需要重启 | 说明 |
|---------|---------|------|
| 装饰器 | ✅ | 导入时绑定 |
| 设置文件 | ✅ | 启动时读取 |
| 模型字段 | ✅ | 需要迁移 |
| URL 配置 | ⚠️  | 大部分情况需要 |
| 视图逻辑 | ❌ | 自动重载 |
| 模板 | ❌ | 自动重载 |
| 静态文件 | ❌ | 自动重载 |

---

## 📝 总结

1. **Django 默认已经有自动重载**，适合大多数情况
2. **装饰器修改必须重启**，这是 Python 的限制
3. **安装 watchfiles** 可以改善重载体验
4. **使用提供的 `runserver.sh` 脚本**简化操作
5. **记住**: 修改装饰器、设置、URL 时，重启是正常的

---

## 🎯 针对你的问题

**Q: 为什么要每次重启服务器才生效？**

A:
- 你修改了 `@never_cache` 装饰器
- 装饰器在模块导入时应用
- Django 自动重载不会重新应用装饰器
- **必须重启服务器进程**才能生效

**Q: 能不能不重启直接生效？**

A:
- **对于装饰器**: 不能，这是 Python 的限制
- **对于其他代码**: Django 默认已经自动重载了
- **最佳方案**: 使用 `./runserver.sh` + 手动重启装饰器修改

**简单记忆**: 改函数体 → 自动重载；改装饰器 → 手动重启
