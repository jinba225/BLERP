#!/usr/bin/env python
"""
统一入库和出库单据前缀

执行方式：
    python manage.py shell < scripts/unify_document_prefixes.py
"""

from core.models import SystemConfig

# 需要更新的配置项
updates = [
    {
        "key": "document_prefix_sales_return",
        "old_value": "SR",
        "new_value": "IN",
        "description": "销售退货前缀 - 销售退货单的单号前缀（Sales Return - Inbound）",
    },
    {
        "key": "document_prefix_material_return",
        "old_value": "MTR",
        "new_value": "IN",
        "description": "退料单前缀 - 生产退料单的单号前缀（Material Return - Inbound）",
    },
    {
        "key": "document_prefix_purchase_return",
        "old_value": "ROUT",
        "new_value": "OUT",
        "description": "采购退货前缀 - 采购退货单的单号前缀（Purchase Return - Outbound）",
    },
    {
        "key": "document_prefix_material_requisition",
        "old_value": "MR",
        "new_value": "OUT",
        "description": "领料单前缀 - 生产领料单的单号前缀（Material Requisition - Outbound）",
    },
]

print("=" * 60)
print("统一入库和出库单据前缀")
print("=" * 60)
print()

for update in updates:
    try:
        config = SystemConfig.objects.get(key=update["key"])
        print(f"✓ 找到配置: {update['key']}")
        print(f"  当前值: {config.value}")
        print(f"  新值: {update['new_value']}")

        if config.value != update["new_value"]:
            config.value = update["new_value"]
            config.description = update["description"]
            config.save()
            print(f"  ✅ 已更新")
        else:
            print(f"  ⏭️  无需更新（已经是目标值）")
        print()
    except SystemConfig.DoesNotExist:
        print(f"⚠️  配置不存在: {update['key']}")
        print(f"  将创建新配置...")
        SystemConfig.objects.create(
            key=update["key"],
            value=update["new_value"],
            config_type="business",
            description=update["description"],
            is_active=True,
        )
        print(f"  ✅ 已创建")
        print()

print("=" * 60)
print("统一完成！")
print("=" * 60)
print()
print("入库单据（IN 前缀）：")
print("  - receipt (采购收货单)")
print("  - stock_in (入库单)")
print("  - sales_return (销售退货)")
print("  - material_return (退料单)")
print()
print("出库单据（OUT 前缀）：")
print("  - delivery (销售发货单)")
print("  - stock_out (出库单)")
print("  - purchase_return (采购退货)")
print("  - material_requisition (领料单)")
print()
print("通过 transaction_type 字段区分具体的单据类型。")
