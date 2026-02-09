from django.core.management.base import BaseCommand
from apps.core.models import Platform, SyncStrategy


class Command(BaseCommand):
    """初始化电商同步模块"""

    help = '初始化电商同步模块，创建默认平台和同步策略'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化电商同步模块...')

        # 创建默认平台
        self._create_default_platforms()

        # 创建默认同步策略
        self._create_default_strategies()

        self.stdout.write(self.style.SUCCESS('电商同步模块初始化完成！'))

    def _create_default_platforms(self):
        """创建默认电商平台"""
        platforms_data = [
            {
                'platform_type': 'taobao',
                'name': '淘宝',
                'base_url': 'https://item.taobao.com',
                'description': '淘宝电商平台',
            },
            {
                'platform_type': 'alibaba',
                'name': '1688',
                'base_url': 'https://detail.1688.com',
                'description': '阿里巴巴1688平台',
            },
        ]

        for data in platforms_data:
            platform, created = Platform.objects.get_or_create(
                platform_type=data['platform_type'],
                defaults={
                    'name': data['name'],
                    'base_url': data['base_url'],
                    'description': data['description'],
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  创建平台: {platform.name}')
                )
            else:
                self.stdout.write(f'  平台已存在: {platform.name}')

    def _create_default_strategies(self):
        """创建默认同步策略"""
        platforms = Platform.objects.all()

        strategies_data = [
            {
                'name': '每日增量同步',
                'strategy_type': 'incremental',
                'update_fields': ['price', 'stock', 'status'],
                'sync_interval_hours': 24,
                'batch_size': 100,
            },
            {
                'name': '每周全量同步',
                'strategy_type': 'full',
                'update_fields': ['price', 'stock', 'status', 'detail'],
                'sync_interval_hours': 168,  # 7天
                'batch_size': 50,
            },
            {
                'name': '价格监控',
                'strategy_type': 'price_only',
                'update_fields': ['price'],
                'sync_interval_hours': 1,
                'batch_size': 200,
            },
        ]

        for platform in platforms:
            for strategy_data in strategies_data:
                strategy, created = SyncStrategy.objects.get_or_create(
                    platform=platform,
                    name=f"{platform.name}_{strategy_data['name']}",
                    defaults={
                        'strategy_type': strategy_data['strategy_type'],
                        'update_fields': strategy_data['update_fields'],
                        'sync_interval_hours': strategy_data['sync_interval_hours'],
                        'batch_size': strategy_data['batch_size'],
                    }
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'  创建策略: {strategy.name}')
                    )
                else:
                    self.stdout.write(f'  策略已存在: {strategy.name}')
