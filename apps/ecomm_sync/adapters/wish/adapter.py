"""
Wish电商平台适配器

Wish是全球知名的移动电商平台
"""
import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Dict, List

from ..base import BaseAdapter

logger = logging.getLogger(__name__)


class WishAdapter(BaseAdapter):
    """Wish电商平台适配器"""

    def __init__(self, account: "PlatformAccount"):
        super().__init__(account)
        self.base_url = "https://merchant.wish.com/api/v2"

        # 从auth_config获取认证信息
        self.api_key = self.auth_config.get("api_key")
        self.merchant_id = self.auth_config.get("merchant_id")

        if not self.api_key or not self.merchant_id:
            raise ValueError("Wish API配置不完整，需要api_key和merchant_id")

    def _setup_session(self):
        """设置Session认证头"""
        self.session.headers.update(
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }
        )

    def _generate_signature(self, params: Dict) -> str:
        """生成API签名

        Wish使用HMAC-SHA256签名
        """
        # 添加API Key
        params["key"] = self.api_key

        # 按字母顺序排序参数
        sorted_params = sorted(params.items())

        # 构建签名字符串
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_params if k != "sign"])

        # 使用HMAC-SHA256签名
        signature = hmac.new(
            self.api_key.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return signature

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            params = {}

            path = "/account"
            signature = self._generate_signature(params)
            params["sign"] = signature

            response = self._make_request("GET", path, params=params)
            return response.get("code") == 0
        except Exception as e:
            logger.error(f"Wish连接测试失败: {e}")
            return False

    def get_orders(self, start_date=None, end_date=None, **filters) -> List[Dict]:
        """获取订单列表"""
        params = {
            "limit": filters.get("limit", 100),
            "start": filters.get("offset", 0),
        }

        if start_date:
            params["start_time"] = int(start_date.timestamp())
        if end_date:
            params["end_time"] = int(end_date.timestamp())

        path = "/order/multi-get"
        signature = self._generate_signature(params)
        params["sign"] = signature

        response = self._make_request("GET", path, params=params)
        orders_data = response.get("data", [])

        return self._parse_orders(orders_data)

    def get_order(self, order_id: str) -> Dict:
        """获取单个订单"""
        params = {"id": order_id}

        path = "/order/get"
        signature = self._generate_signature(params)
        params["sign"] = signature

        response = self._make_request("GET", path, params=params)
        order_data = response.get("data", {})

        return self._parse_order(order_data)

    def update_order_status(self, order_id: str, status: str, tracking_number: str = None) -> bool:
        """更新订单状态"""
        if status != "shipped" or not tracking_number:
            logger.warning(f"Wish仅支持发货更新，需要tracking_number")
            return False

        params = {
            "id": order_id,
            "tracking_number": tracking_number,
            "ship_note": self.auth_config.get("ship_note", ""),
        }

        path = "/order/fulfill-one"
        signature = self._generate_signature(params)
        params["sign"] = signature

        response = self._make_request("POST", path, data=params)
        return response.get("code") == 0

    def get_products(self, **filters) -> List[Dict]:
        """获取商品列表"""
        params = {
            "limit": filters.get("limit", 100),
            "start": filters.get("offset", 0),
        }

        path = "/product/multi-get"
        signature = self._generate_signature(params)
        params["sign"] = signature

        response = self._make_request("GET", path, params=params)
        products_data = response.get("data", [])

        return self._parse_products(products_data)

    def get_product(self, product_id: str) -> Dict:
        """获取单个商品"""
        params = {"id": product_id}

        path = "/product/get"
        signature = self._generate_signature(params)
        params["sign"] = signature

        response = self._make_request("GET", path, params=params)
        product_data = response.get("data", {})

        return self._parse_product(product_data)

    def create_product(self, product_data: Dict) -> Dict:
        """创建商品"""
        params = {
            "name": product_data.get("name"),
            "description": product_data.get("description"),
            "price": product_data.get("price"),
            "inventory": product_data.get("stock", 100),
            "main_image": product_data.get("images", [""])[0] if product_data.get("images") else "",
            "extra_images": ",".join(product_data.get("images", [])[1:7])
            if len(product_data.get("images", [])) > 1
            else "",
            "shipping": product_data.get("shipping", ""),
        }

        path = "/product/add"
        signature = self._generate_signature(params)
        params["sign"] = signature

        response = self._make_request("POST", path, data=params)

        if response.get("code") == 0:
            product_data = response.get("data", {})
            product_data["id"] = product_data.get("id", product_data.get("product_id", ""))
            return self._parse_product(product_data)

        return {}

    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """更新商品"""
        params = {
            "id": product_id,
        }

        if "name" in product_data:
            params["name"] = product_data["name"]
        if "description" in product_data:
            params["description"] = product_data["description"]
        if "price" in product_data:
            params["price"] = product_data["price"]
        if "stock" in product_data:
            params["inventory"] = product_data["stock"]

        path = "/product/update"
        signature = self._generate_signature(params)
        params["sign"] = signature

        response = self._make_request("POST", path, data=params)

        if response.get("code") == 0:
            product_data = response.get("data", {})
            product_data["id"] = product_id
            return self._parse_product(product_data)

        return {}

    def delete_product(self, product_id: str) -> bool:
        """删除商品"""
        params = {"id": product_id, "reason": self.auth_config.get("delete_reason", "Other")}

        path = "/product/disable"
        signature = self._generate_signature(params)
        params["sign"] = signature

        response = self._make_request("POST", path, data=params)
        return response.get("code") == 0

    def update_inventory(self, sku: str, quantity: int) -> bool:
        """更新库存"""
        params = {"sku": sku, "inventory": quantity}

        path = "/product/inventory/update"
        signature = self._generate_signature(params)
        params["sign"] = signature

        response = self._make_request("POST", path, data=params)
        return response.get("code") == 0

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
        shipping = order.get("shipping_detail", {})

        return {
            "order_id": order.get("order_id") or order.get("transaction_id"),
            "status": self._map_order_status(order.get("state")),
            "amount": float(order.get("order_total", 0)),
            "currency": order.get("currency", "USD"),
            "buyer_email": order.get("buyer_email"),
            "buyer_name": shipping.get("name"),
            "buyer_phone": shipping.get("phone_number"),
            "shipping_address": {
                "address": shipping.get("street_address1", ""),
                "city": shipping.get("city", ""),
                "state": shipping.get("state", ""),
                "country": shipping.get("country", ""),
                "postal_code": shipping.get("zipcode", ""),
            },
            "created_at": order.get("order_time"),
            "items": self._parse_order_items(order.get("order_items", [])),
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
            "id": product.get("id") or product.get("product_id"),
            "sku": str(product.get("sku") or product.get("id", "")),
            "name": product.get("name"),
            "description": product.get("description", ""),
            "price": float(product.get("price", 0)),
            "currency": product.get("currency", "USD"),
            "stock": int(product.get("inventory", 0)),
            "status": self._map_product_status(product.get("is_enabled")),
            "images": [product.get("main_image", "")]
            + product.get("extra_images", "").split(",")[:6],
        }

    def _map_order_status(self, status: str) -> str:
        """映射订单状态"""
        status_map = {
            "APPROVED": "pending",
            "IN_PROGRESS": "processing",
            "SHIPPED": "shipped",
            "COMPLETED": "delivered",
            "REFUNDED": "refunded",
            "CANCELLED": "cancelled",
        }
        return status_map.get(status, "pending")

    def _map_product_status(self, status: str) -> str:
        """映射商品状态"""
        if status is True or status == "True" or status == 1:
            return "onsale"
        elif status is False or status == "False" or status == 0:
            return "offshelf"
        return "offshelf"
