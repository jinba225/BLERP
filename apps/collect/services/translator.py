"""
翻译服务
支持多语言翻译
"""

from typing import Dict, Optional

import requests
from django.conf import settings

from .exceptions import TranslationException


class BaseTranslator:
    """翻译器基类"""

    def translate(self, text: str, target_language: str, source_language: str = "auto") -> str:
        """
        翻译文本

        Args:
            text: 待翻译文本
            target_language: 目标语言
            source_language: 源语言（auto为自动检测）

        Returns:
            str: 翻译结果
        """
        raise NotImplementedError("子类必须实现 translate 方法")


class GoogleTranslator(BaseTranslator):
    """Google翻译器"""

    def __init__(self, api_key: str = None):
        """
        初始化Google翻译器

        Args:
            api_key: Google翻译API密钥
        """
        self.api_key = api_key or settings.GOOGLE_TRANSLATE_API_KEY
        self.base_url = "https://translation.googleapis.com/language/translate/v2"

    def translate(self, text: str, target_language: str, source_language: str = "auto") -> str:
        """
        使用Google翻译API翻译文本

        Args:
            text: 待翻译文本
            target_language: 目标语言代码（如: en, zh, ja, ko等）
            source_language: 源语言代码（auto为自动检测）

        Returns:
            str: 翻译结果
        """
        if not self.api_key:
            raise TranslationException(text, target_language, "未配置Google翻译API密钥")

        try:
            params = {"q": text, "target": target_language, "key": self.api_key}

            if source_language != "auto":
                params["source"] = source_language

            response = requests.post(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            if "data" in result and "translations" in result["data"]:
                return result["data"]["translations"][0]["translatedText"]
            else:
                raise TranslationException(text, target_language, "翻译API响应格式错误")

        except requests.exceptions.RequestException as e:
            raise TranslationException(text, target_language, f"翻译请求失败: {str(e)}")
        except Exception as e:
            raise TranslationException(text, target_language, f"翻译失败: {str(e)}")


class BaiduTranslator(BaseTranslator):
    """百度翻译器"""

    def __init__(self, app_id: str = None, secret_key: str = None):
        """
        初始化百度翻译器

        Args:
            app_id: 百度翻译APP ID
            secret_key: 百度翻译密钥
        """
        self.app_id = app_id or settings.BAIDU_TRANSLATE_APP_ID
        self.secret_key = secret_key or settings.BAIDU_TRANSLATE_SECRET_KEY
        self.base_url = "https://fanyi-api.baidu.com/api/trans/vip/translate"

    def translate(self, text: str, target_language: str, source_language: str = "auto") -> str:
        """
        使用百度翻译API翻译文本

        Args:
            text: 待翻译文本
            target_language: 目标语言代码（如: en, zh, jp, kor等）
            source_language: 源语言代码（auto为自动检测）

        Returns:
            str: 翻译结果
        """
        if not self.app_id or not self.secret_key:
            raise TranslationException(text, target_language, "未配置百度翻译APP ID或密钥")

        import hashlib
        import random

        try:
            # 构造请求参数
            salt = str(random.randint(32768, 65536))
            sign_str = self.app_id + text + salt + self.secret_key
            sign = hashlib.md5(sign_str.encode()).hexdigest()

            params = {
                "q": text,
                "from": source_language,
                "to": target_language,
                "appid": self.app_id,
                "salt": salt,
                "sign": sign,
            }

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            if "error_code" in result:
                error_msg = result.get("error_msg", "未知错误")
                raise TranslationException(text, target_language, f"百度翻译API错误: {error_msg}")

            if "trans_result" in result and len(result["trans_result"]) > 0:
                return result["trans_result"][0]["dst"]
            else:
                raise TranslationException(text, target_language, "翻译API响应格式错误")

        except requests.exceptions.RequestException as e:
            raise TranslationException(text, target_language, f"翻译请求失败: {str(e)}")
        except Exception as e:
            raise TranslationException(text, target_language, f"翻译失败: {str(e)}")


class TranslatorFactory:
    """翻译器工厂"""

    @staticmethod
    def get_translator(translator_type: str = "baidu") -> BaseTranslator:
        """
        获取翻译器实例

        Args:
            translator_type: 翻译器类型（google, baidu）

        Returns:
            BaseTranslator: 翻译器实例
        """
        translators = {
            "google": GoogleTranslator,
            "baidu": BaiduTranslator,
        }

        if translator_type not in translators:
            raise TranslationException("", "", f"不支持的翻译器类型: {translator_type}")

        return translators[translator_type]()


def translate_text(
    text: str,
    target_language: str,
    translator_type: str = "baidu",
    source_language: str = "auto",
) -> str:
    """
    翻译文本的便捷函数

    Args:
        text: 待翻译文本
        target_language: 目标语言
        translator_type: 翻译器类型
        source_language: 源语言

    Returns:
        str: 翻译结果
    """
    translator = TranslatorFactory.get_translator(translator_type)
    return translator.translate(text, target_language, source_language)


def translate_product_data(
    product_data: Dict[str, any], target_language: str, translator_type: str = "baidu"
) -> Dict[str, any]:
    """
    翻译产品数据

    Args:
        product_data: 产品数据字典
        target_language: 目标语言
        translator_type: 翻译器类型

    Returns:
        dict: 翻译后的产品数据
    """
    # 需要翻译的字段
    fields_to_translate = [
        "product_name",
        "listing_title",
        "description",
        "specifications",
    ]

    translated_data = product_data.copy()
    translator = TranslatorFactory.get_translator(translator_type)

    for field in fields_to_translate:
        if field in translated_data and translated_data[field]:
            try:
                translated_data[f"{field}_translated"] = translator.translate(
                    translated_data[field], target_language, "zh"  # 假设源语言为中文
                )
            except TranslationException as e:
                print(f"翻译失败: {e.msg}")
                translated_data[f"{field}_translated"] = translated_data[field]

    return translated_data
