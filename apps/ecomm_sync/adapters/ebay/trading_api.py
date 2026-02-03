from ..base import BaseAdapter
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class EbayAdapter(BaseAdapter):
    """eBay Trading API适配器"""

    def __init__(self, account: 'PlatformAccount'):
        super().__init__(account)
        self.api_url = self.account.platform.base_url or "https://api.ebay.com/ws/api.dll"
        self.auth_config = {
            'devID': self.account.auth_config.get('dev_id'),
            'appID': self.account.auth_config.get('app_id'),
            'certID': self.account.auth_config.get('cert_id'),
            'token': self.account.auth_config.get('oauth_token'),
            'siteID': str(self.account.auth_config.get('site_id', '0')),
        }

    def _setup_session(self):
        """eBay使用OAuth Token认证"""
        self.session.headers.update({
            'X-EBAY-API-CALL-NAME': '',
            'X-EBAY-API-SITE-ID': self.auth_config['siteID'],
            'X-EBAY-API-COMPATIBILITY-LEVEL': '967',
            'X-EBAY-API-DEV-NAME': self.auth_config['devID'],
            'X-EBAY-API-APP-NAME': self.auth_config['appID'],
            'X-EBAY-API-CERT-NAME': self.auth_config['certID'],
        })

    def _build_xml_request(self, call_name: str, elements: List[tuple] = None) -> str:
        """构建XML请求体"""
        xml_parts = [
            '<?xml version="1.0" encoding="utf-8"?>',
            f'<{call_name}Request xmlns="urn:ebay:apis:eBLBaseComponents">',
        ]

        if elements:
            for tag, value in elements:
                if isinstance(value, list):
                    for item in value:
                        xml_parts.append(f'<{tag}>{item}</{tag}>')
                else:
                    xml_parts.append(f'<{tag}>{value}</{tag}>')

        xml_parts.append(f'</{call_name}Request>')
        return '\n'.join(xml_parts)

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            xml_data = self._build_xml_request('GeteBayOfficialTime')
            self.session.headers['X-EBAY-API-CALL-NAME'] = 'GeteBayOfficialTime'

            response = self.session.post(
                self.api_url,
                data=xml_data.encode('utf-8'),
                headers={'Content-Type': 'text/xml'}
            )

            response.raise_for_status()
            return 'GeteBayOfficialTimeResponse' in response.text
        except Exception as e:
            logger.error(f"eBay连接测试失败: {e}")
            return False

    def get_orders(self, start_date=None, end_date=None, **filters) -> List[Dict]:
        """获取订单列表"""
        xml_elements = []

        if start_date:
            xml_elements.append(('CreateTimeFrom', start_date.strftime('%Y-%m-%dT%H:%M:%SZ')))
        if end_date:
            xml_elements.append(('CreateTimeTo', end_date.strftime('%Y-%m-%dT%H:%M:%SZ')))

        xml_elements.extend([
            ('OrderRole', 'Seller'),
            ('OrderStatus', 'Active'),
        ])

        xml_data = self._build_xml_request('GetOrders', xml_elements)
        self.session.headers['X-EBAY-API-CALL-NAME'] = 'GetOrders'

        response = self._make_request(
            'POST',
            self.api_url,
            data={'xml': xml_data},
            headers={'Content-Type': 'text/xml'}
        )

        return self._parse_orders(response)

    def get_order(self, order_id: str) -> Dict:
        """获取单个订单"""
        xml_elements = [('OrderID', order_id)]
        xml_data = self._build_xml_request('GetOrderTransactions', xml_elements)
        self.session.headers['X-EBAY-API-CALL-NAME'] = 'GetOrderTransactions'

        response = self._make_request(
            'POST',
            self.api_url,
            data={'xml': xml_data},
            headers={'Content-Type': 'text/xml'}
        )

        orders = self._parse_orders(response)
        return orders[0] if orders else {}

    def update_order_status(self, order_id: str, status: str, tracking_number: str = None) -> bool:
        """更新订单状态"""
        logger.warning("eBay订单状态更新需要通过CompleteSale API，暂未实现")
        return False

    def get_products(self, **filters) -> List[Dict]:
        """获取商品列表"""
        logger.warning("eBay商品列表获取需要通过GetMyeBaySelling API，暂未实现")
        return []

    def get_product(self, product_id: str) -> Dict:
        """获取单个商品"""
        xml_elements = [('ItemID', product_id)]
        xml_data = self._build_xml_request('GetItem', xml_elements)
        self.session.headers['X-EBAY-API-CALL-NAME'] = 'GetItem'

        response = self._make_request(
            'POST',
            self.api_url,
            data={'xml': xml_data},
            headers={'Content-Type': 'text/xml'}
        )

        return self._parse_product(response)

    def create_product(self, product_data: Dict) -> Dict:
        """创建商品"""
        xml_elements = [
            ('Title', product_data.get('name')),
            ('Description', product_data.get('description')),
            ('StartPrice', str(product_data.get('price', 0))),
            ('Quantity', str(product_data.get('quantity', 1))),
            ('Country', product_data.get('country', 'US')),
            ('Currency', product_data.get('currency', 'USD')),
        ]

        xml_data = self._build_xml_request('AddItem', xml_elements)
        self.session.headers['X-EBAY-API-CALL-NAME'] = 'AddItem'

        response = self._make_request(
            'POST',
            self.api_url,
            data={'xml': xml_data},
            headers={'Content-Type': 'text/xml'}
        )

        return {'product_id': response.get('ItemID'), 'success': True}

    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """更新商品"""
        logger.warning("eBay商品更新需要通过ReviseItem API，暂未实现")
        return {}

    def delete_product(self, product_id: str) -> bool:
        """删除商品"""
        xml_elements = [('ItemID', product_id), ('EndingReason', 'NotAvailable')]
        xml_data = self._build_xml_request('EndItem', xml_elements)
        self.session.headers['X-EBAY-API-CALL-NAME'] = 'EndItem'

        response = self._make_request(
            'POST',
            self.api_url,
            data={'xml': xml_data},
            headers={'Content-Type': 'text/xml'}
        )

        return response.get('Ack') == 'Success'

    def update_inventory(self, sku: str, quantity: int) -> bool:
        """更新库存"""
        xml_elements = [
            ('InventoryStatus', [
                ('ItemID', sku),
                ('Quantity', str(quantity)),
            ])
        ]

        xml_data = self._build_xml_request('ReviseInventoryStatus', xml_elements)
        self.session.headers['X-EBAY-API-CALL-NAME'] = 'ReviseInventoryStatus'

        response = self._make_request(
            'POST',
            self.api_url,
            data={'xml': xml_data},
            headers={'Content-Type': 'text/xml'}
        )

        return response.get('Ack') == 'Success'

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

    def _parse_orders(self, response_data: Dict) -> List[Dict]:
        """解析订单数据"""
        if not isinstance(response_data, dict):
            return []

        orders_array = response_data.get('OrderArray', {}).get('Order', [])
        if not isinstance(orders_array, list):
            orders_array = [orders_array] if orders_array else []

        parsed = []
        for order in orders_array:
            parsed.append({
                'order_id': order.get('OrderID'),
                'status': self._map_order_status(order.get('OrderStatus')),
                'amount': float(order.get('Total', {}).get('Amount', 0)),
                'currency': order.get('Total', {}).get('CurrencyID'),
                'buyer_email': order.get('TransactionArray', {}).get('Transaction', [{}])[0].get('Buyer', {}).get('Email'),
                'buyer_name': order.get('ShippingAddress', {}).get('Name'),
                'created_at': order.get('CreatedTime'),
                'items': self._parse_order_items(order.get('TransactionArray', {}).get('Transaction', [])),
            })

        return parsed

    def _parse_order_items(self, transactions: List[Dict]) -> List[Dict]:
        """解析订单商品"""
        if not isinstance(transactions, list):
            transactions = [transactions] if transactions else []

        parsed = []
        for txn in transactions:
            parsed.append({
                'sku': txn.get('Item', {}).get('SKU'),
                'product_name': txn.get('Item', {}).get('Title'),
                'quantity': int(txn.get('QuantityPurchased', 0)),
                'unit_price': float(txn.get('TransactionPrice', {}).get('Amount', 0)),
                'product_id': txn.get('Item', {}).get('ItemID'),
            })

        return parsed

    def _parse_product(self, response_data: Dict) -> Dict:
        """解析单个商品"""
        item = response_data.get('Item', {})
        if not item:
            return {}

        return {
            'id': item.get('ItemID'),
            'sku': item.get('SKU'),
            'name': item.get('Title'),
            'price': float(item.get('StartPrice', {}).get('Amount', 0)),
            'stock': int(item.get('Quantity', 0)),
            'status': 'onsale' if item.get('ListingStatus') == 'Active' else 'offshelf',
        }

    def _map_order_status(self, status: str) -> str:
        """映射订单状态"""
        status_map = {
            'Active': 'paid',
            'Completed': 'delivered',
            'Cancelled': 'cancelled',
            'InProcess': 'processing',
        }
        return status_map.get(status, 'pending')
