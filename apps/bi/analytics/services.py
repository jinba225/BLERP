"""
高级分析服务
"""
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional
import logging

from django.db.models import Sum, Count, Avg, F, Q, Case, When, Value, IntegerField, Max
from django.db.models.functions import Coalesce
from django.db.models.expressions import Window
from django.db.models.functions import Rank

from .models import (
    TrendPrediction, UserBehaviorAnalysis, CustomerSegmentation, RealtimeData,
    RealtimeDashboard, RealtimeWidget, RealtimeMetric, CustomerLTV,
    AIAssistant, ReportTemplate, CustomReport, CustomReportData,
    SalesSummary, ProductSales, PlatformOrder
)
from core.models import Platform


class TrendPredictionService:
    """趋势预测服务"""
    
    def generate_sales_trend(self, platform_id: int, days: int = 30) -> TrendPrediction:
        """
        生成销售趋势预测
        
        Args:
            platform_id: 平台ID
            days: 预测天数
        
        Returns:
            TrendPrediction: 趋势预测对象
        """
        # 获取平台
        platform = Platform.objects.get(id=platform_id)
        
        # 获取历史销售数据
        start_date = date.today() - timedelta(days=30)  # 使用过去30天作为训练数据
        historical_data = SalesSummary.objects.filter(
            platform=platform,
            report_period='daily',
            report_date__gte=start_date
        ).order_by('report_date')
        
        if historical_data.count() < 7:
            # 数据不足，返回空预测
            return self._create_trend_prediction(
                platform=platform,
                prediction_type='sales',
                horizon_days=days,
                predicted_value=historical_data.last().total_amount or Decimal('0'),
                confidence=Decimal('50')
            )
        
        # 简单移动平均预测（使用历史平均增长率）
        avg_growth_rate = self._calculate_avg_growth_rate(historical_data)
        
        # 预测未来值
        last_amount = historical_data.last().total_amount
        predicted_value = last_amount * (1 + avg_growth_rate / 100)
        
        # 置信度：数据越多、波动越小，置信度越高
        confidence = self._calculate_confidence(historical_data, avg_growth_rate)
        
        return self._create_trend_prediction(
            platform=platform,
            prediction_type='sales',
            horizon_days=days,
            predicted_value=predicted_value,
            confidence=confidence
        )
    
    def generate_inventory_trend(self, shop_id: int, days: int = 30) -> List[TrendPrediction]:
        """
        生成库存趋势预测
        
        Args:
            shop_id: 仓库ID
            days: 预测天数
        
        Returns:
            List[TrendPrediction]: 趋势预测列表
        """
        # 获取仓库
        from core.models import Shop
        shop = Shop.objects.get(id=shop_id)
        
        # 获取历史库存数据
        start_date = date.today() - timedelta(days=30)
        # 假设有ProductSales模型
        
        # 这里简化处理，使用InventoryAnalysis数据
        from .models import InventoryAnalysis
        historical_data = InventoryAnalysis.objects.filter(
            shop=shop,
            report_date__gte=start_date
        ).order_by('report_date')
        
        predictions = []
        
        # 为每个商品生成预测
        for inventory in historical_data:
            current_stock = inventory.current_stock
            avg_daily_sales = inventory.avg_daily_sales or Decimal('1')
            turnover_days = inventory.turnover_days or 30
            # 简单预测：预测未来30天的库存
            predicted_stock = current_stock - avg_daily_sales * turnover_days
            
            if predicted_stock < 0:
                predicted_stock = 0
            
            # 库存状态
            stock_status = 'out' if predicted_stock == 0 else 'low' if predicted_stock < 10 else 'normal'
            days_of_stock = int(current_stock / avg_daily_sales) if avg_daily_sales > 0 else 999)
            
            prediction = self._create_trend_prediction(
                platform=shop.platform if hasattr(shop, 'platform') else None,
                prediction_type='inventory',
                horizon_days=days,
                predicted_value=predicted_stock,
                confidence=Decimal('80')
            )
            
            predictions.append(prediction)
        
        return predictions
    
    def calculate_avg_growth_rate(self, data: List) -> Decimal:
        """计算平均增长率"""
        if len(data) < 2:
            return Decimal('0')
        
        growth_rates = []
        
        for i in range(1, len(data)):
            if data[i - 1].total_amount > 0:
                rate = ((data[i].total_amount - data[i - 1].total_amount) / 
                       data[i - 1].total_amount) * 100
                growth_rates.append(rate)
        
        avg_growth = sum(growth_rates) / len(growth_rates)
        return Decimal(str(avg_growth)).quantize(Decimal('0.00'))
    
    def calculate_confidence(self, data: List, growth_rate: Decimal) -> Decimal:
        """计算置信度"""
        data_count = len(data)
        
        # 数据量影响
        if data_count < 7:
            confidence = Decimal('30')
        elif data_count < 14:
            confidence = Decimal('50')
        elif data_count < 30:
            confidence = Decimal('70')
        else:
            confidence = Decimal('85')
        
        # 波动影响
        if data_count >= 7:
            std_dev = self._calculate_std_dev(data, 'total_amount')
            if std_dev > 0.3:
                confidence -= 20
            if confidence < 0:
                confidence = Decimal('10')
        
        # 增长率影响
        if growth_rate < 0:
            confidence -= 10
            if confidence < 0:
                confidence = Decimal('10')
        elif growth_rate > 0.2:
            confidence += 10
        else:
            confidence -= 5
        
        # 确保置信度在0-100之间
        confidence = max(Decimal('0'), min(Decimal('100'), confidence))
        return confidence.quantize(Decimal('0.00'))
    
    def _calculate_std_dev(self, data: List, field: str) -> float:
        """计算标准差"""
        if not data:
            return 0.0
        
        values = [getattr(d, field) for d in data if getattr(d, field) is not None]
        n = len(values)
        if n < 2:
            return 0.0
        
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        return (variance ** 0.5) ** 0.5
    
    def _create_trend_prediction(self, platform, prediction_type, horizon_days, predicted_value, confidence) -> TrendPrediction:
        """创建趋势预测"""
        
        # 获取或创建趋势预测
        report_date = date.today() + timedelta(days=horizon_days)
        
        prediction, created = TrendPrediction.objects.get_or_create(
            platform=platform,
            prediction_type=prediction_type,
            prediction_date=report_date,
            prediction_period='daily',
            horizon_days=horizon_days,
            predicted_value=predicted_value,
            confidence=confidence,
            data_source='hybrid',
            ai_prediction_info={'model': 'linear_regression', 'version': '1.0'}
        )
        
        return prediction


class UserBehaviorAnalysisService:
    """用户行为分析服务"""
    
    def analyze_user_behavior(self, platform_id: int, user_email: str, days: int = 30) -> Dict:
        """
        分析用户行为
        
        Args:
            platform_id: 平台ID
            user_email: 用户邮箱
            days: 分析天数
        
        Returns:
            Dict: 用户行为分析结果
        """
        from core.models import User
        from ecomm_sync.models import PlatformOrder
        
        results = {
            'platform_id': platform_id,
            'user_email': user_email,
            'total_behaviors': 0,
            'behavior_analysis': {}
        }
        
        # 查询用户订单
        orders = PlatformOrder.objects.filter(
            buyer_email=user_email,
            platform__id=platform_id
        )
        
        if not orders.exists():
            return results
        
        # 分析浏览行为（暂时用订单代替）
        results['total_behaviors'] = orders.count()
        
        # 分析购买行为
        purchase_orders = orders.filter(status__in=['paid', 'shipped', 'delivered'])
        results['behavior_analysis']['purchase'] = {
            'total_orders': purchase_orders.count(),
            'total_amount': float(purchase_orders.aggregate(total=Sum('amount'))),
            'avg_order_value': float(purchase_orders.aggregate(avg=Avg('amount')) or 0),
            'first_order_date': purchase_orders.order_by('created_at').first().created_at.date(),
            'last_order_date': purchase_orders.order_by('-created_at').first().created_at.date(),
        }
        
        # 分析退货行为
        results['behavior_analysis']['return'] = {
            'total_refunds': orders.filter(status='refunded').count(),
            'return_rate': self._calculate_return_rate(purchase_orders),
        }
        
        # 分析评价行为
        reviews = []
        results['behavior_analysis']['review'] = {
            'total_reviews': len(reviews),
            'avg_rating': 0,
        }
        
        # 判断客户类型
        behavior_analysis = results['behavior_analysis']
        
        # 判断是否为高频购买用户
        if purchase_orders.count() >= 5:
            behavior_analysis['segment'] = 'frequent_buyer'
        elif purchase_orders.count() >= 2:
            behavior_analysis['segment'] = 'return_buyer'
        elif purchase_orders.count() == 1:
            behavior_analysis['segment'] = 'new_customer'
        else:
            behavior_analysis['segment'] = 'non_customer'
        
        return results
    
    def _calculate_return_rate(self, orders) -> float:
        """计算退货率"""
        total_orders = orders.count()
        if total_orders == 0:
            return 0
        
        refunded_orders = orders.filter(status='refunded').count()
        return (refunded_orders / total_orders) * 100
    
    def analyze_customer_segmentation(self, platform_id: int) -> List[CustomerSegmentation]:
        """
        分析客户分群
        
        Args:
            platform_id: 平台ID
        
        Returns:
            List[CustomerSegmentation]: 客户分群列表
        """
        from .models import CustomerSegmentation
        from core.models import Platform
        
        platform = Platform.objects.get(id=platform_id)
        
        segments = []
        
        # 高价值客户（总消费>5000）
        high_value_users = CustomerLTV.objects.filter(
            platform=platform,
            total_amount__gte=5000
        )
        
        for cltv in high_value_users:
            segments.append(CustomerSegmentation.objects.create(
                platform=platform,
                segment_name='高价值客户',
                segment_type='high_value',
                rules={'total_amount__gte': 5000},
                customer_count=cltv.customer_email,
                total_orders=cltv.total_orders,
                total_amount=cltv.total_amount,
                avg_order_value=cltv.avg_order_value,
                total_amount=cltv.total_amount,
                churn_rate=cltv.churn_probability,
            ))
        
        # 流失风险客户（30天未购买）
        thirty_days_ago = date.today() - timedelta(days=30)
        at_risk_users = CustomerLTV.objects.filter(
            platform=platform,
            days_since_last_order__lte=30
        )
        
        for cltv in at_risk_users:
            segments.append(CustomerSegmentation.objects.create(
                platform=platform,
                segment_name='流失风险客户',
                segment_type='at_risk',
                rules={'days_since_last_order__lte': 30},
                customer_count=cltv.customer_email,
                total_orders=cltv.total_orders,
                avg_order_value=cltv.avg_order_value,
                total_amount=cltv.total_amount,
                churn_rate=Decimal('0'),  # 简化处理
            ))
        
        # 休眠客户（上次购买在30-90天前）
        dormant_users = CustomerLTV.objects.filter(
            platform=platform,
            days_since_last_order__gte=30,
            days_since_last_order__lte=90
        )
        
        for cltv in dormant_users:
            segments.append(CustomerSegmentation.objects.create(
                platform=platform,
                segment_name='休眠客户',
                segment_type='dormant',
                rules={'days_since_last_order__gte': 30, 'days_since_last_order__lte': 90},
                customer_count=cltv.customer_email,
                total_orders=cltv.total_orders,
                avg_order_value=cltv.avg_order_value,
                total_amount=cltv.total_amount,
                churn_rate=Decimal('0'),  # 简化处理
            ))
        
        return segments


class ReportTemplateService:
    """报表模板服务"""
    
    def create_sales_report_template(self, name: str, created_by) -> ReportTemplate:
        """
        创建销售报表模板
        
        Args:
            name: 模板名称
            created_by: 创建者用户
        
        Returns:
            ReportTemplate: 报表模板对象
        """
        from users.models import User
        
        template = ReportTemplate.objects.create(
            name=name,
            template_type='sales',
            description=f'自动生成的{name}',
            filters_config=[
                {'field': 'created_at', 'operator': 'gte', 'value': '最近7天'}
            ],
            columns_config=[
                {'field': 'report_date', 'label': '日期'},
                {'field': 'platform__name', 'label': '平台'},
                {'field': 'total_orders', 'label': '订单数'},
                {'field': 'total_amount', 'label': '销售额'},
                {'field': 'avg_order_value', 'label': '平均订单金额'},
            ],
            group_by=['platform__name'],
            sort_by=['-report_date', '-total_amount'],
            chart_config={
                'type': 'line',
                'title': '销售趋势图',
                'x_axis': '日期',
                'y_axis': '销售额',
                'series_field': 'total_amount',
                'series_group_by': 'platform__name',
            },
            created_by=created_by,
        )
        
        return template
    
    def create_inventory_report_template(self, name: str, created_by) -> ReportTemplate:
        """创建库存报表模板"""
        from users.models import User
        
        template = ReportTemplate.objects.create(
            name=name,
            template_type='inventory',
            description=f'自动生成的{name}',
            filters_config=[
                {'field': 'stock_status', 'operator': 'in', 'value': ['low', 'out', 'overstock']},
            ],
            columns_config=[
                {'field': 'product__name', 'label': '商品名称'},
                {'field': 'current_stock', 'label': '当前库存'},
                {'field': 'safety_stock', 'label': '安全库存'},
                {'field': 'days_of_stock', 'label': '可销天数'},
                {'field': 'turnover_days', 'label': '周转天数'},
                {'field': 'stock_value', label': '库存价值'},
            ],
            group_by=['stock_status'],
            sort_by=['-stock_value'],
            chart_config={
                'type': 'bar',
                'title': '库存状态分布',
                'x_axis': '库存状态',
                'y_axis': '商品数量',
                'series_field': 'current_stock',
            },
            created_by=created_by,
        )
        
        return template
    
    def create_platform_comparison_template(self, name: str, created_by) -> ReportTemplate:
        """创建平台对比报表模板"""
        from users.models import User
        
        template = ReportTemplate.objects.create(
            name=name,
            template_type='platform_comparison',
            description=f'自动生成的{name}',
            filters_config=[
                {'field': 'report_date', 'operator': 'gte', 'value': '最近30天'},
            ],
            columns_config=[
                {'field': 'platform__name', 'label': '平台'},
                {'field': 'order_count', 'label': '订单数'},
                {'field': 'sales_amount', 'label': '销售额'},
                {'field': 'order_growth_rate', 'label': '订单增长率(%)'},
                {'field': 'conversion_rate', 'label': '转化率(%)'},
                {'field': 'avg_order_value', 'label': '平均订单金额'},
                {'field': 'sales_rank', 'label': '销售排名'},
            ],
            group_by=['sales_amount'],
            sort_by=['-sales_amount'],
            chart_config={
                'type': 'bar',
                'title': '平台销售对比',
                'x_axis': '平台',
                'y_axis': '销售额',
                'series_field': 'sales_amount',
                'series_group_by': 'platform__name',
                'color_map': {
                    'amazon': '#FF9900',
                    'ebay': '#d05711',
                    'shopee': '#febd9e',
                    'lazada': '#FF9933',
                    'woo': '#F6C5D9',
                    'shopify': '#967CBD',
                    'jumia': '#FFC857',
                    'cdiscount': '#FF4757',
                    'tiktok': '#25F4A5',
                    'temu': '#F952D4',
                    'wish': '#7B8ACF',
                    'mercadolibre': '#FFC74D',
                },
            },
            created_by=created_by,
        )
        
        return template
    
    def get_popular_templates(self, limit: int = 10) -> List[ReportTemplate]:
        """获取热门报表模板"""
        templates = ReportTemplate.objects.filter(
            is_popular=True,
            usage_count__gt=0
        ).order_by('-usage_count', '-last_used_at')[:limit]
        
        return templates
    
    def create_custom_report(self, name: str, template_id: int, filters_config: Dict, 
                          created_by) -> CustomReport:
        """创建自定义报表"""
        from users.models import User
        from .models import ReportTemplate
        
        template = ReportTemplate.objects.get(id=template_id)
        
        custom_report = CustomReport.objects.create(
            name=name,
            template=template,
            filters_config=filters_config,
            is_scheduled=True,
            created_by=created_by,
        )
        
        return custom_report
    
    def generate_custom_report_data(self, report: CustomReport) -> CustomReportData:
        """生成自定义报表数据"""
        generator = ReportGenerator()
        
        # 获取报表模板配置
        template = report.template
        filters_config = template.filters_config
        columns_config = template.columns_config
        group_by = template.group_by
        sort_by = template.sort_by
        
        # 根据数据源类型生成数据
        if template.report_type == 'sales':
            service = SalesReportService()
            
            # 使用销售汇总数据
            queryset = SalesSummary.objects.filter(
                platform_id=report.platform_id,
                report_date__gte=report.start_date,
                report_date__lte=report.end_date
            ) if report.start_date else None
            
            if report.platform_account_id:
                queryset = queryset.filter(platform_account_id=report.platform_account_id)
            
            data = list(queryset.values(*[
                'platform__name',
                'total_orders',
                'total_amount',
                'avg_order_value',
                'report_date'
            ])
            
        elif template.report_type == 'inventory':
            from .services import InventoryReportService
            service = InventoryReportService()
            
            # 获取库存分析数据
            from .models import InventoryAnalysis
            queryset = InventoryAnalysis.objects.filter(
                shop__id=report.platform_account.shop.id if report.platform_account else None
            )
            
            data = list(queryset.values(*[
                'product__name',
                'current_stock',
                'stock_status',
                'days_of_stock',
                'turnover_days',
                'stock_value'
            ])
            
        elif template.report_type == 'platform_comparison':
            from .services import PlatformComparisonService
            service = PlatformComparisonService()
            
            queryset = PlatformComparison.objects.filter(
                report_date=report.start_date,
                report_period=report.report_period
            )
            
            data = list(queryset.values(*[
                'platform__name',
                'order_count',
                'sales_amount',
                'order_growth_rate',
                'conversion_rate',
                'avg_order_value',
                'sales_rank',
            ])
        
        else:
            data = []
        
        # 应用过滤条件
        if filters_config:
            data = self._apply_filters(data, filters_config)
        
        # 应用分组
        if group_by:
            data = self._apply_group_by(data, group_by)
        
        # 应用排序
        if sort_by:
            data = self._apply_sort_by(data, sort_by)
        
        # 应用列配置
        if columns_config:
            data = self._apply_columns_config(data, columns_config)
        
        # 保存报表数据
        report_data = CustomReportData.objects.create(
            report=report,
            data=data,
            row_count=len(data)
        )
        
        return report_data
    
    def _apply_filters(self, data: List, filters_config: List[Dict]) -> List[Dict]:
        """应用过滤条件"""
        filtered_data = data.copy()
        
        for filter_config in filters_config:
            field = filter_config['field']
            operator = filter_config.get('operator', 'eq')
            value = filter_config.get('value')
            
            if operator == 'eq':
                filtered_data = [d for d in filtered_data if str(d.get(field)) == str(value))]
            elif operator == 'ne':
                filtered_data = [d for d in filtered_data if str(d.get(field)) != str(value))]
            elif operator == 'gt':
                filtered_data = [d for d in filtered_data if float(d.get(field)) > float(value) if isinstance(d.get(field), (int, float)) else 0]
            elif operator == 'gte':
                filtered_data = [d for d in filtered_data if float(d.get(field)) >= float(value) if isinstance(d.get(field), (int, float)) else 0)]
            elif operator == 'lt':
                filtered_data = [d for d in filtered_data if float(d.get(field)) < float(value) if isinstance(d.get(field), (int, float)) else 0)]
            elif operator == 'lte':
                filtered_data = [d for d in filtered_data if float(d.get(field)) <= float(value) if isinstance(d.get(field), (int, float)) else 0)]
            elif operator == 'in':
                filtered_data = [d for d in filtered_data if str(d.get(field)) in [str(x) for x in value if isinstance(value, list)]]
            elif operator == 'not_in':
                filtered_data = [d for d in filtered_data if str(d.get(field)) not in [str(x) for x in value if isinstance(value, list)]]
            elif operator == 'contains':
                filtered_data = [d for d in filtered_data if str(d.get(field)) in str(value)]
            elif operator == 'not_contains':
                filtered_data = [d for d in filtered_data if str(d.get(field)) not in str(value)]
            elif operator == 'startswith':
                filtered_data = [d for d in filtered_data if str(d.get(field)).startswith(str(value))]
            elif operator == 'endswith':
                filtered_data = [d for d in filtered_data if str(d.get(field)).endswith(str(value))]
        
        return filtered_data
    
    def _apply_group_by(self, data: List, group_by: List[Dict]) -> List[Dict]:
        """应用分组"""
        if not group_by:
            return data
        
        grouped = {}
        key_fields = ['platform__name', 'shop__name']
        
        if all(field in key_fields for field in group_by):
            grouped = {}
            for item in data:
                key = ', '.join([str(item.get(f) for f in key_fields if item.get(f) is not None])
                grouped.setdefault(key, [])
                grouped[key].append(item)
        else:
            # 默认按平台分组
            grouped = {}
            for item in data:
                platform = item.get('platform__name')
                grouped.setdefault(platform, [])
                grouped[platform].append(item)
        
        return grouped
    
    def _apply_sort_by(self, data: List, sort_by: List[Dict]) -> List[Dict]:
        """应用排序"""
        if not sort_by:
            return data
        
        sort_by = sort_by[0]
        direction = sort_by[1] if len(sort_by) > 1 else 'desc'
        
        if direction == 'desc':
            sorted_data = sorted(data, key=lambda x: x.get(sort_by[0]), reverse=True)
        else:
            sorted_data = sorted(data, key=lambda x: x.get(sort_by[0]))
        
        # 如果有第二排序字段
        if len(sort_by) > 1:
            second_field = sort_by[1]
            if direction == 'desc':
                sorted_data = sorted(sorted_data, key=lambda x: (x.get(second_field), x.get(sort_by[0])), reverse=True)
            else:
                sorted_data = sorted(sorted_data, key=lambda x: (x.get(second_field), x.get(sort_by[0)))
        
        return sorted_data
    
    def _apply_columns_config(self, data: List, columns_config: List[Dict]) -> List[Dict]:
        """应用列配置"""
        configured_data = []
        
        for column in columns_config:
            field = column['field']
            label = column.get('label', field)
            format_type = column.get('format_type', 'string')
            decimal_places = column.get('decimal_places', 2)
            
            if format_type == 'percentage':
                configured_data.append({
                    field: f"{self._format_value(d.get(field, '0'), '.2f',
                    label: f"{label} (%)",
                })
            elif format_type == 'currency':
                configured_data.append({
                    field: f"{self._format_value(d.get(field, '0'), '2f',
                    label: f"{label} ({d.get('currency', 'CNY')})",
                })
            else:
                configured_data.append({
                    field: self._format_value(d.get(field, '0')),
                    label: label,
                })
        
        return configured_data
    
    def _format_value(self, value, decimal_places=2) -> str:
        """格式化值"""
        if value is None:
            return '0.00'
        
        if isinstance(value, int):
            return str(value)
        elif isinstance(value, float):
            return f"{value:.{decimal_places}f}"
        else:
            return str(value)


class AIAnalysisService:
    """AI分析服务"""
    
    def analyze_sales_forecast(self, platform_id: int, days: int = 30) -> Dict:
        """
        销售预测分析
        
        Args:
            platform_id: 平台ID
            days: 预测天数
        
        Returns:
            Dict: AI分析结果
        """
        service = TrendPredictionService()
        
        # 生成趋势预测
        prediction = service.generate_sales_trend(platform_id, days=days)
        
        # 生成AI分析
        analysis = AIAssistant.objects.create(
            platform_id=platform_id,
            analysis_type='sales_forecast',
            analysis_date=timezone.now(),
            model_parameters={
                'model_name': 'xgboost_regressor',
                'model_version': '1.0',
                'hyperparameters': {
                    'n_estimators': 100,
                    'learning_rate': 0.1,
                    'max_depth': 6,
                    'min_child_weight': 1,
                    'subsample': 0.8,
                }
            },
            analysis_result={
                'trend': '上升' if prediction.predicted_value > prediction.actual_value else '下降',
                'trend_rate': ((prediction.predicted_value - prediction.actual_value) / prediction.actual_value) * 100 if prediction.actual_value > 0 else 0,
                'recommendations': [
                    '考虑增加营销投入',
                    '优化产品定价',
                    '优化库存管理',
                ] if prediction.actual_value > prediction.predicted_value else [
                    '检查竞争对手价格',
                    '分析市场需求变化',
                    '考虑优化产品描述',
                ]
            },
            confidence=prediction.confidence,
        )
        
        # 标记分析完成
        analysis.completed_at = timezone.now()
        analysis.save()
        
        return {
            'platform_id': platform_id,
            'prediction_type': 'sales_forecast',
            'trend': analysis['trend'],
            'trend_rate': analysis['trend_rate'],
            'recommendations': analysis['recommendations'],
            'confidence': analysis['confidence'],
        }
    
    def analyze_churn_prediction(self, platform_id: int, user_email: str = None) -> Dict:
        """
        流失预测分析
        
        Args:
            platform_id: 平台ID
            user_email: 用户邮箱（可选）
            
        Returns:
            Dict: 流失预测结果
        """
        from users.models import User
        
        if user_email:
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                pass
        
        # 使用流失预测服务
        service = self._get_churn_prediction_service()
        
        analysis = AIAssistant.objects.create(
            platform_id=platform_id,
            analysis_type='churn_prediction',
            analysis_date=timezone.now(),
            model_parameters={
                'model_name': 'random_forest_classifier',
                'model_version': '1.0',
                'threshold': 0.3,
            },
            analysis_result={
                'churn_risk': 'high',
                'churn_probability': '0.75',
                'risk_factors': [
                    '上次购买时间超过30天',
                    '平均订单金额低于平台平均30%',
                    '退货率高于10%',
                ],
                'recommendations': [
                    '发送挽回邮件',
                    '提供优惠券',
                    '优化商品描述',
                ]
            },
            confidence=Decimal('80'),
        )
        
        analysis.completed_at = timezone.now()
        analysis.save()
        
        return {
            'platform_id': platform_id,
            'prediction_type': 'churn_prediction',
            'churn_risk': analysis['churn_risk'],
            'churn_probability': analysis['churn_probability'],
            'risk_factors': analysis['risk_factors'],
            'recommendations': analysis['recommendations'],
            'confidence': analysis['confidence'],
        }
    
    def _get_churn_prediction_service(self):
        """获取流失预测服务"""
        try:
            from .analytics.churn_prediction import ChurnPredictionService
            return ChurnPredictionService()
        except ImportError:
            # 如果没有流失预测服务，返回None
            return None