"""
Jumia电商平台适配器

Jumia是非洲最大的电商平台，覆盖多个非洲国家
"""
from ..base import BaseAdapter
from typing import Dict, List
import hashlib
import hmac
import base64
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class JumiaAdapter(BaseAdapter):
    """Jumia电商平台适配器"""

    def __init__(self, account: "PlatformAccount"):
        super().__init__(account)
        self.base_url = "https://sellercenter-api.jumia.com"
        self.api_version = "v1"

        # 从auth_config获取认证信息
        self.seller_id = self.auth_config.get("seller_id")
        self.api_key = self.auth_config.get("api_key")
        self.secret_key = self.auth_config.get("secret_key")

        if not self.seller_id or not self.api_key or not self.secret_key:
            raise ValueError("Jumia API配置不完整，需要seller_id、api_key和secret_key")

    def _setup_session(self):
        """设置Session认证头"""
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _generate_signature(self, params: Dict, endpoint: str) -> str:
        """生成API签名

        Jumia使用HMAC-SHA256签名
        """
        # 添加必需参数
        params["seller_id"] = self.seller_id
        params["timestamp"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # 按字母顺序排序参数
        sorted_params = sorted(params.items())

        # 构建签名字符串
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_params])

        # 使用HMAC-SHA256签名
        signature = hmac.new(
            self.secret_key.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha256
        ).digest()

        return base64.b64encode(signature).decode("utf-8")

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            params = {"action": "Ping"}

            endpoint = f"/{self.api_version}/system/ping"
            signature = self._generate_signature(params, endpoint)
            params["signature"] = signature

            response = self._make_request("GET", endpoint, params=params)
            return response.get("success", False)
        except Exception as e:
            logger.error(f"Jumia连接测试失败: {e}")
            return False

    def get_orders(self, start_date=None, end_date=None, **filters) -> List[Dict]:
        """获取订单列表"""
        params = {
            "action": "GetOrders",
            "limit": filters.get("limit", 100),
            "offset": filters.get("offset", 0),
        }

        if start_date:
            params["created_from"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["created_to"] = end_date.strftime("%Y-%m-%d")

        if filters.get("status"):
            params["status"] = filters["status"]

        endpoint = f"/{self.api_version}/orders"
        signature = self._generate_signature(params, endpoint)
        params["signature"] = signature

        response = self._make_request("GET", endpoint, params=params)
        orders_data = response.get("data", {}).get("orders", [])

        return self._parse_orders(orders_data)

    def get_order(self, order_id: str) -> Dict:
        """获取单个订单"""
        params = {"action": "GetOrder", "order_id": order_id}

        endpoint = f"/{self.api_version}/orders/{order_id}"
        signature = self._generate_signature(params, endpoint)
        params["signature"] = signature

        response = self._make_request("GET", endpoint, params=params)
        order_data = response.get("data", {}).get("order", {})

        return self._parse_order(order_data)

    def update_order_status(self, order_id: str, status: str, tracking_number: str = None) -> bool:
        """更新订单状态"""
        params = {"action": "UpdateOrderStatus", "order_id": order_id, "status": status}

        if tracking_number:
            params["tracking_number"] = tracking_number

        endpoint = f"/{self.api_version}/orders/{order_id}/status"
        signature = self._generate_signature(params, endpoint)
        params["signature"] = signature

        response = self._make_request("POST", endpoint, data=params)
        return response.get("success", False)

    def get_products(self, **filters) -> List[Dict]:
        """获取商品列表"""
        params = {
            "action": "GetProducts",
            "limit": filters.get("limit", 100),
            "offset": filters.get("offset", 0),
        }

        if filters.get("status"):
            params["status"] = filters["status"]

        endpoint = f"/{self.api_version}/products"
        signature = self._generate_signature(params, endpoint)
        params["signature"] = signature

        response = self._make_request("GET", endpoint, params=params)
        products_data = response.get("data", {}).get("products", [])

        return self._parse_products(products_data)

    def get_product(self, product_id: str) -> Dict:
        """获取单个商品"""
        params = {"action": "GetProduct"}

        endpoint = f"/{self.api_version}/products/{product_id}"
        signature = self._generate_signature(params, endpoint)
        params["signature"] = signature

        response = self._make_request("GET", endpoint, params=params)
        product_data = response.get("data", {}).get("product", {})

        return self._parse_product(product_data)

    def create_product(self, product_data: Dict) -> Dict:
        """创建商品"""
        params = {"action": "CreateProduct", **product_data}

        endpoint = f"/{self.api_version}/products"
        signature = self._generate_signature(params, endpoint)
        params["signature"] = signature

        response = self._make_request("POST", endpoint, data=params)

        if response.get("success"):
            return self._parse_product(response.get("data", {}).get("product", {}))

        return {}

    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """更新商品"""
        params = {"action": "UpdateProduct", **product_data}

        endpoint = f"/{self.api_version}/products/{product_id}"
        signature = self._generate_signature(params, endpoint)
        params["signature"] = signature

        response = self._make_request("PUT", endpoint, data=params)

        if response.get("success"):
            return self._parse_product(response.get("data", {}).get("product", {}))

        return {}

    def delete_product(self, product_id: str) -> bool:
        """删除商品"""
        params = {"action": "DeleteProduct"}

        endpoint = f"/{self.api_version}/products/{product_id}"
        signature = self._generate_signature(params, endpoint)
        params["signature"] = signature

        response = self._make_request("DELETE", endpoint, data=params)
        return response.get("success", False)

    def update_inventory(self, sku: str, quantity: int) -> bool:
        """更新库存"""
        params = {"action": "UpdateInventory", "sku": sku, "quantity": quantity}

        endpoint = f"/{self.api_version}/inventory"
        signature = self._generate_signature(params, endpoint)
        params["signature"] = signature

        response = self._make_request("POST", endpoint, data=params)
        return response.get("success", False)

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
        shipping_address = order.get("shipping_address", {})

        return {
            "order_id": order.get("order_id"),
            "status": self._map_order_status(order.get("status")),
            "amount": float(order.get("total_amount", 0)),
            "currency": order.get("currency", "USD"),
            "buyer_email": order.get("buyer_email"),
            "buyer_name": order.get("buyer_name"),
            "buyer_phone": order.get("buyer_phone"),
            "shipping_address": {
                "address": shipping_address.get("address_line1", ""),
                "city": shipping_address.get("city", ""),
                "state": shipping_address.get("state", ""),
                "country": shipping_address.get("country_code", ""),
                "postal_code": shipping_address.get("postal_code", ""),
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
        price_data = product.get("price", {})

        return {
            "id": product.get("product_id"),
            "sku": product.get("sku"),
            "name": product.get("name"),
            "description": product.get("description", ""),
            "price": float(price_data.get("amount", 0)),
            "currency": price_data.get("currency", "USD"),
            "stock": int(product.get("stock", 0)),
            "status": self._map_product_status(product.get("status")),
            "images": product.get("images", [])[:6],
        }

    def _map_order_status(self, status: str) -> str:
        """映射订单状态"""
        status_map = {
            "new": "pending",
            "payment_pending": "pending",
            "paid": "paid",
            "processing": "processing",
            "ready_to_ship": "processing",
            "shipped": "shipped",
            "delivered": "delivered",
            "cancelled": "cancelled",
            "refunded": "refunded",
        }
        return status_map.get(status, "pending")

    def _map_product_status(self, status: str) -> str:
        """映射商品状态"""
        if status in ["active", "enabled", "published"]:
            return "onsale"
        elif status in ["inactive", "disabled", "unpublished", "deleted"]:
            return "offshelf"
        return "offshelf"
