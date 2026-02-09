"""
Django管理命令：预热常用页面缓存

使用方法:
    python manage.py warm_cache                    # 预热缓存
    python manage.py warm_cache --verbose          # 显示详细信息
"""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse


class Command(BaseCommand):
    help = "预热常用页面缓存"

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="显示详细输出",
        )

    def handle(self, *args, **options):
        verbose = options["verbose"]

        self.stdout.write("\n开始预热缓存...\n")

        # 常用页面列表（无需认证的页面）
        pages = [
            ("login", "登录页面"),
            ("core:dashboard", "仪表板"),
        ]

        # 尝试使用测试用户访问需要认证的页面
        User = get_user_model()
        test_user = User.objects.filter(is_superuser=True).first()

        client = Client()

        if test_user:
            client.force_login(test_user)
            if verbose:
                self.stdout.write(f"使用测试用户: {test_user.username}\n")

        success_count = 0
        fail_count = 0

        for url_name, description in pages:
            try:
                url = reverse(url_name)
                response = client.get(url)

                if response.status_code == 200:
                    success_count += 1
                    if verbose:
                        self.stdout.write(self.style.SUCCESS(f"✓ {description} ({url_name})"))
                else:
                    fail_count += 1
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠ {description} ({url_name}) - 状态码: {response.status_code}"
                            )
                        )

            except Exception as e:
                fail_count += 1
                if verbose:
                    self.stdout.write(self.style.ERROR(f"✗ {description} ({url_name}) - {str(e)}"))

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f"预热完成: 成功 {success_count}, 失败 {fail_count}")
        self.stdout.write(f'{"="*60}\n')
