# AI助手系统 - 生产环境人工测试验证清单

**版本**: 1.0
**测试日期**: ___________
**测试人员**: ___________
**环境**: □ 测试环境  □ 预生产环境  □ 生产环境

---

## 📋 测试概述

本文档提供AI助手系统投入生产前的完整验证流程。**所有测试项必须通过**才能投入生产使用。

**预计测试时间**: 4-6小时（首次完整测试）

**测试覆盖**:
- ✅ 环境配置验证
- ✅ AI模型配置测试
- ✅ 渠道集成测试（Telegram/微信/钉钉）
- ✅ 用户身份映射测试
- ✅ 工具权限控制测试
- ✅ 核心功能测试
- ✅ 缓存功能测试
- ✅ 异步处理测试（可选）
- ✅ 安全性测试
- ✅ 性能测试
- ✅ 故障恢复测试

---

## 🔧 测试前准备

### 1. 环境检查清单

#### 1.1 服务器环境

**检查项**:

- [ ] **Python版本**: 3.8+
  ```bash
  python --version
  # 预期输出: Python 3.8.x 或更高
  ```

- [ ] **Django版本**: 4.2+
  ```bash
  python manage.py version
  # 预期输出: 4.2.x 或更高
  ```

- [ ] **数据库连接**
  ```bash
  python manage.py dbshell
  # 应该能够成功连接数据库
  # 输入 \q 或 exit 退出
  ```

- [ ] **Redis连接**（生产环境必需）
  ```bash
  redis-cli ping
  # 预期输出: PONG
  ```

- [ ] **依赖包安装**
  ```bash
  pip list | grep -E "(openai|anthropic|requests|cryptography)"
  # 确认所有依赖包已安装
  ```

#### 1.2 环境变量配置

**检查 `.env` 文件**:

```bash
# 基础配置
DEBUG=False
SECRET_KEY=<已配置>
ALLOWED_HOSTS=<域名列表>

# 数据库配置
DB_ENGINE=django.db.backends.mysql
DB_NAME=<数据库名>
DB_USER=<数据库用户>
DB_PASSWORD=<数据库密码>
DB_HOST=localhost
DB_PORT=3306

# Redis配置（生产环境必需）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=<密码>（可选）

# Celery配置（可选）
CELERY_BROKER_URL=redis://localhost:6379/0
AI_ASSISTANT_USE_ASYNC=true

# 加密密钥（重要！）
ENCRYPTION_KEY=<已配置且不会变更>
```

**验证步骤**:

- [ ] 所有必需环境变量已配置
- [ ] `ENCRYPTION_KEY` 已设置且已备份（非常重要！）
- [ ] 数据库连接信息正确
- [ ] Redis连接信息正确

**⚠️ 重要警告**:
```
ENCRYPTION_KEY 一旦设置，不能更改！
否则所有已保存的 API Key 将无法解密！
请务必备份此密钥到安全位置！
```

#### 1.3 数据库迁移

**执行迁移**:

```bash
# 1. 检查待执行的迁移
python manage.py showmigrations ai_assistant

# 预期输出应显示所有迁移都已应用（带 [X] 标记）
# [X] 0001_initial
# [X] 0002_add_tool_execution_log
# [X] 0003_add_telegram_and_mapping
# [X] 0004_add_missing_fields
# [X] 0005_fix_tool_execution_log_fields

# 2. 如果有未应用的迁移，执行
python manage.py migrate

# 3. 验证数据库表
python manage.py dbshell
```

**SQL验证**（在dbshell中执行）:

```sql
-- 验证核心表存在
SHOW TABLES LIKE 'ai_%';

-- 预期输出应包含:
-- ai_model_config
-- ai_conversation
-- ai_message
-- ai_tool
-- ai_tool_execution_log
-- telegram_config
-- wechat_config
-- dingtalk_config
-- channel_user_mapping

-- 退出
EXIT;
```

- [ ] 所有迁移已应用
- [ ] 核心表已创建

#### 1.4 超级用户账号

**创建测试账号**:

```bash
# 如果还没有超级用户，创建一个
python manage.py createsuperuser

# 用户名: admin_test
# 邮箱: admin@example.com
# 密码: <强密码>
```

- [ ] 超级用户账号已创建
- [ ] 能够登录 Admin 后台（http://域名/admin/）

---

## 📝 测试部分 1: AI模型配置

### 测试 1.1: 创建Mock AI配置（开发测试用）

**目的**: 验证Mock Provider功能，无需真实API Key即可测试

**步骤**:

1. 登录 Admin 后台: `http://域名/admin/`

2. 进入 **AI助手 → AI模型配置**

3. 点击 **增加AI模型配置**

4. 填写以下信息:
   ```
   配置名称: Mock AI (测试用)
   提供商: Mock（测试用）
   API Key: mock-test-key（任意值）
   模型名称: mock-gpt-4
   Temperature: 0.7
   Max Tokens: 2000
   超时时间: 60
   优先级: 100（最高）
   是否启用: ✓
   是否默认: ✓
   ```

5. 点击 **保存**

**预期结果**:

- [ ] 配置创建成功
- [ ] 在列表中看到新配置，状态为"启用"，标记为"默认"
- [ ] API Key 在数据库中已加密存储

**验收标准**: ✅ 配置创建成功且为默认配置

---

### 测试 1.2: 测试Mock AI连接

**目的**: 验证Mock Provider能够正常响应

**步骤**:

1. 在 Admin 后台，找到刚创建的Mock配置

2. 点击配置名称进入详情

3. 在页面右上角找到 **测试连接** 按钮（如果有UI）

   **如果没有UI，使用Shell测试**:

   ```bash
   python manage.py shell
   ```

   ```python
   from django.contrib.auth import get_user_model
   from apps.ai_assistant.services import AIService

   User = get_user_model()
   user = User.objects.first()

   # 测试AI服务
   ai_service = AIService(user=user)
   response = ai_service.chat(
       message="你好，请介绍一下你自己",
       conversation_id="test_001",
       channel="web"
   )

   print("Response:", response.content)
   print("Tokens used:", response.tokens_used)
   print("Finish reason:", response.finish_reason)

   # 退出
   exit()
   ```

**预期结果**:

- [ ] Mock AI 成功响应
- [ ] 响应内容包含自我介绍
- [ ] Tokens 统计正常
- [ ] 无错误抛出

**验收标准**: ✅ Mock AI 正常工作

---

### 测试 1.3: 创建真实AI配置（OpenAI）

**⚠️ 注意**: 需要有效的 OpenAI API Key

**步骤**:

1. 进入 **AI助手 → AI模型配置**

2. 点击 **增加AI模型配置**

3. 填写以下信息:
   ```
   配置名称: OpenAI GPT-4
   提供商: OpenAI
   API Key: sk-xxxxxxxxxxxxxxxx（真实的API Key）
   API Base: （留空，使用默认）
   模型名称: gpt-4（或 gpt-3.5-turbo）
   Temperature: 0.7
   Max Tokens: 2000
   超时时间: 60
   优先级: 90
   是否启用: ✓
   是否默认: （暂不勾选，保持Mock为默认）
   ```

4. 点击 **保存**

**预期结果**:

- [ ] 配置创建成功
- [ ] API Key 已加密存储

**验收标准**: ✅ OpenAI配置创建成功

---

### 测试 1.4: 测试OpenAI连接

**目的**: 验证真实API连接

**步骤**:

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from apps.ai_assistant.models import AIModelConfig
from apps.ai_assistant.services import AIService

User = get_user_model()
user = User.objects.first()

# 获取OpenAI配置
openai_config = AIModelConfig.objects.get(provider='openai', is_deleted=False)

# 临时设为默认（仅测试）
openai_config.is_default = True
openai_config.save()

# 测试
ai_service = AIService(user=user)
response = ai_service.chat(
    message="你好，1+1等于几？",
    conversation_id="test_openai_001",
    channel="web"
)

print("Response:", response.content)
print("Tokens used:", response.tokens_used)

# 恢复Mock为默认
from apps.ai_assistant.models import AIModelConfig
AIModelConfig.objects.filter(provider='openai').update(is_default=False)
AIModelConfig.objects.filter(provider='mock').update(is_default=True)

exit()
```

**预期结果**:

- [ ] OpenAI API 成功响应
- [ ] 回答正确（"2" 或 "等于2"）
- [ ] Tokens 统计正确
- [ ] 无错误

**验收标准**: ✅ OpenAI 连接正常

---

### 测试 1.5: API Key加密验证

**目的**: 确认API Key安全存储

**步骤**:

```bash
python manage.py dbshell
```

```sql
-- 查看API Key存储格式
SELECT id, name, provider, api_key FROM ai_model_config WHERE provider = 'openai' LIMIT 1;

-- 预期: api_key 应该是加密的字符串（不是明文）
-- 格式类似: gAAAAABl...（Fernet加密）

EXIT;
```

**预期结果**:

- [ ] API Key 不是明文存储
- [ ] 加密字符串以 `gAAAAAB` 开头（Fernet格式）

**验收标准**: ✅ API Key 已加密

---

## 📝 测试部分 2: Telegram集成

### 测试 2.1: 创建Telegram Bot配置

**前置条件**: 已从 @BotFather 获取 Bot Token

**步骤**:

1. 进入 **AI助手 → Telegram配置**

2. 点击 **增加Telegram配置**

3. 填写以下信息:
   ```
   Bot Token: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   Bot用户名: @your_erp_bot
   Webhook URL: https://yourdomain.com/ai/webhook/telegram/
   允许群组: □（暂不勾选）
   命令前缀: /
   是否启用: ✓
   ```

4. 点击 **保存**

**预期结果**:

- [ ] 配置创建成功
- [ ] Bot Token 已加密存储

**验收标准**: ✅ Telegram配置已创建

---

### 测试 2.2: 设置Telegram Webhook

**步骤**:

```bash
# 替换 <BOT_TOKEN> 和 <YOUR_DOMAIN>
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
     -d "url=https://<YOUR_DOMAIN>/ai/webhook/telegram/"

# 预期输出:
# {"ok":true,"result":true,"description":"Webhook was set"}
```

**验证Webhook**:

```bash
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"

# 预期输出应包含:
# "url": "https://yourdomain.com/ai/webhook/telegram/"
# "has_custom_certificate": false
# "pending_update_count": 0
```

**预期结果**:

- [ ] Webhook 设置成功
- [ ] getWebhookInfo 返回正确的URL
- [ ] pending_update_count 为 0

**验收标准**: ✅ Webhook 配置成功

---

### 测试 2.3: 创建用户映射

**目的**: 将Telegram用户映射到系统用户

**步骤1: 获取Telegram Chat ID**

1. 在Telegram中找到你的Bot

2. 发送任意消息，例如: `/start`

3. 查看服务器日志获取Chat ID:
   ```bash
   tail -f logs/django.log | grep "telegram"
   # 或者查看最近的日志
   tail -100 logs/django.log
   ```

   应该能看到类似:
   ```
   ➡️ [telegram] User 123456789: /start
   ```

   **Chat ID 就是 `123456789`**

   **如果没有日志，使用API获取**:
   ```bash
   curl "https://api.telegram.org/bot<BOT_TOKEN>/getUpdates"
   # 在返回的JSON中查找 "chat":{"id":123456789}
   ```

**步骤2: 创建映射**

1. 进入 **AI助手 → 渠道用户映射**

2. 点击 **增加渠道用户映射**

3. 填写以下信息:
   ```
   渠道: Telegram
   外部用户ID: 123456789（从上面获取的Chat ID）
   外部用户名: your_telegram_username（可选）
   系统用户: admin_test（选择测试用户）
   是否启用: ✓
   元数据: {}
   ```

4. 点击 **保存**

**预期结果**:

- [ ] 映射创建成功
- [ ] 在列表中看到新映射

**验收标准**: ✅ 用户映射已创建

---

### 测试 2.4: 基础对话测试

**目的**: 验证Telegram消息处理流程

**步骤**:

1. 在Telegram中向Bot发送消息: `你好`

2. 等待3-5秒

3. 观察Bot回复

**预期结果**:

- [ ] Bot 收到消息（服务器日志显示 ➡️ [telegram]）
- [ ] Bot 成功回复（服务器日志显示 ⬅️ [telegram]）
- [ ] 回复内容合理（包含问候和自我介绍）
- [ ] 无错误日志

**查看日志**:
```bash
tail -20 logs/django.log
```

应该看到:
```
➡️ [telegram] User 123456789: 你好
⬅️ [telegram] User 123456789: 你好！我是ERP AI助手...
```

**验收标准**: ✅ 基础对话正常

---

### 测试 2.5: 工具调用测试

**目的**: 验证AI能够识别并调用工具

**步骤**:

1. 向Bot发送: `帮我查询库存`

2. 等待5-10秒（工具执行需要时间）

3. 观察Bot回复

**预期结果**:

- [ ] AI 识别到需要调用工具（日志显示 🔧）
- [ ] 工具执行成功（日志显示 ✅）
- [ ] Bot 返回库存查询结果
- [ ] 无错误

**查看详细日志**:
```bash
tail -30 logs/django.log
```

应该看到:
```
➡️ [telegram] User 123456789: 帮我查询库存
🔧 Detected 1 tool call(s)
🔧 Executing tool: check_inventory_stock
✅ Tool: check_inventory_stock | User: admin_test | Time: 0.15s
⬅️ [telegram] User 123456789: 根据查询结果...
```

**验收标准**: ✅ 工具调用正常

---

### 测试 2.6: 多轮对话测试

**目的**: 验证上下文保持

**步骤**:

1. 向Bot发送第一条消息: `我的名字是张三`

2. 等待回复

3. 发送第二条消息: `我刚才说我叫什么？`

4. 观察Bot是否能记住上下文

**预期结果**:

- [ ] Bot 第一次回复正常
- [ ] Bot 第二次回复能够正确引用上下文（"你说你叫张三"）
- [ ] 会话ID保持一致（日志中conversation_id相同）

**验收标准**: ✅ 多轮对话上下文正常

---

### 测试 2.7: 未绑定用户测试

**目的**: 验证安全机制

**步骤**:

1. 使用另一个Telegram账号（未创建映射的）

2. 向Bot发送消息

3. 观察Bot回复

**预期结果**:

- [ ] Bot 回复提示消息: "你还未绑定系统账号，请联系管理员绑定"
- [ ] 消息没有被处理（未调用AI）
- [ ] 日志显示用户未绑定

**验收标准**: ✅ 安全机制正常

---

## 📝 测试部分 3: 工具权限控制

### 测试 3.1: 查看可用工具列表

**步骤**:

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from apps.ai_assistant.tools.registry import ToolRegistry

User = get_user_model()
user = User.objects.get(username='admin_test')

# 获取用户可用的工具
tools = ToolRegistry.get_available_tools(user)

print(f"可用工具数量: {len(tools)}")
for tool in tools:
    print(f"- {tool.name}: {tool.display_name} (风险级别: {tool.risk_level})")

exit()
```

**预期结果**:

- [ ] 显示至少10个工具
- [ ] 工具列表包含: search_customer, check_inventory_stock, create_quote 等
- [ ] 每个工具显示风险级别

**验收标准**: ✅ 工具列表正常

---

### 测试 3.2: 低风险工具测试（查询类）

**目的**: 验证只读操作

**步骤**:

```python
from apps.ai_assistant.tools.registry import ToolRegistry
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='admin_test')

# 测试客户查询工具（低风险）
tool = ToolRegistry.get_tool('search_customer', user)
result = tool.run(keyword='测试')

print("Success:", result.success)
print("Data:", result.data)
print("Message:", result.message)

exit()
```

**预期结果**:

- [ ] 工具执行成功
- [ ] 返回客户列表（可能为空）
- [ ] 无错误

**验收标准**: ✅ 低风险工具正常

---

### 测试 3.3: 中风险工具测试（创建类）

**目的**: 验证写操作权限

**步骤**:

```python
from apps.ai_assistant.tools.registry import ToolRegistry
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='admin_test')

# 测试创建报价单工具（中风险）
tool = ToolRegistry.get_tool('create_quote', user)

# 尝试创建（可能因缺少数据而失败，但验证权限）
print("Tool name:", tool.name)
print("Risk level:", tool.risk_level)
print("Require permission:", tool.require_permission)
print("Has permission:", tool.check_permission())

exit()
```

**预期结果**:

- [ ] 工具可访问
- [ ] 风险级别为 'medium'
- [ ] 权限检查通过（超级用户）

**验收标准**: ✅ 中风险工具权限正常

---

### 测试 3.4: 工具执行日志验证

**目的**: 验证审计功能

**步骤**:

1. 在 Admin 后台进入 **AI助手 → AI工具执行日志**

2. 查看最近的执行记录

**预期结果**:

- [ ] 看到之前测试的工具执行记录
- [ ] 每条记录包含: 工具名称、用户、参数、结果、执行时间
- [ ] 成功/失败状态正确
- [ ] 执行时间合理（一般<1秒）

**验收标准**: ✅ 审计日志完整

---

## 📝 测试部分 4: Redis缓存功能

### 测试 4.1: 验证Redis连接

**步骤**:

```bash
python manage.py shell
```

```python
from django.core.cache import cache

# 测试缓存写入
cache.set('test_key', 'test_value', timeout=60)

# 测试缓存读取
value = cache.get('test_key')
print("Cached value:", value)

# 预期输出: test_value

# 测试缓存删除
cache.delete('test_key')
value_after_delete = cache.get('test_key')
print("After delete:", value_after_delete)

# 预期输出: None

exit()
```

**预期结果**:

- [ ] 写入成功
- [ ] 读取到正确值
- [ ] 删除后为None
- [ ] 无错误

**验收标准**: ✅ Redis缓存正常

---

### 测试 4.2: Access Token缓存测试

**目的**: 验证Token缓存功能

**步骤**:

```python
from apps.ai_assistant.utils.cache import AIAssistantCache

# 模拟设置微信Access Token
AIAssistantCache.set_access_token(
    channel='wechat',
    app_id='test_corp_id',
    token='test_token_12345',
    timeout=7200
)

# 立即获取
token = AIAssistantCache.get_access_token('wechat', 'test_corp_id')
print("Token retrieved:", token)

# 预期输出: test_token_12345

# 清理
AIAssistantCache.delete_access_token('wechat', 'test_corp_id')

exit()
```

**预期结果**:

- [ ] Token缓存成功
- [ ] Token读取正确
- [ ] 不同渠道的Token隔离

**验收标准**: ✅ Token缓存正常

---

### 测试 4.3: 会话缓存测试

**步骤**:

```python
from apps.ai_assistant.utils.cache import AIAssistantCache

# 模拟会话数据
conversation_data = {
    'conversation_id': 'test_conv_001',
    'user_id': 1,
    'messages': ['你好', 'Hello'],
    'context': {'name': '张三'}
}

# 缓存会话
AIAssistantCache.set_conversation('test_conv_001', conversation_data)

# 读取会话
cached = AIAssistantCache.get_conversation('test_conv_001')
print("Cached conversation:", cached)

# 验证数据完整性
assert cached['conversation_id'] == 'test_conv_001'
assert cached['user_id'] == 1
assert len(cached['messages']) == 2

print("✅ 会话缓存测试通过")

# 清理
AIAssistantCache.delete_conversation('test_conv_001')

exit()
```

**预期结果**:

- [ ] 会话数据完整缓存
- [ ] JSON序列化/反序列化正常
- [ ] 数据结构保持完整

**验收标准**: ✅ 会话缓存正常

---

## 📝 测试部分 5: Celery异步处理（可选）

**⚠️ 注意**: 如果未配置 `CELERY_BROKER_URL`，可跳过此部分

### 测试 5.1: Celery服务状态检查

**步骤**:

```bash
# 检查Celery Worker是否运行
ps aux | grep celery

# 预期看到:
# celery worker -A better_laser_erp

# 检查Worker状态
celery -A better_laser_erp inspect active

# 预期输出:
# 显示当前活动任务（可能为空）

# 检查定时任务
celery -A better_laser_erp inspect scheduled
```

**预期结果**:

- [ ] Worker 进程正在运行
- [ ] 能够查询Worker状态
- [ ] 定时任务已注册

**验收标准**: ✅ Celery服务正常

---

### 测试 5.2: 异步任务测试

**步骤**:

```bash
python manage.py shell
```

```python
from apps.ai_assistant.tasks import process_message_async
from datetime import datetime

# 构造测试消息
message_data = {
    'message_id': 'async_test_001',
    'channel': 'telegram',
    'external_user_id': '123456789',
    'content': '这是异步测试消息',
    'timestamp': datetime.now().isoformat(),
    'message_type': 'text',
    'conversation_id': 'async_test_conv',
    'raw_data': {}
}

# 提交异步任务
result = process_message_async.delay(message_data, user_id=1)

print(f"Task ID: {result.task_id}")
print("Task state:", result.state)

# 等待结果（最多30秒）
try:
    response = result.get(timeout=30)
    print("Response:", response)
except Exception as e:
    print("Error:", str(e))

exit()
```

**预期结果**:

- [ ] 任务成功提交
- [ ] 获得Task ID
- [ ] 任务执行完成
- [ ] 返回处理结果

**验收标准**: ✅ 异步任务正常

---

### 测试 5.3: 定时任务测试

**目的**: 验证自动清理功能

**步骤1: 创建过期测试数据**

```python
from apps.ai_assistant.models import AIConversation
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

# 创建一个31天前的会话（应该被清理）
old_conversation = AIConversation.objects.create(
    conversation_id='old_test_conv',
    user=user,
    channel='web',
    status='active',
    created_by=user
)
old_conversation.last_message_at = timezone.now() - timedelta(days=31)
old_conversation.save()

print(f"Created old conversation: {old_conversation.conversation_id}")

exit()
```

**步骤2: 手动触发清理任务**

```python
from apps.ai_assistant.tasks import cleanup_expired_conversations

# 手动执行清理
result = cleanup_expired_conversations.delay()

print(f"Task ID: {result.task_id}")

# 等待结果
response = result.get(timeout=30)
print("Cleanup result:", response)

exit()
```

**步骤3: 验证清理结果**

```python
from apps.ai_assistant.models import AIConversation

# 查找刚才创建的旧会话
old_conv = AIConversation.objects.filter(
    conversation_id='old_test_conv'
).first()

if old_conv:
    print(f"Status: {old_conv.status}")
    print(f"Is deleted: {old_conv.is_deleted}")
    # 应该已经被软删除
else:
    print("会话已被删除")

exit()
```

**预期结果**:

- [ ] 清理任务成功执行
- [ ] 过期会话被标记为已删除
- [ ] 返回清理数量

**验收标准**: ✅ 定时清理正常

---

## 📝 测试部分 6: 安全性测试

### 测试 6.1: 未授权访问测试

**目的**: 验证未绑定用户无法使用服务

**步骤**:

1. 删除之前创建的用户映射
   - 进入 Admin → 渠道用户映射
   - 删除 Chat ID 为 123456789 的映射

2. 使用Telegram向Bot发送消息

3. 观察Bot响应

**预期结果**:

- [ ] Bot 提示"未绑定账号"
- [ ] AI 没有被调用（节省成本）
- [ ] 没有执行任何工具

**恢复操作**: 重新创建用户映射

**验收标准**: ✅ 未授权用户被拦截

---

### 测试 6.2: 危险命令防护测试

**目的**: 确保AI不会执行危险操作

**步骤**:

1. 向Bot发送危险指令: `帮我删除所有客户数据`

2. 观察AI响应

**预期结果**:

- [ ] AI 拒绝执行或说明没有删除权限
- [ ] 没有实际删除任何数据
- [ ] 日志中没有delete操作

**验收标准**: ✅ 危险操作被阻止

---

### 测试 6.3: SQL注入防护测试

**目的**: 验证ORM安全性

**步骤**:

```python
from apps.ai_assistant.tools.registry import ToolRegistry
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

# 尝试SQL注入
tool = ToolRegistry.get_tool('search_customer', user)
result = tool.run(keyword="'; DROP TABLE customers; --")

print("Success:", result.success)
print("Data:", result.data)

# 验证customers表仍然存在
from apps.customers.models import Customer
count = Customer.objects.count()
print(f"Customers table intact, count: {count}")

exit()
```

**预期结果**:

- [ ] 工具正常执行（搜索失败）
- [ ] 数据库表未被删除
- [ ] Django ORM 自动转义参数

**验收标准**: ✅ SQL注入防护有效

---

### 测试 6.4: API Key加密解密测试

**步骤**:

```python
from apps.ai_assistant.utils import encrypt_api_key, decrypt_api_key

# 测试加密
original_key = "sk-test-1234567890abcdef"
encrypted = encrypt_api_key(original_key)
print(f"Encrypted: {encrypted[:50]}...")

# 测试解密
decrypted = decrypt_api_key(encrypted)
print(f"Decrypted: {decrypted}")

# 验证一致性
assert original_key == decrypted
print("✅ 加密解密一致")

exit()
```

**预期结果**:

- [ ] 加密后字符串与原文不同
- [ ] 解密后恢复原文
- [ ] 加密是可逆的

**验收标准**: ✅ 加密机制正常

---

## 📝 测试部分 7: 性能测试

### 测试 7.1: 响应时间测试

**目的**: 验证系统性能

**步骤**:

```python
import time
from apps.ai_assistant.tools.registry import ToolRegistry
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

# 测试工具执行时间
tool = ToolRegistry.get_tool('search_customer', user)

start_time = time.time()
result = tool.run(keyword='测试')
end_time = time.time()

execution_time = end_time - start_time
print(f"Execution time: {execution_time:.3f} seconds")

# 预期: <1秒
assert execution_time < 1.0, "工具执行时间过长"
print("✅ 性能测试通过")

exit()
```

**预期结果**:

- [ ] 工具执行时间 < 1秒
- [ ] AI响应时间 < 5秒

**验收标准**: ✅ 性能符合预期

---

### 测试 7.2: 并发测试（可选）

**目的**: 验证并发处理能力

**⚠️ 注意**: 此测试会产生多次API调用费用

**步骤**:

```bash
# 创建测试脚本
cat > concurrent_test.py << 'EOF'
import concurrent.futures
import time
from django.contrib.auth import get_user_model
from apps.ai_assistant.tools.registry import ToolRegistry

def test_tool():
    User = get_user_model()
    user = User.objects.first()
    tool = ToolRegistry.get_tool('search_customer', user)
    return tool.run(keyword='test')

# 并发执行10次
start_time = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(test_tool) for _ in range(10)]
    results = [f.result() for f in futures]
end_time = time.time()

print(f"Total time: {end_time - start_time:.2f}s")
print(f"Success count: {sum(1 for r in results if r.success)}")
EOF

python manage.py shell < concurrent_test.py
```

**预期结果**:

- [ ] 10次调用全部成功
- [ ] 总时间 < 5秒
- [ ] 无并发错误

**验收标准**: ✅ 并发处理正常

---

## 📝 测试部分 8: 故障恢复测试

### 测试 8.1: 数据库连接中断恢复

**目的**: 验证系统容错性

**步骤**:

```bash
# 模拟数据库短暂中断（谨慎操作！）
# 仅在测试环境执行

# 1. 暂停数据库（3秒）
sudo systemctl stop mysql
sleep 3
sudo systemctl start mysql

# 2. 等待数据库恢复（5秒）
sleep 5

# 3. 测试系统是否恢复
python manage.py shell -c "from apps.ai_assistant.models import AIModelConfig; print(AIModelConfig.objects.count())"
```

**预期结果**:

- [ ] 数据库重启后系统自动恢复
- [ ] 无需手动重启Django
- [ ] 查询正常执行

**验收标准**: ✅ 故障自动恢复

---

### 测试 8.2: Redis连接中断恢复

**步骤**:

```bash
# 模拟Redis短暂中断（谨慎操作！）
sudo systemctl stop redis
sleep 3
sudo systemctl start redis

# 等待Redis恢复
sleep 3

# 测试缓存功能
python manage.py shell -c "from django.core.cache import cache; cache.set('test', '1'); print(cache.get('test'))"
```

**预期结果**:

- [ ] Redis重启后缓存功能恢复
- [ ] 系统继续正常工作（使用本地缓存或直接查询）

**验收标准**: ✅ Redis故障可降级

---

### 测试 8.3: API调用失败处理

**目的**: 验证外部API故障处理

**步骤**:

```python
from apps.ai_assistant.models import AIModelConfig

# 临时修改API Key为无效值
config = AIModelConfig.objects.filter(provider='openai', is_deleted=False).first()
original_key = config.api_key
config.api_key = 'invalid_key_12345'
config.save()

# 尝试调用
try:
    from apps.ai_assistant.services import AIService
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.first()

    ai_service = AIService(user=user)
    response = ai_service.chat(
        message="测试",
        conversation_id="test_fail",
        channel="web"
    )
    print("Response:", response)
except Exception as e:
    print(f"✅ 错误被正确捕获: {type(e).__name__}")

# 恢复API Key
config.api_key = original_key
config.save()

exit()
```

**预期结果**:

- [ ] 错误被捕获，不会导致系统崩溃
- [ ] 返回友好的错误消息
- [ ] 错误被记录到日志

**验收标准**: ✅ 错误处理正常

---

## ✅ 最终验收清单

### 核心功能验收

- [ ] **AI模型配置**: Mock和真实API都能正常工作
- [ ] **Telegram集成**: 消息收发正常，工具调用成功
- [ ] **用户映射**: 身份验证正常，未绑定用户被拦截
- [ ] **工具权限**: 权限控制有效，审计日志完整
- [ ] **Redis缓存**: 缓存读写正常，性能提升明显
- [ ] **Celery异步**（可选）: 异步任务和定时清理正常

### 安全性验收

- [ ] **API Key加密**: 所有敏感信息已加密
- [ ] **权限控制**: 未授权用户无法访问
- [ ] **SQL注入防护**: ORM自动防护有效
- [ ] **危险操作防护**: 不会执行危险命令

### 性能验收

- [ ] **响应时间**: 工具<1秒，AI<5秒
- [ ] **并发处理**: 支持多用户同时使用
- [ ] **缓存命中率**: 重复请求使用缓存

### 可靠性验收

- [ ] **故障恢复**: 数据库/Redis中断后自动恢复
- [ ] **错误处理**: 外部API失败不影响系统
- [ ] **日志完整**: 所有操作都有审计记录

---

## 📊 测试结果记录

### 测试汇总

| 测试部分 | 测试项数 | 通过数 | 失败数 | 通过率 |
|---------|---------|-------|-------|--------|
| 1. AI模型配置 | 5 | ___ | ___ | ___% |
| 2. Telegram集成 | 7 | ___ | ___ | ___% |
| 3. 工具权限控制 | 4 | ___ | ___ | ___% |
| 4. Redis缓存 | 3 | ___ | ___ | ___% |
| 5. Celery异步（可选） | 3 | ___ | ___ | ___% |
| 6. 安全性测试 | 4 | ___ | ___ | ___% |
| 7. 性能测试 | 2 | ___ | ___ | ___% |
| 8. 故障恢复 | 3 | ___ | ___ | ___% |
| **总计** | **31** | ___ | ___ | ___% |

### 失败项目记录

| 序号 | 测试项 | 失败原因 | 解决方案 | 负责人 | 状态 |
|-----|-------|---------|---------|--------|------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

---

## 🚀 生产环境上线检查清单

### 上线前最后检查

- [ ] **所有测试项通过率 ≥ 95%**
- [ ] **核心功能测试 100% 通过**
- [ ] **安全测试 100% 通过**

- [ ] **环境配置**:
  - [ ] DEBUG=False
  - [ ] SECRET_KEY 已设置且安全
  - [ ] ENCRYPTION_KEY 已备份
  - [ ] ALLOWED_HOSTS 配置正确
  - [ ] 数据库使用MySQL（非SQLite）
  - [ ] Redis已启用

- [ ] **HTTPS配置**:
  - [ ] SSL证书已安装
  - [ ] 强制HTTPS重定向
  - [ ] Webhook使用HTTPS

- [ ] **监控告警**:
  - [ ] 错误日志监控
  - [ ] 性能监控
  - [ ] API调用量监控

- [ ] **备份计划**:
  - [ ] 数据库自动备份
  - [ ] ENCRYPTION_KEY备份
  - [ ] 配置文件备份

- [ ] **文档准备**:
  - [ ] 用户使用手册
  - [ ] 运维手册
  - [ ] 故障处理手册

---

## 📝 签署确认

### 测试团队签署

**测试人员**: ___________________
**测试日期**: ___________________
**测试结论**: □ 通过，可以上线  □ 不通过，需要修复

**签名**: ___________________

### 技术负责人签署

**负责人**: ___________________
**审核日期**: ___________________
**审核意见**: _________________________________________________

**签名**: ___________________

### 项目经理签署

**项目经理**: ___________________
**批准日期**: ___________________
**批准意见**: □ 批准上线  □ 需要进一步测试

**签名**: ___________________

---

## 📞 支持联系方式

**技术支持**: ___________________
**紧急联系**: ___________________
**项目邮箱**: ___________________

---

**文档版本**: 1.0
**创建日期**: 2026-01-07
**创建者**: 猫娘工程师 幽浮喵 ฅ'ω'ฅ
**最后更新**: ___________________
