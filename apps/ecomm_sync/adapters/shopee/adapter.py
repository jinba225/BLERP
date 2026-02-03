"""
Shopee电商平台适配器

Shopee是东南亚领先的电商平台
"""
from ..base import BaseAdapter
from typing import Dict, List
import hashlib
import hmac
import base64
import json
from datetime import datetime
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)


class ShopeeAdapter(BaseAdapter):
    """Shopee电商平台适配器"""

    def __init__(self, account: 'PlatformAccount'):
        super().__init__(account)
        
        # Shopee区分不同区域的API端点
        region = self.auth_config.get('region', 'sg').lower()
        region_map = {
            'tw': 'https://partner.shopee.tw',
            'my': 'https://partner.shopee.my',
            'id': 'https://partner.shopee.co.id',
            'th': 'https://partner.shopee.co.th',
            'vn': 'https://partner.shopee.vn',
            'ph': 'https://partner.shopee.ph',
            'sg': 'https://partner.shopeemobile.com',
            'br': 'https://partner.shopee.com.br',
            'mx': 'https://partner.shopee.com.mx',
        }
        self.base_url = region_map.get(region, 'https://partner.shopeemobile.com')
        self.api_version = 'v1'
        
        # 从auth_config获取认证信息
        self.partner_id = self.auth_config.get('partner_id')
        self.shop_id = self.auth_config.get('shop_id')
        self.partner_key = self.auth_config.get('partner_key')
        
        if not self.partner_id or not self.shop_id or not self.partner_key:
            raise ValueError("Shopee API配置不完整，需要partner_id、shop_id和partner_key")

    def _setup_session(self):
        """设置Session认证头"""
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })

    def _generate_signature(self, path: str, params: Dict, body: str = '') -> str:
        """生成API签名
        
        Shopee使用HMAC-SHA256签名
        """
        # 添加基础参数
        params['partner_id'] = self.partner_id
        params['timestamp'] = int(datetime.now().timestamp())
        
        # 按字母顺序排序参数
        sorted_params = sorted(params.items())
        query_string = urlencode(sorted_params)
        
        # 构建签名字符串
        # 格式: {partner_id}{path}{params}{timestamp}{access_key}
        # 或者: {partner_id}{path}{query_string}{timestamp}{partner_key}
        base_string = f"{self.partner_id}{path}{query_string}{params['timestamp']}{self.partner_key}"
        
        # 使用HMAC-SHA256签名
        signature = hmac.new(
            self.partner_key.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            params = {
                'shop_id': self.shop_id
            }
            
            path = '/api/v1/shop/auth_partner'
            signature = self._generate_signature(path, params)
            params['sign'] = signature
            
            response = self._make_request('GET', path, params=params)
            return 'error' not in response
        except Exception as e:
            logger.error(f"Shopee连接测试失败: {e}")
            return False

    def get_orders(self, start_date=None, end_date=None, **filters) -> List[Dict]:
        """获取订单列表"""
        params = {
            'shop_id': self.shop_id,
            'page_size': filters.get('limit', 100),
            'pagination_offset': filters.get('offset', 0),
            'order_status': filters.get('status', 'ALL')
        }
        
        if start_date:
            params['create_time_from'] = int(start_date.timestamp())
        if end_date:
            params['create_time_to'] = int(end_date.timestamp())
        
        path = '/api/v1/orders/basics'
        signature = self._generate_signature(path, params)
        params['sign'] = signature
        
        response = self._make_request('GET', path, params=params)
        orders_data = response.get('response', {}).get('order_list', [])
        
        return self._parse_orders(orders_data)

    def get_order(self, order_id: str) -> Dict:
        """获取单个订单"""
        params = {
            'shop_id': self.shop_id,
            'ordersn_list': f"[{order_id}]"
        }
        
        path = '/api/v1/orders/detail'
        signature = self._generate_signature(path, params)
        params['sign'] = signature
        
        response = self._make_request('GET', path, params=params)
        order_list = response.get('response', {}).get('order_list', [])
        
        if order_list:
            return self._parse_order(order_list[0])
        return {}

    def update_order_status(self, order_id: str, status: str, tracking_number: str = None) -> bool:
        """更新订单状态"""
        params = {
            'shop_id': self.shop_id,
            'ordersn': order_id
        }
        
        # Shopee使用不同的操作类型
        if status == 'shipped' and tracking_number:
            params['operation_type'] = 'SHIP'
            params['carrier'] = self.auth_config.get('default_carrier', 'Other')
            params['tracking_number'] = tracking_number
        else:
            # Shopee不直接支持其他状态更新
            logger.warning(f"Shopee不支持直接更新订单状态为: {status}")
            return False
        
        path = '/api/v1/orders/ship_order'
        signature = self._generate_signature(path, params)
        params['sign'] = signature
        
        response = self._make_request('POST', path, data=params)
        return 'error' not in response

    def get_products(self, **filters) -> List[Dict]:
        """获取商品列表"""
        params = {
            'shop_id': self.shop_id,
            'pagination_offset': filters.get('offset', 0),
            'page_size': filters.get('limit', 100)
        }
        
        path = '/api/v1/items/get'
        signature = self._generate_signature(path, params)
        params['sign'] = signature
        
        response = self._make_request('GET', path, params=params)
        products_data = response.get('response', {}).get('items', [])
        
        return self._parse_products(products_data)

    def get_product(self, product_id: str) -> Dict:
        """获取单个商品"""
        params = {
            'shop_id': self.shop_id,
            'item_id_list': f"[{product_id}]"
        }
        
        path = '/api/v1/items/get'
        signature = self._generate_signature(path, params)
        params['sign'] = signature
        
        response = self._make_request('GET', path, params=params)
        items = response.get('response', {}).get('items', [])
        
        if items:
            return self._parse_product(items[0])
        return {}

    def create_product(self, product_data: Dict) -> Dict:
        """创建商品"""
        params = {
            'shop_id': self.shop_id
        }
        
        # 构建商品数据
        data = {
            'name': product_data.get('name'),
            'description': product_data.get('description'),
            'original_price': product_data.get('price'),
            'stock': product_data.get('stock', 100),
            'images': product_data.get('images', []),
            'item_skus': product_data.get('skus', []),
            'normal_stock': product_data.get('stock', 100),
        }
        
        path = '/api/v1/item/add'
        signature = self._generate_signature(path, params)
        params['sign'] = signature
        
        response = self._make_request('POST', path, params=params, data={**params, **data})
        
        if 'error' not in response:
            item_data = response.get('response', {}).get('item', {})
            return self._parse_product(item_data)
        
        return {}

    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """更新商品"""
        params = {
            'shop_id': self.shop_id,
            'item_id': product_id
        }
        
        # 构建更新数据
        data = {}
        if 'name' in product_data:
            data['name'] = product_data['name']
        if 'description' in product_data:
            data['description'] = product_data['description']
        if 'price' in product_data:
            data['price'] = product_data['price']
        if 'stock' in product_data:
            data['stock'] = product_data['stock']
        
        path = '/api/v1/item/update'
        signature = self._generate_signature(path, params)
        params['sign'] = signature
        
        response = self._make_request('POST', path, params=params, data={**params, **data})
        
        if 'error' not in response:
            item_data = response.get('response', {}).get('item', {})
            return self._parse_product(item_data)
        
        return {}

    def delete_product(self, product_id: str) -> bool:
        """删除商品"""
        params = {
            'shop_id': self.shop_id,
            'item_id': product_id
        }
        
        path = '/api/v1/item/delete'
        signature = self._generate_signature(path, params)
        params['sign'] = signature
        
        response = self._make_request('POST', path, data=params)
        return 'error' not in response

    def update_inventory(self, sku: str, quantity: int) -> bool:
        """更新库存"""
        params = {
            'shop_id': self.shop_id,
            'item_id': sku.split('_')[0] if '_' in sku else sku,  # 假设SKU格式
            'stock': quantity
        }
        
        path = '/api/v1/item/update_stock'
        signature = self._generate_signature(path, params)
        params['sign'] = signature
        
        response = self._make_request('POST', path, data=params)
        return 'error' not in response

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

    def _parse_orders(self, orders: List[Dict]) -> List[Dict]:
        """解析订单数据"""
        parsed = []
        for order in orders:
            parsed.append(self._parse_order(order))
        return parsed

    def _parse_order(self, order: Dict) -> Dict:
        """解析单个订单"""
        address_data = order.get('recipient_address', {})
        
        return {
            'order_id': order.get('order_sn'),
            'status': self._map_order_status(order.get('order_status')),
            'amount': float(order.get('total_amount', 0)),
            'currency': order.get('currency', 'SGD'),
            'buyer_email': order.get('buyer_username'),
            'buyer_name': address_data.get('name'),
            'buyer_phone': address_data.get('phone'),
            'shipping_address': {
                'address': address_data.get('full_address', ''),
                'city': address_data.get('city', ''),
                'state': address_data.get('state', ''),
                'country': address_data.get('region', ''),
                'postal_code': address_data.get('zipcode', '')
            },
            'created_at': order.get('create_time'),
            'items': self._parse_order_items(order.get('items', []))
        }

    def _parse_order_items(self, items: List[Dict]) -> List[Dict]:
        """解析订单商品"""
        parsed = []
        for item in items:
            parsed.append({
                'sku': item.get('model_sku_c'),
                'product_name': item.get('item_name'),
                'quantity': int(item.get('model_quantity_purchased', 0)),
                'unit_price': float(item.get('model_original_price', 0)),
                'product_id': item.get('item_id')
            })
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
            'id': product.get('item_id'),
            'sku': str(product.get('item_id')),
            'name': product.get('item_name'),
            'description': product.get('description', ''),
            'price': float(product.get('price', 0)),
            'currency': product.get('currency', 'SGD'),
            'stock': int(product.get('stock', 0)),
            'status': self._map_product_status(product.get('status')),
            'images': product.get('images', [])[:6]
        }

    def _map_order_status(self, status: str) -> str:
        """映射订单状态"""
        status_map = {
            'UNPAID': 'pending',
            'PAID': 'paid',
            'READY_TO_SHIP': 'processing',
            'PROCESSED': 'processing',
            'RETRY_SHIP': 'processing',
            'SHIPPED': 'shipped',
            'TO_CONFIRM_RECEIVE': 'shipped',
            'COMPLETED': 'delivered',
            'IN_CANCEL': 'cancelled',
            'CANCELLED': 'cancelled',
            'TO_RETURN': 'refunded',
            'RETURNED': 'refunded'
        }
        return status_map.get(status, 'pending')

    def _map_product_status(self, status: str) -> str:
        """映射商品状态"""
        if status in ['NORMAL', 'ACTIVE', 'LISTED']:
            return 'onsale'
        elif status in ['DELETED', 'INACTIVE', 'UNLISTED', 'BANNED']:
            return 'offshelf'
        return 'offshelf'
