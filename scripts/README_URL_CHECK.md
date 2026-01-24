# Django URL 一致性检查工具

## 功能说明

此脚本用于检查 Django 项目中模板文件使用的 URL name 是否与 `urls.py` 中定义的一致。

## 使用方法

```bash
# 在项目根目录下运行
python scripts/check_url_consistency.py
```

## 检查内容

### 1. 扫描范围

**URL 定义提取**:
- 扫描 `apps/` 目录下所有模块的 `urls.py` 文件
- 提取所有定义的 URL name（包括 namespace）
- 支持嵌套的 include() 和 app_name

**模板文件扫描**:
- 扫描 `templates/` 目录下所有 `.html` 文件
- 提取所有 `{% url %}` 标签中使用的 URL name

### 2. 检查项

1. **未定义的 URL（严重错误）**
   - 模板中引用了但在 `urls.py` 中未定义的 URL name
   - 这会导致模板渲染时出现 `NoReverseMatch` 错误
   - 脚本会提供可能的正确名称建议

2. **未使用的 URL（警告）**
   - 在 `urls.py` 中定义了但模板中未使用的 URL name
   - 这些 URL 可能在以下场景中使用：
     - Python 代码中的重定向（`redirect()`）
     - JavaScript 代码中的 AJAX 调用
     - 第三方集成
   - 如果确实不需要，可以考虑移除以简化 URL 配置

## 输出报告

### 控制台输出

脚本会在控制台输出详细的检查报告，包括：

1. **统计信息**
   - 定义的 URL 总数
   - 模板中使用的 URL 数量
   - 未定义的 URL 数量
   - 未使用的 URL 数量

2. **问题详情**
   - 未定义的 URL 及其引用位置（文件路径和行号）
   - 建议的正确名称（如果可以推断）
   - 未使用的 URL 列表

3. **总结**
   - 检查结果总结

### JSON 报告文件

脚本会生成 `url_consistency_report.json` 文件，包含：

```json
{
  "summary": {
    "total_defined": 771,
    "total_used": 272,
    "undefined_count": 0,
    "unused_count": 69
  },
  "undefined_urls": [
    {
      "name": "错误的URL名称",
      "references": [
        {
          "file": "模板文件相对路径",
          "line": 行号
        }
      ]
    }
  ],
  "unused_urls": [
    {
      "name": "未使用的URL名称",
      "pattern": "URL模式"
    }
  ]
}
```

## 检查结果解读

### ✅ 所有 URL 一致

如果输出显示 `✅ 所有模板中引用的 URL 都已正确定义`，说明：
- 模板中使用的所有 URL name 都在 `urls.py` 中正确定义
- 不存在会导致运行时错误的 URL 引用问题

### ❌ 发现未定义的 URL

如果输出显示 `❌ 模板中引用但未定义的 URL`，需要：
1. 查看具体的文件和行号
2. 检查引用的 URL name 是否正确
3. 确认是否缺少 namespace（例如：`'order_list'` 应该是 `'sales:order_list'`）
4. 在相应的 `urls.py` 文件中添加缺失的 URL 定义

### ⚠️ 发现未使用的 URL

如果显示 `⚠️ 定义了但模板中未使用的 URL`，这通常是正常的，因为：
- API URL 可能只在 JavaScript 或后端代码中使用
- 某些 URL 可能用于后台任务或第三方集成
- 确认不需要后再考虑删除

## 常见问题

### 1. 命名空间问题

**问题**: 模板中使用 `'order_list'`，但实际需要 `'sales:order_list'`

**解决**:
- 检查应用的 `urls.py` 中是否定义了 `app_name = 'sales'`
- 在模板中使用完整的 namespace:name 格式

### 2. 拼写错误

**问题**: URL name 拼写错误

**解决**:
- 查看脚本提供的建议
- 修正模板中的 URL name 拼写

### 3. 动态 URL 参数

**问题**: 使用带参数的 URL（如 `{% url 'sales:order_detail' order.pk %}`）

**说明**:
- 脚本只检查 URL name，不检查参数
- 只要 URL name 正确即可，参数在运行时传递

## 技术实现

### URL 提取机制

1. **Django Resolver 方法**（首选）
   - 使用 `django.urls.get_resolver()` 获取 URL 配置
   - 递归遍历所有 URLPattern 和 URLResolver
   - 自动处理 namespace 和嵌套的 include

2. **文件解析方法**（备用）
   - 直接解析 `urls.py` 文件内容
   - 使用正则表达式提取 `path()` 中的 `name` 参数
   - 适用于 Django 解析器无法使用的情况

### 模板解析机制

- 使用正则表达式匹配 `{% url %}` 标签
- 提取 URL name 和引用位置（文件和行号）
- 处理带引号和不带引号的 URL name

### 相似度建议

- 使用编辑距离算法查找相似的 URL name
- 检查 namespace 缺失问题
- 提供可能的正确名称建议

## 定期检查建议

建议在以下情况运行此检查：

1. **开发新功能后**
   - 确保新添加的 URL 与模板引用一致

2. **重构 URL 配置后**
   - 验证 URL 名称变更后模板是否同步更新

3. **代码审查前**
   - 作为代码审查的自动化检查步骤

4. **部署到生产环境前**
   - 避免因 URL 问题导致的页面错误

## 集成到 CI/CD

可以将此脚本集成到 CI/CD 流程中：

```yaml
# .github/workflows/django-check.yml
- name: Check URL Consistency
  run: |
    python scripts/check_url_consistency.py
    # 如果发现问题，检查退出码
```

## 扩展功能

可以根据需要扩展脚本功能：

1. **检查硬编码 URL**
   - 检测模板和代码中的硬编码 URL 路径

2. **检查重复 URL 定义**
   - 发现重复的 URL name 定义

3. **生成 URL 文档**
   - 自动生成 URL 路由文档

4. **检查权限配置**
   - 验证 URL 的权限要求是否一致

## 报告示例

以下是检查成功的示例输出：

```
======================================================================
Django URL 一致性检查工具
======================================================================
正在提取 URL 定义...
✓ 找到 771 个定义的 URL

正在扫描模板文件...
找到 237 个模板文件
✓ 从模板中提取到 272 个不同的 URL 引用

正在检查未定义的 URL...

正在检查未使用的 URL...

======================================================================
检查报告
======================================================================

📊 统计信息:
  • 定义的 URL 总数: 771
  • 模板中使用的 URL: 272
  • 未定义的 URL: 0
  • 未使用的 URL: 69

✅ 所有模板中引用的 URL 都已正确定义

======================================================================
⚠️  定义了但模板中未使用的 URL (69 个)
======================================================================
（这些 URL 可能在 Python 代码、JavaScript 或重定向中使用）

• ai_assistant:dingtalk_webhook
• ai_assistant:telegram_webhook
• ai_assistant:wechat_webhook
• authentication:change_password
...

======================================================================
✅ 检查完成：所有 URL 一致
======================================================================

📄 详细报告已保存到: url_consistency_report.json
```

## 维护和更新

如需更新或改进脚本：

1. 添加新的检查规则
2. 改进错误提示信息
3. 优化性能（处理大型项目）
4. 添加更多输出格式（HTML、Markdown）

## 联系方式

如有问题或建议，请在项目中提交 Issue。
