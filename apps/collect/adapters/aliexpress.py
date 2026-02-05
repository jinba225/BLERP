"""
阿里国际站（AliExpress）采集适配器
支持AliExpress开放平台API对接
"""
import re
import time
import hmac
import hashlib
import base64
import logging
from typing import Dict, Any, List
from .base import BaseCollectAdapter
from ..exceptions import (
    CollectException,
    DataParseException,
    APIResponseException
)


logger = logging.getLogger(__name__)


class AliExpressCollectAdapter(BaseCollectAdapter):
    """
    阿里国际站采集适配器

    API文档：https://developers.aliexpress.com/en/doc.htm

    特点：
    - OAuth 2.0认证
    - 签名算法：HMAC-SHA256
    - 支持多语言（en, ru, pt, es, fr）
    - 限流：严格限制
    - SKU信息复杂
    """

    def __init__(self, platform_config):
        """
        初始化AliExpress适配器

        Args:
            platform_config: Platform模型实例
        """
        super().__init__(platform_config)

        # AliExpress特有配置
        self.app_key = getattr(platform_config, 'app_key', self.api_key)
        self.app_secret = getattr(platform_config, 'app_secret', self.api_secret)

        # AliExpress API基础URL
        self.api_url = 'https://api.aliexpress.com'  # 生产环境

        # API版本
        self.api_version = '1.0'

        # 默认语言
        self.language = 'en'  # en, ru, pt, es, fr

        logger.info(f"初始化AliExpress采集适配器: app_key={self.app_key}")

    def extract_item_id(self, item_url: str) -> str:
        """
        从AliExpress链接提取商品ID

        Args:
            item_url: AliExpress商品链接

        Returns:
            str: 商品ID

        Example:
            >>> adapter = AliExpressCollectAdapter(config)
            >>> item_id = adapter.extract_item_id('https://www.aliexpress.com/item/1005001234567890.html')
            >>> print(item_id)  # '1005001234567890'
        """
        patterns = [
            r'/item/(\d+)\.html',
            r'productId=(\d+)',
            r'product_id["\']:\s*["\'](\d+)["\']',
        ]

        for pattern in patterns:
            match = re.search(pattern, item_url)
            if match:
                item_id = match.group(1)
                logger.debug(f"从链接提取商品ID: {item_id}")
                return item_id

        raise DataParseException(f"无法从AliExpress链接提取商品ID: {item_url}")

    def sign(self, params: Dict[str, Any]) -> str:
        """
        AliExpress签名算法（HMAC-SHA256）

        签名规则：
        1. 按参数名ASCII码升序排序
        2. 拼接成 key1value1key2value2... 格式
        3. 计算HMAC-SHA256
        4. Base64编码

        Args:
            params: 请求参数

        Returns:
            str: 签名字符串

        Example:
            >>> params = {'method': 'getProductDetail', 'timestamp': '123456'}
            >>> sign = adapter.sign(params)
            >>> print(sign)  # 'abc123...'
        """
        # 1. 排序参数
        sorted_params = sorted(params.items())

        # 2. 拼接字符串
        params_str = "".join([f"{k}{v}" for k, v in sorted_params])

        # 3. HMAC-SHA256加密
        signature = hmac.new(
            self.app_secret.encode('utf-8'),
            params_str.encode('utf-8'),
            hashlib.sha256
        ).digest()

        # 4. Base64编码
        sign = base64.b64encode(signature).decode('utf-8')

        logger.debug(f"生成签名: {sign}")

        return sign

    def collect_item(self, item_url: str) -> Dict[str, Any]:
        """
        采集AliExpress商品

        Args:
            item_url: AliExpress商品链接

        Returns:
            dict: 标准化采集数据

        Raises:
            DataParseException: 数据解析异常
            APIResponseException: API响应异常
            CollectException: 其他采集异常

        Example:
            >>> adapter = AliExpressCollectAdapter(config)
            >>> data = adapter.collect_item('https://www.aliexpress.com/item/1005001234567890.html')
            >>> print(data['product_name'])
        """
        try:
            # 1. 提取商品ID
            product_id = self.extract_item_id(item_url)

            # 2. 构造请求参数
            timestamp = str(int(time.time() * 1000))
            params = {
                'method': 'getProductDetail',
                'app_key': self.app_key,
                'timestamp': timestamp,
                'format': 'json',
                'v': self.api_version,
                'language': self.language,
                'productId': product_id,
                'localCountry': 'US',  # 可选：目标国家
            }

            # 3. 生成签名
            params['sign'] = self.sign(params)

            # 4. 发送API请求
            logger.info(f"开始采集AliExpress商品: product_id={product_id}")
            response = self._make_request('POST', self.api_url, json_data=params)

            # 5. 检查响应
            if 'error_response' in response:
                error_response = response['error_response']
                raise APIResponseException(
                    self.platform_name,
                    error_response.get('code', 'Unknown'),
                    error_response.get('msg', error_response.get('message', 'Unknown error'))
                )

            # 6. 提取商品数据
            if 'result' not in response:
                raise DataParseException(f"AliExpress API响应格式异常: {response}")

            product_data = response['result']

            # 7. 标准化数据
            normalized_data = self.normalize_data(product_data)

            logger.info(f"AliExpress商品采集成功: product_id={product_id}")

            return normalized_data

        except (DataParseException, APIResponseException):
            raise
        except Exception as e:
            logger.error(f"采集AliExpress商品失败: {e}")
            raise CollectException(
                code=500,
                msg=f"采集AliExpress商品失败: {str(e)}",
                details={'item_url': item_url}
            )

    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化AliExpress商品数据

        Args:
            raw_data: AliExpress原始数据

        Returns:
            dict: 标准化数据

        数据映射：
        - productId -> source_sku
        - subject -> product_name
        - imageUrl -> main_image
        - originalPrice -> price
        - stock -> stock
        - description -> description
        """
        try:
            # 提取价格（美元）
            original_price = raw_data.get('originalPrice', {})
            price = float(original_price.get('value', 0))

            # 提取图片列表
            images = self._extract_images(raw_data)

            # 提取店铺信息
            shop_name = raw_data.get('sellerName', 'AliExpress Store')

            # 构造标准化数据
            normalized = {
                # ========== 产品库字段 ==========
                'product_name': raw_data.get('subject', ''),
                'main_image': raw_data.get('imageUrl', ''),
                'price': price,
                'stock': int(raw_data.get('stock', 0)),
                'description': raw_data.get('description', ''),

                # ========== Listing字段 ==========
                'listing_title': raw_data.get('subject', '') + '[Cross-border]',
                'images': images,

                # SKU信息
                'skus': self._extract_skus(raw_data),

                # ========== 源数据 ==========
                'source_sku': str(raw_data.get('productId', '')),
                'source_platform': 'aliexpress',
                'source_url': f"https://www.aliexpress.com/item/{raw_data.get('productId', '')}.html",

                # ========== 店铺信息 ==========
                'shop_name': shop_name,
                'shop_id': str(raw_data.get('sellerId', '')),

                # ========== 平台配置 ==========
                'platform_config': {
                    'aliexpress_product_id': raw_data.get('productId', ''),
                    'aliexpress_seller_id': raw_data.get('sellerId', ''),
                    'aliexpress_category_id': raw_data.get('categoryId', ''),
                    'aliexpress_original_price': price,
                    'aliexpress_sale_price': raw_data.get('salePrice', {}).get('value', price),
                    'aliexpress_language': self.language,
                },

                # ========== 原始数据（备用） ==========
                'raw_data': raw_data,
            }

            logger.debug(f"标准化AliExpress数据: product_name={normalized['product_name']}")

            return normalized

        except Exception as e:
            logger.error(f"标准化AliExpress数据失败: {e}")
            raise DataParseException(f"标准化AliExpress数据失败: {str(e)}")

    def _extract_images(self, raw_data: Dict[str, Any]) -> List[str]:
        """
        提取图片列表

        Args:
            raw_data: 原始数据

        Returns:
            list: 图片URL列表
        """
        images = []

        # 主图
        if 'imageUrl' in raw_data:
            images.append(raw_data['imageUrl'])

        # 商品图片列表
        if 'imageUrls' in raw_data:
            image_urls = raw_data['imageUrls']
            if isinstance(image_urls, list):
                images.extend(image_urls)

        # SKU图片
        if 'sku' in raw_data:
            sku_list = raw_data.get('sku', [])
            if isinstance(sku_list, list):
                for sku in sku_list:
                    if 'imageUrl' in sku:
                        images.append(sku['imageUrl'])

        # 去重并限制数量
        seen = set()
        unique_images = []
        for img in images:
            if img and img not in seen:
                seen.add(img)
                unique_images.append(img)

        return unique_images[:10]  # 最多保留10张

    def _extract_skus(self, raw_data: Dict[str, Any]) -> List[Dict]:
        """
        提取SKU信息

        Args:
            raw_data: 原始数据

        Returns:
            list: SKU列表
        """
        skus = []

        try:
            # AliExpress的SKU信息在sku字段
            sku_list = raw_data.get('sku', [])

            if not isinstance(sku_list, list):
                return skus

            for sku_data in sku_list:
                sku = {
                    'sku_id': str(sku_data.get('skuId', '')),
                    'sku_name': sku_data.get('skuProp', ''),
                    'price': float(sku_data.get('salePrice', {}).get('value', 0)),
                    'stock': int(sku_data.get('stock', 0)),
                    'sku_image': sku_data.get('imageUrl', ''),
                    'attributes': self._extract_sku_attributes(sku_data),
                }
                skus.append(sku)

        except Exception as e:
            logger.warning(f"提取SKU信息失败: {e}")

        return skus

    def _extract_sku_attributes(self, sku_data: Dict[str, Any]) -> Dict[str, str]:
        """
        提取SKU属性

        Args:
            sku_data: SKU数据

        Returns:
            dict: SKU属性
        """
        attributes = {}

        try:
            # 提取SKU属性（如颜色、尺寸等）
            sku_props = sku_data.get('skuPropInfos', [])

            if isinstance(sku_props, list):
                for prop in sku_props:
                    prop_name = prop.get('attrName', '')
                    prop_value = prop.get('attrValue', '')
                    if prop_name and prop_value:
                        attributes[prop_name] = prop_value

        except Exception as e:
            logger.warning(f"提取SKU属性失败: {e}")

        return attributes

    def set_language(self, language: str):
        """
        设置采集语言

        Args:
            language: 语言代码（en, ru, pt, es, fr）

        Example:
            >>> adapter = AliExpressCollectAdapter(config)
            >>> adapter.set_language('ru')  # 俄语
            >>> data = adapter.collect_item(url)
        """
        supported_languages = ['en', 'ru', 'pt', 'es', 'fr']

        if language not in supported_languages:
            logger.warning(f"不支持的语言: {language}，使用默认语言en")
            self.language = 'en'
        else:
            self.language = language

        logger.info(f"设置采集语言: {self.language}")
