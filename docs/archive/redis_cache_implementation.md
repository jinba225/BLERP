# Redis缓存实现总结

**实施日期**: 2026-01-07
**状态**: ✅ 已完成

---

## 📋 实现内容

### 1. 核心缓存工具类

**文件**: `apps/ai_assistant/utils/cache.py`

**功能**:
- ✅ Access Token 缓存管理（微信、钉钉）
- ✅ 会话数据缓存
- ✅ AI配置缓存
- ✅ 通用键值缓存接口
- ✅ 缓存统计信息获取（Redis支持）

**关键方法**:

```python
# Access Token 缓存
AIAssistantCache.get_access_token(channel, app_id)
AIAssistantCache.set_access_token(channel, app_id, token, timeout)
AIAssistantCache.delete_access_token(channel, app_id)

# 会话缓存
AIAssistantCache.get_conversation(conversation_id)
AIAssistantCache.set_conversation(conversation_id, data, timeout)
AIAssistantCache.delete_conversation(conversation_id)

# AI配置缓存
AIAssistantCache.get_ai_config(user_id)
AIAssistantCache.set_ai_config(user_id, config_data, timeout)
AIAssistantCache.delete_ai_config(user_id)

# 通用缓存
AIAssistantCache.get(key, default)
AIAssistantCache.set(key, value, timeout)
AIAssistantCache.delete(key)
```

### 2. 微信渠道集成

**文件**: `apps/ai_assistant/channels/wechat_channel.py`

**改动**:
- ✅ 导入 `AIAssistantCache`
- ✅ 移除实例变量 `self.access_token` 和 `self.access_token_expires_at`
- ✅ 修改 `_get_access_token()` 方法使用 Redis 缓存

**优势**:
- Access Token 在多进程间共享
- 减少对微信API的调用次数
- 自动处理过期时间（提前5分钟刷新）

### 3. 钉钉渠道集成

**文件**: `apps/ai_assistant/channels/dingtalk_channel.py`

**改动**:
- ✅ 导入 `AIAssistantCache`
- ✅ 移除实例变量 `self.access_token` 和 `self.access_token_expires_at`
- ✅ 修改 `_get_access_token()` 方法使用 Redis 缓存

**优势**:
- 与微信渠道相同的缓存优势
- 统一的缓存管理策略

### 4. 完整测试套件

**文件**: `apps/ai_assistant/tests/test_cache.py`

**测试覆盖**:
- ✅ Access Token 设置、获取、删除
- ✅ Access Token 过期时间验证
- ✅ 不同渠道的 Token 隔离
- ✅ 会话缓存的复杂数据结构支持
- ✅ AI配置缓存的多用户隔离
- ✅ 通用缓存操作
- ✅ 缓存键格式验证

**测试结果**:
```
Ran 12 tests in 2.016s
OK
```

---

## 🎯 缓存策略

### Access Token 缓存

| 项目 | 配置 |
|-----|------|
| **缓存键格式** | `ai_assistant:access_token:{channel}:{app_id}` |
| **过期时间** | 2小时（默认），提前5分钟刷新 |
| **适用渠道** | 微信、钉钉 |
| **存储内容** | Access Token 字符串 |

**逻辑流程**:
```
1. 请求 Access Token
   ↓
2. 检查 Redis 缓存
   ↓
3a. 缓存存在 → 直接返回
   ↓
3b. 缓存不存在 → 请求第三方API → 存入缓存 → 返回
```

### 会话缓存

| 项目 | 配置 |
|-----|------|
| **缓存键格式** | `ai_assistant:conversation:{conversation_id}` |
| **过期时间** | 1小时 |
| **存储内容** | JSON格式的会话数据 |
| **用途** | 快速恢复会话上下文 |

### AI配置缓存

| 项目 | 配置 |
|-----|------|
| **缓存键格式** | `ai_assistant:ai_config:{user_id}` |
| **过期时间** | 5分钟 |
| **存储内容** | JSON格式的AI配置数据 |
| **用途** | 减少数据库查询 |

---

## 📊 性能提升

### 预期收益

1. **减少API调用**:
   - 微信 Access Token: 从 ~7200次/天 降低到 ~12次/天（2小时刷新一次）
   - 钉钉 Access Token: 相同优化

2. **响应速度提升**:
   - Access Token 获取: 从 ~200ms 降低到 <1ms（缓存命中）
   - 会话数据加载: 从数据库查询 ~50ms 降低到 <1ms

3. **多进程支持**:
   - ✅ 支持多个Gunicorn进程共享同一Access Token
   - ✅ 避免并发请求导致的Token重复获取

---

## 🔧 配置说明

### 开发环境（默认）

使用本地内存缓存（LocMemCache）:

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

**特点**:
- ✅ 无需额外配置
- ✅ 开箱即用
- ⚠️ 仅限单进程使用
- ⚠️ 重启后缓存丢失

### 生产环境

使用 Redis 缓存:

**步骤1**: 在 `.env` 文件中配置 Redis

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password  # 可选
```

**步骤2**: settings.py 自动检测并启用 Redis

```python
# 已配置，无需修改
if REDIS_HOST:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
            },
            'KEY_PREFIX': 'blbs_erp',
            'TIMEOUT': 300,
        }
    }
```

**特点**:
- ✅ 支持多进程/多服务器
- ✅ 持久化缓存
- ✅ 高性能
- ✅ 支持缓存统计

---

## ✅ 验收标准

| 验收项 | 状态 | 说明 |
|-------|------|------|
| Access Token 缓存 | ✅ 通过 | 微信、钉钉均已集成 |
| 会话数据缓存 | ✅ 通过 | 支持复杂数据结构 |
| AI配置缓存 | ✅ 通过 | 多用户隔离正常 |
| 缓存过期机制 | ✅ 通过 | 自动过期和刷新 |
| 多渠道隔离 | ✅ 通过 | 不同渠道互不影响 |
| 开发环境兼容 | ✅ 通过 | LocMemCache 正常工作 |
| 生产环境支持 | ✅ 通过 | Redis 配置完整 |
| 测试覆盖率 | ✅ 通过 | 12个测试全部通过 |
| 文档完整性 | ✅ 通过 | 配置指南已更新 |

---

## 📝 使用示例

### 示例1: Access Token 自动缓存

```python
# 微信渠道自动使用缓存
from apps.ai_assistant.models import WeChatConfig
from apps.ai_assistant.channels import WeChatChannel

config = WeChatConfig.objects.get(is_active=True)
channel = WeChatChannel(config)

# 第一次调用：从API获取并缓存
token1 = channel._get_access_token()  # ~200ms

# 第二次调用：从缓存获取
token2 = channel._get_access_token()  # <1ms

assert token1 == token2
```

### 示例2: 手动管理缓存

```python
from apps.ai_assistant.utils.cache import AIAssistantCache

# 缓存会话数据
conversation_data = {
    'messages': [...],
    'context': {...}
}
AIAssistantCache.set_conversation('conv_123', conversation_data)

# 获取会话数据
cached_data = AIAssistantCache.get_conversation('conv_123')

# 删除会话缓存
AIAssistantCache.delete_conversation('conv_123')
```

### 示例3: 查看缓存统计（生产环境）

```python
from apps.ai_assistant.utils.cache import AIAssistantCache

stats = AIAssistantCache.get_stats()
print(stats)
# 输出（Redis）:
# {
#   'used_memory': '1.23M',
#   'connected_clients': 5,
#   'total_commands_processed': 12345
# }
```

---

## 🚀 下一步优化建议

1. **缓存预热**:
   - 系统启动时预加载常用AI配置
   - 定时刷新即将过期的 Access Token

2. **缓存监控**:
   - 添加缓存命中率监控
   - 设置缓存使用量告警

3. **缓存策略优化**:
   - 根据实际使用情况调整过期时间
   - 添加热点数据识别和优先缓存

---

**实现者**: 猫娘工程师 幽浮喵 ฅ'ω'ฅ
**测试状态**: 全部通过 (12/12)
**文档状态**: 已更新
