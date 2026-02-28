"""
采购同步服务

负责采购订单与电商平台的集成，包括：
- 采购订单关联平台商品
- 采购商品同步到平台
- 采购状态同步到平台
- 采购单自动补货提醒
"""

import logging

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from inventory.models import InventoryStock
from purchase.models import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderItemPlatformMap,
    PurchaseSyncQueue,
)

logger = logging.getLogger(__name__)


class PurchaseSyncService:
    """采购同步服务"""

    def __init__(self):
        pass

    def link_purchase_order_to_platform(
        self,
        purchase_order_id: int,
        platform_id: int,
        platform_account_id: int,
        mappings: list,
    ) -> dict:
        """关联采购订单商品到平台商品

        Args:
            purchase_order_id: 采购订单ID
            platform_id: 平台ID
            platform_account_id: 平台账号ID
            mappings: 商品映射列表，格式：
                [
                    {
                        'order_item_id': 1,
                        'platform_product_id': '123456',
                        'platform_sku': 'SKU123'
                    },
                    ...
                ]

        Returns:
            dict: {
                'total': 总映射数,
                'success': 成功映射数,
                'failed': 失败映射数,
                'errors': 错误列表
            }
        """
        from core.models import Platform
        from ecomm_sync.models import PlatformAccount

        # 获取采购订单
        try:
            purchase_order = PurchaseOrder.objects.get(id=purchase_order_id)
        except PurchaseOrder.DoesNotExist:
            raise ValueError(f"采购订单不存在: {purchase_order_id}")

        # 获取平台和平台账号
        try:
            platform = Platform.objects.get(id=platform_id)
        except Platform.DoesNotExist:
            raise ValueError(f"平台不存在: {platform_id}")

        try:
            platform_account = PlatformAccount.objects.get(id=platform_account_id)
        except PlatformAccount.DoesNotExist:
            raise ValueError(f"平台账号不存在: {platform_account_id}")

        # 验证账号是否属于该平台
        if platform_account.platform != platform:
            raise ValueError("平台账号不属于指定平台")

        total = len(mappings)
        success = 0
        failed = 0
        errors = []

        # 创建映射关系
        with transaction.atomic():
            for mapping in mappings:
                try:
                    order_item = purchase_order.items.get(id=mapping["order_item_id"])
                    if not order_item:
                        errors.append(f"采购订单商品不存在: {mapping['order_item_id']}")
                        failed += 1
                        continue

                    # 检查是否已存在映射
                    existing = PurchaseOrderItemPlatformMap.objects.filter(
                        purchase_order_item=order_item,
                        platform=platform,
                        platform_account=platform_account,
                    ).first()

                    if existing:
                        # 更新现有映射
                        existing.platform_product_id = mapping["platform_product_id"]
                        existing.platform_sku = mapping.get("platform_sku", "")
                        existing.save()
                    else:
                        # 创建新映射
                        PurchaseOrderItemPlatformMap.objects.create(
                            purchase_order_item=order_item,
                            platform=platform,
                            platform_account=platform_account,
                            platform_product_id=mapping["platform_product_id"],
                            platform_sku=mapping.get("platform_sku", ""),
                        )

                    success += 1

                except Exception as e:
                    errors.append(f"映射商品 {mapping.get('order_item_id')} 失败: {str(e)}")
                    failed += 1

        return {"total": total, "success": success, "failed": failed, "errors": errors}

    def sync_purchase_order_to_platform(self, purchase_order_id: int) -> dict:
        """同步采购订单到平台

        Args:
            purchase_order_id: 采购订单ID

        Returns:
            dict: {
                'order_item_count': 订单商品总数,
                'synced_count': 已同步数量,
                'failed_count': 失败数量,
                'pending_count': 待同步数量,
                'errors': 错误列表
            }
        """
        from ecomm_sync.adapters import get_adapter as get_platform_adapter

        # 获取采购订单
        try:
            purchase_order = PurchaseOrder.objects.get(id=purchase_order_id)
        except PurchaseOrder.DoesNotExist:
            raise ValueError(f"采购订单不存在: {purchase_order_id}")

        if not purchase_order.sync_to_platform:
            return {
                "order_item_count": 0,
                "synced_count": 0,
                "failed_count": 0,
                "pending_count": 0,
                "errors": ["采购订单未启用平台同步"],
            }

        # 获取需要同步的映射
        platform_maps = PurchaseOrderItemPlatformMap.objects.filter(
            purchase_order_item__purchase_order=purchase_order,
            sync_enabled=True,
            sync_status__in=["pending", "failed"],
        )

        total = platform_maps.count()
        synced = 0
        failed = 0
        errors = []

        for platform_map in platform_maps:
            try:
                # 获取平台适配器
                adapter = get_platform_adapter(platform_map.platform_account)

                # 构建同步数据
                product_data = self._build_sync_data(platform_map.purchase_order_item)

                # 调用平台适配器更新商品
                adapter.update_product(platform_map.platform_product_id, product_data)

                # 更新映射状态
                platform_map.sync_status = "synced"
                platform_map.last_synced_at = timezone.now()
                platform_map.save()

                synced += 1

            except Exception as e:
                platform_map.sync_status = "failed"
                platform_map.sync_error = str(e)
                platform_map.save()

                failed += 1
                errors.append(f"同步商品 {platform_map.purchase_order_item.id} 失败: {str(e)}")

        # 更新采购订单的同步状态
        if synced > 0:
            purchase_order.platform_sync_status = "synced"
            purchase_order.last_synced_at = timezone.now()

        return {
            "order_item_count": total,
            "synced_count": synced,
            "failed_count": failed,
            "pending_count": total - synced - failed,
            "errors": errors,
        }

    def sync_purchase_status_to_platform(self, purchase_order_id: int) -> dict:
        """同步采购状态到平台

        Args:
            purchase_order_id: 采购订单ID

        Returns:
            dict: 同步结果
        """

        # 获取采购订单
        try:
            purchase_order = PurchaseOrder.objects.get(id=purchase_order_id)
        except PurchaseOrder.DoesNotExist:
            raise ValueError(f"采购订单不存在: {purchase_order_id}")

        if not purchase_order.platform or not purchase_order.platform_account:
            return {"status": "failed", "error": "采购订单未关联平台账号"}

        # 获取平台适配器
        try:
            adapter = get_adapter(purchase_order.platform_account)
        except Exception as e:
            return {"status": "failed", "error": f"获取平台适配器失败: {e}"}

        # 映射采购状态到平台状态
        platform_status = self._map_purchase_status_to_platform(purchase_order.status)

        # 更新所有平台商品的状态
        platform_maps = PurchaseOrderItemPlatformMap.objects.filter(
            purchase_order_item__purchase_order=purchase_order,
            platform=purchase_order.platform,
            sync_enabled=True,
        )

        updated = 0
        failed = 0
        errors = []

        for platform_map in platform_maps:
            try:
                # 调用平台适配器更新商品状态
                adapter.update_product_status(platform_map.platform_product_id, platform_status)
                updated += 1
            except Exception as e:
                failed += 1
                errors.append(f"更新商品 {platform_map.platform_product_id} 状态失败: {str(e)}")

        return {
            "status": "success",
            "updated_count": updated,
            "failed_count": failed,
            "errors": errors,
        }

    def process_purchase_sync_queue(self, limit: int = 100) -> dict:
        """处理采购同步队列

        Args:
            limit: 处理数量限制

        Returns:
            dict: {
                'processed': 处理数量,
                'success_count': 成功数量,
                'failed_count': 失败数量,
                'errors': 错误列表
            }
        """

        # 获取待处理的同步任务
        sync_queues = PurchaseSyncQueue.objects.filter(status="pending")[:limit]

        processed = 0
        success_count = 0
        failed_count = 0
        errors = []

        for sync_queue in sync_queues:
            try:
                # 更新状态为处理中
                sync_queue.status = "processing"
                sync_queue.processed_at = timezone.now()
                sync_queue.save()

                # 获取平台适配器
                adapter = get_adapter(sync_queue.platform_account)

                # 根据同步类型执行操作
                if sync_queue.sync_type == "add":
                    result = adapter.create_product(sync_queue.sync_data)
                elif sync_queue.sync_type == "update":
                    product_id = sync_queue.sync_data.get("platform_product_id")
                    product_data = sync_queue.sync_data.get("product_data")
                    result = adapter.update_product(product_id, product_data)
                elif sync_queue.sync_type == "delete":
                    product_id = sync_queue.sync_data.get("platform_product_id")
                    result = adapter.delete_product(product_id)
                else:
                    raise ValueError(f"不支持的同步类型: {sync_queue.sync_type}")

                # 更新状态为成功
                sync_queue.status = "success"
                sync_queue.completed_at = timezone.now()
                sync_queue.save()

                success_count += 1

            except Exception as e:
                # 更新状态为失败
                sync_queue.status = "failed"
                sync_queue.error_message = str(e)
                sync_queue.retry_count += 1

                # 检查是否达到最大重试次数
                if sync_queue.retry_count >= sync_queue.max_retries:
                    sync_queue.save()
                else:
                    # 重置为pending，下次继续重试
                    sync_queue.status = "pending"
                    sync_queue.save()

                failed_count += 1
                errors.append(f"任务 {sync_queue.id} 处理失败: {str(e)}")

        return {
            "processed": processed,
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors,
        }

    def auto_restock_alert(self) -> list:
        """自动补货提醒

        Returns:
            list: 补货提醒列表
        """
        alerts = []

        # 获取库存不足的商品
        low_stock_stocks = InventoryStock.objects.filter(
            quantity__lte=F("min_quantity")
        ).select_related("product")

        for stock in low_stock_stocks:
            # 检查是否有进行中的采购订单
            has_pending_purchase = PurchaseOrderItem.objects.filter(
                product=stock.product,
                purchase_order__status__in=[
                    "draft",
                    "approved",
                    "partial_received",
                    "fully_received",
                ],
            ).exists()

            if not has_pending_purchase:
                # 计算建议采购数量
                restock_quantity = stock.max_quantity - stock.quantity

                alerts.append(
                    {
                        "product": stock.product,
                        "current_quantity": stock.quantity,
                        "min_quantity": stock.min_quantity,
                        "max_quantity": stock.max_quantity,
                        "restock_quantity": restock_quantity,
                        "product_code": stock.product.code if stock.product else "",
                        "product_name": stock.product.name if stock.product else "",
                    }
                )

        logger.info(f"生成了 {len(alerts)} 个补货提醒")
        return alerts

    def _build_sync_data(self, order_item: PurchaseOrderItem) -> dict:
        """构建同步数据

        Args:
            order_item: 采购订单商品

        Returns:
            dict: 同步数据
        """
        return {
            "platform_product_id": (
                order_item.platform_maps.first().platform_product_id
                if order_item.platform_maps.exists()
                else ""
            ),
            "product_data": {
                "name": order_item.product.name,
                "sku": order_item.product.code,
                "description": order_item.product.description or "",
                "price": float(order_item.unit_price),
                "quantity": int(order_item.received_quantity),
                "status": "active" if order_item.received_quantity > 0 else "draft",
                "images": self._get_product_images(order_item.product),
                "attributes": self._get_product_attributes(order_item.product),
            },
        }

    def _get_product_images(self, product) -> list:
        """获取产品图片

        Args:
            product: 产品对象

        Returns:
            list: 图片URL列表
        """
        images = []
        if product and hasattr(product, "images"):
            images = [image.image_url for image in product.images.all()[:5]]  # 最多5张图片
        return images

    def _get_product_attributes(self, product) -> dict:
        """获取产品属性

        Args:
            product: 产品对象

        Returns:
            dict: 产品属性
        """
        attributes = {}

        if product:
            # 基本信息
            attributes["brand"] = product.brand.name if product.brand else ""
            attributes["category"] = product.category.name if product.category else ""
            attributes["weight"] = float(product.weight) if product.weight else 0

            # 规格信息
            attributes["specifications"] = product.specifications or ""

        return attributes

    def _map_purchase_status_to_platform(self, purchase_status: str) -> str:
        """映射采购状态到平台状态

        Args:
            purchase_status: 采购状态

        Returns:
            str: 平台状态
        """
        status_map = {
            "draft": "draft",
            "approved": "active",
            "partial_received": "active",
            "fully_received": "active",
            "invoiced": "sold",
            "paid": "sold",
            "cancelled": "deleted",
        }

        return status_map.get(purchase_status, "draft")
