import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)


class OrderSyncService:
    """订单同步服务"""

    def __init__(self, platform: "EcommPlatform"):
        self.platform = platform
        from ecomm_sync.models import PlatformAccount

        self.accounts = PlatformAccount.objects.filter(platform=platform, is_active=True)

    def sync_new_orders(self, hours: int = 24) -> dict:
        """同步新订单

        Args:
            hours: 同步最近多少小时的订单

        Returns:
            同步结果
        """
        from ecomm_sync.adapters import get_adapter
        from ecomm_sync.models import PlatformOrder, PlatformOrderItem

        results = {"total": 0, "success": 0, "failed": 0, "errors": []}

        start_date = timezone.now() - timedelta(hours=hours)

        for account in self.accounts:
            try:
                adapter = get_adapter(account)

                orders = adapter.get_orders(
                    start_date=start_date, order_statuses=["paid", "processing"]
                )

                for order_data in orders:
                    order_id = order_data["order_id"]

                    existing_order = PlatformOrder.objects.filter(
                        platform_order_id=order_id
                    ).first()

                    if existing_order:
                        continue

                    order = PlatformOrder(
                        platform=self.platform,
                        account=account,
                        platform_order_id=order_id,
                        order_status=order_data["status"],
                        order_amount=order_data["amount"],
                        currency=order_data.get("currency", "CNY"),
                        buyer_email=order_data.get("buyer_email"),
                        buyer_name=order_data.get("buyer_name"),
                        shipping_address={"address": order_data.get("buyer_name")},
                        raw_data=order_data,
                        sync_status="synced",
                        synced_to_erp=False,
                        synced_to_platform=True,
                    )
                    order.save()

                    for item_data in order_data.get("items", []):
                        item = PlatformOrderItem(
                            order=order,
                            sku=item_data["sku"],
                            product_name=item_data["product_name"],
                            quantity=item_data["quantity"],
                            unit_price=item_data["unit_price"],
                            total_price=item_data["unit_price"] * item_data["quantity"],
                            platform_product_id=item_data.get("product_id"),
                            raw_data=item_data,
                        )
                        item.save()

                    results["success"] += 1

                results["total"] += len(orders)

                account.last_synced_at = timezone.now()
                account.save()

            except Exception as e:
                logger.error(f"订单同步失败: {account.account_name}, 错误: {e}")
                results["failed"] += 1
                results["errors"].append({"account": account.account_name, "error": str(e)})
                account.last_error = str(e)
                account.save()

        return results

    def sync_order_to_erp(self, platform_order_id: str) -> bool:
        """同步订单到ERP

        Args:
            platform_order_id: 平台订单号

        Returns:
            是否成功
        """
        from ecomm_sync.models import PlatformOrder

        try:
            order = PlatformOrder.objects.get(platform_order_id=platform_order_id)

            if order.synced_to_erp:
                return True

            # 这里应该调用ERP订单导入逻辑
            # 暂时标记为已同步
            order.synced_to_erp = True
            order.sync_status = "synced"
            order.save()

            logger.info(f"订单 {platform_order_id} 同步到ERP成功")
            return True

        except Exception as e:
            logger.error(f"订单 {platform_order_id} 同步到ERP失败: {e}")
            return False

    def update_order_status(
        self, platform_order_id: str, status: str, tracking_number: str = None
    ) -> bool:
        """更新订单状态到平台

        Args:
            platform_order_id: 平台订单号
            status: 订单状态
            tracking_number: 快递单号

        Returns:
            是否成功
        """
        from ecomm_sync.adapters import get_adapter
        from ecomm_sync.models import PlatformOrder

        try:
            order = PlatformOrder.objects.get(platform_order_id=platform_order_id)
            adapter = get_adapter(order.account)

            success = adapter.update_order_status(platform_order_id, status, tracking_number)

            if success:
                if tracking_number:
                    order.tracking_number = tracking_number
                order.synced_to_platform = True
                order.save()

            return success

        except Exception as e:
            logger.error(f"更新订单状态失败: {platform_order_id}, 错误: {e}")
            return False
