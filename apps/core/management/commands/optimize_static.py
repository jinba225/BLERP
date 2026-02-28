"""
优化静态资源命令

合并和压缩CSS和JavaScript文件，减少页面加载时间。
"""

import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """优化静态资源"""

    help = "合并和压缩静态资源，减少页面加载时间"

    def add_arguments(self, parser):
        """添加命令参数"""
        parser.add_argument("--minify", action="store_true", default=True, help="是否压缩静态文件")
        parser.add_argument(
            "--output-dir",
            type=str,
            default=os.path.join(settings.STATIC_ROOT, "optimized"),
            help="优化后静态文件的输出目录",
        )

    def handle(self, *args, **options):
        """执行命令"""
        minify = options["minify"]
        output_dir = options["output_dir"]

        self.stdout.write(self.style.SUCCESS(f"开始优化静态资源，输出目录: {output_dir}"))

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 合并和压缩CSS文件
        css_files = [
            os.path.join(settings.STATIC_ROOT, "css", "components", "output.css"),
            os.path.join(settings.STATIC_ROOT, "css", "layouts", "admin_overrides.css"),
        ]

        if all(os.path.exists(css_file) for css_file in css_files):
            self.stdout.write("合并和压缩CSS文件...")
            self._optimize_css(css_files, os.path.join(output_dir, "combined.css"), minify)
        else:
            self.stdout.write(self.style.WARNING("部分CSS文件不存在，跳过CSS优化"))

        # 合并和压缩JavaScript文件
        js_files = [
            os.path.join(settings.STATIC_ROOT, "js", "searchable-utils.js"),
            os.path.join(settings.STATIC_ROOT, "js", "components", "theme.js"),
            os.path.join(settings.STATIC_ROOT, "js", "layouts", "logo-responsive.js"),
        ]

        if all(os.path.exists(js_file) for js_file in js_files):
            self.stdout.write("合并和压缩JavaScript文件...")
            self._optimize_js(js_files, os.path.join(output_dir, "combined.js"), minify)
        else:
            self.stdout.write(self.style.WARNING("部分JavaScript文件不存在，跳过JavaScript优化"))

        # 优化第三方库
        self.stdout.write("优化第三方库...")
        self._optimize_third_party_libraries(output_dir)

        # 生成资源版本号，用于缓存控制
        version_file = os.path.join(output_dir, "version.txt")
        import time

        version = str(int(time.time()))
        with open(version_file, "w") as f:
            f.write(version)

        self.stdout.write(self.style.SUCCESS(f"生成资源版本号: {version}"))

        # 生成优化报告
        self._generate_report(output_dir)

        self.stdout.write(self.style.SUCCESS("静态资源优化完成"))

    def _optimize_css(self, css_files, output_file, minify):
        """合并和压缩CSS文件"""
        try:
            # 合并CSS文件
            with open(output_file, "w", encoding="utf-8") as out:
                for css_file in css_files:
                    with open(css_file, "r", encoding="utf-8") as f:
                        out.write(f.read())
                        out.write("\n")

            # 压缩CSS文件
            if minify:
                try:
                    # 使用Python内置方法压缩
                    from csscompressor import compress

                    with open(output_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    compressed_content = compress(content)
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(compressed_content)
                    self.stdout.write(self.style.SUCCESS(f"  压缩CSS文件: {output_file}"))
                except ImportError:
                    self.stdout.write(self.style.WARNING("  csscompressor库未安装，跳过CSS压缩"))

            original_size = sum(os.path.getsize(f) for f in css_files)
            optimized_size = os.path.getsize(output_file)
            reduction = (
                ((original_size - optimized_size) / original_size * 100) if original_size > 0 else 0
            )

            self.stdout.write(self.style.SUCCESS(f"  原始大小: {original_size} bytes"))
            self.stdout.write(self.style.SUCCESS(f"  优化后大小: {optimized_size} bytes"))
            self.stdout.write(self.style.SUCCESS(f"  减少: {reduction:.2f}%"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  优化CSS文件失败: {e}"))

    def _optimize_js(self, js_files, output_file, minify):
        """合并和压缩JavaScript文件"""
        try:
            # 合并JavaScript文件
            with open(output_file, "w", encoding="utf-8") as out:
                for js_file in js_files:
                    with open(js_file, "r", encoding="utf-8") as f:
                        out.write(f.read())
                        out.write("\n")

            # 压缩JavaScript文件
            if minify:
                try:
                    # 使用Python内置方法压缩
                    from jsmin import jsmin

                    with open(output_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    compressed_content = jsmin(content)
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(compressed_content)
                    self.stdout.write(self.style.SUCCESS(f"  压缩JavaScript文件: {output_file}"))
                except ImportError:
                    self.stdout.write(self.style.WARNING("  jsmin库未安装，跳过JavaScript压缩"))

            original_size = sum(os.path.getsize(f) for f in js_files)
            optimized_size = os.path.getsize(output_file)
            reduction = (
                ((original_size - optimized_size) / original_size * 100) if original_size > 0 else 0
            )

            self.stdout.write(self.style.SUCCESS(f"  原始大小: {original_size} bytes"))
            self.stdout.write(self.style.SUCCESS(f"  优化后大小: {optimized_size} bytes"))
            self.stdout.write(self.style.SUCCESS(f"  减少: {reduction:.2f}%"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  优化JavaScript文件失败: {e}"))

    def _optimize_third_party_libraries(self, output_dir):
        """优化第三方库"""
        third_party_files = [
            ("alpinejs.min.js", "https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"),
        ]

        for filename, url in third_party_files:
            output_path = os.path.join(output_dir, filename)
            try:
                import requests

                response = requests.get(url, timeout=30)
                response.raise_for_status()
                with open(output_path, "wb") as f:
                    f.write(response.content)
                self.stdout.write(self.style.SUCCESS(f"  下载第三方库: {filename}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  下载第三方库失败: {e}"))

    def _generate_report(self, output_dir):
        """生成优化报告"""
        report_file = os.path.join(output_dir, "optimization_report.txt")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("静态资源优化报告\n")
            f.write("=" * 50 + "\n")

            # 统计优化后的文件大小
            total_size = 0
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    if file not in ["version.txt", "optimization_report.txt"]:
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        total_size += size
                        f.write(f"{file}: {size} bytes\n")

            f.write("=" * 50 + "\n")
            f.write(f"总计: {total_size} bytes\n")

        self.stdout.write(self.style.SUCCESS(f"生成优化报告: {report_file}"))
