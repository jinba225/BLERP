"""
BI报表服务
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
from django.db.models import Sum, Count, Avg, F, Q, Case, When, Value, IntegerField
from django.db.models.functions import Coalesce
from django.db.models.expressions import Window
from django.db.models.functions import Rank

from .models import (
    Report,
    ReportData,
    SalesSummary,
    ProductSales,
    InventoryAnalysis,
    PlatformComparison,
    Dashboard,
    DashboardWidget,
)
from ecomm_sync.models import PlatformOrder, PlatformOrderItem
from core.models import Platform, Shop
from products.models import Product


class SalesReportService:
    """销售报表服务"""

    def generate_daily_sales_summary(
        self,
        platform_id: Optional[int] = None,
        platform_account_id: Optional[int] = None,
        report_date: date = None,
    ) -> SalesSummary:
        """
        生成日销售汇总

        Args:
            platform_id: 平台ID
            platform_account_id: 平台账号ID
            report_date: 报表日期

        Returns:
            SalesSummary: 销售汇总对象
        """
        if report_date is None:
            report_date = date.today()

        # 查询平台订单
        queryset = PlatformOrder.objects.filter(created_at__date=report_date)

        if platform_id:
            queryset = queryset.filter(platform_id=platform_id)
        if platform_account_id:
            queryset = queryset.filter(platform_account_id=platform_account_id)

        # 聚合数据
        orders_data = queryset.aggregate(
            total_orders=Count("id"),
            total_amount=Sum("amount"),
            total_quantity=Sum(F("items__received_quantity")),
            paid_orders=Count("id", filter=Q(status="paid")),
            shipped_orders=Count("id", filter=Q(status="shipped")),
            delivered_orders=Count("id", filter=Q(status="delivered")),
            cancelled_orders=Count("id", filter=Q(status="cancelled")),
            refunded_orders=Count("id", filter=Q(status="refunded")),
        )

        # 计算平均订单金额
        total_orders_count = orders_data["total_orders"] or 0
        total_amount_value = orders_data["total_amount"] or Decimal("0")
        avg_order_value = (
            total_amount_value / total_orders_count if total_orders_count > 0 else Decimal("0")
        )

        # 计算转化率和复购率
        conversion_rate = self._calculate_conversion_rate(queryset)
        repeat_purchase_rate = self._calculate_repeat_purchase_rate(queryset)

        # 获取或创建销售汇总
        platform = Platform.objects.filter(id=platform_id).first() if platform_id else None

        sales_summary, created = SalesSummary.objects.update_or_create(
            platform=platform,
            platform_account_id=platform_account_id,
            report_date=report_date,
            report_period="daily",
            defaults={
                "total_orders": orders_data["total_orders"] or 0,
                "total_amount": total_amount_value,
                "total_quantity": orders_data["total_quantity"] or 0,
                "avg_order_value": avg_order_value,
                "paid_orders": orders_data["paid_orders"] or 0,
                "shipped_orders": orders_data["shipped_orders"] or 0,
                "delivered_orders": orders_data["delivered_orders"] or 0,
                "cancelled_orders": orders_data["cancelled_orders"] or 0,
                "refunded_orders": orders_data["refunded_orders"] or 0,
                "conversion_rate": conversion_rate,
                "repeat_purchase_rate": repeat_purchase_rate,
            },
        )

        # 如果已存在，更新数据
        if not created:
            for field, value in {
                "total_orders": orders_data["total_orders"] or 0,
                "total_amount": total_amount_value,
                "total_quantity": orders_data["total_quantity"] or 0,
                "avg_order_value": avg_order_value,
                "paid_orders": orders_data["paid_orders"] or 0,
                "shipped_orders": orders_data["shipped_orders"] or 0,
                "delivered_orders": orders_data["delivered_orders"] or 0,
                "cancelled_orders": orders_data["cancelled_orders"] or 0,
                "refunded_orders": orders_data["refunded_orders"] or 0,
                "conversion_rate": conversion_rate,
                "repeat_purchase_rate": repeat_purchase_rate,
            }.items():
                setattr(sales_summary, field, value)
            sales_summary.save()

        return sales_summary

    def generate_product_sales_report(
        self,
        platform_id: Optional[int] = None,
        platform_account_id: Optional[int] = None,
        report_date: date = None,
    ) -> List[ProductSales]:
        """
        生成商品销售报表

        Args:
            platform_id: 平台ID
            platform_account_id: 平台账号ID
            report_date: 报表日期

        Returns:
            List[ProductSales]: 商品销售数据列表
        """
        if report_date is None:
            report_date = date.today()

        # 查询订单商品
        queryset = PlatformOrderItem.objects.filter(order__created_at__date=report_date)

        if platform_id:
            queryset = queryset.filter(order__platform_id=platform_id)
        if platform_account_id:
            queryset = queryset.filter(order__platform_account_id=platform_account_id)

        # 按商品聚合
        products_data = queryset.values("product").annotate(
            sold_quantity=Sum("received_quantity"),
            sales_amount=Sum(F("unit_price") * F("received_quantity")),
            order_count=Count("order_id", distinct=True),
        )

        product_sales_list = []

        for data in products_data:
            product = data["product"]
            sold_quantity = data["sold_quantity"] or 0
            sales_amount = data["sales_amount"] or Decimal("0")

            # 计算利润（假设毛利率30%）
            profit = sales_amount * Decimal("0.3")

            # 计算退货率
            return_rate = self._calculate_return_rate(queryset, product)

            # 获取或创建商品销售数据
            product_sales, created = ProductSales.objects.update_or_create(
                product=product,
                platform_id=platform_id,
                report_date=report_date,
                report_period="daily",
                defaults={
                    "sold_quantity": sold_quantity,
                    "sales_amount": sales_amount,
                    "profit": profit,
                    "order_count": data["order_count"] or 0,
                    "return_rate": return_rate,
                },
            )

            if not created:
                for field, value in {
                    "sold_quantity": sold_quantity,
                    "sales_amount": sales_amount,
                    "profit": profit,
                    "order_count": data["order_count"] or 0,
                    "return_rate": return_rate,
                }.items():
                    setattr(product_sales, field, value)
                product_sales.save()

            product_sales_list.append(product_sales)

        return product_sales_list

    def _calculate_conversion_rate(self, queryset) -> Decimal:
        """计算转化率"""
        total_orders = queryset.count()
        paid_orders = queryset.filter(status__in=["paid", "shipped", "delivered"]).count()

        if total_orders == 0:
            return Decimal("0")

        return Decimal(str(paid_orders * 100 / total_orders)).quantize(Decimal("0.00"))

    def _calculate_repeat_purchase_rate(self, queryset) -> Decimal:
        """计算复购率"""
        # 获取买家邮箱
        buyer_emails = queryset.values_list("buyer_email", flat=True).distinct()

        if not buyer_emails:
            return Decimal("0")

        # 统计有多次购买的买家
        repeat_buyers = 0
        for email in buyer_emails:
            order_count = queryset.filter(buyer_email=email).count()
            if order_count > 1:
                repeat_buyers += 1

        return Decimal(str(repeat_buyers * 100 / len(buyer_emails))).quantize(Decimal("0.00"))

    def _calculate_return_rate(self, queryset, product) -> Decimal:
        """计算退货率"""
        order_count = queryset.filter(product=product).count()

        if order_count == 0:
            return Decimal("0")

        # 假设退款订单为退货（简化处理）
        refunded_count = queryset.filter(product=product, order__status="refunded").count()

        return Decimal(str(refunded_count * 100 / order_count)).quantize(Decimal("0.00"))


class InventoryReportService:
    """库存分析服务"""

    def generate_inventory_analysis(
        self, shop_id: int, product_id: Optional[int] = None
    ) -> List[InventoryAnalysis]:
        """
        生成库存分析

        Args:
            shop_id: 仓库ID
            product_id: 商品ID（可选）

        Returns:
            List[InventoryAnalysis]: 库存分析数据列表
        """
        queryset = Product.objects.all()

        if product_id:
            queryset = queryset.filter(id=product_id)

        inventory_analysis_list = []

        for product in queryset:
            # 获取库存数量（从stock_items模型）
            current_stock = self._get_product_stock(product, shop_id)
            safety_stock = product.min_stock or 0
            max_stock = product.max_stock or 0

            # 计算周转指标
            avg_daily_sales = self._calculate_avg_daily_sales(product, shop_id)
            days_of_stock = int(current_stock / avg_daily_sales) if avg_daily_sales > 0 else 999
            turnover_rate = self._calculate_turnover_rate(product, shop_id)
            turnover_days = 365 / turnover_rate if turnover_rate > 0 else 0

            # 确定库存状态
            stock_status = self._determine_stock_status(current_stock, safety_stock, days_of_stock)

            # 计算库存价值
            avg_cost = product.cost_price or Decimal("0")
            stock_value = current_stock * avg_cost

            # 获取或创建库存分析
            platform = product.platforms.first() if hasattr(product, "platforms") else None

            inventory_analysis, created = InventoryAnalysis.objects.update_or_create(
                product=product,
                shop_id=shop_id,
                platform=platform,
                defaults={
                    "current_stock": current_stock,
                    "safety_stock": safety_stock,
                    "max_stock": max_stock,
                    "turnover_days": turnover_days,
                    "turnover_rate": turnover_rate,
                    "avg_daily_sales": avg_daily_sales,
                    "stock_status": stock_status,
                    "days_of_stock": days_of_stock,
                    "stock_value": stock_value,
                    "avg_cost": avg_cost,
                },
            )

            if not created:
                for field, value in {
                    "current_stock": current_stock,
                    "safety_stock": safety_stock,
                    "max_stock": max_stock,
                    "turnover_days": turnover_days,
                    "turnover_rate": turnover_rate,
                    "avg_daily_sales": avg_daily_sales,
                    "stock_status": stock_status,
                    "days_of_stock": days_of_stock,
                    "stock_value": stock_value,
                    "avg_cost": avg_cost,
                }.items():
                    setattr(inventory_analysis, field, value)
                inventory_analysis.save()

            inventory_analysis_list.append(inventory_analysis)

        return inventory_analysis_list

    def _get_product_stock(self, product, shop_id) -> int:
        """获取商品库存数量"""
        # 从stock_items模型获取库存（假设存在）
        try:
            from stock.models import StockItem

            stock_item = StockItem.objects.filter(product=product, shop_id=shop_id).first()
            return stock_item.quantity if stock_item else 0
        except:
            # 如果stock模块不存在，返回0
            return 0

    def _calculate_avg_daily_sales(self, product, shop_id) -> Decimal:
        """计算日均销量"""
        # 查询过去30天的销量
        thirty_days_ago = date.today() - timedelta(days=30)

        try:
            # 从销售记录计算
            sales = ProductSales.objects.filter(
                product=product, report_date__gte=thirty_days_ago
            ).aggregate(total_quantity=Sum("sold_quantity"))

            total_quantity = sales["total_quantity"] or 0
            return Decimal(str(total_quantity / 30)).quantize(Decimal("0.00"))
        except:
            return Decimal("0")

    def _calculate_turnover_rate(self, product, shop_id) -> Decimal:
        """计算周转率"""
        try:
            # 从库存分析历史计算
            avg_stock_value = InventoryAnalysis.objects.filter(
                product=product, shop_id=shop_id
            ).aggregate(avg_value=Avg("stock_value"))["avg_value"] or Decimal("0")

            # 计算年度销售成本
            one_year_ago = date.today() - timedelta(days=365)
            product_sales = ProductSales.objects.filter(
                product=product, report_date__gte=one_year_ago
            ).aggregate(total_sales=Sum("sold_quantity"))

            total_sales = product_sales["total_sales"] or 0
            avg_cost = product.cost_price or Decimal("1")
            annual_sales_cost = total_sales * avg_cost

            if avg_stock_value == 0:
                return Decimal("0")

            turnover_rate = annual_sales_cost / avg_stock_value
            return turnover_rate.quantize(Decimal("0.00"))
        except:
            return Decimal("0")

    def _determine_stock_status(
        self, current_stock: int, safety_stock: int, days_of_stock: int
    ) -> str:
        """确定库存状态"""
        if current_stock == 0:
            return "out"
        elif current_stock <= safety_stock or days_of_stock <= 7:
            return "low"
        elif days_of_stock >= 90:
            return "overstock"
        else:
            return "normal"


class PlatformComparisonService:
    """平台对比服务"""

    def generate_platform_comparison(
        self, report_date: date = None, report_period: str = "daily"
    ) -> List[PlatformComparison]:
        """
        生成平台对比数据

        Args:
            report_date: 报表日期
            report_period: 报表周期（daily, weekly, monthly）

        Returns:
            List[PlatformComparison]: 平台对比数据列表
        """
        if report_date is None:
            report_date = date.today()

        # 获取所有活跃平台
        platforms = Platform.objects.filter(is_active=True)

        comparison_list = []

        for platform in platforms:
            # 查询平台账号
            platform_accounts = platform.accounts.filter(is_active=True)

            for account in platform_accounts:
                # 查询订单数据
                queryset = PlatformOrder.objects.filter(platform=platform, platform_account=account)

                # 根据周期过滤日期
                if report_period == "daily":
                    queryset = queryset.filter(created_at__date=report_date)
                elif report_period == "weekly":
                    week_start = report_date - timedelta(days=report_date.weekday())
                    queryset = queryset.filter(
                        created_at__date__gte=week_start, created_at__date__lte=report_date
                    )
                elif report_period == "monthly":
                    month_start = report_date.replace(day=1)
                    queryset = queryset.filter(
                        created_at__date__gte=month_start, created_at__date__lte=report_date
                    )

                # 聚合数据
                data = queryset.aggregate(
                    order_count=Count("id"),
                    sales_amount=Sum("amount"),
                )

                # 计算增长率（与上期对比）
                order_growth_rate = self._calculate_growth_rate(
                    platform, account, "order", report_date, report_period
                )
                sales_growth_rate = self._calculate_growth_rate(
                    platform, account, "sales", report_date, report_period
                )

                # 计算转化率和平均订单金额
                conversion_rate = SalesReportService._calculate_conversion_rate(None, queryset)
                avg_order_value = (data["sales_amount"] or Decimal("0")) / (
                    data["order_count"] or 1
                )

                # 创建平台对比数据
                comparison = PlatformComparison.objects.create(
                    report_date=report_date,
                    report_period=report_period,
                    platform=platform,
                    platform_account=account,
                    order_count=data["order_count"] or 0,
                    order_growth_rate=order_growth_rate,
                    sales_amount=data["sales_amount"] or Decimal("0"),
                    sales_growth_rate=sales_growth_rate,
                    conversion_rate=conversion_rate,
                    avg_order_value=avg_order_value,
                )

                comparison_list.append(comparison)

        # 计算排名
        self._calculate_rankings(comparison_list, report_date, report_period)

        return comparison_list

    def _calculate_growth_rate(
        self, platform, account, metric_type: str, current_date: date, period: str
    ) -> Decimal:
        """计算增长率"""
        # 获取上期数据
        if period == "daily":
            previous_date = current_date - timedelta(days=1)
        elif period == "weekly":
            previous_date = current_date - timedelta(days=7)
        elif period == "monthly":
            previous_date = current_date - timedelta(days=30)
        else:
            return Decimal("0")

        try:
            # 查询当前期数据
            current_queryset = PlatformOrder.objects.filter(
                platform=platform, platform_account=account, created_at__date__lte=current_date
            )

            # 查询上期数据
            previous_queryset = PlatformOrder.objects.filter(
                platform=platform,
                platform_account=account,
                created_at__date__lte=previous_date,
            )

            if metric_type == "order":
                current_value = current_queryset.count()
                previous_value = previous_queryset.count()
            elif metric_type == "sales":
                current_value = current_queryset.aggregate(total=Sum("amount"))["total"] or Decimal(
                    "0"
                )
                previous_value = previous_queryset.aggregate(total=Sum("amount"))[
                    "total"
                ] or Decimal("0")
            else:
                return Decimal("0")

            # 计算增长率
            if previous_value == 0:
                return Decimal("0") if current_value == 0 else Decimal("100")

            growth_rate = ((current_value - previous_value) / previous_value) * 100
            return growth_rate.quantize(Decimal("0.00"))
        except:
            return Decimal("0")

    def _calculate_rankings(
        self, comparison_list: List[PlatformComparison], report_date: date, period: str
    ):
        """计算排名"""
        # 按销售金额排名
        sorted_by_sales = sorted(comparison_list, key=lambda x: x.sales_amount, reverse=True)
        for idx, item in enumerate(sorted_by_sales):
            item.sales_rank = idx + 1
            item.save()

        # 按订单数排名
        sorted_by_orders = sorted(comparison_list, key=lambda x: x.order_count, reverse=True)
        for idx, item in enumerate(sorted_by_orders):
            item.order_rank = idx + 1
            item.save()


class ReportGenerator:
    """报表生成器"""

    def __init__(self):
        self.sales_service = SalesReportService()
        self.inventory_service = InventoryReportService()
        self.platform_service = PlatformComparisonService()

    def generate_all_daily_reports(self, report_date: date = None):
        """生成所有日报表"""
        if report_date is None:
            report_date = date.today()

        results = {
            "sales_summaries": [],
            "product_sales": [],
            "inventory_analysis": [],
            "platform_comparisons": [],
        }

        # 生成销售汇总
        platforms = Platform.objects.filter(is_active=True)
        for platform in platforms:
            sales_summary = self.sales_service.generate_daily_sales_summary(
                platform_id=platform.id, report_date=report_date
            )
            results["sales_summaries"].append(sales_summary)

        # 生成商品销售报表
        product_sales_list = self.sales_service.generate_product_sales_report(
            report_date=report_date
        )
        results["product_sales"].extend(product_sales_list)

        # 生成库存分析
        shops = Shop.objects.filter(is_active=True)
        for shop in shops:
            inventory_list = self.inventory_service.generate_inventory_analysis(shop_id=shop.id)
            results["inventory_analysis"].extend(inventory_list)

        # 生成平台对比
        platform_comparisons = self.platform_service.generate_platform_comparison(
            report_date=report_date, report_period="daily"
        )
        results["platform_comparisons"].extend(platform_comparisons)

        return results
