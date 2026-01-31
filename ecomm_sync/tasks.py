import asyncio
import logging
from celery import shared_task


logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=False)
def sync_platform_products_task(self, platform_id: int, strategy_type: str = 'incremental'):
    """
    Celery任务：同步平台产品

    Args:
        self: Celery任务实例
        platform_id: 平台ID
        strategy_type: 同步策略类型
    """
    from ecomm_sync.models import EcommPlatform
    from ecomm_sync.services.sync_manager import SyncManager

    logger.info(f'开始同步任务: 平台ID={platform_id}, 策略={strategy_type}')
    
    try:
        platform = EcommPlatform.objects.get(id=platform_id)
        sync_manager = SyncManager()
        
        result = asyncio.run(
            sync_manager.sync_platform_products(platform, strategy_type)
        )
        
        logger.info(f'同步完成: {result}')
        return {'status': 'success', 'result': result}
        
    except Exception as e:
        logger.error(f'同步任务失败: {e}')
        return {'status': 'failed', 'error': str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_price_changes_task(self, platform_id: int):
    """
    Celery任务：同步价格变更

    Args:
        self: Celery任务实例
        platform_id: 平台ID
    """
    from ecomm_sync.models import EcommPlatform
    from ecomm_sync.services.sync_manager import SyncManager
    
    logger.info(f'开始价格监控任务: 平台ID={platform_id}')
    
    try:
        platform = EcommPlatform.objects.get(id=platform_id)
        sync_manager = SyncManager()
        
        result = asyncio.run(
            sync_manager.sync_price_changes(platform)
        )
        
        logger.info(f'价格监控完成: {result}')
        return {'status': 'success', 'result': result}
        
    except Exception as e:
        logger.error(f'价格监控任务失败: {e}')
        return {'status': 'failed', 'error': str(e)}


@shared_task(bind=True, ignore_result=False)
def test_scraper_task(self, platform_id: int):
    """
    Celery任务：测试爬虫

    Args:
        self: Celery任务实例
        platform_id: 平台ID
    """
    from ecomm_sync.models import EcommPlatform
    from ecomm_sync.scrapers.hybrid import HybridScraper
    
    logger.info(f'开始测试爬虫: 平台ID={platform_id}')
    
    try:
        platform = EcommPlatform.objects.get(id=platform_id)
        scraper = HybridScraper(platform)
        
        status = scraper.get_api_status()
        
        logger.info(f'爬虫状态: {status}')
        return {'status': 'success', 'api_status': status}
        
    except Exception as e:
        logger.error(f'测试爬虫失败: {e}')
        return {'status': 'failed', 'error': str(e)}
