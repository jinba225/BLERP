#!/usr/bin/env python
"""
检查模型和迁移是否同步

找出所有在迁移中添加但模型中缺失的字段
"""
import os
import sys
import re
from pathlib import Path

# 设置 Django 环境
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")

import django

django.setup()

from django.db import models
from django.apps import apps


def get_migration_fields():
    """从迁移文件中提取字段定义"""
    migration_fields = {}

    migrations_dir = Path(__file__).parent / "apps" / "inventory" / "migrations"

    for migration_file in migrations_dir.glob("*.py"):
        if migration_file.name.startswith("__") or migration_file.name == "__init__.py":
            continue

        content = migration_file.read_text()

        # 查找 AddField 操作
        add_field_pattern = r"migrations\.AddField\(\s*model_name='([^']+)',\s*name='([^']+)',"
        matches = re.findall(add_field_pattern, content)

        for model_name, field_name in matches:
            key = f"{model_name}.{field_name}"
            if key not in migration_fields:
                migration_fields[key] = {
                    "file": migration_file.name,
                    "model": model_name,
                    "field": field_name,
                }

    return migration_fields


def get_model_fields():
    """从模型定义中提取字段"""
    model_fields = {}

    # 获取所有 inventory 应用的模型
    for model in apps.get_app_config("inventory").get_models():
        model_name = model._meta.model_name

        for field in model._meta.get_fields():
            if hasattr(field, "name"):
                key = f"{model_name}.{field.name}"
                model_fields[key] = {
                    "model": model_name,
                    "field": field.name,
                    "type": type(field).__name__,
                }

    return model_fields


def main():
    print("=" * 60)
    print("检查模型和迁移的同步情况")
    print("=" * 60)

    # 获取迁移中的字段
    migration_fields = get_migration_fields()
    print(f"\n迁移文件中找到 {len(migration_fields)} 个字段")

    # 获取模型中的字段
    model_fields = get_model_fields()
    print(f"模型定义中找到 {len(model_fields)} 个字段")

    # 检查缺失的字段
    missing_fields = []
    for key, info in migration_fields.items():
        if key not in model_fields:
            missing_fields.append(info)

    if missing_fields:
        print(f"\n❌ 发现 {len(missing_fields)} 个缺失字段:")
        print("-" * 60)
        for field_info in missing_fields:
            print(f"  模型: {field_info['model']}")
            print(f"  字段: {field_info['field']}")
            print(f"  迁移文件: {field_info['file']}")
            print()
    else:
        print("\n✅ 所有迁移字段都在模型中定义")

    # 检查额外的字段（模型中有但迁移中没有的）
    extra_fields = []
    for key, info in model_fields.items():
        if key not in migration_fields and not info["field"].startswith("_"):
            # 排除基类字段和反向关系
            if info["type"] not in ["ManyToManyRel", "ManyToOneRel"]:
                extra_fields.append(info)

    if extra_fields:
        print(f"\n⚠️  发现 {len(extra_fields)} 个可能缺少迁移的字段:")
        print("-" * 60)
        for field_info in extra_fields[:10]:  # 只显示前10个
            print(f"  模型: {field_info['model']}")
            print(f"  字段: {field_info['field']}")
            print(f"  类型: {field_info['type']}")
            print()
        if len(extra_fields) > 10:
            print(f"  ... 还有 {len(extra_fields) - 10} 个字段")
    else:
        print("\n✅ 所有模型字段都有对应的迁移")

    return len(missing_fields) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
