"""
适配器模块初始化
"""
from .base import (
    BaseCollectAdapter,
    One688CollectAdapter,
    TaobaoCollectAdapter,
    get_collect_adapter,
)

__all__ = [
    "BaseCollectAdapter",
    "TaobaoCollectAdapter",
    "One688CollectAdapter",
    "get_collect_adapter",
]
