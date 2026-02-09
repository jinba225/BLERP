"""
Temu电商平台适配器

Temu是拼多多旗下的跨境电商平台
"""
import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Dict, List

from ..base import BaseAdapter

logger = logging.getLogger(__name__)


class TemuAdapter(BaseAdapter):
    """Temu电商平台适配器"""

    def __init__(self, account: "PlatformAccount"):
        super().__init__(account)
        self.base_url = "https://seller.kyruus.com/api"
        self.api_version = "v1"

        # 从auth_config获取认证信息
        self.access_key = self.auth_config.get("access_key")
        self.access_secret = self.auth_config.get("access_secret")
        self.seller_id = self.auth_config.get("seller_id")

        if not self.access_key or not self.access_secret or not self.seller_id:
            raise ValueError("Temu API配置不完整，需要access_key、access_secret和seller_id")

    def _setup_session(self):
        """设置Session认证头"""
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.auth_config.get('access_token', '')}",
            }
        )

    def _generate_signature(self, path: str, method: str, params: Dict, body: Dict = None) -> str:
        """生成API签名

        Temu使用HMAC-SHA256签名
        """
        # 添加时间戳
        timestamp = str(int(datetime.now().timestamp()))

        # 构建签名字符串
        # 格式: METHOD + path + query_string + body + timestamp
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])

        body_str = ""
        if body:
            body_str = json.dumps(body, separators=(",", ":"), sort_keys=True)

        sign_str = f"{method.upper()}{path}{query_string}{body_str}{timestamp}"

        # 使用HMAC-SHA256签名
        signature = hmac.new(
            self.access_secret.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return signature

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            params = {"seller_id": self.seller_id}

            path = "/v1/seller/ping"
            signature = self._generate_signature(path, "GET", params)
            params["sign"] = signature
            params["timestamp"] = str(int(datetime.now().timestamp()))

            response = self._make_request("GET", path, params=params)
            return response.get("success", False)
        except Exception as e:
            logger.error(f"Temu连接测试失败: {e}")
            return False

    def get_orders(self, start_date=None, end_date=None, **filters) -> List[Dict]:
        """获取订单列表"""
        params = {
            "seller_id": self.seller_id,
            "page_size": filters.get("limit", 100),
            "page": filters.get("offset", 0) + 1,
            "order_status": filters.get("status", "ALL"),
        }

        if start_date:
            params["start_date"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["end_date"] = end_date.strftime("%Y-%m-%d")

        path = "/v1/orders"
        signature = self._generate_signature(path, "GET", params)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("GET", path, params=params)
        orders_data = response.get("data", {}).get("orders", [])

        return self._parse_orders(orders_data)

    def get_order(self, order_id: str) -> Dict:
        """获取单个订单"""
        params = {"seller_id": self.seller_id, "order_id": order_id}

        path = f"/v1/orders/{order_id}"
        signature = self._generate_signature(path, "GET", params)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("GET", path, params=params)
        order_data = response.get("data", {}).get("order", {})

        return self._parse_order(order_data)

    def update_order_status(self, order_id: str, status: str, tracking_number: str = None) -> bool:
        """更新订单状态"""
        if status != "shipped" or not tracking_number:
            logger.warning(f"Temu仅支持发货更新，需要tracking_number")
            return False

        params = {
            "seller_id": self.seller_id,
        }

        body = {
            "order_id": order_id,
            "tracking_number": tracking_number,
            "carrier": self.auth_config.get("default_carrier", "Other"),
        }

        path = f"/v1/orders/{order_id}/ship"
        signature = self._generate_signature(path, "POST", params, body)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("POST", path, params=params, data=body)
        return response.get("success", False)

    def get_products(self, **filters) -> List[Dict]:
        """获取商品列表"""
        params = {
            "seller_id": self.seller_id,
            "page_size": filters.get("limit", 100),
            "page": filters.get("offset", 0) + 1,
            "status": filters.get("status", "ACTIVE"),
        }

        path = "/v1/products"
        signature = self._generate_signature(path, "GET", params)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("GET", path, params=params)
        products_data = response.get("data", {}).get("products", [])

        return self._parse_products(products_data)

    def get_product(self, product_id: str) -> Dict:
        """获取单个商品"""
        params = {
            "seller_id": self.seller_id,
        }

        path = f"/v1/products/{product_id}"
        signature = self._generate_signature(path, "GET", params)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("GET", path, params=params)
        product_data = response.get("data", {}).get("product", {})

        return self._parse_product(product_data)

    def create_product(self, product_data: Dict) -> Dict:
        """创建商品"""
        params = {
            "seller_id": self.seller_id,
        }

        body = {
            "name": product_data.get("name"),
            "description": product_data.get("description"),
            "price": product_data.get("price"),
            "stock": product_data.get("stock", 100),
            "images": product_data.get("images", []),
            "skus": product_data.get("skus", []),
        }

        path = "/v1/products"
        signature = self._generate_signature(path, "POST", params, body)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("POST", path, params=params, data=body)

        if response.get("success"):
            product_data = response.get("data", {}).get("product", {})
            return self._parse_product(product_data)

        return {}

    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """更新商品"""
        params = {
            "seller_id": self.seller_id,
        }

        body = {"product_id": product_id, **product_data}

        path = f"/v1/products/{product_id}"
        signature = self._generate_signature(path, "PUT", params, body)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("PUT", path, params=params, data=body)

        if response.get("success"):
            product_data = response.get("data", {}).get("product", {})
            return self._parse_product(product_data)

        return {}

    def delete_product(self, product_id: str) -> bool:
        """删除商品"""
        params = {
            "seller_id": self.seller_id,
        }

        path = f"/v1/products/{product_id}"
        signature = self._generate_signature(path, "DELETE", params)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("DELETE", path, params=params)
        return response.get("success", False)

    def update_inventory(self, sku: str, quantity: int) -> bool:
        """更新库存"""
        params = {
            "seller_id": self.seller_id,
        }

        body = {"sku": sku, "quantity": quantity}

        path = "/v1/inventory"
        signature = self._generate_signature(path, "POST", params, body)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("POST", path, params=params, data=body)
        return response.get("success", False)

    def batch_update_inventory(self, updates: List[Dict]) -> List[Dict]:
        """批量更新库存"""
        params = {
            "seller_id": self.seller_id,
        }

        body = {"updates": updates}

        path = "/v1/inventory/batch"
        signature = self._generate_signature(path, "POST", params, body)
        params["sign"] = signature
        params["timestamp"] = str(int(datetime.now().timestamp()))

        response = self._make_request("POST", path, params=params, data=body)

        if response.get("success"):
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
        shipping = order.get("shipping_address", {})

        return {
            "order_id": order.get("order_id"),
            "status": self._map_order_status(order.get("status")),
            "amount": float(order.get("total_amount", 0)),
            "currency": order.get("currency", "USD"),
            "buyer_email": order.get("buyer_email"),
            "buyer_name": shipping.get("name"),
            "buyer_phone": shipping.get("phone"),
            "shipping_address": {
                "address": shipping.get("address_line1", ""),
                "city": shipping.get("city", ""),
                "state": shipping.get("state", ""),
                "country": shipping.get("country", ""),
                "postal_code": shipping.get("zip", ""),
            },
            "created_at": order.get("created_at"),
            "items": self._parse_order_items(order.get("items", [])),
        }

    def _parse_order_items(self, items: List[Dict]) -> List[Dict]:
        """解析订单商品"""
        parsed = []
        for item in items:
            parsed.append(
                {
                    "sku": item.get("sku"),
                    "product_name": item.get("product_name"),
                    "quantity": int(item.get("quantity", 0)),
                    "unit_price": float(item.get("unit_price", 0)),
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
            "PENDING": "pending",
            "PAID": "paid",
            "PROCESSING": "processing",
            "SHIPPED": "shipped",
            "DELIVERED": "delivered",
            "CANCELLED": "cancelled",
            "REFUNDED": "refunded",
        }
        return status_map.get(status, "pending")

    def _map_product_status(self, status: str) -> str:
        """映射商品状态"""
        if status in ["ACTIVE", "ON_SALE", "LISTED"]:
            return "onsale"
        elif status in ["INACTIVE", "OFF_SALE", "DELETED"]:
            return "offshelf"
        return "offshelf"
