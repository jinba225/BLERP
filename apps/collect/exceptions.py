"""
统一异常定义
"""
from django.core.exceptions import ValidationError


class CollectException(Exception):
    """采集异常基类"""

    def __init__(self, code=500, msg="采集异常", details=None):
        self.code = code
        self.msg = msg
        self.details = details or {}
        super().__init__(self.msg)

    def to_dict(self):
        """转换为字典"""
        return {"code": self.code, "msg": self.msg, "details": self.details}


class PlatformConfigException(CollectException):
    """平台配置异常"""

    def __init__(self, platform_name, msg="平台配置不完整"):
        super().__init__(code=400, msg=f"{platform_name}: {msg}")
        self.platform_name = platform_name


class NetworkException(CollectException):
    """网络请求异常"""

    def __init__(self, msg="网络请求失败"):
        super().__init__(code=500, msg=msg)


class APIResponseException(CollectException):
    """API响应异常"""

    def __init__(self, platform_name, error_code, error_msg):
        super().__init__(
            code=500,
            msg=f"{platform_name} API调用失败: {error_msg}",
            details={"error_code": error_code},
        )
        self.platform_name = platform_name


class DataParseException(CollectException):
    """数据解析异常"""

    def __init__(self, msg="数据解析失败", field=None, value=None):
        super().__init__(code=422, msg=msg)
        self.field = field
        self.value = value


class ProductCreateException(CollectException):
    """产品创建异常"""

    def __init__(self, msg="产品创建失败", product_data=None):
        super().__init__(code=422, msg=msg)
        self.product_data = product_data


class ListingCreateException(CollectException):
    """Listing创建异常"""

    def __init__(self, msg="Listing创建失败", listing_data=None):
        super().__init__(code=422, msg=msg)
        self.listing_data = listing_data


class SyncException(CollectException):
    """同步异常"""

    def __init__(self, msg="同步失败", platform_name=None):
        if platform_name:
            msg = f"{platform_name} 同步失败"
        super().__init__(code=500, msg=msg)
        self.platform_name = platform_name


class ImageDownloadException(CollectException):
    """图片下载异常"""

    def __init__(self, url, msg="图片下载失败"):
        super().__init__(code=500, msg=f"{url}: {msg}")
        self.url = url


class TranslationException(CollectException):
    """翻译异常"""

    def __init__(self, text, target_language, msg="翻译失败"):
        super().__init__(code=500, msg=f"翻译失败: {text[:50]}... -> {target_language}")
        self.text = text
        self.target_language = target_language
