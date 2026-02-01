"""
电商同步适配器模块

统一导出所有适配器和工厂方法
"""
from ecomm_sync.adapters.base import get_adapter, BaseAdapter

__all__ = ['get_adapter', 'BaseAdapter']
