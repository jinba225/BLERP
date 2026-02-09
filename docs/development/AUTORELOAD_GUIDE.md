# Django自动重启配置说明

## 🔄 自动重启功能

Django开发服务器支持**自动重启**功能，当您修改代码后，服务器会自动检测文件变化并重新加载，无需手动重启。

## ✅ 当前状态

### 已安装组件
- ✅ **watchdog** (6.0.0) - 文件监控库
- ✅ Django 5.0.9 - 支持自动重载

### 自动重启原理
```python
# Django 启动时自动检测并使用重载器
if watchdog_installed:
    use WatchdogReloader()  # 事件驱动，毫秒级响应
else:
    use StatReloader()        # 轮询机制，可能不稳定
```

## 🚀 使用方法

### 方法1：使用自动重启脚本（推荐）

```bash
# 运行自动重启脚本
./restart_django.sh
```

**优点：**
- 自动清理缓存
- 自动停止旧进程
- 明确的状态提示

### 方法2：手动启动（当前方式）

```bash
python3 manage.py runserver
```

## 🔍 验证自动重启是否工作

### 测试步骤：

1. **启动服务器**
   ```bash
   python3 manage.py runserver
   ```

2. **查看启动日志**
   应该看到类似这样的消息：
   ```
   Watching for file changes with...
   ```

   **如果看到 "StatReloader"** - 轮询模式（可能不稳定）
   **如果看到 "WatchdogReloader"** - 事件监控模式（推荐）✅

3. **测试自动重启**
   - 任意打开一个视图文件（如 `apps/finance/views.py`）
   - 在文件末尾添加一个空行
   - 保存文件
   - **1-2秒内**应该看到服务器重启消息：
     ```
     Detected file change: /path/to/file.py
     Restarting with file changes
     ```

## ⚠️ 如果自动重启不工作

### 可能原因和解决方案：

#### 1. watchdog未被正确使用
**检查：**
```bash
pip list | grep watchdog
```

**如果已安装但仍使用StatReloader：**
```bash
# 卸载并重新安装watchdog
pip uninstall watchdog -y
pip install watchdog
```

#### 2. Python缓存问题
**解决：**
```bash
# 清理Python缓存
find . -type d -name __pycache__ -exec rm -rf {} +
```

#### 3. IDE干扰
某些IDE的"运行"按钮可能禁用自动重载：
- **PyCharm**: 不使用IDE的运行按钮，使用终端运行 `python manage.py runserver`
- **VS Code**: 确保没有使用Django调试模式

#### 4. 静态文件变化
默认情况下，静态文件变化不会触发重启。如果需要：
```python
# 使用 --nostatic 选项可以监控静态文件
python manage.py runserver --nostatic
```

## 📊 Django重载器对比

| 特性 | StatReloader | WatchdogReloader |
|------|-------------|------------------|
| **实现方式** | 轮询文件修改时间 | 操作系统文件监控事件 |
| **检测延迟** | 约 1 秒 | 毫秒级 |
| **CPU 使用** | 持续轮询 | 事件驱动（低） |
| **macOS 兼容性** | ⚠️ 经常失效 | ✅ 稳定可靠 |
| **Linux 兼容性** | ✅ 正常 | ✅ 更好 |
| **依赖** | 无（Python 内置） | 需要 `watchdog` 库 |

## 💡 最佳实践

### 1. 推荐启动方式
```bash
# 使用脚本（推荐）
./restart_django.sh

# 或直接运行
python3 manage.py runserver
```

### 2. 验证自动重载
- 修改一个视图文件
- 添加注释或空行
- 保存文件
- 观察终端是否显示重启消息

### 3. 修改后验证
- 等待1-2秒
- 刷新浏览器（Ctrl+F5 或 Cmd+Shift+R）
- 检查修改是否生效

## 🚨 常见问题

### Q1: 修改代码后服务器没有反应
**检查清单：**
1. 查看终端是否有重启消息
2. 确认保存了文件
3. 清理Python缓存：`find . -type d -name __pycache__ -exec rm -rf {} +`
4. 重启服务器

### Q2: 重启太频繁
**解决方案：**
某些编辑器会创建临时文件，导致频繁重启。可以：
- 配置编辑器的临时目录
- 或忽略特定文件类型

### Q3: 模板文件变化不重启
**说明：**
默认情况下，模板文件变化会触发重启。如果不行：
```bash
# 使用 --nostatic 选项监控所有文件
python manage.py runserver --nostatic
```

### Q4: 静态文件变化不生效
**说明：**
静态文件（CSS/JS）变化不会触发重启，这是正常的。刷新浏览器即可。

## 🎯 当前配置

### 已安装的自动重载组件：
- ✅ Django 5.0.9
- ✅ watchdog 6.0.0

### 启动命令：
```bash
python3 manage.py runserver
```

### 预期行为：
- 修改代码 → 保存 → 1-2秒内自动重启
- 终端显示：`Restarting with file changes`
- 浏览器刷新后看到最新修改

## 📝 开发建议

1. **始终使用终端运行服务器**
   - 不要使用IDE的"运行"按钮
   - 使用 `python manage.py runserver`

2. **修改代码后保存文件**
   - 确保文件已保存
   - 等待1-2秒让服务器重启

3. **刷新浏览器**
   - 强制刷新：Ctrl+F5（Windows/Linux）
   - 强制刷新：Cmd+Shift+R（Mac）

4. **查看终端确认**
   - 应该看到 "Restarting with file changes" 消息
   - 如果没有，可能需要手动重启

## 🔧 故障排除

如果自动重启完全不工作：

```bash
# 1. 完全重装watchdog
pip uninstall watchdog -y
pip install watchdog

# 2. 清理缓存并重启
find . -type d -name __pycache__ -exec rm -rf {} +
python3 manage.py runserver

# 3. 检查启动日志
# 查看是否使用 "WatchdogReloader"
```

## 总结

自动重启功能应该已经正常工作（watchdog已安装）。如果仍然不工作，请：
1. 检查终端输出，确认使用了哪个重载器
2. 如果是 "StatReloader"，重新安装watchdog
3. 如果是 "WatchdogReloader"，但仍有问题，检查文件权限和IDE配置

正常情况下，修改代码后1-2秒内会自动重启！
