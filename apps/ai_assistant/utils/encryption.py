"""
API Key 加密工具

用于加密/解密 AI 服务的 API Key
"""

import base64

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class APIKeyEncryption:
    """API Key 加密类"""

    def __init__(self, encryption_key=None):
        """初始化加密器

        Args:
            encryption_key: 加密密钥（32字节的base64编码字符串）
                           如果未提供，则从 settings.ENCRYPTION_KEY 获取
                           如果也没有，则使用固定密钥（仅开发环境）
        """
        if encryption_key:
            key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        elif hasattr(settings, "ENCRYPTION_KEY") and settings.ENCRYPTION_KEY:
            key = (
                settings.ENCRYPTION_KEY.encode()
                if isinstance(settings.ENCRYPTION_KEY, str)
                else settings.ENCRYPTION_KEY
            )
        else:
            # 开发环境使用固定密钥（生产环境必须配置 ENCRYPTION_KEY）
            if settings.DEBUG:
                key = b"development-key-for-testing-only-12345678"
            else:
                raise ImproperlyConfigured(
                    "ENCRYPTION_KEY must be set in production environment. "
                    "Please set it in your .env file: ENCRYPTION_KEY=your-32-byte-key"
                )

        # 确保密钥长度正确（Fernet 需要的 base64 编码的 32 字节密钥）
        if len(key) != 44:
            # 如果不是44字符的base64字符串，则将其转换为 Fernet 密钥
            import hashlib

            key = base64.urlsafe_b64encode(hashlib.sha256(key).digest())

        self.cipher = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """加密明文

        Args:
            plaintext: 明文（API Key）

        Returns:
            加密后的 base64 字符串
        """
        if not plaintext:
            return ""

        encrypted = self.cipher.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        """解密密文

        Args:
            ciphertext: 加密后的 base64 字符串

        Returns:
            解密后的明文（API Key）
        """
        if not ciphertext:
            return ""

        try:
            encrypted = base64.b64decode(ciphertext.encode())
            decrypted = self.cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt API key: {str(e)}")


# 创建全局加密器实例
_global_encryption = None


def get_encryption():
    """获取全局加密器实例"""
    global _global_encryption
    if _global_encryption is None:
        _global_encryption = APIKeyEncryption()
    return _global_encryption


def encrypt_api_key(api_key: str) -> str:
    """加密 API Key

    Args:
        api_key: API Key 明文

    Returns:
        加密后的字符串
    """
    return get_encryption().encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """解密 API Key

    Args:
        encrypted_key: 加密的 API Key

    Returns:
        API Key 明文
    """
    return get_encryption().decrypt(encrypted_key)
