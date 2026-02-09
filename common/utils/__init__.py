"""
通用工具函数

从以下来源整合：
- 原根目录 utils/ (rbac.py)
- apps/core/utils/ (database_helper, document_number, code_generator)
- apps/ai_assistant/utils/ (cache, encryption, logger, permissions)
"""

# RBAC 工具 (来自根目录 utils)
# 实用工具 (来自 ai_assistant)
# 核心工具 (来自 core)
from . import (
    cache,
    code_generator,
    database_helper,
    document_number,
    encryption,
    logger,
    permissions,
    rbac,
)
from .cache import AIAssistantCache

# Core 工具导出
from .document_number import DocumentNumberGenerator

# AI Assistant 相关导出
from .encryption import APIKeyEncryption, decrypt_api_key, encrypt_api_key
from .logger import AIAssistantLogger
from .permissions import (
    clear_user_permission_cache,
    get_user_permissions,
    get_user_roles,
    has_custom_permission,
)

__all__ = [
    # 模块
    "database_helper",
    "document_number",
    "code_generator",
    "cache",
    "encryption",
    "logger",
    "permissions",
    "rbac",
    # AI Assistant 相关类和函数
    "APIKeyEncryption",
    "AIAssistantCache",
    "AIAssistantLogger",
    "has_custom_permission",
    "get_user_permissions",
    "get_user_roles",
    "clear_user_permission_cache",
    "encrypt_api_key",
    "decrypt_api_key",
    # Core 工具类
    "DocumentNumberGenerator",
]
