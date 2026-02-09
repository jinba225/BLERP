import asyncio
import logging
from typing import Dict

from django.utils import timezone
from ecomm_sync.models import EcommPlatform, EcommProduct, ProductChangeLog, SyncLog

from .scrapers.base import BaseScraper
from .scrapers.hybrid import HybridScraper
from .transformers.product import ProductTransformer
from .woocommerce.batch_sync import WooCommerceBatchSync

logger = logging.getLogger(__name__)


class ChangeDetector:
    """商品变更检测器"""

    def __init__(self, platform: EcommPlatform):
        """
        初始化变更检测器

        Args:
            platform: 电商平台
        """
        self.platform = platform

    def detect_changes(self, scrape_result: Dict, ecomm_product: EcommProduct) -> list:
        """
        检测商品变更

        Args:
            scrape_result: 最新采集数据
            ecomm_product: 电商产品实例

        Returns:
            变更日志列表
        """
        changes = []
        product = ecomm_product.product

        if not product:
            return changes

        old_price = product.selling_price
        new_price = float(str(scrape_result.get("price", 0)))

        if abs(new_price - old_price) > 0.1:
            changes.append(
                ProductChangeLog(
                    ecomm_product=ecomm_product,
                    change_type="price",
                    old_value={"price": str(old_price)},
                    new_value={"price": str(new_price)},
                )
            )
            logger.info(f"价格变更: {product.code} ¥{old_price} -> ¥{new_price}")

        old_stock = ecomm_product.min_stock or 0
        new_stock = int(scrape_result.get("stock", 0))

        if old_stock != new_stock:
            changes.append(
                ProductChangeLog(
                    ecomm_product=ecomm_product,
                    change_type="stock",
                    old_value={"stock": old_stock},
                    new_value={"stock": new_stock},
                )
            )
            logger.info(f"库存变更: {product.code} {old_stock} -> {new_stock}")

        old_status = product.status
        new_status = self._map_status(scrape_result.get("status"))

        if old_status != new_status:
            changes.append(
                ProductChangeLog(
                    ecomm_product=ecomm_product,
                    change_type="status",
                    old_value={"status": old_status},
                    new_value={"status": new_status},
                )
            )
            logger.info(f"状态变更: {product.code} {old_status} -> {new_status}")

        old_desc = product.description
        new_desc = scrape_result.get("description", "")

        if old_desc != new_desc and len(new_desc) > 0:
            changes.append(
                ProductChangeLog(
                    ecomm_product=ecomm_product,
                    change_type="detail",
                    old_value={"description": old_desc},
                    new_value={"description": new_desc},
                )
            )
            logger.info(f"详情变更: {product.code}")

        return changes

    def _map_status(self, status_str: str) -> str:
        """
        映射状态

        Args:
            status_str: 平台状态字符串

        Returns:
            ERP状态
        """
        if not status_str:
            return "inactive"

        status_str = str(status_str).strip().lower()

        if "在售" in status_str or "有货" in status_str:
            return "active"
        elif "下架" in status_str or "缺货" in status_str:
            return "inactive"
        else:
            return "inactive"


class SyncManager:
    """同步管理器"""

    def __init__(self):
        """初始化同步管理器"""
        self.woo_syncer = WooCommerceBatchSync()

    async def sync_platform_products(
        self, platform: EcommPlatform, strategy_type: str = "incremental", limit: int = 100
    ) -> dict:
        """
        同步平台产品

        Args:
            platform: 电商平台
            strategy_type: 策略类型
            limit: 限制数量

        Returns:
            同步结果
        """
        logger.info(f"开始同步: {platform.name}, 策略: {strategy_type}")

        sync_log = SyncLog.objects.create(
            log_type="incremental" if strategy_type == "incremental" else "full_sync",
            platform=platform,
            status="running",
        )

        start_time = timezone.now()

        try:
            scraper = HybridScraper(platform)

            if strategy_type == "incremental":
                ecomm_products = EcommProduct.objects.filter(
                    platform=platform, sync_status="synced", product__isnull=False
                )[:limit]
            else:
                ecomm_products = EcommProduct.objects.filter(
                    platform=platform, product__isnull=False
                )[:limit]

            results = {"total": ecomm_products.count(), "succeeded": 0, "failed": 0, "errors": []}

            for ecomm_product in ecomm_products:
                try:
                    latest_data = await scraper.scrape_product(ecomm_product.external_id)

                    detector = ChangeDetector(platform)
                    changes = detector.detect_changes(latest_data, ecomm_product)

                    if changes:
                        ProductChangeLog.objects.bulk_create(changes)
                        ecomm_product.raw_data = latest_data
                        ecomm_product.last_scraped_at = timezone.now()
                        ecomm_product.save()

                        results["succeeded"] += 1
                    else:
                        results["succeeded"] += 1

                except Exception as e:
                    logger.error(f"同步失败: {ecomm_product.external_id}, 错误: {e}")
                    results["failed"] += 1
                    results["errors"].append(
                        {"external_id": ecomm_product.external_id, "error": str(e)}
                    )

            execution_time = (timezone.now() - start_time).total_seconds()

            SyncLog.update_sync_log(
                sync_log=sync_log,
                status="success",
                records_processed=results["total"],
                records_succeeded=results["succeeded"],
                records_failed=results["failed"],
                execution_time=execution_time,
            )

            logger.info(
                f'同步完成: 成功 {results["succeeded"]}/{results["total"]}, '
                f'失败 {results["failed"]}, 耗时 {execution_time:.1f}秒'
            )

            return results

        except Exception as e:
            execution_time = (timezone.now() - start_time).total_seconds()

            SyncLog.update_sync_log(
                sync_log=sync_log,
                status="failed",
                records_processed=0,
                records_succeeded=0,
                records_failed=0,
                error_message=str(e),
                execution_time=execution_time,
            )

            logger.error(f"同步任务失败: {e}")
            raise

    async def sync_price_changes(self, platform: EcommPlatform) -> dict:
        """
        同步价格变更

        Args:
            platform: 电商平台

        Returns:
            同步结果
        """
        logger.info(f"开始价格监控: {platform.name}")

        sync_log = SyncLog.objects.create(log_type="sync", platform=platform, status="running")

        start_time = timezone.now()

        try:
            scraper = HybridScraper(platform)
            ecomm_products = EcommProduct.objects.filter(
                platform=platform, sync_status="synced", product__isnull=False
            )[:200]

            changes_detected = 0

            for ecomm_product in ecomm_products:
                try:
                    latest_data = await scraper.scrape_product(ecomm_product.external_id)

                    detector = ChangeDetector(platform)
                    changes = detector.detect_changes(latest_data, ecomm_product)

                    price_changes = [c for c in changes if c.change_type == "price"]

                    if price_changes:
                        changes_detected += 1
                        ProductChangeLog.objects.bulk_create(price_changes)

                        ecomm_product.raw_data = latest_data
                        ecomm_product.product.selling_price = float(latest_data.get("price", 0))
                        ecomm_product.product.save()
                        ecomm_product.last_scraped_at = timezone.now()
                        ecomm_product.save()

                except Exception as e:
                    logger.error(f"价格检测失败: {e}")
                    continue

            execution_time = (timezone.now() - start_time).total_seconds()

            SyncLog.update_sync_log(
                sync_log=sync_log,
                status="success",
                records_processed=ecomm_products.count(),
                records_succeeded=changes_detected,
                records_failed=ecomm_products.count() - changes_detected,
                execution_time=execution_time,
            )

            logger.info(f"价格监控完成: 检测到 {changes_detected} 个价格变化, " f"耗时 {execution_time:.1f}秒")

            return {"total": ecomm_products.count(), "price_changes": changes_detected}

        except Exception as e:
            execution_time = (timezone.now() - start_time).total_seconds()

            SyncLog.update_sync_log(
                sync_log=sync_log,
                status="failed",
                error_message=str(e),
                execution_time=execution_time,
            )

            logger.error(f"价格监控任务失败: {e}")
            raise
