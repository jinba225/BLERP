"""
顺丰物流适配器

参考顺丰API文档实现
"""
import base64
import hashlib
import hmac
import logging
import time
from typing import Any, Dict, List

import requests
from logistics.adapters.base import LogisticsAdapterBase
from logistics.adapters.factory import register_adapter
from logistics.models import ShippingOrder

logger = logging.getLogger(__name__)


@register_adapter("SF")
class SFAdapter(LogisticsAdapterBase):
    """顺丰物流适配器"""

    def __init__(self, logistics_company):
        super().__init__(logistics_company)

        # 顺丰API配置
        self.client_id = self.config.get("client_id")
        self.client_secret = self.config.get("client_secret")
        self.check_word = self.config.get("check_word", "")
        self.api_url = self.api_url or "https://sfapi.sf-express.com/std/service"

        if not self.client_id or not self.client_secret:
            raise ValueError("顺丰API配置不完整，需要client_id和client_secret")

    def _sign_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """签名请求

        Args:
            params: 请求参数

        Returns:
            Dict: 签名后的参数
        """
        # 添加时间戳
        timestamp = str(int(time.time()))
        params["timestamp"] = timestamp

        # 生成签名
        sign_str = self.client_secret + timestamp + str(params)
        sign = hmac.new(
            self.client_secret.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha256
        ).digest()

        signature = base64.b64encode(sign).decode("utf-8")
        params["signature"] = signature

        return params

    def test_connection(self) -> bool:
        """测试连接

        Returns:
            bool: 连接成功返回True，否则返回False
        """
        try:
            # 使用顺丰服务测试接口
            url = f"{self.api_url}/route/test"
            params = {}

            signed_params = self._sign_request(params)

            response = requests.get(url, params=signed_params, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data.get("code") == 200

        except Exception as e:
            logger.error(f"顺丰连接测试失败: {e}")
            return False

    def create_waybill(self, shipping_order: ShippingOrder) -> str:
        """创建运单

        Args:
            shipping_order: 物流订单对象

        Returns:
            str: 快递单号

        Raises:
            Exception: 创建运单失败时抛出异常
        """
        try:
            # 获取平台订单信息
            platform_order = shipping_order.platform_order
            shipping_address = platform_order.shipping_address or {}

            # 构建请求参数
            params = {
                "order_type": 1,  # 1: 标准快递
                "express_type": 1,  # 1: 标准快递
                "pay_method": 1,  # 1: 寄件方付
                "cargo": "商品",
                "express_desc": "电商商品",
                "weight": float(shipping_order.weight or 1),
                "sender": {
                    "name": self.config.get("sender_name", ""),
                    "mobile": self.config.get("sender_phone", ""),
                    "province": self.config.get("sender_province", ""),
                    "city": self.config.get("sender_city", ""),
                    "address": self.config.get("sender_address", ""),
                },
                "receiver": {
                    "name": platform_order.buyer_name or "",
                    "mobile": platform_order.buyer_phone or "",
                    "address": shipping_address.get("address", ""),
                    "province": shipping_address.get("province", ""),
                    "city": shipping_address.get("city", ""),
                    "district": shipping_address.get("district", ""),
                },
            }

            # 签名
            signed_params = self._sign_request(params)

            # 发送请求
            url = f"{self.api_url}/order/create"
            response = requests.post(url, json=signed_params, timeout=60)
            response.raise_for_status()

            data = response.json()

            if data.get("code") == 200:
                tracking_number = data.get("data", {}).get("waybill_no")
                if not tracking_number:
                    raise Exception("顺丰API返回数据格式错误：缺少waybill_no")
                return tracking_number
            else:
                raise Exception(f"创建顺丰运单失败: {data.get('message', '未知错误')}")

        except requests.RequestException as e:
            logger.error(f"顺丰API请求失败: {e}")
            raise Exception(f"顺丰API请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"创建顺丰运单失败: {e}")
            raise

    def track_shipping(self, tracking_number: str) -> List[Dict[str, Any]]:
        """查询物流轨迹

        Args:
            tracking_number: 快递单号

        Returns:
            List[Dict]: 轨迹信息列表

        Raises:
            Exception: 查询失败时抛出异常
        """
        try:
            # 构建请求参数
            params = {"waybill_no": tracking_number}

            # 签名
            signed_params = self._sign_request(params)

            # 发送请求
            url = f"{self.api_url}/route/track"
            response = requests.post(url, json=signed_params, timeout=60)
            response.raise_for_status()

            data = response.json()

            if data.get("code") == 200:
                routes = data.get("data", {}).get("routes", [])

                # 转换为统一格式
                tracking_infos = []
                for route in routes:
                    tracking_infos.append(
                        {
                            "track_time": route.get("time"),
                            "track_status": route.get("status"),
                            "track_location": route.get("location", ""),
                            "track_description": route.get("description", ""),
                            "operator": route.get("operator", ""),
                            "raw_data": route,
                        }
                    )

                return tracking_infos
            else:
                raise Exception(f"查询顺丰物流失败: {data.get('message', '未知错误')}")

        except requests.RequestException as e:
            logger.error(f"顺丰API请求失败: {e}")
            raise Exception(f"顺丰API请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"查询顺丰物流失败: {e}")
            raise

    def print_waybill(self, shipping_order: ShippingOrder) -> str:
        """打印面单

        Args:
            shipping_order: 物流订单对象

        Returns:
            str: 面单文件路径

        Raises:
            Exception: 打印面单失败时抛出异常
        """
        try:
            # 构建请求参数
            params = {
                "waybill_no": shipping_order.tracking_number,
                "print_type": "pdf",  # 或 'image'
            }

            # 签名
            signed_params = self._sign_request(params)

            # 发送请求
            url = f"{self.api_url}/waybill/print"
            response = requests.post(url, json=signed_params, timeout=60)
            response.raise_for_status()

            data = response.json()

            if data.get("code") == 200:
                # 这里应该保存返回的PDF或图片文件
                # 简化实现，返回URL
                waybill_url = data.get("data", {}).get("waybill_url")
                if not waybill_url:
                    raise Exception("顺丰API返回数据格式错误：缺少waybill_url")
                return waybill_url
            else:
                raise Exception(f"打印顺丰面单失败: {data.get('message', '未知错误')}")

        except requests.RequestException as e:
            logger.error(f"顺丰API请求失败: {e}")
            raise Exception(f"顺丰API请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"打印顺丰面单失败: {e}")
            raise

    def cancel_waybill(self, tracking_number: str) -> bool:
        """取消运单

        Args:
            tracking_number: 快递单号

        Returns:
            bool: 取消成功返回True，否则返回False

        Raises:
            Exception: 取消运单失败时抛出异常
        """
        try:
            # 构建请求参数
            params = {"waybill_no": tracking_number}

            # 签名
            signed_params = self._sign_request(params)

            # 发送请求
            url = f"{self.api_url}/order/cancel"
            response = requests.post(url, json=signed_params, timeout=60)
            response.raise_for_status()

            data = response.json()

            return data.get("code") == 200

        except requests.RequestException as e:
            logger.error(f"顺丰API请求失败: {e}")
            raise Exception(f"顺丰API请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"取消顺丰运单失败: {e}")
            raise

    def get_shipping_cost(self, weight: float, destination: str) -> Dict[str, Any]:
        """查询物流费用（可选实现）

        Args:
            weight: 重量（kg）
            destination: 目的地

        Returns:
            Dict: 费用信息
        """
        try:
            # 构建请求参数
            params = {"weight": weight, "destination": destination}

            # 签名
            signed_params = self._sign_request(params)

            # 发送请求
            url = f"{self.api_url}/price/query"
            response = requests.post(url, json=signed_params, timeout=60)
            response.raise_for_status()

            data = response.json()

            if data.get("code") == 200:
                price_data = data.get("data", {})
                return {
                    "freight": price_data.get("freight", 0),
                    "fuel_surcharge": price_data.get("fuel_surcharge", 0),
                    "remote_area_fee": price_data.get("remote_area_fee", 0),
                    "total": price_data.get("total", 0),
                }
            else:
                logger.warning(f"查询顺丰物流费用失败: {data.get('message', '未知错误')}")
                return {}

        except Exception as e:
            logger.error(f"查询顺丰物流费用失败: {e}")
            return {}
