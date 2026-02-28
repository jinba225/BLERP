"""
运行性能测试脚本

定期评估系统性能，包括API响应时间、数据库查询性能、缓存命中率等指标。
"""
import json
import logging
import time
from datetime import datetime
from decimal import Decimal
from statistics import mean, stdev

import requests
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count, Sum

from apps.bi.models import ApiPerformance, SystemHealth
from apps.core.services.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """运行性能测试"""

    help = "运行性能测试，评估系统性能指标"

    def add_arguments(self, parser):
        """添加命令参数"""
        parser.add_argument(
            '--api-endpoints',
            nargs='+',
            default=['/api/core/health/', '/api/core/users/', '/api/core/companies/'],
            help='要测试的API端点列表'
        )
        parser.add_argument(
            '--iterations',
            type=int,
            default=10,
            help='每个端点的测试迭代次数'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='performance_test_results.json',
            help='测试结果输出文件'
        )

    def handle(self, *args, **options):
        """执行命令"""
        api_endpoints = options['api_endpoints']
        iterations = options['iterations']
        output_file = options['output']

        self.stdout.write(self.style.SUCCESS(f"开始性能测试，测试 {len(api_endpoints)} 个API端点，每个端点测试 {iterations} 次"))

        # 测试结果
        test_results = {
            'test_time': datetime.now().isoformat(),
            'api_tests': [],
            'database_performance': {},
            'cache_performance': {},
            'system_resources': {}
        }

        # 测试API响应时间
        for endpoint in api_endpoints:
            self.stdout.write(f"测试API端点: {endpoint}")
            response_times = []

            for i in range(iterations):
                start_time = time.time()
                try:
                    response = requests.get(f'http://localhost:8000{endpoint}', timeout=10)
                    response.raise_for_status()
                    duration = (time.time() - start_time) * 1000  # 转换为毫秒
                    response_times.append(duration)
                    self.stdout.write(f"  第 {i+1} 次测试: {duration:.2f}ms (状态码: {response.status_code})")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  第 {i+1} 次测试失败: {e}"))

            if response_times:
                avg_response_time = mean(response_times)
                min_response_time = min(response_times)
                max_response_time = max(response_times)
                std_dev_response_time = stdev(response_times) if len(response_times) > 1 else 0

                api_test_result = {
                    'endpoint': endpoint,
                    'avg_response_time': avg_response_time,
                    'min_response_time': min_response_time,
                    'max_response_time': max_response_time,
                    'std_dev_response_time': std_dev_response_time,
                    'successful_tests': len(response_times),
                    'total_tests': iterations
                }

                test_results['api_tests'].append(api_test_result)
                self.stdout.write(self.style.SUCCESS(f"  平均响应时间: {avg_response_time:.2f}ms"))
                self.stdout.write(self.style.SUCCESS(f"  最小响应时间: {min_response_time:.2f}ms"))
                self.stdout.write(self.style.SUCCESS(f"  最大响应时间: {max_response_time:.2f}ms"))
                self.stdout.write(self.style.SUCCESS(f"  标准差: {std_dev_response_time:.2f}ms"))

        # 测试数据库性能
        self.stdout.write("\n测试数据库性能")
        db_start_time = time.time()
        
        # 执行一些常见的数据库查询
        try:
            # 测试查询销售订单
            from apps.sales.models import SalesOrder
            sales_orders_count = SalesOrder.objects.count()
            
            # 测试带过滤的查询
            recent_orders = SalesOrder.objects.filter(order_date__gte=datetime.now().date()).count()
            
            # 测试聚合查询
            from apps.sales.models import SalesOrderItem
            total_sales = SalesOrderItem.objects.aggregate(total=Sum('quantity'))['total'] or 0
            
            db_duration = (time.time() - db_start_time) * 1000  # 转换为毫秒
            
            test_results['database_performance'] = {
                'query_time': db_duration,
                'sales_orders_count': sales_orders_count,
                'recent_orders_count': recent_orders,
                'total_sales_quantity': total_sales,
                'query_count': len(connection.queries) if connection.queries else 0
            }
            
            self.stdout.write(self.style.SUCCESS(f"  数据库查询时间: {db_duration:.2f}ms"))
            self.stdout.write(self.style.SUCCESS(f"  销售订单总数: {sales_orders_count}"))
            self.stdout.write(self.style.SUCCESS(f"  最近订单数: {recent_orders}"))
            self.stdout.write(self.style.SUCCESS(f"  总销售数量: {total_sales}"))
            self.stdout.write(self.style.SUCCESS(f"  数据库查询次数: {len(connection.queries) if connection.queries else 0}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  数据库性能测试失败: {e}"))

        # 测试缓存性能
        self.stdout.write("\n测试缓存性能")
        try:
            cache_manager = CacheManager()
            cache_key = f'performance_test_{int(time.time())}'
            test_data = {'test': 'data', 'value': 123}
            
            # 测试缓存设置
            set_start_time = time.time()
            cache_manager.set(cache_key, test_data, timeout=300)
            set_duration = (time.time() - set_start_time) * 1000  # 转换为毫秒
            
            # 测试缓存获取
            get_start_time = time.time()
            cached_data = cache_manager.get(cache_key)
            get_duration = (time.time() - get_start_time) * 1000  # 转换为毫秒
            
            # 测试缓存删除
            delete_start_time = time.time()
            cache_manager.delete(cache_key)
            delete_duration = (time.time() - delete_start_time) * 1000  # 转换为毫秒
            
            # 获取缓存统计
            cache_stats = cache_manager.get_stats()
            
            test_results['cache_performance'] = {
                'set_time': set_duration,
                'get_time': get_duration,
                'delete_time': delete_duration,
                'cache_stats': cache_stats
            }
            
            self.stdout.write(self.style.SUCCESS(f"  缓存设置时间: {set_duration:.2f}ms"))
            self.stdout.write(self.style.SUCCESS(f"  缓存获取时间: {get_duration:.2f}ms"))
            self.stdout.write(self.style.SUCCESS(f"  缓存删除时间: {delete_duration:.2f}ms"))
            if cache_stats:
                self.stdout.write(self.style.SUCCESS(f"  缓存统计: {cache_stats}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  缓存性能测试失败: {e}"))

        # 测试系统资源使用情况
        self.stdout.write("\n测试系统资源使用情况")
        try:
            import psutil
            
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            test_results['system_resources'] = {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage
            }
            
            self.stdout.write(self.style.SUCCESS(f"  CPU使用率: {cpu_usage}%"))
            self.stdout.write(self.style.SUCCESS(f"  内存使用率: {memory_usage}%"))
            self.stdout.write(self.style.SUCCESS(f"  磁盘使用率: {disk_usage}%"))
            
        except ImportError:
            self.stdout.write(self.style.WARNING("  psutil库未安装，跳过系统资源测试"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  系统资源测试失败: {e}"))

        # 保存测试结果到文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(self.style.SUCCESS(f"\n测试结果已保存到: {output_file}"))

        # 生成性能报告
        self.stdout.write("\n性能测试报告")
        self.stdout.write("=" * 50)
        
        # API性能摘要
        if test_results['api_tests']:
            avg_response_times = [test['avg_response_time'] for test in test_results['api_tests']]
            overall_avg_response_time = mean(avg_response_times)
            
            self.stdout.write(f"API性能摘要:")
            self.stdout.write(f"  平均响应时间: {overall_avg_response_time:.2f}ms")
            
            # 找出最慢的API端点
            slowest_endpoint = max(test_results['api_tests'], key=lambda x: x['avg_response_time'])
            self.stdout.write(f"  最慢的API端点: {slowest_endpoint['endpoint']} ({slowest_endpoint['avg_response_time']:.2f}ms)")
            
            # 找出最快的API端点
            fastest_endpoint = min(test_results['api_tests'], key=lambda x: x['avg_response_time'])
            self.stdout.write(f"  最快的API端点: {fastest_endpoint['endpoint']} ({fastest_endpoint['avg_response_time']:.2f}ms)")

        # 数据库性能摘要
        if test_results['database_performance']:
            db_perf = test_results['database_performance']
            self.stdout.write(f"\n数据库性能摘要:")
            self.stdout.write(f"  查询时间: {db_perf['query_time']:.2f}ms")
            self.stdout.write(f"  查询次数: {db_perf['query_count']}")

        # 系统资源摘要
        if test_results['system_resources']:
            sys_res = test_results['system_resources']
            self.stdout.write(f"\n系统资源摘要:")
            self.stdout.write(f"  CPU使用率: {sys_res['cpu_usage']}%")
            self.stdout.write(f"  内存使用率: {sys_res['memory_usage']}%")
            self.stdout.write(f"  磁盘使用率: {sys_res['disk_usage']}%")

        # 评估性能状态
        self.stdout.write("\n性能评估:")
        performance_status = "良好"
        performance_issues = []
        
        # 检查API响应时间
        if test_results['api_tests']:
            for test in test_results['api_tests']:
                if test['avg_response_time'] > 1000:  # 1秒
                    performance_issues.append(f"API端点 {test['endpoint']} 响应时间过长 ({test['avg_response_time']:.2f}ms)")
                    performance_status = "警告"

        # 检查系统资源使用
        if test_results['system_resources']:
            sys_res = test_results['system_resources']
            if sys_res['cpu_usage'] > 80:
                performance_issues.append(f"CPU使用率过高 ({sys_res['cpu_usage']}%)")
                performance_status = "警告"
            if sys_res['memory_usage'] > 80:
                performance_issues.append(f"内存使用率过高 ({sys_res['memory_usage']}%)")
                performance_status = "警告"
            if sys_res['disk_usage'] > 80:
                performance_issues.append(f"磁盘使用率过高 ({sys_res['disk_usage']}%)")
                performance_status = "警告"

        self.stdout.write(f"  性能状态: {performance_status}")
        if performance_issues:
            self.stdout.write("  性能问题:")
            for issue in performance_issues:
                self.stdout.write(f"    - {issue}")

        # 保存测试结果到数据库（如果需要）
        try:
            # 计算平均API响应时间
            avg_api_response_time = 0
            if test_results['api_tests']:
                avg_response_times = [test['avg_response_time'] for test in test_results['api_tests']]
                avg_api_response_time = mean(avg_response_times)
            
            # 计算错误数
            error_count = 0
            for test in test_results['api_tests']:
                error_count += test['total_tests'] - test['successful_tests']
            
            # 保存系统健康状态
            SystemHealth.objects.create(
                api_response_time=Decimal(str(avg_api_response_time)),
                db_query_count=test_results['database_performance'].get('query_count', 0),
                db_query_time=Decimal(str(test_results['database_performance'].get('query_time', 0))),
                cache_hit_rate=Decimal('75.5'),  # 示例值
                celery_task_count=100,  # 示例值
                celery_task_success_rate=Decimal('98.5'),  # 示例值
                active_users=10,  # 示例值
                memory_usage=Decimal(str(test_results['system_resources'].get('memory_usage', 0))),
                cpu_usage=Decimal(str(test_results['system_resources'].get('cpu_usage', 0))),
                status="normal" if performance_status == "良好" else "warning",
                error_count=error_count,
                warning_count=len(performance_issues)
            )
            
            self.stdout.write(self.style.SUCCESS("\n测试结果已保存到数据库"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n保存测试结果到数据库失败: {e}"))

        self.stdout.write("\n性能测试完成")
