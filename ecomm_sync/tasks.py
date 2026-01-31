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
    from core.models import Platform
    from ecomm_sync.services.sync_manager import SyncManager

    logger.info(f'开始同步任务: 平台ID={platform_id}, 策略={strategy_type}')
    
    try:
        platform = Platform.objects.get(id=platform_id)
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
    from core.models import Platform
    from ecomm_sync.services.sync_manager import SyncManager
    
    logger.info(f'开始价格监控任务: 平台ID={platform_id}')
    
    try:
        platform = Platform.objects.get(id=platform_id)
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
def sync_orders_task(self, platform_id: int, hours: int = 24):
    """
    Celery任务：同步平台订单

    Args:
        self: Celery任务实例
        platform_id: 平台ID
        hours: 同步最近多少小时的订单
    """
    from core.models import Platform
    from ecomm_sync.services.order_sync import OrderSyncService
    
    logger.info(f'开始订单同步: 平台ID={platform_id}, 最近{hours}小时')
    
    try:
        platform = Platform.objects.get(id=platform_id)
        service = OrderSyncService(platform)
        results = service.sync_new_orders(hours=hours)
        
        logger.info(f'订单同步完成: {results}')
        return {'status': 'success', 'result': results}
        
    except Exception as e:
        logger.error(f'订单同步失败: {e}')
        return {'status': 'failed', 'error': str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_stock_task(self, sku: str):
    """
    Celery任务：同步库存到平台

    Args:
        self: Celery任务实例
        sku: SKU代码
    """
    from ecomm_sync.services.stock_sync import StockSyncService
    
    logger.info(f'开始库存同步: SKU={sku}')
    
    try:
        service = StockSyncService()
        results = service.sync_to_platforms(sku)
        
        logger.info(f'库存同步完成: {results}')
        return {'status': 'success', 'result': results}
        
    except Exception as e:
        logger.error(f'库存同步失败: {e}')
        return {'status': 'failed', 'error': str(e)}


@shared_task(bind=True, ignore_result=False)
def process_stock_queue_task(self, limit: int = 100):
    """
    Celery任务：处理库存同步队列

    Args:
        self: Celery任务实例
        limit: 处理数量限制
    """
    from ecomm_sync.services.stock_sync import StockSyncService
    
    logger.info(f'开始处理库存同步队列, 限制={limit}')
    
    try:
        service = StockSyncService()
        results = service.process_queue(limit=limit)
        
        logger.info(f'库存队列处理完成: {results}')
        return {'status': 'success', 'result': results}
        
    except Exception as e:
        logger.error(f'库存队列处理失败: {e}')
        return {'status': 'failed', 'error': str(e)}


@shared_task(bind=True, ignore_result=False)
def test_scraper_task(self, platform_id: int):
    """
    Celery任务：测试爬虫

    Args:
        self: Celery任务实例
        platform_id: 平台ID
    """
    from core.models import Platform
    from ecomm_sync.scrapers.hybrid import HybridScraper
    
    logger.info(f'开始测试爬虫: 平台ID={platform_id}')
    
    try:
        platform = Platform.objects.get(id=platform_id)
        scraper = HybridScraper(platform)
        
        status = scraper.get_api_status()
        
        logger.info(f'爬虫状态: {status}')
        return {'status': 'success', 'api_status': status}
        
    except Exception as e:
        logger.error(f'测试爬虫失败: {e}')
        return {'status': 'failed', 'error': str(e)}
