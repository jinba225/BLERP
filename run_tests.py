#!/usr/bin/env python
"""
Django ERP 测试运行脚本

由于目录结构重组（apps/），Django 的测试发现器存在问题。
这个脚本提供了替代的测试运行方式。

使用方式:
    python run_tests.py              # 运行所有测试
    python run_tests.py collect      # 运行特定应用的测试
    python run_tests.py collect.tests.test_models.PlatformModelTest  # 运行特定测试
"""

import os
import sys
from pathlib import Path

from django.conf import settings
from django.test.utils import get_runner

# 添加项目根目录到路径
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# 添加 apps/ 到路径
APPS_DIR = BASE_DIR / "apps"
sys.path.insert(0, str(APPS_DIR))

# 设置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")

import django  # noqa: E402

django.setup()


def run_tests(test_labels=None, verbosity=2, keepdb=False):
    """
    运行测试

    Args:
        test_labels: 测试标签列表（如 ['collect', 'sales']）
        verbosity: 详细程度（0-2）
        keepdb: 是否保留测试数据库
    """
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=verbosity, interactive=False, keepdb=keepdb)

    if not test_labels:
        # 如果没有指定标签，运行所有测试
        test_labels = []

    failures = test_runner.run_tests(test_labels)

    return failures


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Django ERP 测试运行器")
    parser.add_argument("labels", nargs="*", help="测试标签（应用名、模块名或测试类名）")
    parser.add_argument(
        "-v",
        "--verbosity",
        type=int,
        default=2,
        choices=[0, 1, 2, 3],
        help="输出详细程度",
    )
    parser.add_argument("-k", "--keepdb", action="store_true", help="保留测试数据库")

    args = parser.parse_args()

    # 转换标签格式
    # 如果用户输入 'collect'，我们转换为 'collect'
    # 如果用户输入 'collect.tests.test_models'，我们保持不变
    test_labels = []
    for label in args.labels:
        # 移除 'apps.' 前缀（如果有）
        if label.startswith("apps."):
            label = label[5:]
        test_labels.append(label)

    print(f"🧪 运行测试: {test_labels if test_labels else '所有测试'}")
    print(f"📂 应用目录: {APPS_DIR}")
    print()

    failures = run_tests(test_labels=test_labels, verbosity=args.verbosity, keepdb=args.keepdb)

    sys.exit(bool(failures))
