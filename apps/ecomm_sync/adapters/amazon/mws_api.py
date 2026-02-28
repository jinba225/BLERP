import base64
import hashlib
import hmac
import logging
from datetime import datetime
from typing import Dict, List
from urllib.parse import quote

from ..base import BaseAdapter

logger = logging.getLogger(__name__)


class AmazonAdapter(BaseAdapter):
    """Amazon MWS适配器"""

    def __init__(self, account: "PlatformAccount"):
        super().__init__(account)
        self.mws_endpoint = self.account.platform.base_url or "https://mws.amazonservices.com"
        self.auth_config = {
            "SellerId": self.account.platform_user_id,
            "AWSAccessKeyId": self.account.auth_config.get("access_key_id"),
            "SecretKey": self.account.auth_config.get("secret_access_key"),
            "MWSAuthToken": self.account.auth_config.get("mws_auth_token"),
        }

    def _setup_session(self):
        """Amazon MWS不需要Session认证，使用签名"""
        pass

    def _generate_signature(self, params: Dict, endpoint: str) -> str:
        """生成MWS签名"""
        params["AWSAccessKeyId"] = self.auth_config["AWSAccessKeyId"]
        params["SellerId"] = self.auth_config["SellerId"]
        params["Timestamp"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        canonical_query_string = "&".join(
            f"{quote(k, safe='-_.~')}={quote(str(v), safe='-_.~')}"
            for k, v in sorted(params.items())
        )

        string_to_sign = f"GET\n{self.mws_endpoint.replace('https://', '').replace('http://', '')}\n{endpoint}\n{canonical_query_string}"

        signature = hmac.new(
            self.auth_config["SecretKey"].encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        return base64.b64encode(signature).decode("utf-8")

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            params = {
                "Action": "GetServiceStatus",
                "Version": "2013-09-01",
            }

            signature = self._generate_signature(params, "/Orders/2013-09-01")
            params["Signature"] = signature

            response = self._make_request(
                "GET", f"/Orders/2013-09-01?signature={signature}", params=params
            )
            return "GetServiceStatusResult" in response
        except Exception as e:
            logger.error(f"Amazon连接测试失败: {e}")
            return False

    def get_orders(self, start_date=None, end_date=None, **filters) -> List[Dict]:
        """获取订单列表"""
        params = {
            "Action": "ListOrders",
            "Version": "2013-09-01",
            "OrderStatus.Status.1": "Unshipped",
            "OrderStatus.Status.2": "PartiallyShipped",
            "OrderStatus.Status.3": "Shipped",
            "OrderStatus.Status.4": "Canceled",
        }

        if start_date:
            params["CreatedAfter"] = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        if end_date:
            params["CreatedBefore"] = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        signature = self._generate_signature(params, "/Orders/2013-09-01")
        response = self._make_request(
            "GET", f"/Orders/2013-09-01", params={**params, "Signature": signature}
        )

        orders = response.get("ListOrdersResult", {}).get("Orders", {}).get("Order", [])
        if not isinstance(orders, list):
            orders = [orders]

        return self._parse_orders(orders)

    def get_order(self, order_id: str) -> Dict:
        """获取单个订单"""
        params = {
            "Action": "GetOrder",
            "Version": "2013-09-01",
            "AmazonOrderId.Id.1": order_id,
        }

        signature = self._generate_signature(params, "/Orders/2013-09-01")
        response = self._make_request(
            "GET", f"/Orders/2013-09-01", params={**params, "Signature": signature}
        )

        order_data = response.get("GetOrderResult", {}).get("Order")
        if order_data:
            return self._parse_order(order_data)
        return {}

    def update_order_status(self, order_id: str, status: str, tracking_number: str = None) -> bool:
        """更新订单状态（Amazon不直接支持更新订单状态）"""
        logger.warning(f"Amazon不支持直接更新订单状态，请通过Shipments API操作")
        return False

    def get_products(self, **filters) -> List[Dict]:
        """获取商品列表"""
        params = {
            "Action": "ListInventorySupply",
            "Version": "2010-10-01",
            "ResponseGroup": "Detailed",
        }

        signature = self._generate_signature(params, "/FBAInbound/v0")
        response = self._make_request(
            "GET", f"/FBAInbound/v0", params={**params, "Signature": signature}
        )

        inventory = (
            response.get("ListInventorySupplyResult", {})
            .get("InventorySupplyList", {})
            .get("member", [])
        )
        if not isinstance(inventory, list):
            inventory = [inventory]

        return self._parse_products(inventory)

    def get_product(self, product_id: str) -> Dict:
        """获取单个商品"""
        params = {
            "Action": "GetMatchingProductForId",
            "Version": "2011-10-01",
            "IdType": "ASIN",
            "IdList.Id.1": product_id,
        }

        signature = self._generate_signature(params, "/Products/2011-10-01")
        response = self._make_request(
            "GET", f"/Products/2011-10-01", params={**params, "Signature": signature}
        )

        product_data = (
            response.get("GetMatchingProductForIdResult", {}).get("Products", {}).get("Product", {})
        )
        return self._parse_product(product_data)

    def create_product(self, product_data: Dict) -> Dict:
        """创建商品"""
        logger.warning("Amazon创建商品需要通过Feeds API，暂未实现")
        return {}

    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """更新商品"""
        logger.warning("Amazon更新商品需要通过Feeds API，暂未实现")
        return {}

    def delete_product(self, product_id: str) -> bool:
        """删除商品"""
        logger.warning("Amazon删除商品需要通过Feeds API，暂未实现")
        return False

    def update_inventory(self, sku: str, quantity: int) -> bool:
        """更新库存"""
        params = {
            "Action": "UpdateInventorySupply",
            "Version": "2010-10-01",
            "Item.SellerSKU": sku,
            "Item.Quantity": str(quantity),
        }

        signature = self._generate_signature(params, "/FBAInbound/v0")
        response = self._make_request("POST", f"/FBAInbound/v0", data=params)
        response["Signature"] = signature

        return response.get("ResponseMetadata", {}).get("StatusCode") == "200"

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
        return {
            "order_id": order.get("AmazonOrderId"),
            "status": self._map_order_status(order.get("OrderStatus")),
            "amount": float(order.get("OrderTotal", {}).get("Amount", 0)),
            "currency": order.get("OrderTotal", {}).get("CurrencyCode"),
            "buyer_email": order.get("BuyerEmail"),
            "buyer_name": order.get("BuyerName"),
            "created_at": order.get("PurchaseDate"),
            "items": self._parse_order_items(order.get("OrderItems", {}).get("OrderItem", [])),
        }

    def _parse_order_items(self, items: List[Dict]) -> List[Dict]:
        """解析订单商品"""
        if not isinstance(items, list):
            items = [items]

        parsed = []
        for item in items:
            parsed.append(
                {
                    "sku": item.get("SellerSKU"),
                    "product_name": item.get("Title"),
                    "quantity": int(item.get("QuantityOrdered", 0)),
                    "unit_price": float(item.get("ItemPrice", {}).get("Amount", 0)),
                    "product_id": item.get("ASIN"),
                }
            )
        return parsed

    def _parse_products(self, products: List[Dict]) -> List[Dict]:
        """解析商品数据"""
        parsed = []
        for product in products:
            parsed.append(
                {
                    "id": product.get("SellerSKU"),
                    "sku": product.get("SellerSKU"),
                    "name": product.get("ItemCondition"),
                    "price": 0,
                    "stock": int(product.get("TotalSupplyQuantity", 0)),
                    "status": (
                        "onsale" if int(product.get("TotalSupplyQuantity", 0)) > 0 else "offshelf"
                    ),
                }
            )
        return parsed

    def _parse_product(self, product: Dict) -> Dict:
        """解析单个商品"""
        # 商品详情解析较复杂，这里简化处理
        return {
            "id": "",
            "name": "",
            "price": 0,
            "stock": 0,
            "status": "offshelf",
        }

    def _map_order_status(self, status: str) -> str:
        """映射订单状态"""
        status_map = {
            "PendingAvailability": "pending",
            "Pending": "pending",
            "Unshipped": "paid",
            "PartiallyShipped": "paid",
            "Shipped": "shipped",
            "Canceled": "cancelled",
        }
        return status_map.get(status, "pending")
