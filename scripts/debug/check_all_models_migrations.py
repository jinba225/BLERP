#!/usr/bin/env python
"""
检查整个项目中所有应用的模型和迁移是否同步

找出所有在迁移中添加但模型中缺失的字段
"""

import os
import re
import sys
from pathlib import Path

# 设置 Django 环境
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")

import django

django.setup()

from django.apps import apps


def check_app_for_missing_fields(app_name):
    """检查单个应用"""
    issues = []

    try:
        app_config = apps.get_app_config(app_name)
        migrations_dir = Path(__file__).parent / "apps" / app_name / "migrations"

        if not migrations_dir.exists():
            return issues

        # 收集所有迁移中的字段
        migration_fields = set()
        for migration_file in migrations_dir.glob("*.py"):
            if migration_file.name.startswith("__") or migration_file.name == "__init__.py":
                continue

            try:
                content = migration_file.read_text()
                # 查找 AddField 操作
                add_field_pattern = (
                    r"migrations\.AddField\(\s*model_name='([^']+)',\s*name='([^']+)',"
                )
                matches = re.findall(add_field_pattern, content)

                for model_name, field_name in matches:
                    migration_fields.add(f"{model_name}.{field_name}")
            except Exception as e:
                pass

        # 收集模型中的字段
        model_fields = set()
        for model in app_config.get_models():
            model_name = model._meta.model_name
            for field in model._meta.get_fields():
                if hasattr(field, "name"):
                    model_fields.add(f"{model_name}.{field.name}")

        # 检查缺失的字段
        missing = migration_fields - model_fields
        if missing:
            issues.append({"app": app_name, "missing_fields": sorted(list(missing))})

    except Exception as e:
        issues.append({"app": app_name, "error": str(e)})

    return issues


def main():
    print("=" * 80)
    print("检查整个项目中所有应用的模型和迁移同步情况")
    print("=" * 80)

    # 获取所有应用
    all_apps = [
        "core",
        "users",
        "authentication",
        "customers",
        "products",
        "inventory",
        "sales",
        "purchase",
        "suppliers",
        "departments",
        "finance",
        "ai_assistant",
        "ecomm_sync",
        "collect",
        "logistics",
        "bi",
    ]

    all_issues = []

    for app_name in all_apps:
        issues = check_app_for_missing_fields(app_name)
        all_issues.extend(issues)

    # 报告结果
    if not all_issues:
        print("\n✅ 所有应用的模型和迁移都是同步的")
        return True
    else:
        print(f"\n❌ 发现 {len(all_issues)} 个应用存在问题:")
        print("=" * 80)

        for issue in all_issues:
            app_name = issue["app"]
            print(f"\n应用: {app_name}")
            print("-" * 80)

            if "error" in issue:
                print(f"  错误: {issue['error']}")
            elif "missing_fields" in issue:
                print(f"  缺失字段数量: {len(issue['missing_fields'])}")
                for field_key in issue["missing_fields"]:
                    print(f"    - {field_key}")

        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
