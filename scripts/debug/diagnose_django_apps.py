"""
Django应用注册诊断脚本
"""

import os
import sys

# 添加apps目录到Python路径
apps_dir = os.path.join(os.path.dirname(__file__), "..", "apps")
if apps_dir not in sys.path:
    sys.path.insert(0, apps_dir)

print(f"Python路径: {sys.path[:3]}")

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_erp.settings")

import django

print(f"设置Django settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")

# 尝试导入settings
try:
    from django.conf import settings

    print(f"✓ 成功导入settings")
    print(
        f"  INSTALLED_APPS包含: {[app for app in settings.INSTALLED_APPS if 'purchase' in app or 'suppliers' in app]}"
    )
except Exception as e:
    print(f"✗ 无法导入settings: {e}")
    sys.exit(1)

# 尝试setup Django
try:
    django.setup()
    print(f"✓ 成功执行django.setup()")
except Exception as e:
    print(f"✗ django.setup()失败: {e}")
    sys.exit(1)

# 尝试导入应用配置
try:
    from django.apps import apps

    print(f"✓ 成功导入apps registry")

    # 检查purchase应用是否注册
    if "purchase" in apps.app_configs:
        config = apps.app_configs["purchase"]
        print(f"✓ purchase应用已注册:")
        print(f"  name: {config.name}")
        print(f"  module: {config.module}")
    else:
        print(f"✗ purchase应用未注册")
        print(f"  已注册的应用: {list(apps.app_configs.keys())}")
except Exception as e:
    print(f"✗ 无法检查应用注册: {e}")

# 尝试导入模型
try:
    from apps.purchase.models import PurchaseOrder

    print(f"✓ 成功导入PurchaseOrder模型")
except Exception as e:
    print(f"✗ 无法导入PurchaseOrder: {e}")
    print(f"\n诊断信息:")
    print(f"  sys.path包含apps目录: {apps_dir in sys.path}")

    # 尝试直接导入purchase模块
    try:
        import purchase

        print(f"  可以导入purchase模块")
        print(f"  purchase模块位置: {purchase.__file__}")
    except Exception as e2:
        print(f"  无法导入purchase模块: {e2}")

    # 尝试导入purchase.models
    try:
        from purchase import models as purchase_models

        print(f"  可以从purchase导入models")
    except Exception as e3:
        print(f"  无法从purchase导入models: {e3}")

print("\n=== 诊断完成 ===")
