import hashlib
import logging
import time
from typing import Dict, List

from ..base import BaseAdapter

logger = logging.getLogger(__name__)


class LazadaAdapter(BaseAdapter):
    """Lazada API适配器"""

    def __init__(self, account: "PlatformAccount"):
        super().__init__(account)
        self.api_base = self.account.platform.base_url or "https://api.lazada.com/rest"
        self.auth_config = {
            "app_key": self.account.auth_config.get("app_key"),
            "app_secret": self.account.auth_config.get("app_secret"),
            "userId": self.account.platform_user_id,
            "countryCode": self.account.auth_config.get("country_code", "my"),
        }

    def _setup_session(self):
        """Lazada使用API Key认证"""
        self.base_url = self.api_base
        self.session.params.update(
            {
                "app_key": self.auth_config["app_key"],
                "timestamp": "",
                "sign": "",
            }
        )

    def _generate_signature(self, parameters: Dict) -> str:
        """生成签名"""
        parameters["app_key"] = self.auth_config["app_key"]
        parameters["timestamp"] = str(int(time.time() * 1000))

        parameters_sorted = sorted(parameters.items(), key=lambda x: x[0])
        sign_str = "".join([f"{k}{v}" for k, v in parameters_sorted])
        sign_str = self.auth_config["app_secret"] + sign_str + self.auth_config["app_secret"]

        return hashlib.sha256(sign_str.encode("utf-8")).hexdigest()

    def _make_request_with_signature(self, method: str, action: str, params: Dict = None) -> Dict:
        """发送带签名的请求"""
        if params is None:
            params = {}

        params["timestamp"] = str(int(time.time() * 1000))
        params["sign"] = self._generate_signature(params)

        endpoint = f"/{action}"

        return self._make_request(method, endpoint, params=params)

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            params = {
                "userId": self.auth_config["userId"],
                "countryCode": self.auth_config["countryCode"],
            }

            response = self._make_request_with_signature("GET", "/products/get", params)
            return "data" in response or "success" in str(response).lower()
        except Exception as e:
            logger.error(f"Lazada连接测试失败: {e}")
            return False

    def get_orders(self, start_date=None, end_date=None, **filters) -> List[Dict]:
        """获取订单列表"""
        params = {
            "userId": self.auth_config["userId"],
            "countryCode": self.auth_config["countryCode"],
        }

        if start_date:
            params["createdAfter"] = start_date.strftime("%Y-%m-%d %H:%M:%S")
        if end_date:
            params["createdBefore"] = end_date.strftime("%Y-%m-%d %H:%M:%S")

        order_statuses = filters.get("order_statuses", ["pending", "paid", "ready_to_ship"])
        for i, status in enumerate(order_statuses, 1):
            params[f"status.{i}"] = status

        response = self._make_request_with_signature("GET", "/orders/get", params)

        orders = response.get("data", {}).get("orders", [])
        return self._parse_orders(orders)

    def get_order(self, order_id: str) -> Dict:
        """获取单个订单"""
        params = {
            "order_id": order_id,
        }

        response = self._make_request_with_signature("GET", "/orders/get", params)

        orders = response.get("data", {}).get("orders", [])
        if orders:
            return self._parse_order(orders[0])
        return {}

    def update_order_status(self, order_id: str, status: str, tracking_number: str = None) -> bool:
        """更新订单状态（发货）"""
        try:
            if status != "shipped":
                logger.warning("Lazada目前只支持发货状态更新")
                return False

            params = {
                "order_id": order_id,
                "delivery_type": "dropship",
                "shipping_provider": "standard_express",
            }

            if tracking_number:
                params["tracking_number"] = tracking_number

            response = self._make_request_with_signature("POST", "/order/rma/create", params)

            return response.get("success", False)

        except Exception as e:
            logger.error(f"Lazada订单状态更新失败: {e}")
            return False

    def get_products(self, **filters) -> List[Dict]:
        """获取商品列表"""
        params = {
            "filter": "all",
        }

        if "limit" in filters:
            params["limit"] = str(filters["limit"])
        else:
            params["limit"] = "100"

        if "offset" in filters:
            params["offset"] = str(filters["offset"])

        response = self._make_request_with_signature("GET", "/products/get", params)

        products = response.get("data", {}).get("products", [])
        return self._parse_products(products)

    def get_product(self, product_id: str) -> Dict:
        """获取单个商品"""
        params = {
            "filter": "all",
            "sku": product_id,
        }

        response = self._make_request_with_signature("GET", "/products/get", params)

        products = response.get("data", {}).get("products", [])
        if products:
            return self._parse_product(products[0])
        return {}

    def create_product(self, product_data: Dict) -> Dict:
        """创建商品"""
        logger.warning("Lazada创建商品需要通过Feeds API，暂未实现")
        return {}

    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """更新商品"""
        logger.warning("Lazada更新商品需要通过Feeds API，暂未实现")
        return {}

    def delete_product(self, product_id: str) -> bool:
        """删除商品"""
        logger.warning("Lazada删除商品需要通过Feeds API，暂未实现")
        return False

    def update_inventory(self, sku: str, quantity: int) -> bool:
        """更新库存"""
        params = {
            "seller_sku": sku,
            "quantity": str(quantity),
        }

        response = self._make_request_with_signature("POST", "/product/quantity/update", params)

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
        items = order.get("items", [])
        order_items = []
        for item in items:
            order_items.append(
                {
                    "sku": item.get("sku"),
                    "product_name": item.get("name"),
                    "quantity": int(item.get("quantity", 0)),
                    "unit_price": float(item.get("paid_price", 0)),
                    "product_id": item.get("item_id"),
                }
            )

        return {
            "order_id": order.get("order_id"),
            "status": self._map_order_status(
                order.get("statuses", [{}])[0].get("status", "pending")
            ),
            "amount": float(order.get("price", 0)),
            "currency": order.get("currency", "USD"),
            "buyer_email": order.get("customer_email", ""),
            "buyer_name": order.get("address_billing", {}).get("first_name", ""),
            "created_at": order.get("created_at"),
            "items": order_items,
        }

    def _parse_products(self, products: List[Dict]) -> List[Dict]:
        """解析商品数据"""
        parsed = []
        for product in products:
            parsed.append(self._parse_product(product))
        return parsed

    def _parse_product(self, product: Dict) -> Dict:
        """解析单个商品"""
        skus = product.get("skus", [])
        if skus:
            sku_data = skus[0]
            return {
                "id": product.get("item_id"),
                "sku": sku_data.get("SellerSku"),
                "name": product.get("name"),
                "price": float(sku_data.get("price", 0)),
                "stock": int(sku_data.get("quantity", 0)),
                "status": "onsale" if product.get("status") == "active" else "offshelf",
            }
        else:
            return {
                "id": product.get("item_id"),
                "sku": "",
                "name": product.get("name"),
                "price": 0,
                "stock": 0,
                "status": "offshelf",
            }

    def _map_order_status(self, status: str) -> str:
        """映射订单状态"""
        status_map = {
            "pending": "pending",
            "canceled": "cancelled",
            "paid": "paid",
            "ready_to_ship": "paid",
            "shipped": "shipped",
            "delivered": "delivered",
            "failed": "cancelled",
        }
        return status_map.get(status, "pending")
