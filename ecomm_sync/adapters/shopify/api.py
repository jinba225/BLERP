from ..base import BaseAdapter
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class ShopifyAdapter(BaseAdapter):
    """Shopify REST API适配器"""

    def __init__(self, account: 'PlatformAccount'):
        super().__init__(account)
        shop_url = self.account.auth_config.get('shop_url')
        self.api_key = self.account.auth_config.get('api_key')
        self.api_secret = self.account.auth_config.get('api_secret')

        self.base_url = f"{shop_url.rstrip('/')}/admin/api/2024-01"
        self.api_key = self.api_key
        self.api_secret = self.api_secret
        self.auth_config = {
            'api_key': self.api_key,
            'api_secret': self.api_secret,
        }

    def _setup_session(self):
        """Shopify使用API Key认证"""
        self.session.auth = (self.api_key, self.api_secret)
        self.session.headers.update({
            'Content-Type': 'application/json',
        })

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            response = self._make_request('GET', '/shop.json')
            return 'shop' in response
        except Exception as e:
            logger.error(f"Shopify连接测试失败: {e}")
            return False

    def get_orders(self, start_date=None, end_date=None, **filters) -> List[Dict]:
        """获取订单列表"""
        params = {
            'status': 'any',
            'limit': '250',
        }

        if start_date:
            params['created_at_min'] = start_date.strftime('%Y-%m-%dT%H:%M:%S%z')
        if end_date:
            params['created_at_max'] = end_date.strftime('%Y-%m-%dT%H:%M:%S%z')

        response = self._make_request('GET', '/orders.json', params=params)

        orders = response.get('orders', [])
        return self._parse_orders(orders)

    def get_order(self, order_id: str) -> Dict:
        """获取单个订单"""
        response = self._make_request('GET', f'/orders/{order_id}.json')

        order_data = response.get('order', {})
        if order_data:
            return self._parse_order(order_data)
        return {}

    def update_order_status(self, order_id: str, status: str, tracking_number: str = None) -> bool:
        """更新订单状态"""
        try:
            if status == 'shipped':
                fulfillment_data = {
                    'fulfillment': {
                        'tracking_number': tracking_number or '',
                        'tracking_company': 'Other',
                        'notify_customer': True,
                    }
                }

                response = self._make_request(
                    'POST',
                    f'/orders/{order_id}/fulfillments.json',
                    data=fulfillment_data
                )

                return 'fulfillment' in response

            elif status == 'cancelled':
                order_data = {
                    'order': {
                        'id': order_id,
                        'status': 'cancelled',
                    }
                }

                response = self._make_request(
                    'PUT',
                    f'/orders/{order_id}.json',
                    data=order_data
                )

                return 'order' in response

            return False

        except Exception as e:
            logger.error(f"Shopify订单状态更新失败: {e}")
            return False

    def get_products(self, **filters) -> List[Dict]:
        """获取商品列表"""
        params = {
            'limit': '250',
        }

        if 'limit' in filters:
            params['limit'] = str(filters['limit'])

        response = self._make_request('GET', '/products.json', params=params)

        products = response.get('products', [])
        return self._parse_products(products)

    def get_product(self, product_id: str) -> Dict:
        """获取单个商品"""
        response = self._make_request('GET', f'/products/{product_id}.json')

        product_data = response.get('product', {})
        if product_data:
            return self._parse_product(product_data)
        return {}

    def create_product(self, product_data: Dict) -> Dict:
        """创建商品"""
        shopify_product = self._transform_to_shopify_product(product_data)

        response = self._make_request('POST', '/products.json', data={'product': shopify_product})

        return {
            'product_id': response.get('product', {}).get('id'),
            'success': True
        }

    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """更新商品"""
        shopify_product = self._transform_to_shopify_product(product_data)

        response = self._make_request('PUT', f'/products/{product_id}.json', data={'product': shopify_product})

        return {
            'product_id': response.get('product', {}).get('id'),
            'success': True
        }

    def delete_product(self, product_id: str) -> bool:
        """删除商品"""
        response = self._make_request('DELETE', f'/products/{product_id}.json')

        return response is None

    def update_inventory(self, sku: str, quantity: int) -> bool:
        """更新库存"""
        inventory_level_data = {
            'inventory_item': {
                'sku': sku,
                'available': quantity,
            }
        }

        response = self._make_request('POST', '/inventory_levels/set.json', data=inventory_level_data)

        return 'inventory_item' in response

    def batch_update_inventory(self, updates: List[Dict]) -> List[Dict]:
        """批量更新库存"""
        results = []
        for update in updates:
            result = self.update_inventory(update['sku'], update['quantity'])
            results.append({
                'sku': update['sku'],
                'success': result
            })
        return results

    def _transform_to_shopify_product(self, product_data: Dict) -> Dict:
        """转换为Shopify商品格式"""
        return {
            'title': product_data.get('name'),
            'body_html': product_data.get('description', ''),
            'vendor': product_data.get('brand', ''),
            'product_type': product_data.get('category', ''),
            'status': 'active' if product_data.get('status') == 'onsale' else 'draft',
            'variants': [{
                'sku': product_data.get('sku'),
                'price': str(product_data.get('price', 0)),
                'inventory_quantity': product_data.get('stock', 0),
                'inventory_management': 'shopify',
            }],
        }

    def _parse_orders(self, orders: List[Dict]) -> List[Dict]:
        """解析订单数据"""
        parsed = []
        for order in orders:
            parsed.append(self._parse_order(order))
        return parsed

    def _parse_order(self, order: Dict) -> Dict:
        """解析单个订单"""
        items = order.get('line_items', [])
        order_items = []
        for item in items:
            order_items.append({
                'sku': item.get('sku'),
                'product_name': item.get('title'),
                'quantity': int(item.get('quantity', 0)),
                'unit_price': float(item.get('price', 0)),
                'product_id': item.get('product_id'),
            })

        return {
            'order_id': str(order.get('id')),
            'status': self._map_order_status(order.get('financial_status', 'pending')),
            'amount': float(order.get('total_price', 0)),
            'currency': order.get('currency', 'USD'),
            'buyer_email': order.get('email', ''),
            'buyer_name': f"{order.get('shipping_address', {}).get('first_name', '')} {order.get('shipping_address', {}).get('last_name', '')}",
            'created_at': order.get('created_at'),
            'items': order_items,
        }

    def _parse_products(self, products: List[Dict]) -> List[Dict]:
        """解析商品数据"""
        parsed = []
        for product in products:
            parsed.append(self._parse_product(product))
        return parsed

    def _parse_product(self, product: Dict) -> Dict:
        """解析单个商品"""
        variants = product.get('variants', [])
        if variants:
            variant = variants[0]
            return {
                'id': str(product.get('id')),
                'sku': variant.get('sku'),
                'name': product.get('title'),
                'price': float(variant.get('price', 0)),
                'stock': int(variant.get('inventory_quantity', 0)),
                'status': 'onsale' if product.get('status') == 'active' else 'offshelf',
            }
        else:
            return {
                'id': str(product.get('id')),
                'sku': '',
                'name': product.get('title'),
                'price': 0,
                'stock': 0,
                'status': 'offshelf',
            }

    def _map_order_status(self, status: str) -> str:
        """映射订单状态"""
        status_map = {
            'pending': 'pending',
            'authorized': 'paid',
            'paid': 'paid',
            'partially_paid': 'paid',
            'voided': 'cancelled',
            'refunded': 'cancelled',
        }
        return status_map.get(status, 'pending')
