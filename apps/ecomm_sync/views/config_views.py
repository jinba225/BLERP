"""配置管理视图"""
import logging

logger = logging.getLogger(__name__)


class PlatformConfigListView:
    """平台配置列表视图"""

    def get_context_data(self):
        return {
            "page_title": "电商平台配置",
            "breadcrumb_list": [
                {"name": "电商同步", "url": "/ecomm_sync/dashboard"},
                {"name": "配置管理", "url": "/admin/ecomm_sync_platform/"},
            ],
            "action_url": "/admin/ecomm_sync_platform_add/",
            "config_list_url": "/admin/ecomm_sync_platform_list/",
            "platform_choices": ["淘宝", "1688", "京东"],
        }


class WooConfigListView:
    """WooCommerce配置列表视图"""

    def get_context_data(self):
        return {
            "page_title": "WooCommerce店铺配置",
            "breadcrumb_list": [
                {"name": "电商同步", "url": "/ecomm_sync/dashboard"},
                {"name": "配置管理", "url": "/admin/ecomm_sync_platform/"},
            ],
            "action_url": "/admin/ecomm_sync_woo_shop_config_add/",
            "woo_config_list_url": "/admin/ecomm_sync_woo_shop_list/",
            "woo_config_detail_url": "/admin/ecomm_sync_woo_shop_config/",
        }


class StrategyConfigListView:
    """同步策略配置列表视图"""

    def get_context_data(self):
        return {
            "page_title": "同步策略配置",
            "breadcrumb_list": [
                {"name": "电商同步", "url": "/ecomm_sync/dashboard"},
                {"name": "配置管理", "url": "/admin/ecomm_sync_platform/"},
            ],
            "action_url": "/admin/ecomm_sync_strategy_add/",
            "strategy_list_url": "/admin/ecomm_sync_strategy_list/",
            "platform_choices": ["淘宝", "1688", "京东"],
            "strategy_type_choices": ["incremental", "full_sync", "price_monitor"],
        }


class ConfigDetailView:
    """配置详情视图"""

    def get_context_data(self):
        return {
            "page_title": "配置详情",
            "breadcrumb_list": [
                {"name": "电商同步", "url": "/ecomm_sync/dashboard"},
                {"name": "配置管理", "url": "/admin/ecomm_sync_platform/"},
                {"name": "配置详情", "url": "#"},
            ],
            "back_url": "/admin/ecomm_sync_platform_list/",
        }
