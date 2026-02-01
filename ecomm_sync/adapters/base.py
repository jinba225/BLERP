from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import requests
import time
import logging

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """平台适配器基类"""

    def __init__(self, account: 'PlatformAccount'):
        """
        初始化适配器

        Args:
            account: 平台账号实例
        """
        self.account = account
        self.auth_config = account.auth_config
        self.base_url = ''
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 2

        self.session = requests.Session()
        self._setup_session()

    @abstractmethod
    def _setup_session(self):
        """设置Session（认证方式不同）"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """测试连接"""
        pass

    # ========== 订单相关 ==========

    @abstractmethod
    def get_orders(self, start_date=None, end_date=None, **filters) -> List[Dict]:
        """获取订单列表

        Args:
            start_date: 开始日期
            end_date: 结束日期
            **filters: 其他过滤条件

        Returns:
            订单数据列表
        """
        pass

    @abstractmethod
    def get_order(self, order_id: str) -> Dict:
        """获取单个订单

        Args:
            order_id: 平台订单号

        Returns:
            订单数据字典
        """
        pass

    @abstractmethod
    def update_order_status(self, order_id: str, status: str, tracking_number: str = None) -> bool:
        """更新订单状态

        Args:
            order_id: 平台订单号
            status: 订单状态
            tracking_number: 快递单号

        Returns:
            是否成功
        """
        pass

    # ========== 商品相关 ==========

    @abstractmethod
    def get_products(self, **filters) -> List[Dict]:
        """获取商品列表

        Args:
            **filters: 过滤条件

        Returns:
            商品数据列表
        """
        pass

    @abstractmethod
    def get_product(self, product_id: str) -> Dict:
        """获取单个商品

        Args:
            product_id: 平台商品ID

        Returns:
            商品数据字典
        """
        pass

    @abstractmethod
    def create_product(self, product_data: Dict) -> Dict:
        """创建商品

        Args:
            product_data: 商品数据

        Returns:
            创建的商品数据
        """
        pass

    @abstractmethod
    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """更新商品

        Args:
            product_id: 平台商品ID
            product_data: 商品数据

        Returns:
            更新后的商品数据
        """
        pass

    @abstractmethod
    def delete_product(self, product_id: str) -> bool:
        """删除商品

        Args:
            product_id: 平台商品ID

        Returns:
            是否成功
        """
        pass

    # ========== 库存相关 ==========

    @abstractmethod
    def update_inventory(self, sku: str, quantity: int) -> bool:
        """更新库存

        Args:
            sku: SKU编码
            quantity: 库存数量

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def batch_update_inventory(self, updates: List[Dict]) -> List[Dict]:
        """批量更新库存

        Args:
            updates: 更新列表 [{'sku': 'xxx', 'quantity': 100}, ...]

        Returns:
            更新结果列表
        """
        pass

    # ========== 通用方法 ==========

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None,
        headers: Dict = None,
        retry_count: int = 0
    ) -> Dict:
        """发送HTTP请求（带重试）

        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求体数据
            params: URL参数
            headers: 请求头
            retry_count: 当前重试次数

        Returns:
            API响应数据

        Raises:
            Exception: 请求失败
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if self.base_url else endpoint

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout as e:
            logger.warning(f"请求超时 ({retry_count + 1}/{self.max_retries}): {endpoint}")
            if retry_count < self.max_retries - 1:
                time.sleep(self.retry_delay * (retry_count + 1))
                return self._make_request(method, endpoint, data, params, headers, retry_count + 1)
            raise Exception(f"请求超时: {url}")

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code

            if status_code == 429:
                logger.warning(f"API限流: {endpoint}")
                if retry_count < self.max_retries - 1:
                    time.sleep(5 ** (retry_count + 1))
                    return self._make_request(method, endpoint, data, params, headers, retry_count + 1)
                raise Exception(f"API限流: {url}")

            error_data = {}
            try:
                error_data = e.response.json()
            except:
                pass

            error_msg = error_data.get('message', str(e))
            logger.error(f"HTTP错误 {status_code}: {endpoint}, 错误: {error_msg}")

            raise Exception(f"HTTP错误 {status_code}: {url}")

        except Exception as e:
            logger.error(f"请求失败: {endpoint}, 错误: {e}")
            raise Exception(f"请求失败: {str(e)}")

    def _extract_price(self, price_str: str) -> float:
        """提取价格

        Args:
            price_str: 价格字符串

        Returns:
            价格数值
        """
        if not price_str:
            return 0.0

        price_str = str(price_str).replace('¥', '').replace(',', '').replace('元', '').strip()

        try:
            return float(price_str)
        except ValueError:
            return 0.0

    def _extract_stock(self, stock_str: str) -> int:
        """提取库存

        Args:
            stock_str: 库存字符串

        Returns:
            库存数量
        """
        if not stock_str:
            return 0

        stock_str = str(stock_str).strip().lower()

        if '有货' in stock_str or '库存' in stock_str:
            return 999
        elif '无货' in stock_str or '缺货' in stock_str:
            return 0
        elif '件' in stock_str:
            try:
                return int(''.join(filter(str.isdigit, stock_str)))
            except ValueError:
                return 0
        else:
            return 0

    def _map_status(self, status_str: str) -> str:
        """映射状态

        Args:
            status_str: 平台状态字符串

        Returns:
            ERP状态
        """
        if not status_str:
            return 'inactive'

        status_str = str(status_str).strip().lower()

        status_map = {
            'onsale': ['在售', '销售中', '有货', 'active', 'published'],
            'offshelf': ['下架', '已下架', 'offshelf', 'inactive', 'discontinued', 'draft'],
        }

        for erp_status, keywords in status_map.items():
            for keyword in keywords:
                if keyword in status_str:
                    return erp_status

        return 'inactive'

    def _normalize_images(self, images: List[str]) -> List[str]:
        """标准化图片URL

        Args:
            images: 图片URL列表

        Returns:
            标准化后的图片列表（最多6张）
        """
        normalized = []
        seen = set()

        for img in images:
            if not img:
                continue

            img_url = str(img).strip()

            if img_url in seen:
                continue
            seen.add(img_url)

            if not img_url.startswith('http'):
                continue

            normalized.append(img_url)

        return normalized[:6]

    def is_rate_limited(self, response_status: int = None, error_msg: str = '') -> bool:
        """判断是否被限流

        Args:
            response_status: 响应状态码
            error_msg: 错误消息

        Returns:
            是否被限流
        """
        if response_status == 429:
            return True

        rate_limit_keywords = [
            'rate limit', '频率限制', '访问频率',
            'too many requests', '请求过多',
            '限流', '访问过快'
        ]

        if error_msg:
            return any(keyword in error_msg.lower() for keyword in rate_limit_keywords)

        return False


def get_adapter(account: 'PlatformAccount') -> BaseAdapter:
    """
    工厂方法：获取对应平台的适配器实例

    Args:
        account: 平台账号实例

    Returns:
        适配器实例

    Raises:
        ValueError: 不支持的平台类型
    """
    from ecomm_sync.models import PlatformAccount

    platform_type = account.account_type

    if platform_type == 'amazon':
        from .amazon.mws_api import AmazonAdapter
        return AmazonAdapter(account)
    elif platform_type == 'ebay':
        from .ebay.trading_api import EbayAdapter
        return EbayAdapter(account)
    elif platform_type == 'aliexpress':
        from .aliexpress.api import AliexpressAdapter
        return AliexpressAdapter(account)
    elif platform_type == 'lazada':
        from .lazada.api import LazadaAdapter
        return LazadaAdapter(account)
    elif platform_type == 'shopify':
        from .shopify.api import ShopifyAdapter
        return ShopifyAdapter(account)
    elif platform_type == 'woo':
        from .woo.api import WooCommerceAdapter
        return WooCommerceAdapter(account)
    elif platform_type == 'jumia':
        from .jumia.adapter import JumiaAdapter
        return JumiaAdapter(account)
    elif platform_type == 'cdiscount':
        from .cdiscount.adapter import CdiscountAdapter
        return CdiscountAdapter(account)
    elif platform_type == 'shopee':
        from .shopee.adapter import ShopeeAdapter
        return ShopeeAdapter(account)
    elif platform_type == 'tiktok':
        from .tiktok.adapter import TikTokAdapter
        return TikTokAdapter(account)
    elif platform_type == 'temu':
        from .temu.adapter import TemuAdapter
        return TemuAdapter(account)
    elif platform_type == 'wish':
        from .wish.adapter import WishAdapter
        return WishAdapter(account)
    elif platform_type == 'mercadolibre':
        from .mercadolibre.adapter import MercadoLibreAdapter
        return MercadoLibreAdapter(account)
    else:
        raise ValueError(f'不支持的平台类型: {platform_type}')
