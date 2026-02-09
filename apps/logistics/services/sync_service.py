"""
物流同步服务

负责物流订单的创建、追踪、状态同步等核心功能
"""
import logging
from typing import Any, Dict, List

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from ecomm_sync.adapters import get_adapter as get_platform_adapter
from logistics.adapters.factory import LogisticsAdapterFactory
from logistics.models import LogisticsCompany, ShippingOrder, TrackingInfo

logger = logging.getLogger(__name__)


class LogisticsSyncService:
    """物流同步服务"""

    def __init__(self):
        self.adapter_cache = {}

    def create_shipping_order(
        self, platform_order_id: int, logistics_company_id: int
    ) -> ShippingOrder:
        """创建物流订单

        Args:
            platform_order_id: 平台订单ID
            logistics_company_id: 物流公司ID

        Returns:
            ShippingOrder: 创建的物流订单

        Raises:
            ValueError: 参数错误
            Exception: 创建失败
        """
        from ecomm_sync.models import PlatformOrder

        # 获取平台订单
        try:
            platform_order = PlatformOrder.objects.get(id=platform_order_id)
        except PlatformOrder.DoesNotExist:
            raise ValueError(f"平台订单不存在: {platform_order_id}")

        # 获取物流公司
        try:
            logistics_company = LogisticsCompany.objects.get(id=logistics_company_id)
        except LogisticsCompany.DoesNotExist:
            raise ValueError(f"物流公司不存在: {logistics_company_id}")

        # 获取物流适配器
        try:
            adapter = LogisticsAdapterFactory.get_adapter(logistics_company)
        except ValueError as e:
            raise ValueError(f"获取物流适配器失败: {e}")

        # 创建物流订单记录（待发货状态）
        shipping_order = ShippingOrder.objects.create(
            platform_order=platform_order,
            logistics_company=logistics_company,
            shipping_status="pending",
        )

        # 调用适配器创建运单
        try:
            tracking_number = adapter.create_waybill(shipping_order)

            # 更新物流订单信息
            shipping_order.tracking_number = tracking_number
            shipping_order.shipping_status = "shipped"
            shipping_order.shipped_at = timezone.now()
            shipping_order.save()

            # 同步运单号到平台
            self._sync_tracking_to_platform(platform_order, tracking_number)

            logger.info(f"创建物流订单成功: {tracking_number}")

        except Exception as e:
            shipping_order.shipping_status = "failed"
            shipping_order.note = f"创建运单失败: {str(e)}"
            shipping_order.save()

            logger.error(f"创建物流订单失败: {e}")
            raise

        return shipping_order

    def track_shipping(self, shipping_order_id: int) -> ShippingOrder:
        """追踪物流

        Args:
            shipping_order_id: 物流订单ID

        Returns:
            ShippingOrder: 更新后的物流订单

        Raises:
            ValueError: 物流订单不存在
            Exception: 追踪失败
        """
        # 获取物流订单
        try:
            shipping_order = ShippingOrder.objects.get(id=shipping_order_id)
        except ShippingOrder.DoesNotExist:
            raise ValueError(f"物流订单不存在: {shipping_order_id}")

        # 获取物流适配器
        adapter = LogisticsAdapterFactory.get_adapter(shipping_order.logistics_company)

        # 调用适配器查询物流轨迹
        try:
            routes = adapter.track_shipping(shipping_order.tracking_number)

            # 保存轨迹信息
            for route in routes:
                track_time = route.get("track_time")
                track_status = route.get("track_status")
                track_location = route.get("track_location", "")
                track_description = route.get("track_description", "")
                operator = route.get("operator", "")
                raw_data = route.get("raw_data", {})

                # 避免重复保存
                TrackingInfo.objects.get_or_create(
                    shipping_order=shipping_order,
                    track_time=track_time,
                    defaults={
                        "track_status": track_status,
                        "track_location": track_location,
                        "track_description": track_description,
                        "operator": operator,
                        "raw_data": raw_data,
                    },
                )

            # 更新物流订单状态
            if routes:
                latest_route = routes[-1]
                latest_status = latest_route.get("track_status")

                # 映射物流状态
                new_status = self._map_logistics_status(latest_status)

                if new_status != shipping_order.shipping_status:
                    shipping_order.shipping_status = new_status

                    # 如果已签收，更新签收时间
                    if new_status == "delivered":
                        shipping_order.delivered_at = latest_route.get("track_time")

                    shipping_order.last_track_at = timezone.now()
                    shipping_order.save()

                    # 同步状态到平台
                    self._sync_status_to_platform(shipping_order, new_status)

        except Exception as e:
            logger.error(f"追踪物流失败: {shipping_order.tracking_number}, 错误: {e}")
            raise

        return shipping_order

    def batch_track_shipping(self, limit: int = 100) -> int:
        """批量追踪物流

        Args:
            limit: 处理数量限制

        Returns:
            int: 处理的物流订单数量
        """
        # 获取需要追踪的物流订单
        # 条件：已发货、运输中、派送中，且1小时内未查询
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)

        shipping_orders = ShippingOrder.objects.filter(
            shipping_status__in=["shipped", "in_transit", "out_for_delivery"],
            last_track_at__lt=one_hour_ago,
        )[:limit]

        count = 0
        for shipping_order in shipping_orders:
            try:
                self.track_shipping(shipping_order.id)
                count += 1
            except Exception as e:
                logger.error(f"批量追踪物流失败: {shipping_order.id}, 错误: {e}")
                continue

        return count

    def print_waybill(self, shipping_order_id: int) -> str:
        """打印面单

        Args:
            shipping_order_id: 物流订单ID

        Returns:
            str: 面单文件路径或URL

        Raises:
            ValueError: 物流订单不存在
            Exception: 打印失败
        """
        # 获取物流订单
        try:
            shipping_order = ShippingOrder.objects.get(id=shipping_order_id)
        except ShippingOrder.DoesNotExist:
            raise ValueError(f"物流订单不存在: {shipping_order_id}")

        # 获取物流适配器
        adapter = LogisticsAdapterFactory.get_adapter(shipping_order.logistics_company)

        # 调用适配器打印面单
        waybill_url = adapter.print_waybill(shipping_order)

        return waybill_url

    def cancel_waybill(self, shipping_order_id: int) -> bool:
        """取消运单

        Args:
            shipping_order_id: 物流订单ID

        Returns:
            bool: 取消成功返回True，否则返回False

        Raises:
            ValueError: 物流订单不存在
            Exception: 取消失败
        """
        # 获取物流订单
        try:
            shipping_order = ShippingOrder.objects.get(id=shipping_order_id)
        except ShippingOrder.DoesNotExist:
            raise ValueError(f"物流订单不存在: {shipping_order_id}")

        # 获取物流适配器
        adapter = LogisticsAdapterFactory.get_adapter(shipping_order.logistics_company)

        # 调用适配器取消运单
        result = adapter.cancel_waybill(shipping_order.tracking_number)

        if result:
            # 更新物流订单状态
            shipping_order.shipping_status = "cancelled"
            shipping_order.save()

        return result

    def get_shipping_statistics(self, start_date, end_date) -> Dict[str, Any]:
        """获取物流统计数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            Dict: 统计数据
        """
        from decimal import Decimal

        # 统计总订单数
        total_orders = ShippingOrder.objects.filter(
            created_at__range=[start_date, end_date]
        ).count()

        # 统计各状态订单数
        status_counts = (
            ShippingOrder.objects.filter(created_at__range=[start_date, end_date])
            .values("shipping_status")
            .annotate(count=Count("id"))
            .order_by("shipping_status")
        )

        # 统计平均运输天数
        delivered_orders = ShippingOrder.objects.filter(
            shipping_status="delivered",
            shipped_at__isnull=False,
            delivered_at__isnull=False,
            created_at__range=[start_date, end_date],
        )

        avg_days = delivered_orders.annotate(
            days=Avg("delivered_at") - Avg("shipped_at")
        ).aggregate(avg=Avg("days"))["avg"]

        # 统计物流成本
        total_cost = ShippingOrder.objects.filter(
            created_at__range=[start_date, end_date]
        ).aggregate(total=Sum("shipping_cost"))["total"] or Decimal("0")

        # 统计各物流公司订单数
        company_counts = (
            ShippingOrder.objects.filter(created_at__range=[start_date, end_date])
            .values("logistics_company__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return {
            "total_orders": total_orders,
            "status_counts": {item["shipping_status"]: item["count"] for item in status_counts},
            "avg_days_in_transit": avg_days.days if avg_days else 0,
            "total_cost": float(total_cost),
            "company_counts": list(company_counts),
        }

    def _sync_tracking_to_platform(self, platform_order, tracking_number: str):
        """同步运单号到平台

        Args:
            platform_order: 平台订单对象
            tracking_number: 快递单号
        """
        try:
            # 获取平台适配器
            platform_adapter = get_platform_adapter(platform_order.account)

            # 更新平台订单的快递单号
            platform_order.tracking_number = tracking_number
            platform_order.synced_to_platform = True
            platform_order.save()

            logger.info(f"同步运单号到平台成功: {platform_order.platform_order_id} -> {tracking_number}")

        except Exception as e:
            logger.error(f"同步运单号到平台失败: {platform_order.platform_order_id}, 错误: {e}")

    def _sync_status_to_platform(self, shipping_order: ShippingOrder, status: str):
        """同步物流状态到平台

        Args:
            shipping_order: 物流订单对象
            status: 物流状态
        """
        try:
            platform_order = shipping_order.platform_order

            # 获取平台适配器
            platform_adapter = get_platform_adapter(platform_order.account)

            # 映射物流状态到平台状态
            platform_status = self._map_platform_status(status)

            # 更新平台订单状态
            platform_order.order_status = platform_status
            platform_order.save()

            logger.info(f"同步物流状态到平台成功: {platform_order.platform_order_id} -> {platform_status}")

        except Exception as e:
            logger.error(f"同步物流状态到平台失败: {shipping_order.tracking_number}, 错误: {e}")

    def _map_logistics_status(self, logistics_status: str) -> str:
        """映射物流状态到系统状态

        Args:
            logistics_status: 物流公司返回的状态

        Returns:
            str: 系统状态
        """
        status_map = {
            "已揽收": "shipped",
            "已发货": "shipped",
            "运输中": "in_transit",
            "派送中": "out_for_delivery",
            "已签收": "delivered",
            "已送达": "delivered",
            "配送失败": "failed",
            "已退货": "returned",
            "已取消": "cancelled",
        }

        return status_map.get(logistics_status, "in_transit")

    def _map_platform_status(self, logistics_status: str) -> str:
        """映射物流状态到平台订单状态

        Args:
            logistics_status: 物流状态

        Returns:
            str: 平台订单状态
        """
        status_map = {
            "shipped": "processing",
            "in_transit": "shipped",
            "out_for_delivery": "shipped",
            "delivered": "shipped",
            "failed": "cancelled",
            "returned": "cancelled",
            "cancelled": "cancelled",
        }

        return status_map.get(logistics_status, "processing")
