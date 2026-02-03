"""
物流适配器工厂

根据物流公司代码动态创建适配器实例
"""
from typing import Dict, Type
from logistics.adapters.base import LogisticsAdapterBase


class LogisticsAdapterFactory:
    """物流适配器工厂"""
    
    _adapter_map: Dict[str, Type[LogisticsAdapterBase]] = {}
    
    @classmethod
    def register(cls, code: str, adapter_class: Type[LogisticsAdapterBase]):
        """注册物流适配器
        
        Args:
            code: 物流公司代码，如'SF'、'YTO'等
            adapter_class: 适配器类
        """
        cls._adapter_map[code] = adapter_class
        
    @classmethod
    def get_adapter(cls, logistics_company):
        """获取对应平台的适配器实例
        
        Args:
            logistics_company: 物流公司对象
            
        Returns:
            LogisticsAdapterBase: 适配器实例
            
        Raises:
            ValueError: 不支持的物流公司代码
        """
        code = logistics_company.code.upper()
        
        adapter_class = cls._adapter_map.get(code)
        if not adapter_class:
            raise ValueError(f"不支持的物流公司代码: {code}")
            
        return adapter_class(logistics_company)
    
    @classmethod
    def get_supported_codes(cls) -> list:
        """获取所有支持的物流公司代码
        
        Returns:
            list: 物流公司代码列表
        """
        return list(cls._adapter_map.keys())


def register_adapter(code: str):
    """装饰器：注册物流适配器
    
    用法:
        @register_adapter('SF')
        class SFAdapter(LogisticsAdapterBase):
            pass
    """
    def decorator(adapter_class: Type[LogisticsAdapterBase]):
        LogisticsAdapterFactory.register(code, adapter_class)
        return adapter_class
    return decorator
