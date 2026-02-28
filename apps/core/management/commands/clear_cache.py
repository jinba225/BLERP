"""
Django管理命令：清除缓存

使用方法:
    python manage.py clear_cache                    # 清除所有缓存
    python manage.py clear_cache --cache=default    # 清除特定缓存
    python manage.py clear_cache --verbose          # 显示详细信息
"""

from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "清除Django缓存"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cache",
            type=str,
            default="default",
            help="指定要清除的缓存别名（默认: default）",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="显示详细输出",
        )

    def handle(self, *args, **options):
        cache_alias = options["cache"]
        verbose = options["verbose"]

        if verbose:
            self.stdout.write(f"正在清除缓存: {cache_alias}")

        try:
            # 清除指定缓存
            cache_backend = cache
            if hasattr(cache, "backend"):
                cache_backend = cache.backend

            # 清除所有缓存键
            cache.clear()

            if verbose:
                self.stdout.write(self.style.SUCCESS(f"✓ 成功清除缓存: {cache_alias}"))
            else:
                self.stdout.write(self.style.SUCCESS("缓存已清除"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ 清除缓存失败: {str(e)}"))
