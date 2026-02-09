"""
TikTok Shop电商平台适配器

TikTok Shop是TikTok旗下的电商平台
"""
from ..base import BaseAdapter
from typing import Dict, List
import hashlib
import hmac
import base64
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TikTokAdapter(BaseAdapter):
    """TikTok Shop电商平台适配器"""

    def __init__(self, account: "PlatformAccount"):
        super().__init__(account)

        # TikTok Shop有全球版和地区版
        region = self.auth_config.get("region", "global").lower()
        region_map = {
            "global": "https://open-api.tiktokglobalshop.com",
            "us": "https://open-api.tiktokglobalshop.com",
            "uk": "https://open-api.tiktokglobalshop.com",
            "sea": "https://open-api.tiktokglobalshop.com",
        }
        self.base_url = region_map.get(region, "https://open-api.tiktokglobalshop.com")
        self.api_version = "v1"

        # 从auth_config获取认证信息
        self.app_key = self.auth_config.get("app_key")
        self.app_secret = self.auth_config.get("app_secret")
        self.shop_id = self.auth_config.get("shop_id")

        if not self.app_key or not self.app_secret or not self.shop_id:
            raise ValueError("TikTok Shop API配置不完整，需要app_key、app_secret和shop_id")

    def _setup_session(self):
        """设置Session认证头"""
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-tts-access-token": self.auth_config.get("access_token", ""),
            }
        )

    def _generate_signature(self, path: str, params: Dict, body: Dict = None) -> str:
        """生成API签名

        TikTok Shop使用HMAC-SHA256签名
        """
        # 添加时间戳
        timestamp = str(int(datetime.now().timestamp()))

        # 构建签名字符串
        # 格式: app_key + path + sorted_params + timestamp + app_secret
        sorted_params = sorted(params.items())
        query_string = "&".join([f"{k}={v}" for k, v in sorted_params])

        body_str = ""
        if body:
            body_str = json.dumps(body, separators=(",", ":"), sort_keys=True)

        sign_str = f"{self.app_key}{path}{query_string}{timestamp}{body_str}"

        # 使用HMAC-SHA256签名并转换为十六进制
        signature = hmac.new(
            self.app_secret.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return signature

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            params = {"app_key": self.app_key, "shop_id": self.shop_id}

            path = "/api/v1/orders/auth/test"
            signature = self._generate_signature(path, params)
            params["sign"] = signature
            params["timestamp"] = str(int(datetime.now().timestamp()))

            response = self._make_request("GET", path, params=params)
            return response.get("code") == 0
        except Exception as e:
            logger.error(f"TikTok Shop连接测试失败: {e}")
            return False

    def get_orders(self, start_date=None, end_date=None, **filters) -> List[Dict]:
        """获取订单列表"""
        params = {
            "app_key": self.app_key,
            "shop_id": self.shop_id,
            "page_size": filters.get("limit", 100),
            "page_number": filters.get("offset", 0) + 1,
            "order_status": filters.get("status", ""),
        }

        if start_date:
            params["create_time_from"] = int(start_date.timestamp())
        if end_date:
            params["create_time_to"] = int(end_date.timestamp())

        path = "/api/v1/orders/query"
        signature = self._generate_signature(path, params)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("GET", path, params=params)
        orders_data = response.get("data", {}).get("order_list", [])

        return self._parse_orders(orders_data)

    def get_order(self, order_id: str) -> Dict:
        """获取单个订单"""
        params = {"app_key": self.app_key, "shop_id": self.shop_id, "order_id": order_id}

        path = "/api/v1/orders/query"
        signature = self._generate_signature(path, params)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("GET", path, params=params)
        order_list = response.get("data", {}).get("order_list", [])

        if order_list:
            return self._parse_order(order_list[0])
        return {}

    def update_order_status(self, order_id: str, status: str, tracking_number: str = None) -> bool:
        """更新订单状态"""
        if status != "shipped" or not tracking_number:
            logger.warning(f"TikTok Shop仅支持发货更新，需要tracking_number")
            return False

        params = {
            "app_key": self.app_key,
            "shop_id": self.shop_id,
        }

        body = {
            "order_id": order_id,
            "tracking_number": tracking_number,
            "provider_type": self.auth_config.get("logistics_provider", "OTHER"),
        }

        path = "/api/v1/orders/ship"
        signature = self._generate_signature(path, params, body)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("POST", path, params=params, data=body)
        return response.get("code") == 0

    def get_products(self, **filters) -> List[Dict]:
        """获取商品列表"""
        params = {
            "app_key": self.app_key,
            "shop_id": self.shop_id,
            "page_size": filters.get("limit", 100),
            "page_number": filters.get("offset", 0) + 1,
            "status": filters.get("status", "ACTIVE"),
        }

        path = "/api/v1/products/query"
        signature = self._generate_signature(path, params)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("GET", path, params=params)
        products_data = response.get("data", {}).get("products", [])

        return self._parse_products(products_data)

    def get_product(self, product_id: str) -> Dict:
        """获取单个商品"""
        params = {"app_key": self.app_key, "shop_id": self.shop_id, "product_id": product_id}

        path = "/api/v1/products/query"
        signature = self._generate_signature(path, params)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("GET", path, params=params)
        products = response.get("data", {}).get("products", [])

        if products:
            return self._parse_product(products[0])
        return {}

    def create_product(self, product_data: Dict) -> Dict:
        """创建商品"""
        params = {
            "app_key": self.app_key,
            "shop_id": self.shop_id,
        }

        body = {
            "name": product_data.get("name"),
            "description": product_data.get("description"),
            "price": product_data.get("price"),
            "stock": product_data.get("stock", 100),
            "images": product_data.get("images", []),
            "skus": product_data.get("skus", []),
        }

        path = "/api/v1/products/create"
        signature = self._generate_signature(path, params, body)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("POST", path, params=params, data=body)

        if response.get("code") == 0:
            product_data = response.get("data", {}).get("product", {})
            return self._parse_product(product_data)

        return {}

    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """更新商品"""
        params = {
            "app_key": self.app_key,
            "shop_id": self.shop_id,
        }

        body = {"product_id": product_id, **product_data}

        path = "/api/v1/products/update"
        signature = self._generate_signature(path, params, body)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("POST", path, params=params, data=body)

        if response.get("code") == 0:
            product_data = response.get("data", {}).get("product", {})
            return self._parse_product(product_data)

        return {}

    def delete_product(self, product_id: str) -> bool:
        """删除商品"""
        params = {
            "app_key": self.app_key,
            "shop_id": self.shop_id,
        }

        body = {"product_id": product_id}

        path = "/api/v1/products/delete"
        signature = self._generate_signature(path, params, body)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("POST", path, params=params, data=body)
        return response.get("code") == 0

    def update_inventory(self, sku: str, quantity: int) -> bool:
        """更新库存"""
        params = {
            "app_key": self.app_key,
            "shop_id": self.shop_id,
        }

        body = {"sku_id": sku, "stock": quantity}

        path = "/api/v1/products/stocks/update"
        signature = self._generate_signature(path, params, body)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("POST", path, params=params, data=body)
        return response.get("code") == 0

    def batch_update_inventory(self, updates: List[Dict]) -> List[Dict]:
        """批量更新库存"""
        params = {
            "app_key": self.app_key,
            "shop_id": self.shop_id,
        }

        body = {"stocks": updates}

        path = "/api/v1/products/stocks/batch_update"
        signature = self._generate_signature(path, params, body)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("POST", path, params=params, data=body)

        if response.get("code") == 0:
            return [{"sku": u["sku"], "success": True} for u in updates]
        else:
            return [{"sku": u["sku"], "success": False} for u in updates]

    def _parse_orders(self, orders: List[Dict]) -> List[Dict]:
        """解析订单数据"""
        parsed = []
        for order in orders:
            parsed.append(self._parse_order(order))
        return parsed

    def _parse_order(self, order: Dict) -> Dict:
        """解析单个订单"""
        address = order.get("recipient_address", {})

        return {
            "order_id": order.get("order_id"),
            "status": self._map_order_status(order.get("order_status")),
            "amount": float(order.get("total_amount", 0)),
            "currency": order.get("currency", "USD"),
            "buyer_email": order.get("buyer_email"),
            "buyer_name": order.get("buyer_name"),
            "buyer_phone": address.get("phone"),
            "shipping_address": {
                "address": address.get("address_line1", ""),
                "city": address.get("city", ""),
                "state": address.get("state", ""),
                "country": address.get("country", ""),
                "postal_code": address.get("zip", ""),
            },
            "created_at": order.get("created_time"),
            "items": self._parse_order_items(order.get("items", [])),
        }

    def _parse_order_items(self, items: List[Dict]) -> List[Dict]:
        """解析订单商品"""
        parsed = []
        for item in items:
            parsed.append(
                {
                    "sku": item.get("sku_id"),
                    "product_name": item.get("product_name"),
                    "quantity": int(item.get("quantity", 0)),
                    "unit_price": float(item.get("price", 0)),
                    "product_id": item.get("product_id"),
                }
            )
        return parsed

    def _parse_products(self, products: List[Dict]) -> List[Dict]:
        """解析商品数据"""
        parsed = []
        for product in products:
            parsed.append(self._parse_product(product))
        return parsed

    def _parse_product(self, product: Dict) -> Dict:
        """解析单个商品"""
        return {
            "id": product.get("product_id"),
            "sku": str(product.get("product_id")),
            "name": product.get("name"),
            "description": product.get("description", ""),
            "price": float(product.get("price", 0)),
            "currency": product.get("currency", "USD"),
            "stock": int(product.get("stock", 0)),
            "status": self._map_product_status(product.get("status")),
            "images": product.get("images", [])[:6],
        }

    def _map_order_status(self, status: str) -> str:
        """映射订单状态"""
        status_map = {
            "UNPAID": "pending",
            "AWAITING_SHIPMENT": "paid",
            "AWAITING_COLLECTION": "processing",
            "IN_TRANSIT": "shipped",
            "DELIVERED": "delivered",
            "COMPLETED": "delivered",
            "CANCELLED": "cancelled",
            "REFUNDED": "refunded",
        }
        return status_map.get(status, "pending")

    def _map_product_status(self, status: str) -> str:
        """映射商品状态"""
        if status in ["ACTIVE", "ON_SALE", "NORMAL"]:
            return "onsale"
        elif status in ["INACTIVE", "OFF_SALE", "DELETED"]:
            return "offshelf"
        return "offshelf"
