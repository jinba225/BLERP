"""仪表盘视图"""
import logging
from django.utils import timezone


logger = logging.getLogger(__name__)


class DashboardView:
    """仪表盘视图（临时）"""
    
    def get_context_data(self):
        from ecomm_sync.models import EcommProduct, SyncLog
        
        now = timezone.now()
        
        stats = {
            'total_products': EcommProduct.objects.count(),
            'synced_products': EcommProduct.objects.filter(sync_status='synced').count(),
            'pending_products': Ecomm_Product.objects.filter(sync_status='pending').count(),
            'recent_syncs': SyncLog.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).order_by('-created_at')[:5],
        }
        
        sync_summary = {
            'last_sync': SyncLog.objects.order_by('-created_at').first(),
            'sync_status': '正常运行' if SyncLog.objects.filter(
                status='running'
            ).exists() else '空闲',
        }
        
        # 获取同步日志（最近7天）
        recent_logs = SyncLog.objects.filter(
            created_at__gte=now - timezone.timedelta(days=7)
        ).order_by('-created_at')[:10]
        
        sync_log_summary = {
            'total': SyncLog.objects.count(),
            'success': SyncLog.objects.filter(status='success').count(),
            'failed': SyncLog.objects.filter(status='failed').count(),
            'running': SyncLog.objects.filter(status='running').count(),
            'warning': SyncLog.objects.filter(status='warning').count(),
        }
        
        return {
            'page_title': '同步监控仪表盘',
            'breadcrumb_list': [
                {'name': '主页', 'url': '/'},
                {'name': '电商同步', 'url': '/ecomm_sync/dashboard'},
            ],
            'stats': stats,
            'sync_summary': sync_summary,
            'recent_syncs': recent_logs,
            'sync_log_summary': sync_log_summary,
            'platform_choices': ['淘宝', '1688'],
            'platform_sync_counts': [
                {'platform': '淘宝', 'count': Ecomm_Product.objects.filter(platform__platform_type='taobao').count()},
                {'platform': '1688', 'count': Ecomm_Product.objects.filter(platform__platform_type='alibaba').count()},
            ],
        }
