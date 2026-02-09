"""
采集适配器模块
采用适配器模式封装不同平台的采集逻辑
"""
import hashlib
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings

from ..exceptions import (
    APIResponseException,
    CollectException,
    DataParseException,
    NetworkException,
    PlatformConfigException,
)


class BaseCollectAdapter(ABC):
    """基础采集适配器：定义统一接口"""

    def __init__(self, platform_config):
        """
        初始化适配器

        Args:
            platform_config: Platform模型实例（包含api_key/api_secret/api_url等）
        """
        self.api_key = getattr(platform_config, "api_key", "")
        self.api_secret = getattr(platform_config, "api_secret", "")
        self.api_url = getattr(platform_config, "api_url", "")
        self.api_version = getattr(platform_config, "api_version", "2.0")
        self.platform_name = getattr(platform_config, "platform_name", "未知平台")
        self.platform_code = getattr(platform_config, "platform_code", "unknown")

        # 校验API配置
        if not all([self.api_key, self.api_secret, self.api_url]):
            raise PlatformConfigException(
                self.platform_name, "API配置不完整，请检查api_key, api_secret, api_url"
            )

        # OAuth相关
        self.access_token = getattr(platform_config, "access_token", "")
        self.refresh_token = getattr(platform_config, "refresh_token", "")

        # 请求超时设置
        self.timeout = 30

    @abstractmethod
    def collect_item(self, item_url: str) -> Dict[str, Any]:
        """
        采集单个商品

        Args:
            item_url: 商品链接

        Returns:
            dict: 标准化采集数据

        Raises:
            CollectException: 采集异常
        """
        pass

    def sign(self, params: Dict[str, Any]) -> str:
        """
        通用签名方法（各平台可重写）

        Args:
            params: 请求参数

        Returns:
            str: 签名字符串
        """
        # 按平台规则拼接参数+api_secret，做MD5/SHA256签名
        params_str = "".join([f"{k}{v}" for k, v in sorted(params.items())]) + self.api_secret
        return hashlib.md5(params_str.encode()).hexdigest()

    def _make_request(
        self,
        method: str,
        url: str,
        params: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
        headers: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        发起HTTP请求的通用方法

        Args:
            method: HTTP方法 (GET, POST, etc.)
            url: 请求URL
            params: URL参数
            json_data: JSON请求体
            headers: 请求头

        Returns:
            dict: 响应数据

        Raises:
            NetworkException: 网络异常
            APIResponseException: API响应异常
        """
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(
                    url, json=json_data, params=params, headers=headers, timeout=self.timeout
                )
            else:
                raise NetworkException(f"不支持的HTTP方法: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise NetworkException(f"{self.platform_name} API请求超时")
        except requests.exceptions.RequestException as e:
            raise NetworkException(f"{self.platform_name} API网络请求失败: {str(e)}")
        except ValueError as e:
            raise DataParseException(f"{self.platform_name} API响应数据格式错误: {str(e)}")

    def extract_item_id(self, item_url: str) -> str:
        """
        从商品链接中提取商品ID（需要子类实现）

        Args:
            item_url: 商品链接

        Returns:
            str: 商品ID
        """
        raise NotImplementedError("子类必须实现 extract_item_id 方法")

    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化采集数据（需要子类实现）

        Args:
            raw_data: 原始数据

        Returns:
            dict: 标准化数据
        """
        raise NotImplementedError("子类必须实现 normalize_data 方法")


class TaobaoCollectAdapter(BaseCollectAdapter):
    """淘宝采集适配器：对接淘宝开放平台API"""

    def extract_item_id(self, item_url: str) -> str:
        """从淘宝链接中提取商品ID"""
        patterns = [r"id=(\d+)", r"/item\.htm.*id=(\d+)", r"/(\d+)\.html"]

        for pattern in patterns:
            match = re.search(pattern, item_url)
            if match:
                return match.group(1)

        raise DataParseException(f"无法从链接中提取商品ID: {item_url}")

    def collect_item(self, item_url: str) -> Dict[str, Any]:
        """
        采集淘宝商品

        Args:
            item_url: 淘宝商品链接

        Returns:
            dict: 标准化采集数据
        """
        # 1. 提取商品ID
        try:
            item_id = self.extract_item_id(item_url)
        except DataParseException as e:
            raise e

        # 2. 构造淘宝开放平台API请求参数
        params = {
            "method": "taobao.item.get",
            "app_key": self.api_key,
            "v": self.api_version,
            "format": "json",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "num_iid": item_id,
            "fields": "num_iid,title,nick,pic_url,cid,price,type,delist_time,postage,score,volume,location,props_name,props,desc,sku,created,modified,approve_status",
        }

        # 3. 生成签名
        params["sign"] = self.sign(params)

        # 4. 调用淘宝API
        try:
            response = self._make_request("GET", self.api_url, params=params)
        except (NetworkException, DataParseException) as e:
            raise e

        # 5. 检查API响应
        if "error_response" in response:
            error_response = response["error_response"]
            raise APIResponseException(
                self.platform_name,
                error_response.get("code", "Unknown"),
                error_response.get("sub_msg", error_response.get("msg", "Unknown error")),
            )

        # 6. 提取商品数据
        if "item_get_response" not in response or "item" not in response["item_get_response"]:
            raise DataParseException("淘宝API响应数据格式异常")

        raw_item_data = response["item_get_response"]["item"]

        # 7. 标准化数据
        return self.normalize_data(raw_item_data)

    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化淘宝商品数据

        Args:
            raw_data: 淘宝原始数据

        Returns:
            dict: 标准化数据
        """
        return {
            # 产品库字段
            "product_name": raw_data.get("title", ""),
            "main_image": raw_data.get("pic_url", ""),
            "price": float(raw_data.get("price", 0)),
            "stock": int(raw_data.get("num", 0)),
            "description": raw_data.get("desc", ""),
            "category_id": raw_data.get("cid", ""),
            "shop_name": raw_data.get("nick", ""),
            # Listing字段
            "listing_title": raw_data.get("title", "") + "[跨境精品]",
            "images": self._extract_images(raw_data),
            # 源数据
            "source_sku": str(raw_data.get("num_iid", "")),
            "source_platform": "taobao",
            "source_url": f"https://item.taobao.com/item.htm?id={raw_data.get('num_iid', '')}",
            # 平台配置
            "platform_config": {
                "taobao_props": raw_data.get("props", {}),
                "taobao_location": raw_data.get("location", {}),
                "taobao_created": raw_data.get("created", ""),
                "taobao_modified": raw_data.get("modified", ""),
            },
            # 原始数据（备用）
            "raw_data": raw_data,
        }

    def _extract_images(self, raw_data: Dict[str, Any]) -> List[str]:
        """提取图片列表"""
        images = []

        # 主图
        if "pic_url" in raw_data:
            images.append(raw_data["pic_url"])

        # SKU图片
        if "sku" in raw_data and "properties" in raw_data["sku"]:
            for prop in raw_data["sku"]["properties"]:
                if "pic_url" in prop:
                    images.append(prop["pic_url"])

        # 描述中的图片（从desc字段中提取）
        desc = raw_data.get("desc", "")
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
        desc_images = re.findall(img_pattern, desc)
        images.extend(desc_images[:5])  # 最多取5张描述图

        # 去重
        return list(set(images))


class One688CollectAdapter(BaseCollectAdapter):
    """1688采集适配器：对接1688开放平台API"""

    def extract_item_id(self, item_url: str) -> str:
        """从1688链接中提取商品ID"""
        patterns = [r"/offer/(\d+)\.html", r"offerId=(\d+)", r"/(\d+)\.html"]

        for pattern in patterns:
            match = re.search(pattern, item_url)
            if match:
                return match.group(1)

        raise DataParseException(f"无法从链接中提取商品ID: {item_url}")

    def collect_item(self, item_url: str) -> Dict[str, Any]:
        """
        采集1688商品

        Args:
            item_url: 1688商品链接

        Returns:
            dict: 标准化采集数据
        """
        # 1. 提取商品ID
        try:
            item_id = self.extract_item_id(item_url)
        except DataParseException as e:
            raise e

        # 2. 构造1688 API请求参数
        params = {
            "method": "alibaba.product.get",
            "app_key": self.api_key,
            "v": self.api_version,
            "format": "json",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "offerId": item_id,
            "fields": "offerId,subject,imageList,skuInfos,priceRangeInfo,amountOnSale,company,category,description,details",
        }

        # 3. 生成签名（1688签名规则可能不同）
        params["sign"] = self.sign(params)

        # 4. 调用1688 API
        try:
            response = self._make_request("GET", self.api_url, params=params)
        except (NetworkException, DataParseException) as e:
            raise e

        # 5. 检查API响应
        if "error_response" in response:
            error_response = response["error_response"]
            raise APIResponseException(
                self.platform_name,
                error_response.get("code", "Unknown"),
                error_response.get("sub_msg", error_response.get("msg", "Unknown error")),
            )

        # 6. 提取商品数据
        if (
            "product_get_response" not in response
            or "offer" not in response["product_get_response"]
        ):
            raise DataParseException("1688 API响应数据格式异常")

        raw_item_data = response["product_get_response"]["offer"]

        # 7. 标准化数据
        return self.normalize_data(raw_item_data)

    def normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化1688商品数据

        Args:
            raw_data: 1688原始数据

        Returns:
            dict: 标准化数据
        """
        # 提取价格范围
        price_range = raw_data.get("priceRangeInfo", {})
        min_price = float(price_range.get("minPrice", 0))
        max_price = float(price_range.get("maxPrice", 0))
        avg_price = (min_price + max_price) / 2 if min_price and max_price else 0

        # 提取图片
        image_list = raw_data.get("imageList", {})
        images = []
        if isinstance(image_list, dict):
            images = [
                image_list.get(f"img{i}", "") for i in range(1, 10) if f"img{i}" in image_list
            ]
        elif isinstance(image_list, list):
            images = image_list

        # 提取公司信息
        company = raw_data.get("company", {})
        company_name = company.get("companyName", "")

        return {
            # 产品库字段
            "product_name": raw_data.get("subject", ""),
            "main_image": images[0] if images else "",
            "price": avg_price,
            "stock": int(raw_data.get("amountOnSale", 0)),
            "description": raw_data.get("description", ""),
            "category_id": raw_data.get("category", ""),
            "shop_name": company_name,
            # Listing字段
            "listing_title": raw_data.get("subject", "") + "[跨境精品]",
            "images": images,
            # 源数据
            "source_sku": str(raw_data.get("offerId", "")),
            "source_platform": "1688",
            "source_url": f"https://detail.1688.com/offer/{raw_data.get('offerId', '')}.html",
            # 平台配置
            "platform_config": {
                "alibaba_company": company_name,
                "alibaba_category": raw_data.get("category", ""),
                "alibaba_created": raw_data.get("gmtCreate", ""),
            },
            # 原始数据（备用）
            "raw_data": raw_data,
        }


def get_collect_adapter(platform_config) -> BaseCollectAdapter:
    """
    采集适配器工厂

    Args:
        platform_config: Platform模型实例

    Returns:
        BaseCollectAdapter子类实例

    Raises:
        CollectException: 不支持的平台
    """
    platform_code = getattr(platform_config, "platform_code", "").lower()

    adapter_map = {
        "taobao": TaobaoCollectAdapter,
        "1688": One688CollectAdapter,
        # 新增采集平台：在这里添加映射
        # "pdd": PddCollectAdapter,
        # "jd": JdCollectAdapter,
    }

    if platform_code not in adapter_map:
        raise CollectException(
            code=400,
            msg=f"暂不支持采集{getattr(platform_config, 'platform_name', '未知')}平台",
            details={"platform_code": platform_code},
        )

    return adapter_map[platform_code](platform_config)
