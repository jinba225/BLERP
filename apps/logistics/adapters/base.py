"""
物流适配器基类

定义物流适配器的统一接口
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from logistics.models import ShippingOrder


class LogisticsAdapterBase(ABC):
    """物流适配器基类 - 定义统一接口"""

    def __init__(self, logistics_company):
        from logistics.models import LogisticsCompany

        if not isinstance(logistics_company, LogisticsCompany):
            raise TypeError(f"期望LogisticsCompany对象，获得{type(logistics_company)}")

        self.company = logistics_company
        self.config = logistics_company.api_config
        self.api_url = logistics_company.api_endpoint

    @abstractmethod
    def test_connection(self) -> bool:
        """测试连接

        Returns:
            bool: 连接成功返回True，否则返回False
        """
        pass

    @abstractmethod
    def create_waybill(self, shipping_order: ShippingOrder) -> str:
        """创建运单

        Args:
            shipping_order: 物流订单对象

        Returns:
            str: 快递单号

        Raises:
            Exception: 创建运单失败时抛出异常
        """
        pass

    @abstractmethod
    def track_shipping(self, tracking_number: str) -> List[Dict[str, Any]]:
        """查询物流轨迹

        Args:
            tracking_number: 快递单号

        Returns:
            List[Dict]: 轨迹信息列表，每个元素包含：
                - track_time: 轨迹时间
                - track_status: 轨迹状态
                - track_location: 轨迹地点
                - track_description: 轨迹描述
                - operator: 操作人
                - raw_data: 原始数据

        Raises:
            Exception: 查询失败时抛出异常
        """
        pass

    @abstractmethod
    def print_waybill(self, shipping_order: ShippingOrder) -> str:
        """打印面单

        Args:
            shipping_order: 物流订单对象

        Returns:
            str: 面单文件路径（PDF或图片）

        Raises:
            Exception: 打印面单失败时抛出异常
        """
        pass

    @abstractmethod
    def cancel_waybill(self, tracking_number: str) -> bool:
        """取消运单

        Args:
            tracking_number: 快递单号

        Returns:
            bool: 取消成功返回True，否则返回False

        Raises:
            Exception: 取消运单失败时抛出异常
        """
        pass

    def get_shipping_cost(self, weight: float, destination: str) -> Dict[str, Any]:
        """查询物流费用（可选实现）

        Args:
            weight: 重量（kg）
            destination: 目的地

        Returns:
            Dict: 费用信息，包含：
                - freight: 运费
                - fuel_surcharge: 燃油费
                - remote_area_fee: 偏远费
                - total: 总费用

        Note:
            默认实现返回空字典，子类可以覆盖此方法
        """
        return {}

    def get_waybill_url(self, tracking_number: str) -> str:
        """获取面单URL

        Args:
            tracking_number: 快递单号

        Returns:
            str: 面单URL
        """
        if self.company.tracking_url_template:
            return self.company.tracking_url_template.format(tracking_number=tracking_number)
        return ""
