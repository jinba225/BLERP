"""
Django管理命令：查看缓存统计信息

使用方法:
    python manage.py cache_stats                    # 显示缓存统计
    python manage.py cache_stats --cache=default    # 查看特定缓存统计
"""
from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "显示缓存统计信息"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cache",
            type=str,
            default="default",
            help="指定要查看的缓存别名（默认: default）",
        )

    def handle(self, *args, **options):
        cache_alias = options["cache"]

        self.stdout.write(f'\n{"=" * 60}')
        self.stdout.write(f"缓存统计信息: {cache_alias}")
        self.stdout.write(f'{"=" * 60}\n')

        try:
            # 获取缓存后端信息
            cache_backend = cache
            if hasattr(cache, "backend"):
                cache_backend = cache.backend

            # 缓存类型
            cache_class = cache_backend.__class__.__name__
            self.stdout.write(f"缓存类型: {cache_class}")

            # 尝试获取缓存配置信息
            if hasattr(cache_backend, "options"):
                options = cache_backend.options
                if "LOCATION" in options or "location" in options:
                    location = options.get("LOCATION") or options.get("location", "N/A")
                    self.stdout.write(f"缓存位置: {location}")

                if "TIMEOUT" in options or "timeout" in options:
                    timeout = options.get("TIMEOUT") or options.get("timeout", "N/A")
                    self.stdout.write(f"默认超时: {timeout} 秒")

                if "KEY_PREFIX" in options or "key_prefix" in options:
                    key_prefix = options.get("KEY_PREFIX") or options.get("key_prefix", "N/A")
                    self.stdout.write(f"键前缀: {key_prefix}")

            # 测试缓存连接
            test_key = "__django_erp_cache_test__"
            cache.set(test_key, "test", 10)
            if cache.get(test_key) == "test":
                self.stdout.write(self.style.SUCCESS("✓ 缓存状态: 正常运行"))
                cache.delete(test_key)
            else:
                self.stdout.write(self.style.WARNING("⚠ 缓存状态: 可能存在问题"))

            self.stdout.write(f'\n{"=" * 60}\n')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ 获取缓存信息失败: {str(e)}"))
            self.stdout.write("\n提示: 请确保缓存已正确配置\n")
