[根目录](../../../CLAUDE.md) > [django_erp](../../) > [apps](../) > **authentication**

# Authentication模块文档

## 模块职责

Authentication模块负责系统的身份认证和权限控制。主要职责包括：
- **JWT认证**: 基于JWT的API认证机制
- **用户登录**: 用户身份验证和会话管理
- **权限控制**: 基于Django权限系统的访问控制
- **安全管理**: 登录安全和会话安全

## 核心功能

### JWT认证
- 自定���JWT认证类 (`JWTAuthentication`)
- 支持Token刷新机制
- JWT密钥和算法配置

### 配置项
```python
# settings.py
JWT_SECRET_KEY = config('JWT_SECRET_KEY', default=SECRET_KEY)
JWT_ALGORITHM = 'HS256'  
JWT_EXPIRATION_DELTA = 86400  # 24 hours

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.authentication.authentication.JWTAuthentication',
    ],
}
```

## 主要文件
- `authentication.py` - JWT认证实现
- `serializers.py` - 认证相关序列化器
- `views.py` - 登录视图逻辑
- `urls.py` - 认证相关路由

## API路由
```python
path('api/auth/', include('apps.authentication.urls'))  # 认证API
```

## 集成关系
- **Users**: 用户模型的认证支持
- **Core**: 审计日志的用户跟踪
- **Frontend**: 前端JWT Token管理

## 测试与质量

### 测试文件位置
```bash
apps/authentication/tests/
├── __init__.py
└── test_authentication.py  # JWT认证和工具函数测试
```

### 测试覆盖情况
✅ **测试完成度: 100%** (15/15 测试通过)

#### JWT Token生成测试 (3个测试)
- ✅ `test_generate_jwt_token` - JWT token生成
- ✅ `test_token_payload` - Token payload结构验证
- ✅ `test_token_expiration` - Token过期时间设置

#### JWT认证测试 (10个测试)
- ✅ `test_authenticate_with_valid_token` - 有效token认证
- ✅ `test_authenticate_without_header` - 缺少认证头处理
- ✅ `test_authenticate_with_invalid_prefix` - 无效前缀处理
- ✅ `test_authenticate_with_expired_token` - 过期token处理
- ✅ `test_authenticate_with_invalid_token` - 无效token处理
- ✅ `test_authenticate_with_nonexistent_user` - 不存在用户处理
- ✅ `test_authenticate_with_inactive_user` - 禁用用户处理
- ✅ `test_authenticate_with_single_part_header` - 单部分header处理
- ✅ `test_authenticate_with_multi_part_header` - 多部分header处理

#### 工具函数测试 (3个测试)
- ✅ `test_get_ip_from_remote_addr` - 从REMOTE_ADDR获取IP
- ✅ `test_get_ip_from_x_forwarded_for` - 从X-Forwarded-For获取IP
- ✅ `test_get_ip_from_single_x_forwarded_for` - 单一IP的X-Forwarded-For

### 测试要点
- **Token生成**: 验证JWT token格式、payload内容、过期时间设置
- **认证流程**: 测试各种有效和无效的认证场景
- **错误处理**: 测试各种异常情况的错误消息
- **安全性**: 验证过期token、无效token、禁用用户的拒绝逻辑
- **IP提取**: 测试从不同HTTP头提取客户端IP地址

## 变更记录
### 2025-11-13
- **测试完成**: 添加15个单元测试，覆盖JWT认证核心功能
- **测试通过率**: 100% (15/15)
- **测试内容**: Token生成、认证流程、IP提取工具

### 2025-11-08 23:26:47
- 文档初始化，识别JWT认证核心功能