# AI助手配置和使用指南

本文档提供ERP AI助手系统的完整配置和使用说明。

---

## 📋 目录

1. [系统概述](#系统概述)
2. [功能特性](#功能特性)
3. [环境要求](#环境要求)
4. [快速开始](#快速开始)
5. [AI模型配置](#ai模型配置)
6. [渠道集成配置](#渠道集成配置)
7. [用户映射配置](#用户映射配置)
8. [工具权限配置](#工具权限配置)
9. [测试验证](#测试验证)
10. [故障排查](#故障排查)
11. [常见问题](#常见问题)

---

## 系统概述

ERP AI助手是一个智能对话系统，支持通过多种渠道（Telegram、微信企业号、钉钉企业应用）与用户交互，并能调用ERP系统的各种工具来完成业务操作。

### 核心组件

- **AI服务层**: 统一的AI模型调用接口，支持多种AI Provider
- **渠道集成层**: 支持Telegram、微信、钉钉等多渠道消息接收和发送
- **工具系统**: 15个内置ERP工具，支持销售、采购、库存、报表等操作
- **用户映射**: 将外部渠道用户映射到系统内部用户

---

## 功能特性

### ✅ 已实现功能

#### AI能力
- ✅ 多AI Provider支持（OpenAI、Claude、百度文心、Mock测试）
- ✅ 会话上下文管理（多轮对话）
- ✅ 工具调用（Function Calling）
- ✅ 流式对话支持
- ✅ Token使用统计

#### 渠道集成
- ✅ Telegram Bot（完整支持）
- ✅ 微信企业号（基础支持）
- ✅ 钉钉企业应用（基础支持）

#### 工具能力
- ✅ 15个内置工具：
  - 销售：客户查询、订单查询、创建报价单、订单审核
  - 采购：供应商查询、采购订单查询、创建采购申请、订单审核
  - 库存：库存查询、产品查询、低库存预警
  - 报表：销售报表、采购报表、库存报表

#### 安全特性
- ✅ Webhook签名验证
- ✅ API Key加密存储
- ✅ 三级工具权限控制（低/中/高风险）
- ✅ 操作审计日志
- ✅ 用户身份映射

### 🚧 待优化功能

- ⏳ Redis缓存（Access Token）
- ⏳ Celery异步处理
- ⏳ 消息限流
- ⏳ 群组消息支持
- ⏳ 富文本消息（图片、文件等）

---

## 环境要求

### 系统要求
- Python 3.8+
- Django 4.2+
- SQLite（开发）/ MySQL（生产）
- Redis（可选，用于缓存）

### Python依赖
```bash
# 已在requirements.txt中定义
openai==1.54.0         # OpenAI SDK
anthropic==0.39.0      # Anthropic Claude SDK
requests==2.31.0       # HTTP请求
cryptography          # API Key加密
```

---

## 快速开始

### 1. 安装依赖

```bash
# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 应用数据库迁移

```bash
python manage.py migrate
```

### 3. 创建超级用户

```bash
python manage.py createsuperuser
```

### 4. 启动开发服务器

```bash
python manage.py runserver
```

### 5. 访问Admin后台

打开浏览器访问：`http://localhost:8000/admin/`

---

## AI模型配置

### 配置位置

Admin后台 → AI助手 → AI模型配置

### 支持的Provider

#### 1. Mock Provider（测试用）

**用途**: 本地测试，无需真实API Key

**配置步骤**:
1. 在Admin后台创建新配置
2. 填写信息：
   - 配置名称：`Mock AI (测试用)`
   - 提供商：`Mock（测试用）`
   - API Key：任意值（会被忽略）
   - 模型名称：`mock-gpt-4`
   - Temperature：`0.7`
   - Max Tokens：`2000`
3. 勾选"是否默认"和"是否启用"
4. 保存

#### 2. OpenAI

**配置步骤**:
1. 获取API Key：访问 [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. 在Admin后台创建配置：
   - 配置名称：`OpenAI GPT-4`
   - 提供商：`OpenAI`
   - API Key：`sk-xxxxxxxxxxxxxxxx`（从OpenAI获取）
   - API Base：留空（使用默认）或自定义地址
   - 模型名称：`gpt-4`、`gpt-4-turbo`、`gpt-3.5-turbo`
   - Temperature：`0.7`
   - Max Tokens：`2000`
   - 超时时间：`60`秒
3. 设置优先级和默认状态
4. 保存

**注意事项**:
- API Key会被自动加密存储
- 建议在生产环境设置`ENCRYPTION_KEY`环境变量

#### 3. Anthropic Claude

**配置步骤**:
1. 获取API Key：访问 [https://console.anthropic.com/](https://console.anthropic.com/)
2. 配置信息：
   - 提供商：`Anthropic Claude`
   - API Key：`sk-ant-xxxxxxxxxxxxxxxx`
   - 模型名称：`claude-3-5-sonnet-20241022`、`claude-3-opus-20240229`
   - 其他参数同上

#### 4. 百度文心一言

**配置步骤**:
1. 获取API Key和Secret Key：访问 [百度智能云](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application)
2. 配置信息：
   - 提供商：`百度文心一言`
   - API Key：`API_KEY,SECRET_KEY`（格式：用逗号分隔）
   - 模型名称：`ernie-bot-4`、`ernie-bot-turbo`

---

## 渠道集成配置

### Telegram Bot配置

#### 步骤1: 创建Bot

1. 在Telegram中搜索 `@BotFather`
2. 发送 `/newbot` 命令
3. 按提示设置Bot名称和用户名
4. 获取Bot Token（格式：`123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`）

#### 步骤2: 配置Webhook

```bash
# 设置Webhook（替换<YOUR_BOT_TOKEN>和<YOUR_DOMAIN>）
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -d "url=https://<YOUR_DOMAIN>/ai/webhook/telegram/"

# 验证Webhook
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

**注意**:
- Webhook URL必须是HTTPS（生产环境）
- 开发环境可以使用ngrok等工具创建临时HTTPS隧道

#### 步骤3: 在Admin后台配置

Admin后台 → AI助手 → Telegram配置

- Bot Token：从@BotFather获取的Token
- Bot用户名：Bot的@username（如：@my_erp_bot）
- Webhook URL：`https://yourdomain.com/ai/webhook/telegram/`
- 允许群组：是否允许在群组中使用（默认：否）
- 命令前缀：`/`（默认）
- 是否启用：勾选

#### 步骤4: 创建用户映射

Admin后台 → AI助手 → 渠道用户映射

1. 点击"新增"
2. 填写信息：
   - 渠道：Telegram
   - 外部用户ID：Telegram Chat ID（从消息日志或Bot消息中获取）
   - 外部用户名：用户的Telegram用户名（可选）
   - 系统用户：选择对应的ERP用户
   - 是否启用：勾选
3. 保存

**如何获取Chat ID**:
1. 用户向Bot发送任意消息
2. 查看服务器日志，会显示Chat ID
3. 或访问：`https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`

---

### 微信企业号配置

#### 步骤1: 创建企业应用

1. 登录[企业微信管理后台](https://work.weixin.qq.com/)
2. 应用管理 → 自建 → 创建应用
3. 获取配置信息：
   - Corp ID：企业ID
   - Agent ID：应用AgentID
   - Secret：应用Secret

#### 步骤2: 配置接收消息

1. 在应用配置中，找到"接收消息"设置
2. 设置回调URL：`https://yourdomain.com/ai/webhook/wechat/`
3. 生成Token和EncodingAESKey（或自定义）

#### 步骤3: 在Admin后台配置

Admin后台 → AI助手 → 微信配置

- Corp ID：企业ID
- Corp Secret：应用Secret
- Agent ID：应用AgentID
- Token：自定义Token
- EncodingAESKey：自定义密钥
- 是否启用：勾选

#### 步骤4: 验证URL

企业微信会发送验证请求，服务器需要正确响应echostr。

---

### 钉钉企业应用配置

#### 步骤1: 创建企业应用

1. 登录[钉钉开放平台](https://open-dev.dingtalk.com/)
2. 创建企业内部应用
3. 获取：
   - AppKey
   - AppSecret
   - AgentID

#### 步骤2: 配置消息推送

1. 在应用配置中找到"服务器出口IP"和"消息接收"
2. 设置回调URL：`https://yourdomain.com/ai/webhook/dingtalk/`

#### 步骤3: 在Admin后台配置

Admin后台 → AI助手 → 钉钉配置

- App Key
- App Secret
- Agent ID
- 是否启用：勾选

---

## 用户映射配置

### 为什么需要用户映射？

外部渠道（Telegram、微信、钉钉）使用各自的用户标识（Chat ID、OpenID、UserID），需要映射到ERP系统的内部用户才能：
- 验证用户身份和权限
- 记录操作审计日志
- 执行需要权限的工具

### 映射配置步骤

1. **获取外部用户ID**：
   - Telegram：Chat ID（从Bot接收到的消息中获取）
   - 微信：OpenID（从企业微信回调中获取）
   - 钉钉：UserID（从钉钉回调中获取）

2. **创建映射**：
   Admin后台 → 渠道用户映射 → 新增
   - 渠道：选择Telegram/微信/钉钉
   - 外部用户ID：填写获取的ID
   - 外部用户名：用户昵称（可选）
   - 系统用户：选择对应的ERP用户
   - 元数据：JSON格式的额外信息（可选）

3. **验证映射**：
   用户发送消息后，如果映射成功，会收到AI回复；否则会提示绑定账号。

---

## 工具权限配置

### 三级风险等级

| 等级 | 说明 | 示例工具 | 是否需要审核 |
|------|------|----------|------------|
| **low** | 只读操作 | 查询客户、查询库存 | 否 |
| **medium** | 写操作（可逆） | 创建报价单、创建采购申请 | 否 |
| **high** | 高风险操作 | 审核订单、生成报表 | 可选 |

### 配置工具权限

Admin后台 → AI助手 → AI工具定义

每个工具可以配置：
- **工具名称**: 唯一标识（不可修改）
- **显示名称**: 用户友好名称
- **分类**: 销售/采购/库存/财务/报表/系统
- **描述**: 工具功能说明
- **参数定义**: JSON Schema格式
- **处理器路径**: 工具实现类的路径
- **是否需要审核**: 勾选后需要管理员批准
- **必需权限**: 执行工具所需的Django权限（可选）
- **是否启用**: 控制工具可用性

---

## 测试验证

### 1. 测试AI模型配置

```bash
python manage.py shell

from django.contrib.auth import get_user_model
from apps.ai_assistant.services import AIService

User = get_user_model()
user = User.objects.first()

# 测试AI服务
ai_service = AIService(user=user)
response = ai_service.chat(
    message="你好",
    conversation_id="test_001",
    channel="web"
)

print(response.content)
```

### 2. 测试Telegram集成

1. 找到你的Bot（搜索@your_bot_username）
2. 点击"Start"或发送 `/start`
3. 如果未绑定，会收到提示消息
4. 绑定后，发送"你好"测试
5. 测试工具调用：发送"查询库存"

### 3. 测试工具调用

```bash
python manage.py shell

from apps.ai_assistant.tools.registry import ToolRegistry
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

# 获取可用工具
tools = ToolRegistry.get_available_tools(user)
print(f"可用工具: {[t.name for t in tools]}")

# 测试单个工具
tool = ToolRegistry.get_tool('search_customer', user)
result = tool.run(keyword='测试')
print(result.to_dict())
```

---

## 故障排查

### 问题1: Webhook验证失败

**症状**: Telegram/微信/钉钉显示Webhook验证失败

**可能原因**:
- URL不可访问（检查防火墙、HTTPS）
- 签名验证失败（检查Token/Secret配置）
- 服务器响应格式错误

**解决方法**:
1. 检查服务器日志：`tail -f logs/django.log`
2. 确认URL可访问：`curl https://yourdomain.com/ai/webhook/telegram/`
3. 验证配置正确（Token、Secret等）

### 问题2: 用户收到"未绑定账号"提示

**症状**: 用户发送消息后收到"你还未绑定系统账号，请联系管理员绑定"

**原因**: 未创建用户映射

**解决方法**:
1. 查看服务器日志获取外部用户ID
2. 在Admin后台创建用户映射
3. 用户重新发送消息测试

### 问题3: AI不响应

**症状**: 消息发送成功，但AI无回复

**可能原因**:
- AI模型配置错误
- API Key无效或过期
- 网络连接问题

**解决方法**:
1. 检查AI模型配置状态（是否启用、是否默认）
2. 验证API Key有效性
3. 查看日志中的错误信息
4. 测试AI服务连接：`python manage.py shell` → 运行测试代码

### 问题4: 工具调用失败

**症状**: AI识别工具但执行失败

**可能原因**:
- 用户无相应权限
- 工具参数缺失或错误
- 数据库数据问题

**解决方法**:
1. 检查工具执行日志（Admin后台 → AI工具执行日志）
2. 查看错误信息
3. 验证用户权限
4. 检查参数是否正确

### 问题5: API Key解密失败

**症状**: 错误信息"API Key解密失败"

**原因**: 加密密钥不一致

**解决方法**:
1. 设置固定的加密密钥：
   ```bash
   # .env文件
   ENCRYPTION_KEY=<生成的密钥>
   ```

2. 生成新密钥：
   ```python
   from cryptography.fernet import Fernet
   print(Fernet.generate_key().decode())
   ```

3. 重新保存所有AI模型配置（使用新密钥加密）

---

## 常见问题

### Q: 如何切换AI模型？

A: 在Admin后台修改AI模型配置的"是否默认"和"优先级"字段。系统会选择：
1. 优先级最高的配置
2. 如果优先级相同，选择标记为"默认"的配置
3. 如果都没有，选择第一个启用的配置

### Q: 如何添加新的工具？

A:
1. 创建工具类（继承`BaseTool`）
2. 实现`execute()`和`get_parameters_schema()`方法
3. 在`tools/registry.py`中注册工具
4. 在Admin后台添加工具定义记录

### Q: 如何限制某些用户只能使用特定工具？

A:
1. 在工具定义中设置"必需权限"
2. 在Django用户/组管理中分配权限
3. 未授权用户调用工具时会被拒绝

### Q: 支持哪些消息类型？

A: 当前版本仅支持文本消息。图片、文件、语音等类型暂不支持。

### Q: 如何查看AI使用统计？

A: Admin后台 → AI模型配置，查看：
- 总请求数
- 总Token数
- 最后使用时间

### Q: 如何备份和恢复配置？

A:
```bash
# 导出配置
python manage.py dumpdata ai_assistant --indent 2 > ai_assistant_backup.json

# 导入配置
python manage.py loaddata ai_assistant_backup.json
```

---

## 性能优化建议

### 生产环境配置

1. **使用Redis缓存**（✅ 已实现）:

   **功能说明**：
   - ✅ 微信/钉钉 Access Token 自动缓存（2小时）
   - ✅ 会话数据缓存（1小时）
   - ✅ AI配置缓存（5分钟）
   - ✅ 支持本地内存缓存（开发环境）和Redis（生产环境）

   **配置步骤**：

   a. 在 `.env` 文件中添加 Redis 配置：
   ```bash
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=your_redis_password  # 可选
   ```

   b. 系统会自动启用 Redis 缓存（settings.py 已配置）

   c. 验证缓存是否工作：
   ```python
   from apps.ai_assistant.utils.cache import AIAssistantCache

   # 测试缓存
   AIAssistantCache.set('test_key', 'test_value')
   value = AIAssistantCache.get('test_key')
   print(value)  # 应输出: test_value

   # 查看缓存统计（仅Redis支持）
   stats = AIAssistantCache.get_stats()
   print(stats)
   ```

   **缓存优势**：
   - 减少对微信/钉钉服务器的API调用
   - 多进程/多实例共享 Access Token
   - 加快响应速度
   - 降低第三方API限流风险

2. **使用Celery异步处理**（✅ 已实现）:

   **功能说明**：
   - ✅ 消息异步处理（避免Webhook超时）
   - ✅ 工具异步执行（长时间运行的工具）
   - ✅ 定时任务（清理过期会话和旧日志）
   - ✅ 任务重试机制（最多3次重试）
   - ✅ 支持同步/异步灵活切换

   **配置步骤**：

   a. 在 `.env` 文件中添加 Celery 配置：
   ```bash
   # Redis作为Celery Broker
   CELERY_BROKER_URL=redis://localhost:6379/0

   # 启用AI助手异步处理（可选）
   AI_ASSISTANT_USE_ASYNC=true
   ```

   b. 启动 Celery Worker：
   ```bash
   # 开发环境
   celery -A better_laser_erp worker -l info

   # 生产环境（后台运行）
   celery -A better_laser_erp worker -l info --detach --pidfile=/var/run/celery/worker.pid
   ```

   c. 启动 Celery Beat（定时任务）：
   ```bash
   # 开发环境
   celery -A better_laser_erp beat -l info

   # 生产环境（后台运行）
   celery -A better_laser_erp beat -l info --detach --pidfile=/var/run/celery/beat.pid
   ```

   d. 验证异步处理是否工作：
   ```python
   from apps.ai_assistant.tasks import process_message_async

   # 测试异步任务
   result = process_message_async.delay(message_data, user_id)
   print(result.task_id)  # 任务ID
   ```

   **定时任务**：
   - ✅ 每小时清理过期会话（30天未活跃）
   - ✅ 每天凌晨2点清理旧日志（90天前）

   **异步处理优势**：
   - Webhook快速响应（避免超时）
   - 长时间工具不阻塞其他请求
   - 自动重试失败的任务
   - 定时清理降低数据库负载

   **注意事项**：
   - 异步处理需要Redis支持
   - 开发环境可以不启用（默认同步处理）
   - 异步模式下用户会先收到"正在处理"提示

3. **数据库优化**:
   - 添加索引（conversation_id、external_user_id等）
   - 定期清理旧消息和日志
   - 使用MySQL替代SQLite

4. **监控和告警**:
   - 监控Webhook失败率
   - 监控AI API调用失败率
   - 设置Token使用预警

---

## 安全建议

1. **API Key管理**:
   - 设置环境变量`ENCRYPTION_KEY`
   - 定期轮换API Key
   - 不在代码中硬编码密钥

2. **Webhook安全**:
   - 启用HTTPS
   - 验证请求签名
   - 限制来源IP（如果可能）

3. **权限控制**:
   - 为敏感工具设置权限要求
   - 启用工具审核功能
   - 定期审查用户映射

4. **日志审计**:
   - 定期查看工具执行日志
   - 监控异常请求模式
   - 保留日志至少30天

---

## 联系支持

- 项目文档：`/docs/`
- 问题反馈：在项目Issues中提交
- 更新日志：`CHANGELOG.md`

---

**文档版本**: 1.0
**更新日期**: 2026-01-07
**作者**: 猫娘工程师 幽浮喵 ฅ'ω'ฅ
