"""
BI报表API视图
"""
from django.db.models import Avg, Count, Sum
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.bi.models import (
    Dashboard,
    DashboardWidget,
    InventoryAnalysis,
    PlatformComparison,
    ProductSales,
    Report,
    ReportData,
    SalesSummary,
    SystemHealth,
    ApiPerformance,
)
from apps.bi.serializers import (
    DashboardSerializer,
    DashboardWidgetSerializer,
    InventoryAnalysisSerializer,
    PlatformComparisonSerializer,
    ProductSalesSerializer,
    ReportSerializer,
    SalesSummarySerializer,
    SystemHealthSerializer,
    ApiPerformanceSerializer,
)
from apps.bi.services import ReportGenerator


class ReportViewSet(viewsets.ModelViewSet):
    """报表视图集"""

    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        """生成报表"""
        report = self.get_object()
        service = ReportGenerator()

        # 根据报表类型生成对应数据
        if report.report_type == "sales":
            results = service.sales_service.generate_daily_sales_summary(
                platform_id=report.platform_id, platform_account_id=report.platform_account_id
            )
            serializer = SalesSummarySerializer(results)
        elif report.report_type == "inventory":
            results = service.inventory_service.generate_inventory_analysis(
                shop_id=report.platform_account_id if report.platform_account_id else 1
            )
            serializer = InventoryAnalysisSerializer(results, many=True)
        else:
            return Response({"error": "不支持的报表类型"}, status=status.HTTP_400_BAD_REQUEST)

        # 保存报表数据
        report_data = ReportData.objects.create(
            report=report,
            data=serializer.data,
            row_count=len(serializer.data) if isinstance(serializer.data, list) else 1,
        )

        return Response(
            {"report_id": report.id, "report_data_id": report_data.id, "data": serializer.data}
        )


class SalesSummaryViewSet(viewsets.ModelViewSet):
    """销售汇总视图集"""

    queryset = SalesSummary.objects.all()
    serializer_class = SalesSummarySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        platform_id = self.request.query_params.get("platform_id")
        platform_account_id = self.request.query_params.get("platform_account_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if platform_id:
            queryset = queryset.filter(platform_id=platform_id)
        if platform_account_id:
            queryset = queryset.filter(platform_account_id=platform_account_id)
        if start_date:
            queryset = queryset.filter(report_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(report_date__lte=end_date)

        return queryset

    @action(detail=False, methods=["get"])
    def trends(self, request):
        """获取销售趋势"""
        queryset = self.get_queryset()

        # 按日期分组统计
        trend_data = (
            queryset.values("report_date")
            .annotate(
                total_amount=Sum("total_amount"),
                total_orders=Sum("total_orders"),
                avg_order_value=Avg("avg_order_value"),
            )
            .order_by("report_date")
        )

        return Response(trend_data)

    @action(detail=False, methods=["get"])
    def comparison(self, request):
        """获取平台对比"""
        queryset = self.get_queryset()

        # 按平台分组统计
        comparison_data = (
            queryset.values("platform__name", "platform_id")
            .annotate(
                total_amount=Sum("total_amount"),
                total_orders=Sum("total_orders"),
                avg_order_value=Avg("avg_order_value"),
                conversion_rate=Avg("conversion_rate"),
            )
            .order_by("-total_amount")
        )

        return Response(comparison_data)


class ProductSalesViewSet(viewsets.ModelViewSet):
    """商品销售视图集"""

    queryset = ProductSales.objects.all()
    serializer_class = ProductSalesSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        platform_id = self.request.query_params.get("platform_id")
        product_id = self.request.query_params.get("product_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if platform_id:
            queryset = queryset.filter(platform_id=platform_id)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if start_date:
            queryset = queryset.filter(report_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(report_date__lte=end_date)

        return queryset.order_by("-sales_amount")

    @action(detail=False, methods=["get"])
    def ranking(self, request):
        """获取商品销售排行"""
        queryset = self.get_queryset()

        # 按销售金额排序并添加排名
        ranked_products = []
        for idx, product_sale in enumerate(queryset[:100]):  # 前100名
            data = ProductSalesSerializer(product_sale).data
            data["rank"] = idx + 1
            ranked_products.append(data)

        return Response(ranked_products)


class InventoryAnalysisViewSet(viewsets.ModelViewSet):
    """库存分析视图集"""

    queryset = InventoryAnalysis.objects.all()
    serializer_class = InventoryAnalysisSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        shop_id = self.request.query_params.get("shop_id")
        product_id = self.request.query_params.get("product_id")
        stock_status = self.request.query_params.get("stock_status")

        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if stock_status:
            queryset = queryset.filter(stock_status=stock_status)

        return queryset.order_by("-turnover_rate")

    @action(detail=False, methods=["get"])
    def alerts(self, request):
        """获取库存预警"""
        queryset = self.get_queryset().filter(stock_status__in=["low", "out", "overstock"])

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def turnover_analysis(self, request):
        """获取周转分析"""
        queryset = self.get_queryset()

        # 按周转率分组统计
        turnover_data = queryset.values("stock_status").annotate(
            count=Count("id"),
            avg_turnover_rate=Avg("turnover_rate"),
            avg_turnover_days=Avg("turnover_days"),
            total_stock_value=Sum("stock_value"),
        )

        return Response(turnover_data)


class PlatformComparisonViewSet(viewsets.ModelViewSet):
    """平台对比视图集"""

    queryset = PlatformComparison.objects.all()
    serializer_class = PlatformComparisonSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        report_date = self.request.query_params.get("report_date")
        report_period = self.request.query_params.get("report_period", "daily")
        platform_id = self.request.query_params.get("platform_id")

        if report_date:
            queryset = queryset.filter(report_date=report_date)
        if report_period:
            queryset = queryset.filter(report_period=report_period)
        if platform_id:
            queryset = queryset.filter(platform_id=platform_id)

        return queryset.order_by("-sales_amount")

    @action(detail=False, methods=["get"])
    def overview(self, request):
        """获取平台概览"""
        queryset = self.get_queryset()

        # 获取最新日期的数据
        latest_date = queryset.values("report_date").order_by("-report_date").first()
        if latest_date:
            latest_data = queryset.filter(report_date=latest_date["report_date"])
            serializer = self.get_serializer(latest_data, many=True)
            return Response(serializer.data)

        return Response([])


class DashboardViewSet(viewsets.ModelViewSet):
    """仪表盘视图集"""

    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # 只返回公开的或用户有权限的仪表盘
        queryset = queryset.filter(
            Q(is_public=True) | Q(created_by=user) | Q(allowed_users=user)
        ).distinct()

        return queryset

    @action(detail=True, methods=["get"])
    def widgets(self, request, pk=None):
        """获取仪表盘组件"""
        dashboard = self.get_object()
        widgets = dashboard.widgets.all()

        serializer = DashboardWidgetSerializer(widgets, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def update_layout(self, request, pk=None):
        """更新仪表盘布局"""
        dashboard = self.get_object()

        # 检查权限
        if dashboard.created_by != request.user and not dashboard.is_public:
            return Response({"error": "无权限修改此仪表盘"}, status=status.HTTP_403_FORBIDDEN)

        # 更新布局
        dashboard.layout = request.data.get("layout", {})
        dashboard.save()

        return Response({"success": True})


class DashboardWidgetViewSet(viewsets.ModelViewSet):
    """仪表盘组件视图集"""

    queryset = DashboardWidget.objects.all()
    serializer_class = DashboardWidgetSerializer

    @action(detail=False, methods=["get"])
    def types(self, request):
        """获取所有组件类型"""
        types = DashboardWidget.WIDGET_TYPES
        return Response([{"value": t[0], "label": t[1]} for t in types])


class DataExportViewSet(viewsets.ViewSet):
    """数据导出视图集"""

    @action(detail=False, methods=["get"])
    def sales(self, request):
        """导出销售数据"""
        format = request.query_params.get("format", "json")

        queryset = SalesSummary.objects.all()

        if format == "csv":
            # 生成CSV格式
            import csv

            from django.http import HttpResponse

            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="sales_export.csv"'

            writer = csv.writer(response)
            writer.writerow(["日期", "平台", "订单数", "销售额", "平均订单金额"])

            for item in queryset:
                writer.writerow(
                    [
                        item.report_date,
                        item.platform.name if item.platform else "",
                        item.total_orders,
                        item.total_amount,
                        item.avg_order_value,
                    ]
                )

            return response

        # 默认返回JSON
        serializer = SalesSummarySerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def inventory(self, request):
        """导出库存数据"""
        queryset = InventoryAnalysis.objects.all()
        serializer = InventoryAnalysisSerializer(queryset, many=True)
        return Response(serializer.data)


class SystemHealthViewSet(viewsets.ModelViewSet):
    """系统健康状态视图集"""

    queryset = SystemHealth.objects.all()
    serializer_class = SystemHealthSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        time_range = self.request.query_params.get("time_range", "24h")

        # 根据时间范围过滤
        if time_range == "24h":
            from django.utils import timezone
            queryset = queryset.filter(record_time__gte=timezone.now() - timezone.timedelta(hours=24))
        elif time_range == "7d":
            from django.utils import timezone
            queryset = queryset.filter(record_time__gte=timezone.now() - timezone.timedelta(days=7))

        return queryset.order_by("-record_time")

    @action(detail=False, methods=["get"])
    def latest(self, request):
        """获取最新系统健康状态"""
        latest = SystemHealth.objects.order_by("-record_time").first()
        if latest:
            serializer = self.get_serializer(latest)
            return Response(serializer.data)
        return Response({"status": "no_data"})

    @action(detail=False, methods=["get"])
    def status_summary(self, request):
        """获取状态摘要"""
        from django.utils import timezone
        last_24h = timezone.now() - timezone.timedelta(hours=24)
        
        # 统计最近24小时的状态
        status_counts = SystemHealth.objects.filter(record_time__gte=last_24h).values("status").annotate(count=Count("id"))
        
        # 计算平均响应时间
        avg_response_time = SystemHealth.objects.filter(record_time__gte=last_24h).aggregate(avg=Avg("api_response_time"))
        
        # 计算平均错误率
        error_count = SystemHealth.objects.filter(record_time__gte=last_24h).aggregate(total=Sum("error_count"))
        total_records = SystemHealth.objects.filter(record_time__gte=last_24h).count()
        avg_error_rate = (error_count["total"] / total_records * 100) if total_records > 0 else 0
        
        return Response({
            "status_counts": status_counts,
            "avg_response_time": avg_response_time["avg"],
            "avg_error_rate": avg_error_rate,
            "total_records": total_records
        })


class ApiPerformanceViewSet(viewsets.ModelViewSet):
    """API性能监控视图集"""

    queryset = ApiPerformance.objects.all()
    serializer_class = ApiPerformanceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        endpoint = self.request.query_params.get("endpoint")
        method = self.request.query_params.get("method")
        status_code = self.request.query_params.get("status_code")
        time_range = self.request.query_params.get("time_range", "24h")

        if endpoint:
            queryset = queryset.filter(endpoint__icontains=endpoint)
        if method:
            queryset = queryset.filter(method=method)
        if status_code:
            queryset = queryset.filter(status_code=status_code)
        
        # 根据时间范围过滤
        if time_range == "24h":
            from django.utils import timezone
            queryset = queryset.filter(request_time__gte=timezone.now() - timezone.timedelta(hours=24))
        elif time_range == "7d":
            from django.utils import timezone
            queryset = queryset.filter(request_time__gte=timezone.now() - timezone.timedelta(days=7))

        return queryset.order_by("-request_time")

    @action(detail=False, methods=["get"])
    def slow_endpoints(self, request):
        """获取慢API端点"""
        threshold = float(request.query_params.get("threshold", 1000))  # 默认1秒
        queryset = self.get_queryset().filter(response_time__gt=threshold)
        
        # 按响应时间降序排序
        slow_endpoints = queryset.order_by("-response_time")[:100]
        
        serializer = self.get_serializer(slow_endpoints, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def error_endpoints(self, request):
        """获取错误API端点"""
        queryset = self.get_queryset().filter(status_code__gte=400)
        
        # 按请求时间降序排序
        error_endpoints = queryset.order_by("-request_time")[:100]
        
        serializer = self.get_serializer(error_endpoints, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def performance_summary(self, request):
        """获取性能摘要"""
        from django.utils import timezone
        last_24h = timezone.now() - timezone.timedelta(hours=24)
        
        # 统计最近24小时的API性能
        total_requests = ApiPerformance.objects.filter(request_time__gte=last_24h).count()
        error_requests = ApiPerformance.objects.filter(request_time__gte=last_24h, status_code__gte=400).count()
        avg_response_time = ApiPerformance.objects.filter(request_time__gte=last_24h).aggregate(avg=Avg("response_time"))
        
        # 按端点分组统计
        endpoint_stats = ApiPerformance.objects.filter(request_time__gte=last_24h).values("endpoint").annotate(
            count=Count("id"),
            avg_response_time=Avg("response_time"),
            error_count=Count("id", filter=models.Q(status_code__gte=400))
        ).order_by("-count")[:20]
        
        return Response({
            "total_requests": total_requests,
            "error_requests": error_requests,
            "error_rate": (error_requests / total_requests * 100) if total_requests > 0 else 0,
            "avg_response_time": avg_response_time["avg"],
            "top_endpoints": endpoint_stats
        })
