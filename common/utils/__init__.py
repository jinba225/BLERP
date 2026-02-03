"""
通用工具函数

从以下来源整合：
- 原根目录 utils/ (rbac.py)
- apps/core/utils/ (database_helper, document_number, code_generator)
- apps/ai_assistant/utils/ (cache, encryption, logger, permissions)
"""

# 核心工具 (来自 core)
from . import database_helper
from . import document_number
from . import code_generator

# 实用工具 (来自 ai_assistant)
from . import cache
from . import encryption
from . import logger
from . import permissions

# RBAC 工具 (来自根目录 utils)
from . import rbac

# AI Assistant 相关导出
from .encryption import APIKeyEncryption, encrypt_api_key, decrypt_api_key
from .cache import AIAssistantCache
from .logger import AIAssistantLogger
from .permissions import (
    has_custom_permission,
    get_user_permissions,
    get_user_roles,
    clear_user_permission_cache,
)

__all__ = [
    # 模块
    'database_helper',
    'document_number',
    'code_generator',
    'cache',
    'encryption',
    'logger',
    'permissions',
    'rbac',
    # AI Assistant 相关类和函数
    'APIKeyEncryption',
    'AIAssistantCache',
    'AIAssistantLogger',
    'has_custom_permission',
    'get_user_permissions',
    'get_user_roles',
    'clear_user_permission_cache',
    'encrypt_api_key',
    'decrypt_api_key',
]
