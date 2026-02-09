import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


class ListingService:
    """Listing管理服务"""

    def publish_listing(self, product: "Product", platforms: list) -> dict:
        """发布商品到多个平台

        Args:
            product: 产品实例
            platforms: 平台ID列表

        Returns:
            发布结果
        """
        from core.models import Platform, PlatformAccount, ProductListing
        from ecomm_sync.adapters import get_adapter
        from products.models import Product

        results = {"total": len(platforms), "success": 0, "failed": 0, "errors": []}

        for platform_id in platforms:
            try:
                platform = Platform.objects.get(id=platform_id)
                account = PlatformAccount.objects.filter(platform=platform, is_active=True).first()

                if not account:
                    results["failed"] += 1
                    results["errors"].append({"platform": platform.name, "error": "未找到启用的账号"})
                    continue

                adapter = get_adapter(account)

                product_data = self._transform_to_platform_format(product)

                result = adapter.create_product(product_data)

                if result and "product_id" in result:
                    listing = ProductListing(
                        product=product,
                        platform=platform,
                        account=account,
                        platform_product_id=result["product_id"],
                        platform_sku=product.code,
                        listing_title=product.name,
                        listing_status="onsale",
                        price=product.selling_price,
                        quantity=product.min_stock or 0,
                        sync_enabled=True,
                        auto_update_price=True,
                        auto_update_stock=True,
                    )
                    listing.save()

                    results["success"] += 1
                    logger.info(
                        f"商品 {product.code} 发布到 {platform.name} 成功，平台ID: {result['product_id']}"
                    )
                else:
                    results["failed"] += 1
                    results["errors"].append({"platform": platform.name, "error": "商品创建失败"})

            except Exception as e:
                logger.error(f"发布商品失败: {product.code} -> 平台{platform_id}, 错误: {e}")
                results["failed"] += 1
                results["errors"].append({"platform_id": platform_id, "error": str(e)})

        return results

    def update_listing_price(self, listing_id: int, new_price: float) -> bool:
        """更新Listing价格

        Args:
            listing_id: Listing ID
            new_price: 新价格

        Returns:
            是否成功
        """
        from ecomm_sync.adapters import get_adapter
        from ecomm_sync.models import ProductListing

        try:
            listing = ProductListing.objects.get(id=listing_id)
            adapter = get_adapter(listing.account)

            success = adapter.update_product(listing.platform_product_id, {"price": new_price})

            if success:
                listing.price = new_price
                listing.last_synced_at = timezone.now()
                listing.save()

                logger.info(f"Listing {listing_id} 价格更新成功: ¥{new_price}")
                return True

            return False

        except Exception as e:
            logger.error(f"Listing价格更新失败: {listing_id}, 错误: {e}")
            return False

    def update_listing_stock(self, listing_id: int, new_stock: int) -> bool:
        """更新Listing库存

        Args:
            listing_id: Listing ID
            new_stock: 新库存数量

        Returns:
            是否成功
        """
        from ecomm_sync.adapters import get_adapter
        from ecomm_sync.models import ProductListing

        try:
            listing = ProductListing.objects.get(id=listing_id)
            adapter = get_adapter(listing.account)

            success = adapter.update_inventory(listing.platform_sku, new_stock)

            if success:
                listing.quantity = new_stock
                listing.last_synced_at = timezone.now()
                listing.save()

                logger.info(f"Listing {listing_id} 库存更新成功: {new_stock}")
                return True

            return False

        except Exception as e:
            logger.error(f"Listing库存更新失败: {listing_id}, 错误: {e}")
            return False

    def delete_listing(self, listing_id: int) -> bool:
        """删除Listing

        Args:
            listing_id: Listing ID

        Returns:
            是否成功
        """
        from ecomm_sync.adapters import get_adapter
        from ecomm_sync.models import ProductListing

        try:
            listing = ProductListing.objects.get(id=listing_id)
            adapter = get_adapter(listing.account)

            success = adapter.delete_product(listing.platform_product_id)

            if success:
                listing.listing_status = "offshelf"
                listing.save()

                logger.info(f"Listing {listing_id} 已删除")
                return True

            return False

        except Exception as e:
            logger.error(f"Listing删除失败: {listing_id}, 错误: {e}")
            return False

    def sync_product_listings(self, product_id: int) -> dict:
        """同步产品所有Listing

        Args:
            product_id: 产品ID

        Returns:
            同步结果
        """
        from ecomm_sync.adapters import get_adapter
        from ecomm_sync.models import ProductListing
        from ecomm_sync.services.stock_sync import StockSyncService
        from products.models import Product

        try:
            product = Product.objects.get(id=product_id)
            listings = ProductListing.objects.filter(product=product, sync_enabled=True)

            results = {
                "total": listings.count(),
                "price_updated": 0,
                "stock_updated": 0,
                "failed": 0,
            }

            stock_service = StockSyncService()

            for listing in listings:
                try:
                    adapter = get_adapter(listing.account)

                    if listing.auto_update_price:
                        success = self.update_listing_price(listing.id, product.selling_price)
                        if success:
                            results["price_updated"] += 1

                    if listing.auto_update_stock:
                        from inventory.models import ProductStock

                        stock = ProductStock.objects.filter(product=product).first()
                        if stock:
                            success = adapter.update_inventory(
                                listing.platform_sku, stock.qty_in_stock
                            )
                            if success:
                                listing.quantity = stock.qty_in_stock
                                listing.last_synced_at = timezone.now()
                                listing.save()
                                results["stock_updated"] += 1

                except Exception as e:
                    logger.error(f"同步Listing失败: {listing.id}, 错误: {e}")
                    results["failed"] += 1
                    listing.sync_error = str(e)
                    listing.save()

            return results

        except Product.DoesNotExist:
            return {"success": False, "error": "产品不存在"}
        except Exception as e:
            logger.error(f"同步产品Listing失败: {product_id}, 错误: {e}")
            return {"success": False, "error": str(e)}

    def _transform_to_platform_format(self, product: "Product") -> dict:
        """转换为平台格式

        Args:
            product: 产品实例

        Returns:
            平台格式数据
        """
        from products.models import ProductImage

        images = ProductImage.objects.filter(product=product, is_primary=True)
        image_url = images.first().image.url if images.exists() else ""

        return {
            "name": product.name,
            "description": product.description or "",
            "sku": product.code,
            "price": float(product.selling_price),
            "stock": product.min_stock or 0,
            "category": "",
            "brand": "",
            "status": "onsale" if product.status == "active" else "offshelf",
            "images": [image_url] if image_url else [],
        }
