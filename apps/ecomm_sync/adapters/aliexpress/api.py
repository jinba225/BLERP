import logging
from datetime import datetime
from typing import Dict, List

from ..base import BaseAdapter

logger = logging.getLogger(__name__)


class AliexpressAdapter(BaseAdapter):
    """速卖通适配器（OAuth 2.0）"""

    def __init__(self, account: "PlatformAccount"):
        super().__init__(account)
        self.api_base = self.account.platform.base_url or "https://gw.api.alibaba.com/openapi"
        self.auth_config = {
            "appKey": self.account.auth_config.get("app_key"),
            "appSecret": self.account.auth_config.get("app_secret"),
            "accessToken": self.account.auth_config.get("access_token"),
            "refreshToken": self.account.auth_config.get("refresh_token"),
        }

    def _setup_session(self):
        """速卖通使用access_token认证"""
        self.base_url = self.api_base
        self.session.params.update(
            {
                "access_token": self.auth_config["accessToken"],
            }
        )

    def _get_common_params(self) -> Dict:
        """获取通用参数"""
        return {
            "method": "",
            "app_key": self.auth_config["appKey"],
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5",
            "session": self.auth_config["accessToken"],
        }

    def _generate_sign(self, params: Dict) -> str:
        """生成签名"""
        import hashlib

        params_sorted = sorted(params.items())
        sign_str = "".join([f"{k}{v}" for k, v in params_sorted])
        sign_str += self.auth_config["appSecret"]

        return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            params = {
                "method": "aliexpress.solution.order.info.query",
                "pageSize": "1",
            }
            params.update(self._get_common_params())
            params["sign"] = self._generate_sign(params)

            response = self._make_request(
                "GET", "/param2/1/aliexpress/solution/order/info/query", params=params
            )
            return "result" in response
        except Exception as e:
            logger.error(f"速卖通连接测试失败: {e}")
            return False

    def get_orders(self, start_date=None, end_date=None, **filters) -> List[Dict]:
        """获取订单列表"""
        params = {
            "method": "aliexpress.solution.order.info.query",
            "pageSize": "100",
        }

        if start_date:
            params["createDateStart"] = start_date.strftime("%Y-%m-%d %H:%M:%S")
        if end_date:
            params["createDateEnd"] = end_date.strftime("%Y-%m-%d %H:%M:%S")

        order_statuses = filters.get(
            "order_statuses",
            [
                "place_order_success",
                "in_payment",
                "in_cancel",
                "wait_seller_send_goods",
            ],
        )
        for i, status in enumerate(order_statuses, 1):
            params[f"orderStatus.{i}"] = status

        params.update(self._get_common_params())
        params["sign"] = self._generate_sign(params)

        response = self._make_request(
            "GET", "/param2/1/aliexpress/solution/order/info/query", params=params
        )

        orders = response.get("result", {}).get("targetList", [])
        return self._parse_orders(orders)

    def get_order(self, order_id: str) -> Dict:
        """获取单个订单"""
        params = {
            "method": "aliexpress.solution.order.detail.query",
            "orderId": order_id,
        }
        params.update(self._get_common_params())
        params["sign"] = self._generate_sign(params)

        response = self._make_request(
            "GET", "/param2/1/aliexpress/solution/order/detail/query", params=params
        )

        order_data = response.get("result", {})
        if order_data:
            return self._parse_order(order_data)
        return {}

    def update_order_status(self, order_id: str, status: str, tracking_number: str = None) -> bool:
        """更新订单状态（发货）"""
        try:
            if status != "shipped":
                logger.warning("速卖通目前只支持发货状态更新")
                return False

            params = {
                "method": "aliexpress.solution.order.info.seller.ship",
                "orderId": order_id,
                "serviceName": "other",
                "trackingNumber": tracking_number or "",
            }
            params.update(self._get_common_params())
            params["sign"] = self._generate_sign(params)

            response = self._make_request(
                "POST",
                "/param2/1/aliexpress/solution/order/info/seller/ship",
                data=params,
            )

            return response.get("success") is True
        except Exception as e:
            logger.error(f"速卖通订单状态更新失败: {e}")
            return False

    def get_products(self, **filters) -> List[Dict]:
        """获取商品列表"""
        params = {
            "method": "aliexpress.solution.product.info.query",
            "pageSize": "100",
        }
        params.update(self._get_common_params())
        params["sign"] = self._generate_sign(params)

        response = self._make_request(
            "GET", "/param2/1/aliexpress/solution/product/info/query", params=params
        )

        products = response.get("result", {}).get("targetList", [])
        return self._parse_products(products)

    def get_product(self, product_id: str) -> Dict:
        """获取单个商品"""
        params = {
            "method": "aliexpress.solution.product.info.query",
            "productId": product_id,
        }
        params.update(self._get_common_params())
        params["sign"] = self._generate_sign(params)

        response = self._make_request(
            "GET", "/param2/1/aliexpress/solution/product/info/query", params=params
        )

        products = response.get("result", {}).get("targetList", [])
        if products:
            return self._parse_product(products[0])
        return {}

    def create_product(self, product_data: Dict) -> Dict:
        """创建商品"""
        logger.warning("速卖通创建商品需要通过Feeds API，暂未实现")
        return {}

    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """更新商品"""
        logger.warning("速卖通更新商品需要通过Feeds API，暂未实现")
        return {}

    def delete_product(self, product_id: str) -> bool:
        """删除商品"""
        logger.warning("速卖通删除商品需要通过Feeds API，暂未实现")
        return False

    def update_inventory(self, sku: str, quantity: int) -> bool:
        """更新库存"""
        logger.warning("速卖通库存更新需要通过Feeds API，暂未实现")
        return False

    def batch_update_inventory(self, updates: List[Dict]) -> List[Dict]:
        """批量更新库存"""
        results = []
        for update in updates:
            result = self.update_inventory(update["sku"], update["quantity"])
            results.append({"sku": update["sku"], "success": result})
        return results

    def refresh_token(self) -> bool:
        """刷新access_token"""
        try:
            params = {
                "grant_type": "refresh_token",
                "client_id": self.auth_config["appKey"],
                "client_secret": self.auth_config["appSecret"],
                "refresh_token": self.auth_config["refreshToken"],
                "sp": "ae",
            }

            response = self.session.post("https://oauth.aliexpress.com/token", data=params)

            if response.status_code == 200:
                data = response.json()
                self.auth_config["accessToken"] = data["access_token"]
                self.auth_config["refreshToken"] = data["refresh_token"]

                self.session.params.update(
                    {
                        "access_token": self.auth_config["accessToken"],
                    }
                )

                return True

            return False

        except Exception as e:
            logger.error(f"速卖通Token刷新失败: {e}")
            return False

    def _parse_orders(self, orders: List[Dict]) -> List[Dict]:
        """解析订单数据"""
        parsed = []
        for order in orders:
            parsed.append(self._parse_order(order))
        return parsed

    def _parse_order(self, order: Dict) -> Dict:
        """解析单个订单"""
        return {
            "order_id": order.get("orderId"),
            "status": self._map_order_status(order.get("orderStatus")),
            "amount": float(order.get("productAmount", {}).get("amount", 0)),
            "currency": order.get("productAmount", {}).get("currencyCode"),
            "buyer_email": order.get("logisticsAddress", {}).get("email"),
            "buyer_name": order.get("logisticsAddress", {}).get("contactPerson"),
            "created_at": order.get("gmtCreate"),
            "items": self._parse_order_items(order.get("childOrderList", [])),
        }

    def _parse_order_items(self, items: List[Dict]) -> List[Dict]:
        """解析订单商品"""
        parsed = []
        for item in items:
            parsed.append(
                {
                    "sku": item.get("skuCode"),
                    "product_name": item.get("productName"),
                    "quantity": int(item.get("productCount", 0)),
                    "unit_price": float(item.get("productUnitPrice", {}).get("amount", 0)),
                    "product_id": item.get("productId"),
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
            "id": product.get("productId"),
            "sku": product.get("subject"),
            "name": product.get("subject"),
            "price": float(product.get("price", {}).get("amount", 0)),
            "stock": int(product.get("wsDisplayNum", 0)),
            "status": "onsale" if product.get("wsDisplayNum", 0) > 0 else "offshelf",
        }

    def _map_order_status(self, status: str) -> str:
        """映射订单状态"""
        status_map = {
            "place_order_success": "pending",
            "in_payment": "pending",
            "in_cancel": "cancelled",
            "wait_seller_send_goods": "paid",
            "wait_buyer_accept_goods": "shipped",
            "in_finish": "delivered",
        }
        return status_map.get(status, "pending")
