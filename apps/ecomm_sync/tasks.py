import asyncio
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=False)
def sync_platform_products_task(self, platform_id: int, strategy_type: str = "incremental"):
    """
    Celery任务：同步平台产品

    Args:
        self: Celery任务实例
        platform_id: 平台ID
        strategy_type: 同步策略类型
    """
    from core.models import Platform
    from ecomm_sync.services.sync_manager import SyncManager

    logger.info(f"开始同步任务: 平台ID={platform_id}, 策略={strategy_type}")

    try:
        platform = Platform.objects.get(id=platform_id)
        sync_manager = SyncManager()

        result = asyncio.run(sync_manager.sync_platform_products(platform, strategy_type))

        logger.info(f"同步完成: {result}")
        return {"status": "success", "result": result}

    except Exception as e:
        logger.error(f"同步任务失败: {e}")
        return {"status": "failed", "error": str(e)}


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

    logger.info(f"开始价格监控任务: 平台ID={platform_id}")

    try:
        platform = Platform.objects.get(id=platform_id)
        sync_manager = SyncManager()

        result = asyncio.run(sync_manager.sync_price_changes(platform))

        logger.info(f"价格监控完成: {result}")
        return {"status": "success", "result": result}

    except Exception as e:
        logger.error(f"价格监控任务失败: {e}")
        return {"status": "failed", "error": str(e)}


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

    logger.info(f"开始订单同步: 平台ID={platform_id}, 最近{hours}小时")

    try:
        platform = Platform.objects.get(id=platform_id)
        service = OrderSyncService(platform)
        results = service.sync_new_orders(hours=hours)

        logger.info(f"订单同步完成: {results}")
        return {"status": "success", "result": results}

    except Exception as e:
        logger.error(f"订单同步失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_stock_task(self, sku: str):
    """
    Celery任务：同步库存到平台

    Args:
        self: Celery任务实例
        sku: SKU代码
    """
    from ecomm_sync.services.stock_sync import StockSyncService

    logger.info(f"开始库存同步: SKU={sku}")

    try:
        service = StockSyncService()
        results = service.sync_to_platforms(sku)

        logger.info(f"库存同步完成: {results}")
        return {"status": "success", "result": results}

    except Exception as e:
        logger.error(f"库存同步失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def process_stock_queue_task(self, limit: int = 100):
    """
    Celery任务：处理库存同步队列

    Args:
        self: Celery任务实例
        limit: 处理数量限制
    """
    from ecomm_sync.services.stock_sync import StockSyncService

    logger.info(f"开始处理库存同步队列, 限制={limit}")

    try:
        service = StockSyncService()
        results = service.process_queue(limit=limit)

        logger.info(f"库存队列处理完成: {results}")
        return {"status": "success", "result": results}

    except Exception as e:
        logger.error(f"库存队列处理失败: {e}")
        return {"status": "failed", "error": str(e)}


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

    logger.info(f"开始测试爬虫: 平台ID={platform_id}")

    try:
        platform = Platform.objects.get(id=platform_id)
        scraper = HybridScraper(platform)

        status = scraper.get_api_status()

        logger.info(f"爬虫状态: {status}")
        return {"status": "success", "api_status": status}

    except Exception as e:
        logger.error(f"测试爬虫失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def link_purchase_order_to_platform_task(
    self, purchase_order_id: int, platform_id: int, platform_account_id: int, mappings: list
):
    """
    Celery任务：关联采购订单商品到平台商品

    Args:
        self: Celery任务实例
        purchase_order_id: 采购订单ID
        platform_id: 平台ID
        platform_account_id: 平台账号ID
        mappings: 商品映射列表
    """
    from purchase.services.purchase_sync import PurchaseSyncService

    logger.info(f"开始关联采购订单商品到平台: 采购订单ID={purchase_order_id}")

    try:
        service = PurchaseSyncService()
        result = service.link_purchase_order_to_platform(
            purchase_order_id, platform_id, platform_account_id, mappings
        )

        logger.info(f"关联采购订单商品完成: {result}")
        return {"status": "success", "result": result}

    except Exception as e:
        logger.error(f"关联采购订单商品失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_purchase_order_to_platform_task(self, purchase_order_id: int):
    """
    Celery任务：同步采购订单到平台

    Args:
        self: Celery任务实例
        purchase_order_id: 采购订单ID
    """
    from purchase.services.purchase_sync import PurchaseSyncService

    logger.info(f"开始同步采购订单到平台: 采购订单ID={purchase_order_id}")

    try:
        service = PurchaseSyncService()
        result = service.sync_purchase_order_to_platform(purchase_order_id)

        logger.info(f"同步采购订单完成: {result}")
        return {"status": "success", "result": result}

    except Exception as e:
        logger.error(f"同步采购订单到平台失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_purchase_status_to_platform_task(self, purchase_order_id: int):
    """
    Celery任务：同步采购状态到平台

    Args:
        self: Celery任务实例
        purchase_order_id: 采购订单ID
    """
    from purchase.services.purchase_sync import PurchaseSyncService

    logger.info(f"开始同步采购状态到平台: 采购订单ID={purchase_order_id}")

    try:
        service = PurchaseSyncService()
        result = service.sync_purchase_status_to_platform(purchase_order_id)

        logger.info(f"同步采购状态完成: {result}")
        return {"status": "success", "result": result}

    except Exception as e:
        logger.error(f"同步采购状态到平台失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def process_purchase_sync_queue_task(self, limit: int = 100):
    """
    Celery任务：处理采购同步队列

    Args:
        self: Celery任务实例
        limit: 处理数量限制
    """
    from purchase.services.purchase_sync import PurchaseSyncService

    logger.info(f"开始处理采购同步队列, 限制={limit}")

    try:
        service = PurchaseSyncService()
        count = service.process_purchase_sync_queue(limit=limit)

        logger.info(f"采购同步队列处理完成: 处理{count}个任务")
        return {"status": "success", "count": count}

    except Exception as e:
        logger.error(f"处理采购同步队列失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def auto_restock_alert_task(self):
    """
    Celery任务：自动补货提醒
    """
    from purchase.services.purchase_sync import PurchaseSyncService

    logger.info("开始检查自动补货提醒")

    try:
        service = PurchaseSyncService()
        alerts = service.auto_restock_alert()

        logger.info(f"自动补货提醒完成: {len(alerts)}个提醒")
        return {"status": "success", "count": len(alerts)}

    except Exception as e:
        logger.error(f"自动补货提醒失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def create_shipping_order_task(self, platform_order_id: int, logistics_company_id: int):
    """
    Celery任务：创建物流订单

    Args:
        self: Celery任务实例
        platform_order_id: 平台订单ID
        logistics_company_id: 物流公司ID
    """
    from logistics.services.sync_service import LogisticsSyncService

    logger.info(f"开始创建物流订单: 平台订单ID={platform_order_id}, 物流公司ID={logistics_company_id}")

    try:
        service = LogisticsSyncService()
        shipping_order = service.create_shipping_order(platform_order_id, logistics_company_id)

        logger.info(f"物流订单创建成功: {shipping_order.tracking_number}")
        return {"status": "success", "tracking_number": shipping_order.tracking_number}

    except Exception as e:
        logger.error(f"创建物流订单失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def track_shipping_task(self, shipping_order_id: int):
    """
    Celery任务：追踪物流

    Args:
        self: Celery任务实例
        shipping_order_id: 物流订单ID
    """
    from logistics.services.sync_service import LogisticsSyncService

    logger.info(f"开始追踪物流: 物流订单ID={shipping_order_id}")

    try:
        service = LogisticsSyncService()
        shipping_order = service.track_shipping(shipping_order_id)

        logger.info(f"物流追踪完成: 状态={shipping_order.shipping_status}")
        return {"status": "success", "shipping_status": shipping_order.shipping_status}

    except Exception as e:
        logger.error(f"物流追踪失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def batch_track_shipping_task(self, limit: int = 100):
    """
    Celery任务：批量追踪物流

    Args:
        self: Celery任务实例
        limit: 处理数量限制
    """
    from logistics.services.sync_service import LogisticsSyncService

    logger.info(f"开始批量追踪物流, 限制={limit}")

    try:
        service = LogisticsSyncService()
        count = service.batch_track_shipping(limit=limit)

        logger.info(f"批量物流追踪完成: 处理{count}个订单")
        return {"status": "success", "count": count}

    except Exception as e:
        logger.error(f"批量物流追踪失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_jumia_products_task(self, platform_account_id: int, limit: int = 100):
    """
    Celery任务：同步Jumia商品

    Args:
        self: Celery任务实例
        platform_account_id: 平台账号ID
        limit: 同步数量限制
    """
    from ecomm_sync.adapters.base import get_adapter
    from ecomm_sync.models import PlatformAccount

    logger.info(f"开始同步Jumia商品: 账号ID={platform_account_id}")

    try:
        account = PlatformAccount.objects.get(id=platform_account_id, account_type="jumia")
        adapter = get_adapter(account)

        products = adapter.get_products(limit=limit)

        logger.info(f"Jumia商品同步完成: 获取{len(products)}个商品")
        return {"status": "success", "count": len(products), "products": products}

    except Exception as e:
        logger.error(f"同步Jumia商品失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_jumia_orders_task(self, platform_account_id: int, hours: int = 24):
    """
    Celery任务：同步Jumia订单

    Args:
        self: Celery任务实例
        platform_account_id: 平台账号ID
        hours: 同步最近多少小时的订单
    """
    from datetime import datetime, timedelta

    from ecomm_sync.adapters.base import get_adapter
    from ecomm_sync.models import PlatformAccount

    logger.info(f"开始同步Jumia订单: 账号ID={platform_account_id}, 最近{hours}小时")

    try:
        account = PlatformAccount.objects.get(id=platform_account_id, account_type="jumia")
        adapter = get_adapter(account)

        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)

        orders = adapter.get_orders(start_date=start_date, end_date=end_date)

        logger.info(f"Jumia订单同步完成: 获取{len(orders)}个订单")
        return {"status": "success", "count": len(orders), "orders": orders}

    except Exception as e:
        logger.error(f"同步Jumia订单失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_cdiscount_products_task(self, platform_account_id: int, limit: int = 100):
    """
    Celery任务：同步Cdiscount商品

    Args:
        self: Celery任务实例
        platform_account_id: 平台账号ID
        limit: 同步数量限制
    """
    from ecomm_sync.adapters.base import get_adapter
    from ecomm_sync.models import PlatformAccount

    logger.info(f"开始同步Cdiscount商品: 账号ID={platform_account_id}")

    try:
        account = PlatformAccount.objects.get(id=platform_account_id, account_type="cdiscount")
        adapter = get_adapter(account)

        products = adapter.get_products(limit=limit)

        logger.info(f"Cdiscount商品同步完成: 获取{len(products)}个商品")
        return {"status": "success", "count": len(products), "products": products}

    except Exception as e:
        logger.error(f"同步Cdiscount商品失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_cdiscount_orders_task(self, platform_account_id: int, hours: int = 24):
    """
    Celery任务：同步Cdiscount订单

    Args:
        self: Celery任务实例
        platform_account_id: 平台账号ID
        hours: 同步最近多少小时的订单
    """
    from datetime import datetime, timedelta

    from ecomm_sync.adapters.base import get_adapter
    from ecomm_sync.models import PlatformAccount

    logger.info(f"开始同步Cdiscount订单: 账号ID={platform_account_id}, 最近{hours}小时")

    try:
        account = PlatformAccount.objects.get(id=platform_account_id, account_type="cdiscount")
        adapter = get_adapter(account)

        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)

        orders = adapter.get_orders(start_date=start_date, end_date=end_date)

        logger.info(f"Cdiscount订单同步完成: 获取{len(orders)}个订单")
        return {"status": "success", "count": len(orders), "orders": orders}

    except Exception as e:
        logger.error(f"同步Cdiscount订单失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_shopee_products_task(self, platform_account_id: int, limit: int = 100):
    """
    Celery任务：同步Shopee商品

    Args:
        self: Celery任务实例
        platform_account_id: 平台账号ID
        limit: 同步数量限制
    """
    from ecomm_sync.adapters.base import get_adapter
    from ecomm_sync.models import PlatformAccount

    logger.info(f"开始同步Shopee商品: 账号ID={platform_account_id}")

    try:
        account = PlatformAccount.objects.get(id=platform_account_id, account_type="shopee")
        adapter = get_adapter(account)

        products = adapter.get_products(limit=limit)

        logger.info(f"Shopee商品同步完成: 获取{len(products)}个商品")
        return {"status": "success", "count": len(products), "products": products}

    except Exception as e:
        logger.error(f"同步Shopee商品失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_shopee_orders_task(self, platform_account_id: int, hours: int = 24):
    """
    Celery任务：同步Shopee订单

    Args:
        self: Celery任务实例
        platform_account_id: 平台账号ID
        hours: 同步最近多少小时的订单
    """
    from datetime import datetime, timedelta

    from ecomm_sync.adapters.base import get_adapter
    from ecomm_sync.models import PlatformAccount

    logger.info(f"开始同步Shopee订单: 账号ID={platform_account_id}, 最近{hours}小时")

    try:
        account = PlatformAccount.objects.get(id=platform_account_id, account_type="shopee")
        adapter = get_adapter(account)

        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)

        orders = adapter.get_orders(start_date=start_date, end_date=end_date)

        logger.info(f"Shopee订单同步完成: 获取{len(orders)}个订单")
        return {"status": "success", "count": len(orders), "orders": orders}

    except Exception as e:
        logger.error(f"同步Shopee订单失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_tiktok_products_task(self, platform_account_id: int, limit: int = 100):
    """
    Celery任务：同步TikTok Shop商品

    Args:
        self: Celery任务实例
        platform_account_id: 平台账号ID
        limit: 同步数量限制
    """
    from ecomm_sync.adapters.base import get_adapter
    from ecomm_sync.models import PlatformAccount

    logger.info(f"开始同步TikTok Shop商品: 账号ID={platform_account_id}")

    try:
        account = PlatformAccount.objects.get(id=platform_account_id, account_type="tiktok")
        adapter = get_adapter(account)

        products = adapter.get_products(limit=limit)

        logger.info(f"TikTok Shop商品同步完成: 获取{len(products)}个商品")
        return {"status": "success", "count": len(products), "products": products}

    except Exception as e:
        logger.error(f"同步TikTok Shop商品失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_tiktok_orders_task(self, platform_account_id: int, hours: int = 24):
    """
    Celery任务：同步TikTok Shop订单

    Args:
        self: Celery任务实例
        platform_account_id: 平台账号ID
        hours: 同步最近多少小时的订单
    """
    from datetime import datetime, timedelta

    from ecomm_sync.adapters.base import get_adapter
    from ecomm_sync.models import PlatformAccount

    logger.info(f"开始同步TikTok Shop订单: 账号ID={platform_account_id}, 最近{hours}小时")

    try:
        account = PlatformAccount.objects.get(id=platform_account_id, account_type="tiktok")
        adapter = get_adapter(account)

        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)

        orders = adapter.get_orders(start_date=start_date, end_date=end_date)

        logger.info(f"TikTok Shop订单同步完成: 获取{len(orders)}个订单")
        return {"status": "success", "count": len(orders), "orders": orders}

    except Exception as e:
        logger.error(f"同步TikTok Shop订单失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_temu_products_task(self, platform_account_id: int, limit: int = 100):
    """
    Celery任务：同步Temu商品

    Args:
        self: Celery任务实例
        platform_account_id: 平台账号ID
        limit: 同步数量限制
    """
    from ecomm_sync.adapters.base import get_adapter
    from ecomm_sync.models import PlatformAccount

    logger.info(f"开始同步Temu商品: 账号ID={platform_account_id}")

    try:
        account = PlatformAccount.objects.get(id=platform_account_id, account_type="temu")
        adapter = get_adapter(account)

        products = adapter.get_products(limit=limit)

        logger.info(f"Temu商品同步完成: 获取{len(products)}个商品")
        return {"status": "success", "count": len(products), "products": products}

    except Exception as e:
        logger.error(f"同步Temu商品失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_temu_orders_task(self, platform_account_id: int, hours: int = 24):
    """
    Celery任务：同步Temu订单

    Args:
        self: Celery任务实例
        platform_account_id: 平台账号ID
        hours: 同步最近多少小时的订单
    """
    from datetime import datetime, timedelta

    from ecomm_sync.adapters.base import get_adapter
    from ecomm_sync.models import PlatformAccount

    logger.info(f"开始同步Temu订单: 账号ID={platform_account_id}, 最近{hours}小时")

    try:
        account = PlatformAccount.objects.get(id=platform_account_id, account_type="temu")
        adapter = get_adapter(account)

        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)

        orders = adapter.get_orders(start_date=start_date, end_date=end_date)

        logger.info(f"Temu订单同步完成: 获取{len(orders)}个订单")
        return {"status": "success", "count": len(orders), "orders": orders}

    except Exception as e:
        logger.error(f"同步Temu订单失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_wish_products_task(self, platform_account_id: int, limit: int = 100):
    """
    Celery任务：同步Wish商品

    Args:
        self: Celery任务实例
        platform_account_id: 平台账号ID
        limit: 同步数量限制
    """
    from ecomm_sync.adapters.base import get_adapter
    from ecomm_sync.models import PlatformAccount

    logger.info(f"开始同步Wish商品: 账号ID={platform_account_id}")

    try:
        account = PlatformAccount.objects.get(id=platform_account_id, account_type="wish")
        adapter = get_adapter(account)

        products = adapter.get_products(limit=limit)

        logger.info(f"Wish商品同步完成: 获取{len(products)}个商品")
        return {"status": "success", "count": len(products), "products": products}

    except Exception as e:
        logger.error(f"同步Wish商品失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_wish_orders_task(self, platform_account_id: int, hours: int = 24):
    """
    Celery任务：同步Wish订单

    Args:
        self: Celery任务实例
        platform_account_id: 平台账号ID
        hours: 同步最近多少小时的订单
    """
    from datetime import datetime, timedelta

    from ecomm_sync.adapters.base import get_adapter
    from ecomm_sync.models import PlatformAccount

    logger.info(f"开始同步Wish订单: 账号ID={platform_account_id}, 最近{hours}小时")

    try:
        account = PlatformAccount.objects.get(id=platform_account_id, account_type="wish")
        adapter = get_adapter(account)

        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)

        orders = adapter.get_orders(start_date=start_date, end_date=end_date)

        logger.info(f"Wish订单同步完成: 获取{len(orders)}个订单")
        return {"status": "success", "count": len(orders), "orders": orders}

    except Exception as e:
        logger.error(f"同步Wish订单失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_mercadolibre_products_task(self, platform_account_id: int, limit: int = 100):
    """
    Celery任务：同步MercadoLibre商品

    Args:
        self: Celery任务实例
        platform_account_id: 平台账号ID
        limit: 同步数量限制
    """
    from ecomm_sync.adapters.base import get_adapter
    from ecomm_sync.models import PlatformAccount

    logger.info(f"开始同步MercadoLibre商品: 账号ID={platform_account_id}")

    try:
        account = PlatformAccount.objects.get(id=platform_account_id, account_type="mercadolibre")
        adapter = get_adapter(account)

        products = adapter.get_products(limit=limit)

        logger.info(f"MercadoLibre商品同步完成: 获取{len(products)}个商品")
        return {"status": "success", "count": len(products), "products": products}

    except Exception as e:
        logger.error(f"同步MercadoLibre商品失败: {e}")
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, ignore_result=False)
def sync_mercadolibre_orders_task(self, platform_account_id: int, hours: int = 24):
    """
    Celery任务：同步MercadoLibre订单

    Args:
        self: Celery任务实例
        platform_account_id: 平台账号ID
        hours: 同步最近多少小时的订单
    """
    from datetime import datetime, timedelta

    from ecomm_sync.adapters.base import get_adapter
    from ecomm_sync.models import PlatformAccount

    logger.info(f"开始同步MercadoLibre订单: 账号ID={platform_account_id}, 最近{hours}小时")

    try:
        account = PlatformAccount.objects.get(id=platform_account_id, account_type="mercadolibre")
        adapter = get_adapter(account)

        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)

        orders = adapter.get_orders(start_date=start_date, end_date=end_date)

        logger.info(f"MercadoLibre订单同步完成: 获取{len(orders)}个订单")
        return {"status": "success", "count": len(orders), "orders": orders}

    except Exception as e:
        logger.error(f"同步MercadoLibre订单失败: {e}")
        return {"status": "failed", "error": str(e)}
