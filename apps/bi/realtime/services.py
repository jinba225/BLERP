"""
实时数据服务
"""
import logging
from datetime import date, datetime
from typing import Dict

from bi.models import SalesSummary
from core.models import Platform, Shop
from django.db.models import Avg, Coalesce, Count, Q, Sum
from django.utils import timezone
from ecomm_sync.models import PlatformOrder

from .models import Dashboard, RealtimeData

logger = logging.getLogger(__name__)


class RealtimeDataService:
    """实时数据服务"""

    def update_sales_realtime_data(
        self, platform_id: int, platform_account_id: int = None, limit: int = 100
    ) -> RealtimeData:
        """
        更新销售实时数据

        Args:
            platform_id: 平台ID
            platform_account_id: 平台账户ID（可选）
            limit: 数据条数限制

        Returns:
            RealtimeData: 实时数据对象
        """
        platform = Platform.objects.get(id=platform_id)

        # 获取今日销售数据
        today = date.today()
        start_date = today

        queryset = SalesSummary.objects.filter(
            platform=platform, report_date__gte=start_date, report_period="daily"
        )

        if platform_account_id:
            queryset = queryset.filter(platform_account_id=platform_account_id)

        # 汇聚数据
        sales_data = queryset.aggregate(
            total_orders=Count("id"),
            total_amount=Sum("total_amount"),
            total_quantity=Sum("total_quantity"),
            paid_orders=Count(
                "id", filter=Q(status="paid") | Q(status="shipped") | Q(status="delivered")
            ),
            cancelled_orders=Count("id", filter=Q(status="cancelled")),
            conversion_rate=Coalesce(Avg("conversion_rate"), 0) * 100,
        )

        # 获取平台名称
        platform_name = platform.name

        # 构建数据内容
        data = {
            "total_orders": sales_data["total_orders"],
            "total_amount": float(sales_data["total_amount"] or 0),
            "total_quantity": sales_data["total_quantity"] or 0,
            "paid_orders": sales_data["paid_orders"],
            "cancelled_orders": sales_data["cancelled_orders"],
            "conversion_rate": float(sales_data["conversion_rate"]),
            "platform_name": platform_name,
        }

        # 获取订单详情
        recent_orders = list(
            PlatformOrder.objects.filter(platform=platform, created_at__date=today).values(
                "order_id",
                "buyer_name",
                "buyer_email",
                "order_amount",
                "status",
                "created_at",
            )[:10]
        )

        data["recent_orders"] = recent_orders

        # 保存或更新实时数据
        realtime_data, created = RealtimeData.objects.update_or_create(
            platform=platform,
            data_type="sales",
            data=data,
            data_count=sales_data["total_orders"],
            last_updated_at=timezone.now(),
        )

        return realtime_data

    def update_inventory_realtime_data(self, shop_id: int, limit: int = 100) -> RealtimeData:
        """更新库存实时数据"""
        shop = Shop.objects.get(id=shop_id)
        platform = shop.platform if shop else None

        # 获取当前库存数据
        inventory_data = []

        # 从InventoryAnalysis获取数据
        from .models import InventoryAnalysis

        analysis_queryset = InventoryAnalysis.objects.filter(shop=shop).select_related("product")

        for item in analysis_queryset[:limit]:
            inventory_data.append(
                {
                    "product_id": item.product.id,
                    "product_name": item.product.name,
                    "product_code": item.product.code or "",
                    "current_stock": item.current_stock,
                    "stock_status": item.stock_status,
                    "days_of_stock": item.days_of_stock,
                    "turnover_days": item.turnover_days,
                }
            )

        data = {
            "shop_id": shop_id,
            "data_type": "inventory",
            "data": inventory_data,
            "data_count": len(inventory_data),
            "last_updated_at": timezone.now(),
        }

        realtime_data, created = RealtimeData.objects.update_or_create(
            platform=platform,
            shop=shop,
            data_type="inventory",
            data=data,
            data_count=len(inventory_data),
            last_updated_at=timezone.now(),
        )

        return realtime_data

    def update_visitor_realtime_data(self, platform_id: int, limit: int = 100) -> RealtimeData:
        """更新访客实时数据"""
        platform = Platform.objects.get(id=platform_id)

        # 模拟访客数据（暂时使用订单数量作为访客指标）
        today = date.today()
        visitor_data = {
            "total_visitors": PlatformOrder.objects.filter(
                platform=platform, created_at__date=today
            ).count(),
            "unique_visitors": PlatformOrder.objects.filter(
                platform=platform, created_at__date=today
            )
            .values("buyer_email")
            .distinct()
            .count(),
            "bounce_rate": Decimal("0"),  # 简化处理
            "total_page_views": 0,
            "avg_session_duration": 0,
            "realtime_sales": Decimal("0"),
        }

        data = {
            "platform_id": platform_id,
            "data_type": "visitor",
            "data": visitor_data,
            "data_count": 1,
            "last_updated_at": timezone.now(),
        }

        realtime_data, created = RealtimeData.objects.update_or_create(
            platform=platform,
            data_type="visitor",
            data=visitor_data,
            data_count=1,
            last_updated_at=timezone.now(),
        )

        return realtime_data

    def update_platform_comparison_realtime_data(
        self, platform_id: int, limit: int = 100
    ) -> RealtimeData:
        """更新平台对比实时数据"""
        platform = Platform.objects.get(id=platform_id)

        # 获取今日平台对比数据
        today = date.today()

        queryset = (
            PlatformComparison.objects.filter(
                platform=platform, report_date=today, report_period="daily"
            )
            .select_related("platform")
            .order_by("-sales_amount")
        )

        # 构建平台对比数据
        comparison_data = []

        for item in queryset[:limit]:
            comparison_data.append(
                {
                    "platform": item.platform.name,
                    "platform_id": item.platform_id,
                    "order_count": item.order_count,
                    "sales_amount": float(item.sales_amount),
                    "sales_growth_rate": float(item.sales_growth_rate)
                    if item.sales_growth_rate
                    else 0,
                    "conversion_rate": float(item.conversion_rate) if item.conversion_rate else 0,
                    "avg_order_value": float(item.avg_order_value),
                    "sales_rank": item.sales_rank if item.sales_rank else 0,
                    "order_rank": item.order_rank if item.order_rank else 0,
                }
            )

        data = {
            "platform_id": platform_id,
            "data_type": "platform_comparison",
            "data": comparison_data,
            "data_count": len(comparison_data),
            "last_updated_at": timezone.now(),
        }

        realtime_data, created = RealtimeData.objects.update_or_create(
            platform=platform,
            data_type="platform_comparison",
            data=data,
            data_count=len(comparison_data),
            last_updated_at=timezone.now(),
        )

        return realtime_data


class RealtimeDashboardService:
    """实时大屏服务"""

    def get_dashboard_config(self, dashboard_id: int) -> Dict:
        """获取大屏配置"""
        dashboard = Dashboard.objects.get(id=dashboard_id)

        widgets = []
        widget_configs = dashboard.widgets.all().select_related("widget").order_by("order")

        for widget in widgets:
            try:
                # 获取实时数据
                if widget.data_source:
                    realtime_data = self._get_widget_realtime_data(widget)
                else:
                    realtime_data = self._get_default_widget_data(widget)

                widget_config = widget.widget_configs.first()

                widgets.append(
                    {
                        "widget_id": widget.id,
                        "widget_name": widget.name,
                        "widget_type": widget.widget_type,
                        "title": widget.title,
                        "description": widget.description,
                        "display_config": widget.display_config,
                        "data_source": widget.data_source,
                        "data_params": widget.data_params,
                        "data_refresh_interval": widget.data_refresh_interval,
                        "layout_config": widget.layout_config,
                        "config": widget_config,
                    }
                )
            except Exception as e:
                logger.error(f"Error getting widget config: {e}")

        return {
            "dashboard_id": dashboard.id,
            "name": dashboard.name,
            "description": dashboard.description,
            "layout": dashboard.layout,
            "widgets": widgets,
            "background_image": dashboard.cover_image.url if dashboard.cover_image else "",
            "refresh_interval": dashboard.refresh_interval,
        }

    def _get_widget_realtime_data(self, widget) -> Dict:
        """获取组件实时数据"""
        service = RealtimeDataService()

        # 根据数据源获取实时数据
        if widget.data_source == "SalesSummary":
            data = service.update_sales_realtime_data(
                platform_id=widget.dashboard.platform_id, limit=widget.data_params.get("limit", 100)
            )
        elif widget.data_source == "InventoryAnalysis":
            data = service.update_inventory_realtime_data(
                shop_id=widget.dashboard.shop_id, limit=widget.data_params.get("limit", 100)
            )
        elif widget.data_source == "PlatformComparison":
            data = service.update_platform_comparison_realtime_data(
                platform_id=widget.dashboard.platform_id, limit=widget.data_params.get("limit", 100)
            )
        else:
            # 默认数据
            data = {
                "widget_id": widget.id,
                "widget_name": widget.name,
                "data": {"value": 0},
                "timestamp": datetime.now().isoformat(),
            }

        return data

    def _get_default_widget_data(self, widget) -> Dict:
        """获取组件默认数据"""
        if widget.data_source == "SalesSummary":
            return {
                "widget_id": widget.id,
                "data": {"total_orders": 0, "total_amount": 0, "paid_orders": 0},
                "timestamp": datetime.now().isoformat(),
            }
        elif widget.data_source == "InventoryAnalysis":
            return {
                "widget_id": widget.id,
                "data": {
                    "product_name": "",
                    "current_stock": 0,
                    "stock_status": "normal",
                    "days_of_stock": 0,
                    "turnover_days": 0,
                },
                "timestamp": datetime.now().isoformat(),
            }
        else:
            return {
                "widget_id": widget.id,
                "data": {"value": 0},
                "timestamp": datetime.now().isoformat(),
            }

    def update_dashboard_data(self, dashboard_id: int) -> bool:
        """更新大屏数据"""
        service = RealtimeDashboardService()

        dashboard = service.get_dashboard_config(dashboard_id)

        # 获取大屏配置
        widgets = dashboard.widgets.all()

        for widget in widgets:
            widget_data = self._get_widget_realtime_data(widget)
            widget.data.refresh_interval = widget.data_refresh_interval

            # 更新RealtimeWidgetConfig
            try:
                widget_config, created = RealtimeWidgetConfig.objects.update_or_create(
                    dashboard=dashboard,
                    widget=widget,
                    config={"last_updated_at": widget_data["timestamp"]},
                )
            except Exception as e:
                logger.error(f"Error updating widget config: {e}")

        return True

    def get_dashboard_summary(self, dashboard_id: int) -> Dict:
        """获取大屏摘要"""
        service = RealtimeDashboardService()
        dashboard = service.get_dashboard_config(dashboard_id)

        summary = {
            "dashboard_id": dashboard.id,
            "name": dashboard.name,
            "widget_count": dashboard.widgets.count(),
            "last_updated_at": dashboard.updated_at.strftime("%Y-%m-%d %H:%M")
            if dashboard.updated_at
            else "",
            "widgets": [
                {
                    "widget_id": widget.id,
                    "title": widget.title,
                    "widget_type": widget.widget_type,
                    "title": widget.title,
                }
                for widget in dashboard.widgets.all()
            ],
        }

        return summary

    def generate_dashboard_data(self, dashboard_id: int) -> Dict:
        """生成大屏数据"""
        service = RealtimeDashboardService()

        dashboard = service.get_dashboard_config(dashboard_id)
        dashboard_summary = service.get_dashboard_summary(dashboard_id)

        dashboard_data = {
            "dashboard_id": dashboard.id,
            "name": dashboard.name,
            "description": dashboard.description,
            "cover_image": dashboard.cover_image.url if dashboard.cover_image else "",
            "theme": dashboard.theme,
            "layout": dashboard.layout,
            "widgets": [],
            "last_updated_at": dashboard.updated_at.strftime("%Y-%m-%d %H:%M")
            if dashboard.updated_at
            else "",
            "refresh_interval": dashboard.refresh_interval,
            "total_widgets": dashboard.widgets.count(),
        }

        # 获取组件数据
        for widget in dashboard.widgets.all():
            widget_data = self._get_widget_realtime_data(widget)

            dashboard_data["widgets"].append(
                {
                    "widget_id": widget.id,
                    "name": widget.name,
                    "widget_type": widget.widget_type,
                    "title": widget.title,
                    "description": widget.description,
                    "display_config": widget.display_config,
                    "data": widget_data.get("data", {}),
                    "timestamp": widget_data.get("timestamp", ""),
                }
            )

        return dashboard_data

    def get_widget_data(self, widget_id: int) -> Dict:
        """获取组件数据"""
        try:
            from .models import RealtimeWidget

            widget = RealtimeWidget.objects.select_related("dashboard").get(id=widget_id)

            service = RealtimeDashboardService()
            return service._get_widget_realtime_data(widget)
        except Exception as e:
            logger.error(f"Error getting widget data: {e}")
            return {"error": str(e)}

    def update_realtime_data_cache(self):
        """更新实时数据缓存"""
        from ecomm_sync.models import Platform

        # 获取所有活跃平台
        platforms = Platform.objects.filter(is_active=True)

        for platform in platforms:
            try:
                # 更新销售数据
                self.update_sales_realtime_data(platform.id, 500)

                # 更新库存数据
                for shop in platform.shops.filter(is_active=True):
                    self.update_inventory_realtime_data(shop.id, 500)

                # 更新访客数据
                self.update_visitor_realtime_data(platform.id, 1000)

                # 更新平台对比数据
                self.update_platform_comparison_realtime_data(platform.id, 100)

            except Exception as e:
                logger.error(f"Error updating real-time data for platform {platform.name}: {e}")

        return True
