"""
拼多多采集适配器
支持拼多多开放平台API对接
"""
import re
import time
import hashlib
import logging
from typing import Dict, Any
from .base import BaseCollectAdapter
from ..exceptions import CollectException, DataParseException, APIResponseException


logger = logging.getLogger(__name__)


class PddCollectAdapter(BaseCollectAdapter):
    """
    拼多多采集适配器

    API文档：https://open.pinduoduo.com/application/document/browse

    特点：
    - 需要clientId和clientSecret
    - 签名算法：MD5(params_str + clientSecret)
    - 限流：40次/分钟
    - 支持商品详情、SKU、店铺信息采集
    """

    def __init__(self, platform_config):
        """
        初始化拼多多适配器

        Args:
            platform_config: Platform模型实例
        """
        super().__init__(platform_config)

        # 拼多多特有配置
        self.client_id = getattr(platform_config, "client_id", self.api_key)
        self.client_secret = getattr(platform_config, "client_secret", self.api_secret)

        # 拼多多API基础URL
        self.api_url = "https://gw-api.pinduoduo.com/api/router"

        # 拼多多API版本
        self.api_version = "V1"

        logger.info(f"初始化拼多多采集适配器: client_id={self.client_id}")

    def extract_item_id(self, item_url: str) -> str:
        """
        从拼多多链接提取商品ID

        Args:
            item_url: 拼多多商品链接

        Returns:
            str: 商品ID

        Example:
            >>> adapter = PddCollectAdapter(config)
            >>> item_id = adapter.extract_item_id('https://mobile.yangkeduo.com/goods.html?goods_id=123456')
            >>> print(item_id)  # '123456'
        """
        patterns = [
            r"/goods/(\d+)",
            r"goods_id=(\d+)",
            r'goods_id["\']:\s*["\'](\d+)["\']',
        ]

        for pattern in patterns:
            match = re.search(pattern, item_url)
            if match:
                item_id = match.group(1)
                logger.debug(f"从链接提取商品ID: {item_id}")
                return item_id

        raise DataParseException(f"无法从拼多多链接提取商品ID: {item_url}")

    def sign(self, params: Dict[str, Any]) -> str:
        """
        拼多多签名算法

        签名规则：
        1. 按参数名ASCII码升序排序
        2. 拼接成 key1value1key2value2... 格式
        3. 在末尾追加client_secret
        4. 进行MD5加密，转大写

        Args:
            params: 请求参数

        Returns:
            str: 签名字符串

        Example:
            >>> params = {'type': 'pdd.ddk.goods.detail', 'timestamp': '123456'}
            >>> sign = adapter.sign(params)
            >>> print(sign)  # 'ABC123...'
        """
        # 1. 排序参数
        sorted_params = sorted(params.items())

        # 2. 拼接字符串
        params_str = "".join([f"{k}{v}" for k, v in sorted_params])

        # 3. 追加密钥
        params_str += self.client_secret

        # 4. MD5加密并转大写
        sign = hashlib.md5(params_str.encode("utf-8")).hexdigest().upper()

        logger.debug(f"生成签名: {sign}")

        return sign

    def collect_item(self, item_url: str) -> Dict[str, Any]:
        """
        采集拼多多商品

        Args:
            item_url: 拼多多商品链接

        Returns:
            dict: 标准化采集数据

        Raises:
            DataParseException: 数据解析异常
            APIResponseException: API响应异常
            CollectException: 其他采集异常

        Example:
            >>> adapter = PddCollectAdapter(config)
            >>> data = adapter.collect_item('https://mobile.yangkeduo.com/goods.html?goods_id=123456')
            >>> print(data['product_name'])
        """
        try:
            # 1. 提取商品ID
            item_id = self.extract_item_id(item_url)

            # 2. 构造请求参数
            params = {
                "type": "pdd.ddk.goods.detail",
                "client_id": self.client_id,
                "access_token": getattr(self, "access_token", ""),
                "timestamp": str(int(time.time())),
                "format": "json",
                "version": self.api_version,
                "goods_id_list": f"[{item_id}]",
            }

            # 3. 生成签名
            params["sign"] = self.sign(params)

            # 4. 发送API请求
            logger.info(f"开始采集拼多多商品: goods_id={item_id}")
            response = self._make_request("GET", self.api_url, params=params)

            # 5. 检查响应
            if "error_response" in response:
                error_response = response["error_response"]
                raise APIResponseException(
                    self.platform_name,
                    error_response.get("error_code", "Unknown"),
                    error_response.get("error_msg", error_response.get("msg", "Unknown error")),
                )

            # 6. 提取商品数据
            if "goods_detail_get_response" not in response:
                raise DataParseException(f"拼多多API响应格式异常: {response}")

            goods_list = response["goods_detail_get_response"].get("goods_details", [])

            if not goods_list:
                raise DataParseException(f"未找到商品: goods_id={item_id}")

            raw_data = goods_list[0]

            # 7. 标准化数据
            normalized_data = self.normalize_data(raw_data)

            logger.info(f"拼多多商品采集成功: goods_id={item_id}")

            return normalized_data

        except (DataParseException, APIResponseException):
            raise
        except Exception as e:
            logger.error(f"采集拼多多商品失败: {e}")
            raise CollectException(
                code=500, msg=f"采集拼多多商品失败: {str(e)}", details={"item_url": item_url}
            )

    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化拼多多商品数据

        Args:
            raw_data: 拼多多原始数据

        Returns:
            dict: 标准化数据

        数据映射：
        - goods_id -> source_sku
        - goods_name -> product_name
        - goods_thumbnail_url -> main_image
        - min_group_price -> price (取最小团购价)
        - quantity -> stock
        - goods_desc -> description
        """
        try:
            # 提取价格（最小团购价，单位：分）
            min_group_price = raw_data.get("min_group_price", 0)
            price = min_group_price / 100  # 转换为元

            # 提取图片列表
            images = self._extract_images(raw_data)

            # 提取店铺信息
            mall_name = raw_data.get("mall_name", "拼多多店铺")
            shop_name = raw_data.get("shop_name", mall_name)

            # 构造标准化数据
            normalized = {
                # ========== 产品库字段 ==========
                "product_name": raw_data.get("goods_name", ""),
                "main_image": raw_data.get("goods_thumbnail_url", ""),
                "price": price,
                "stock": int(raw_data.get("quantity", 0)),
                "description": raw_data.get("goods_desc", ""),
                "category_id": raw_data.get("cat_id", ""),
                # ========== Listing字段 ==========
                "listing_title": raw_data.get("goods_name", "") + "[跨境精品]",
                "images": images,
                # SKU信息
                "skus": self._extract_skus(raw_data),
                # ========== 源数据 ==========
                "source_sku": str(raw_data.get("goods_id", "")),
                "source_platform": "pdd",
                "source_url": f"https://mobile.yangkeduo.com/goods.html?goods_id={raw_data.get('goods_id', '')}",
                # ========== 店铺信息 ==========
                "shop_name": shop_name,
                "shop_id": str(raw_data.get("mall_id", "")),
                # ========== 平台配置 ==========
                "platform_config": {
                    "pdd_cat_id": raw_data.get("cat_id", ""),
                    "pdd_mall_id": raw_data.get("mall_id", ""),
                    "pdd_mall_name": mall_name,
                    "pdd_sales": raw_data.get("sales", 0),
                    "pdd_min_group_price": min_group_price,
                },
                # ========== 原始数据（备用） ==========
                "raw_data": raw_data,
            }

            logger.debug(f"标准化拼多多数据: product_name={normalized['product_name']}")

            return normalized

        except Exception as e:
            logger.error(f"标准化拼多多数据失败: {e}")
            raise DataParseException(f"标准化拼多多数据失败: {str(e)}")

    def _extract_images(self, raw_data: Dict[str, Any]) -> list:
        """
        提取图片列表

        Args:
            raw_data: 原始数据

        Returns:
            list: 图片URL列表
        """
        images = []

        # 主图
        if "goods_thumbnail_url" in raw_data:
            images.append(raw_data["goods_thumbnail_url"])

        # 商品图片列表
        if "goods_gallery_urls" in raw_data:
            gallery_urls = raw_data["goods_gallery_urls"]
            if isinstance(gallery_urls, str):
                images.append(gallery_urls)
            elif isinstance(gallery_urls, list):
                images.extend(gallery_urls)

        # 去重并限制数量
        seen = set()
        unique_images = []
        for img in images:
            if img and img not in seen:
                seen.add(img)
                unique_images.append(img)

        return unique_images[:10]  # 最多保留10张

    def _extract_skus(self, raw_data: Dict[str, Any]) -> list:
        """
        提取SKU信息

        Args:
            raw_data: 原始数据

        Returns:
            list: SKU列表
        """
        skus = []

        try:
            # 拼多多的SKU信息在goods_specs字段
            specs_list = raw_data.get("specs_list", [])

            for spec in specs_list:
                sku = {
                    "sku_id": str(spec.get("spec_id", "")),
                    "sku_name": spec.get("spec_name", ""),
                    "price": spec.get("group_price", 0) / 100,  # 转换为元
                    "stock": int(spec.get("quantity", 0)),
                    "sku_image": spec.get("spec_image", ""),
                }
                skus.append(sku)

        except Exception as e:
            logger.warning(f"提取SKU信息失败: {e}")

        return skus
