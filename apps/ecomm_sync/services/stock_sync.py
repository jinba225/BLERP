import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class StockSyncService:
    """库存同步服务"""

    def sync_to_platforms(self, sku: str) -> dict:
        """同步库存到所有平台

        Args:
            sku: SKU代码

        Returns:
            同步结果
        """
        from inventory.models import ProductStock
        from ecomm_sync.models import ProductListing
        from ecomm_sync.adapters import get_adapter

        stock = ProductStock.objects.filter(product__code=sku).first()
        if not stock:
            return {"success": False, "error": "库存不存在"}

        total_stock = stock.qty_in_stock

        listings = ProductListing.objects.filter(product__code=sku, sync_enabled=True)

        results = {"total": listings.count(), "success": 0, "failed": 0}

        for listing in listings:
            try:
                adapter = get_adapter(listing.account)

                success = adapter.update_inventory(sku=listing.platform_sku, quantity=total_stock)

                if success:
                    results["success"] += 1
                    listing.quantity = total_stock
                    listing.last_synced_at = timezone.now()
                    listing.sync_error = ""
                    listing.save()

                    logger.info(f"库存同步成功: {sku} -> {listing.platform.name}, 数量: {total_stock}")
                else:
                    results["failed"] += 1
                    listing.sync_error = "更新失败"
                    listing.save()

            except Exception as e:
                logger.error(f"库存同步失败: {sku} -> {listing.platform.name}, 错误: {e}")
                results["failed"] += 1
                listing.sync_error = str(e)
                listing.save()

        return results

    def pull_from_platforms(self, platform_id: int) -> dict:
        """从平台拉取库存

        Args:
            platform_id: 平台ID

        Returns:
            同步结果
        """
        from ecomm_sync.models import PlatformAccount, StockSyncQueue
        from ecomm_sync.adapters import get_adapter

        from django.utils import timezone

        platform = PlatformAccount.objects.get(id=platform_id).platform
        accounts = PlatformAccount.objects.filter(platform=platform, is_active=True)

        results = {"total": 0, "success": 0, "failed": 0}

        for account in accounts:
            try:
                adapter = get_adapter(account)
                products = adapter.get_products()

                for product_data in products:
                    sku = product_data["sku"]
                    quantity = product_data["stock"]

                    queue = StockSyncQueue(
                        product__code=sku,
                        platform=platform,
                        account=account,
                        sync_type="pull",
                        quantity=quantity,
                        status="pending",
                    )
                    queue.save()

                    results["total"] += 1

            except Exception as e:
                logger.error(f"从平台拉取库存失败: {e}")
                results["failed"] += 1

        return results

    def process_queue(self, limit: int = 100) -> dict:
        """处理库存同步队列

        Args:
            limit: 处理数量限制

        Returns:
            处理结果
        """
        from ecomm_sync.models import StockSyncQueue, ProductListing
        from ecomm_sync.adapters import get_adapter
        from inventory.models import ProductStock

        queues = (
            StockSyncQueue.objects.filter(status="pending")
            .select_for_update()
            .order_by("created_at")[:limit]
        )

        results = {"total": queues.count(), "success": 0, "failed": 0}

        for queue in queues:
            try:
                queue.status = "processing"
                queue.save()

                if queue.sync_type == "push":
                    stock = ProductStock.objects.filter(product__code=queue.product.code).first()
                    if not stock:
                        queue.status = "failed"
                        queue.error_message = "库存不存在"
                        queue.save()
                        continue

                    listings = ProductListing.objects.filter(
                        product=queue.product, platform=queue.platform, sync_enabled=True
                    )

                    for listing in listings:
                        adapter = get_adapter(listing.account)
                        success = adapter.update_inventory(
                            sku=listing.platform_sku, quantity=queue.quantity
                        )

                        if success:
                            listing.quantity = queue.quantity
                            listing.last_synced_at = timezone.now()
                            listing.save()
                            results["success"] += 1
                        else:
                            results["failed"] += 1

                elif queue.sync_type == "pull":
                    stock = ProductStock.objects.filter(product__code=queue.product.code).first()
                    if stock:
                        stock.qty_in_stock = queue.quantity
                        stock.save()
                        results["success"] += 1
                    else:
                        results["failed"] += 1

                queue.status = "success"
                queue.processed_at = timezone.now()
                queue.save()

            except Exception as e:
                logger.error(f"处理库存同步队列失败: {queue.id}, 错误: {e}")
                queue.status = "failed"
                queue.error_message = str(e)
                queue.retry_count += 1
                queue.save()

                if queue.retry_count >= queue.max_retries:
                    results["failed"] += 1

        return results

    def sync_product_stock(self, product_id: int) -> dict:
        """同步单个产品库存到所有平台

        Args:
            product_id: 产品ID

        Returns:
            同步结果
        """
        from products.models import Product

        try:
            product = Product.objects.get(id=product_id)
            return self.sync_to_platforms(product.code)
        except Product.DoesNotExist:
            return {"success": False, "error": "产品不存在"}
