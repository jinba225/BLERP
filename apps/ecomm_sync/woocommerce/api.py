import requests
from typing import Dict, List, Optional
from django.conf import settings
from apps.ecomm_sync.models import WooShopConfig


class WooCommerceAPIError(Exception):
    """WooCommerce API错误"""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class WooCommerceAPI:
    """WooCommerce REST API客户端"""

    def __init__(self, shop_config: WooShopConfig):
        """
        初始化WooCommerce API客户端

        Args:
            shop_config: WooCommerce店铺配置
        """
        self.shop_config = shop_config
        self.base_url = f"{shop_config.shop_url.rstrip('/')}/wp-json/wc/v3"
        self.consumer_key = shop_config.consumer_key
        self.consumer_secret = shop_config.consumer_secret
        self.timeout = getattr(settings, 'ECOMM_SYNC_TIMEOUT', 30)

        self.session = requests.Session()
        self.session.auth = (self.consumer_key, self.consumer_secret)
        self.session.headers.update({
            'User-Agent': 'Django-ERP-EcommSync/1.0',
            'Accept': 'application/json',
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        data: dict = None,
        params: dict = None
    ) -> dict:
        """
        发送HTTP请求

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE)
            endpoint: API端点
            data: 请求数据
            params: URL参数

        Returns:
            API响应数据

        Raises:
            WooCommerceAPIError: API请求失败
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:
            raise WooCommerceAPIError(
                f"请求超时: {url}",
                status_code=408
            )

        except requests.exceptions.HTTPError as e:
            error_data = {}
            try:
                error_data = e.response.json()
            except:
                pass

            raise WooCommerceAPIError(
                f"HTTP错误: {e.response.status_code}",
                status_code=e.response.status_code,
                response_data=error_data
            )

        except Exception as e:
            raise WooCommerceAPIError(
                f"请求失败: {str(e)}"
            )

    def get_product(self, product_id: int) -> dict:
        """
        获取单个产品

        Args:
            product_id: 产品ID

        Returns:
            产品数据
        """
        return self._request('GET', f'/products/{product_id}')

    def get_products(
        self,
        page: int = 1,
        per_page: int = 100,
        **filters
    ) -> List[dict]:
        """
        获取产品列表

        Args:
            page: 页码
            per_page: 每页数量
            **filters: 过滤条件

        Returns:
            产品列表
        """
        params = {'page': page, 'per_page': per_page}
        params.update(filters)

        return self._request('GET', '/products', params=params)

    def create_product(self, product_data: dict) -> dict:
        """
        创建产品

        Args:
            product_data: 产品数据

        Returns:
            创建的产品数据
        """
        return self._request('POST', '/products', data=product_data)

    def update_product(self, product_id: int, product_data: dict) -> dict:
        """
        更新产品

        Args:
            product_id: 产品ID
            product_data: 产品数据

        Returns:
            更新后的产品数据
        """
        return self._request('PUT', f'/products/{product_id}', data=product_data)

    def batch_update_products(self, updates: List[dict]) -> dict:
        """
        批量更新产品

        Args:
            updates: 更新列表 [{'id': 123, 'regular_price': '99.99'}, ...]

        Returns:
            批量更新结果
        """
        return self._request('POST', '/products/batch', data={'update': updates})

    def delete_product(self, product_id: int, force: bool = False) -> dict:
        """
        删除产品

        Args:
            product_id: 产品ID
            force: 是否强制删除

        Returns:
            删除结果
        """
        params = {'force': force} if force else {}
        return self._request('DELETE', f'/products/{product_id}', params=params)

    def get_categories(self, **filters) -> List[dict]:
        """
        获取分类列表

        Args:
            **filters: 过滤条件

        Returns:
            分类列表
        """
        return self._request('GET', '/products/categories', params=filters)

    def create_category(self, category_data: dict) -> dict:
        """
        创建分类

        Args:
            category_data: 分类数据

        Returns:
            创建的分类数据
        """
        return self._request('POST', '/products/categories', data=category_data)

    def upload_image(self, image_file: str) -> dict:
        """
        上传图片

        Args:
            image_file: 图片文件路径

        Returns:
            上传的图片数据
        """
        url = f"{self.base_url}/media"

        with open(image_file, 'rb') as f:
            files = {'file': f}
            response = self.session.post(url, files=files, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

    def test_connection(self) -> bool:
        """
        测试API连接

        Returns:
            连接是否成功
        """
        try:
            self.get_products(per_page=1)
            return True
        except Exception:
            return False

    @classmethod
    def get_active(cls) -> Optional['WooCommerceAPI']:
        """
        获取激活的WooCommerce API客户端

        Returns:
            激活的API客户端实例
        """
        try:
            shop_config = WooShopConfig.objects.filter(is_active=True).first()
            if shop_config:
                return cls(shop_config)
            return None
        except Exception:
            return None
