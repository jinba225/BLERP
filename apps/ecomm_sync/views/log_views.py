"""日志管理视图"""

import logging

logger = logging.getLogger(__name__)


class LogListView:
    """日志列表视图（临时）"""

    def get_context_data(self):
        return {
            "page_title": "同步日志",
            "breadcrumb_list": [
                {"name": "电商同步", "url": "/ecomm_sync/dashboard"},
                {"name": "同步日志", "url": "#"},
            ],
            "filter_fields": ["platform", "log_type", "status", "created_at"],
            "log_type_choices": [
                "incremental",
                "full_sync",
                "sync",
            ],
            "status_choices": ["success", "failed", "running", "warning"],
        }


class LogDetailView:
    """日志详情视图（临时）"""

    def get_context_data(self):
        return {
            "page_title": "日志详情",
            "breadcrumb_list": [
                {"name": "电商同步", "url": "/ecomm_sync/dashboard"},
                {"name": "同步日志", "url": "#"},
            ],
            "back_url": "/ecomm_sync/logs/",
        }
