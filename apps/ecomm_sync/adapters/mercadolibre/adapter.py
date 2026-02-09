"""
MercadoLibre电商平台适配器

MercadoLibre是拉丁美洲最大的电商平台
"""
import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Dict, List

import requests

from ..base import BaseAdapter

logger = logging.getLogger(__name__)


class MercadoLibreAdapter(BaseAdapter):
    """MercadoLibre电商平台适配器"""

    def __init__(self, account: "PlatformAccount"):
        # 先设置属性，再调用super().__init__
        self.account = account
        self.auth_config = account.auth_config

        # MercadoLibre区分不同国家的API端点
        site_id = self.auth_config.get("site_id", "MLB").upper()
        site_map = {
            "MLB": "https://api.mercadolibre.com",  # Brazil
            "MLM": "https://api.mercadolibre.com",  # Mexico
            "MLA": "https://api.mercadolibre.com",  # Argentina
            "MLC": "https://api.mercadolibre.com",  # Chile
            "MCO": "https://api.mercadolibre.com",  # Colombia
            "MLU": "https://api.mercadolibre.com",  # Uruguay
            "MLP": "https://api.mercadolibre.com",  # Peru
            "MPE": "https://api.mercadolibre.com",  # Peru
            "MLV": "https://api.mercadolibre.com",  # Venezuela
        }
        self.base_url = site_map.get(site_id, "https://api.mercadolibre.com")

        # 从auth_config获取认证信息
        self.access_token = self.auth_config.get("access_token")
        self.seller_id = self.auth_config.get("seller_id")
        self.app_id = self.auth_config.get("app_id")
        self.secret_key = self.auth_config.get("secret_key")

        if not self.access_token or not self.seller_id:
            raise ValueError("MercadoLibre API配置不完整，需要access_token和seller_id")

        # 设置默认值
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 2

        # 创建Session
        self.session = requests.Session()

        # 最后调用_setup_session
        self._setup_session()

    def _setup_session(self):
        """设置Session认证头"""
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.access_token}",
            }
        )

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            path = "/users/me"
            response = self._make_request("GET", path)
            return "id" in response
        except Exception as e:
            logger.error(f"MercadoLibre连接测试失败: {e}")
            return False

    def get_orders(self, start_date=None, end_date=None, **filters) -> List[Dict]:
        """获取订单列表"""
        params = {
            "seller": self.seller_id,
            "limit": filters.get("limit", 100),
            "offset": filters.get("offset", 0),
        }

        if filters.get("status"):
            params["order.status"] = filters["status"]

        path = "/orders/search"
        response = self._make_request("GET", path, params=params)
        orders_data = response.get("results", [])

        return self._parse_orders(orders_data)

    def get_order(self, order_id: str) -> Dict:
        """获取单个订单"""
        path = f"/orders/{order_id}"
        response = self._make_request("GET", path)

        return self._parse_order(response)

    def update_order_status(self, order_id: str, status: str, tracking_number: str = None) -> bool:
        """更新订单状态"""
        if status != "shipped" or not tracking_number:
            logger.warning(f"MercadoLibre仅支持发货更新，需要tracking_number")
            return False

        body = {
            "tracking_number": tracking_number,
            "service_id": self.auth_config.get("service_id", 1),
        }

        path = f"/orders/{order_id}/shipments"
        response = self._make_request("POST", path, data=body)
        return "id" in response

    def get_products(self, **filters) -> List[Dict]:
        """获取商品列表"""
        params = {
            "seller_id": self.seller_id,
            "limit": filters.get("limit", 100),
            "offset": filters.get("offset", 0),
            "status": filters.get("status", "active"),
        }

        path = "/users/me/items/search"
        response = self._make_request("GET", path, params=params)
        products_data = response.get("results", [])

        return self._parse_products(products_data)

    def get_product(self, product_id: str) -> Dict:
        """获取单个商品"""
        path = f"/items/{product_id}"
        response = self._make_request("GET", path)

        return self._parse_product(response)

    def create_product(self, product_data: Dict) -> Dict:
        """创建商品"""
        body = {
            "title": product_data.get("name"),
            "description": product_data.get("description"),
            "price": product_data.get("price"),
            "available_quantity": product_data.get("stock", 100),
            "pictures": [{"source": img} for img in product_data.get("images", [])[:6]],
            "currency_id": product_data.get("currency", "BRL"),
            "condition": product_data.get("condition", "new"),
            "listing_type_id": product_data.get("listing_type_id", "gold_special"),
        }

        path = "/items"
        response = self._make_request("POST", path, data=body)

        if "id" in response:
            return self._parse_product(response)

        return {}

    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """更新商品"""
        body = {}

        if "name" in product_data:
            body["title"] = product_data["name"]
        if "description" in product_data:
            body["description"] = product_data["description"]
        if "price" in product_data:
            body["price"] = product_data["price"]
        if "stock" in product_data:
            body["available_quantity"] = product_data["stock"]

        path = f"/items/{product_id}"
        response = self._make_request("PUT", path, data=body)

        if "id" in response:
            return self._parse_product(response)

        return {}

    def delete_product(self, product_id: str) -> bool:
        """删除商品（改为下架）"""
        path = f"/items/{product_id}"
        body = {"status": "paused"}

        response = self._make_request("PUT", path, data=body)
        return response.get("status") == "paused"

    def update_inventory(self, sku: str, quantity: int) -> bool:
        """更新库存"""
        # MercadoLibre通过item ID更新库存
        product_id = sku

        body = {"available_quantity": quantity}

        path = f"/items/{product_id}"
        response = self._make_request("PUT", path, data=body)
        return "id" in response

    def batch_update_inventory(self, updates: List[Dict]) -> List[Dict]:
        """批量更新库存"""
        results = []

        for update in updates:
            result = self.update_inventory(update["sku"], update["quantity"])
            results.append({"sku": update["sku"], "success": result})

        return results

    def _parse_orders(self, orders: List[Dict]) -> List[Dict]:
        """解析订单数据"""
        parsed = []
        for order in orders:
            parsed.append(self._parse_order(order))
        return parsed

    def _parse_order(self, order: Dict) -> Dict:
        """解析单个订单"""
        shipping = order.get("shipping", {})
        buyer = order.get("buyer", {})
        address = shipping.get("receiver_address", {})

        return {
            "order_id": order.get("id"),
            "status": self._map_order_status(order.get("status")),
            "amount": float(order.get("total_amount", 0)),
            "currency": order.get("currency_id", "BRL"),
            "buyer_email": buyer.get("email"),
            "buyer_name": address.get("receiver_name"),
            "buyer_phone": address.get("receiver_phone"),
            "shipping_address": {
                "address": address.get("address_line", ""),
                "city": address.get("city", {}).get("name", ""),
                "state": address.get("state", {}).get("name", ""),
                "country": address.get("country", {}).get("name", ""),
                "postal_code": address.get("zip_code", ""),
            },
            "created_at": order.get("date_created"),
            "items": self._parse_order_items(order.get("order_items", [])),
        }

    def _parse_order_items(self, items: List[Dict]) -> List[Dict]:
        """解析订单商品"""
        parsed = []
        for item in items:
            item_data = item.get("item", {})
            parsed.append(
                {
                    "sku": item_data.get("id"),
                    "product_name": item_data.get("title"),
                    "quantity": int(item.get("quantity", 0)),
                    "unit_price": float(item.get("unit_price", 0)),
                    "product_id": item_data.get("id"),
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
        pictures = product.get("pictures", [])
        images = [pic.get("secure_url", "") for pic in pictures[:6]]

        return {
            "id": product.get("id"),
            "sku": str(product.get("id")),
            "name": product.get("title"),
            "description": product.get("description", ""),
            "price": float(product.get("price", 0)),
            "currency": product.get("currency_id", "BRL"),
            "stock": int(product.get("available_quantity", 0)),
            "status": self._map_product_status(product.get("status")),
            "images": images,
        }

    def _map_order_status(self, status: str) -> str:
        """映射订单状态"""
        status_map = {
            "payment_required": "pending",
            "payment_in_process": "pending",
            "payment_required": "pending",
            "paid": "paid",
            "confirmed": "paid",
            "handling": "processing",
            "payment_received": "processing",
            "shipped": "shipped",
            "delivered": "delivered",
            "cancelled": "cancelled",
            "refunded": "refunded",
        }
        return status_map.get(status, "pending")

    def _map_product_status(self, status: str) -> str:
        """映射商品状态"""
        if status in ["active", "paused", "closed"]:
            return "onsale"
        elif status in ["inactive", "deleted"]:
            return "offshelf"
        return "offshelf"
