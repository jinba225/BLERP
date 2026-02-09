"""商品管理视图"""
import logging


logger = logging.getLogger(__name__)


class ProductListView:
    """商品列表视图（临时）"""

    def get_context_data(self, **kwargs):
        return {
            "page_title": "电商商品管理",
            "breadcrumb_list": [
                {"name": "电商同步", "url": "/ecomm_sync/dashboard"},
                {"name": "商品管理", "url": "#"},
            ],
            "filter_fields": [
                "platform",
                "sync_status",
                "product_name",
                "product_code",
                "last_scraped_at",
                "created_at",
            ],
            "action_url": "/admin/ecomm_sync_product_add",
            "platform_choices": [],
        }


class ProductDetailView:
    """商品详情视图（临时）"""

    def get_context_data(self, **kwargs):
        return {
            "page_title": "商品详情",
            "breadcrumb_list": [
                {"name": "电商同步", "url": "/ecomm_sync/dashboard"},
                {"name": "商品管理", "url": "#"},
                {"name": "商品详情", "url": "#"},
            ],
            "actions": [
                {"label": "编辑", "url": "#"},
                {"label": "删除", "url": "#"},
                {"label": "同步到Woo", "url": "#"},
            ],
        }


class ProductSyncView:
    """商品同步视图（临时）"""

    def get_context_data(self, **kwargs):
        return {
            "page_title": "商品同步",
            "breadcrumb_list": [
                {"name": "电商同步", "url": "/ecomm_sync/dashboard"},
                {"name": "商品管理", "url": "#"},
            ],
            "sync_options": [
                {"value": "price_only", "label": "仅同步价格"},
                {"value": "stock_only", "label": "仅同步库存"},
                {"value": "status_only", "label": "仅同步状态"},
                {"value": "full_sync", "label": "全量同步"},
            ],
        }
