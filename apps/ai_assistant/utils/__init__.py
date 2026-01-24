"""
API Key 加密工具

使用 Fernet 对称加密算法加密存储敏感的API密钥
"""

import os
from cryptography.fernet import Fernet
from django.conf import settings


class APIKeyEncryption:
    """API Key 加密工具类"""

    @staticmethod
    def _get_encryption_key() -> bytes:
        """
        获取加密密钥

        从环境变量或settings中获取加密密钥
        如果不存在则生成新密钥（仅开发环境）
        """
        # 优先从环境变量获取
        key = os.getenv('ENCRYPTION_KEY')

        if not key:
            # 从settings获取
            key = getattr(settings, 'ENCRYPTION_KEY', None)

        if not key:
            # 开发环境：生成临时密钥（生产环境应该报错）
            if settings.DEBUG:
                key = Fernet.generate_key().decode()
                print(f"⚠️  警告: 使用临时加密密钥。请在 .env 中设置 ENCRYPTION_KEY={key}")
            else:
                raise ValueError(
                    "未找到加密密钥！请在环境变量或settings.py中设置 ENCRYPTION_KEY"
                )

        # 确保key是bytes类型
        if isinstance(key, str):
            key = key.encode()

        return key

    @classmethod
    def encrypt(cls, plain_text: str) -> str:
        """
        加密明文

        Args:
            plain_text: 明文字符串

        Returns:
            加密后的字符串（Base64编码）
        """
        if not plain_text:
            return ''

        try:
            key = cls._get_encryption_key()
            f = Fernet(key)
            encrypted = f.encrypt(plain_text.encode())
            return encrypted.decode()
        except Exception as e:
            raise ValueError(f"加密失败: {str(e)}")

    @classmethod
    def decrypt(cls, encrypted_text: str) -> str:
        """
        解密密文

        Args:
            encrypted_text: 加密的字符串（Base64编码）

        Returns:
            解密后的明文字符串
        """
        if not encrypted_text:
            return ''

        try:
            key = cls._get_encryption_key()
            f = Fernet(key)
            decrypted = f.decrypt(encrypted_text.encode())
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"解密失败: {str(e)}")

    @classmethod
    def generate_key(cls) -> str:
        """
        生成新的加密密钥

        Returns:
            Base64编码的密钥字符串
        """
        return Fernet.generate_key().decode()


# 便捷函数
def encrypt_api_key(api_key: str) -> str:
    """加密API Key"""
    return APIKeyEncryption.encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """解密API Key"""
    return APIKeyEncryption.decrypt(encrypted_key)
