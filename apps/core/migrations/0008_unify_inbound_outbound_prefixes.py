# Generated manually to unify inbound/outbound document prefixes
from django.db import migrations


def create_unified_prefix_configs(apps, schema_editor):
    """创建统一的入库/出库单据前缀配置"""
    SystemConfig = apps.get_model("core", "SystemConfig")

    # 入库单据前缀配置（统一为 IN）
    inbound_configs = [
        {
            "key": "document_prefix_receipt",
            "value": "IN",
            "config_type": "business",
            "description": "采购收货单前缀（入库）",
        },
        {
            "key": "document_prefix_stock_in",
            "value": "IN",
            "config_type": "business",
            "description": "入库单前缀（入库）",
        },
        {
            "key": "document_prefix_sales_return",
            "value": "IN",
            "config_type": "business",
            "description": "销售退货单前缀（入库）",
        },
        {
            "key": "document_prefix_material_return",
            "value": "IN",
            "config_type": "business",
            "description": "退料单前缀（入库）",
        },
    ]

    # 出库单据前缀配置（统一为 OUT）
    outbound_configs = [
        {
            "key": "document_prefix_delivery",
            "value": "OUT",
            "config_type": "business",
            "description": "销售发货单前缀（出库）",
        },
        {
            "key": "document_prefix_stock_out",
            "value": "OUT",
            "config_type": "business",
            "description": "出库单前缀（出库）",
        },
        {
            "key": "document_prefix_purchase_return",
            "value": "OUT",
            "config_type": "business",
            "description": "采购退货单前缀（出库）",
        },
        {
            "key": "document_prefix_material_requisition",
            "value": "OUT",
            "config_type": "business",
            "description": "领料单前缀（出库）",
        },
    ]

    # 创建或更新配置
    for config_data in inbound_configs + outbound_configs:
        config, created = SystemConfig.objects.get_or_create(
            key=config_data["key"],
            defaults={
                "value": config_data["value"],
                "config_type": config_data["config_type"],
                "description": config_data["description"],
                "is_active": True,
            },
        )
        if not created:
            # 如果配置已存在，更新为统一前缀
            config.value = config_data["value"]
            config.description = config_data["description"]
            config.save()


def reverse_unify_prefixes(apps, schema_editor):
    """回滚迁移（删除配置）"""
    SystemConfig = apps.get_model("core", "SystemConfig")

    # 删除统一前缀配置
    keys_to_delete = [
        "document_prefix_receipt",
        "document_prefix_stock_in",
        "document_prefix_sales_return",
        "document_prefix_material_return",
        "document_prefix_delivery",
        "document_prefix_stock_out",
        "document_prefix_purchase_return",
        "document_prefix_material_requisition",
    ]

    SystemConfig.objects.filter(key__in=keys_to_delete).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_add_borrow_prefix_config"),
    ]

    operations = [
        migrations.RunPython(create_unified_prefix_configs, reverse_unify_prefixes),
    ]
