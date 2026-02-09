"""
Django ERP 数据完整性扫描器

扫描项目代码和数据，识别潜在问题:
1. Decimal字段精度检查
2. 外键级联删除检查
3. 状态流转完整性检查
4. 计算方法正确性检查

使用方法:
    from tests.scanners.scanner_data_integrity import ModelFieldScanner

    scanner = ModelFieldScanner()
    issues = scanner.scan_all()
    scanner.print_report(issues)
"""

from django.apps import apps
from django.db import models


class ModelFieldScanner:
    """模型字段一致性扫描器"""

    def __init__(self):
        """初始化扫描器"""
        self.issues = []
        self.warnings = []

    def scan_decimal_fields(self):
        """
        扫描所有Decimal字段的精度设置

        规则:
        - 金额字段（amount, price, total）应该有足够的精度
        - 建议精度: max_digits >= 12, decimal_places = 2
        """
        issues = []

        for model in apps.get_models():
            for field in model._meta.get_fields():
                if isinstance(field, models.DecimalField):
                    # 检查金额字段
                    if any(
                        keyword in field.name
                        for keyword in ["amount", "price", "total", "quantity"]
                    ):
                        if field.max_digits < 12 or field.decimal_places != 2:
                            issues.append(
                                {
                                    "model": model.__name__,
                                    "field": field.name,
                                    "severity": "warning",
                                    "message": f"字段精度不足: ({field.max_digits}, {field.decimal_places})",
                                    "recommendation": "建议精度: (12, 2) 或 (15, 2)",
                                }
                            )

        self.issues.extend(issues)
        return issues

    def scan_foreign_key_cascades(self):
        """
        扫描外键级联删除设置

        规则:
        - 核心业务数据应该使用 PROTECT，避免误删
        - 金额、数量等计算字段应该谨慎级联
        """
        issues = []

        # 核心业务模型列表
        core_models = [
            "PurchaseOrder",
            "SalesOrder",
            "PurchaseReceipt",
            "SalesDelivery",
            "SupplierAccount",
            "CustomerAccount",
            "InventoryStock",
            "InventoryTransaction",
        ]

        for model in apps.get_models():
            if model.__name__ not in core_models:
                continue

            for field in model._meta.get_fields():
                if isinstance(field, models.ForeignKey):
                    # 检查是否使用 CASCADE
                    if field.remote_field.on_delete == models.CASCADE:
                        issues.append(
                            {
                                "model": model.__name__,
                                "field": field.name,
                                "related_model": field.related_model.__name__,
                                "severity": "warning",
                                "message": f"外键使用 CASCADE 级联删除",
                                "recommendation": "考虑使用 PROTECT 保护核心数据",
                            }
                        )

        self.issues.extend(issues)
        return issues

    def scan_status_transitions(self):
        """
        扫描状态字段的完整性

        规则:
        - 状态字段应该有 choices 定义
        - 应该有明确的状态流转逻辑
        """
        issues = []

        for model in apps.get_models():
            for field in model._meta.get_fields():
                if isinstance(field, models.CharField) and "status" in field.name:
                    # 检查是否有 choices
                    if not field.choices:
                        issues.append(
                            {
                                "model": model.__name__,
                                "field": field.name,
                                "severity": "info",
                                "message": "状态字段没有定义 choices",
                                "recommendation": "建议定义状态枚举",
                            }
                        )

        self.issues.extend(issues)
        return issues

    def scan_calculation_methods(self):
        """
        扫描计算方法的存在性

        规则:
        - 有 total_amount 字段的模型应该有 calculate_totals() 方法
        - 有 line_total 字段的模型应该自动计算
        """
        issues = []

        for model in apps.get_models():
            # 检查是否有 total_amount 字段
            if any(field.name == "total_amount" for field in model._meta.get_fields()):
                # 检查是否有 calculate_totals 方法
                if not hasattr(model, "calculate_totals"):
                    issues.append(
                        {
                            "model": model.__name__,
                            "field": "total_amount",
                            "severity": "warning",
                            "message": "有 total_amount 字段但没有 calculate_totals() 方法",
                            "recommendation": "实现 calculate_totals() 方法自动计算总金额",
                        }
                    )

        self.issues.extend(issues)
        return issues

    def scan_index_optimization(self):
        """
        扫描索引优化机会

        规则:
        - 频繁查询的字段应该有索引
        - 外键字段自动有索引
        """
        issues = []

        for model in apps.get_models():
            # 检查常用的查询字段
            common_query_fields = ["status", "order_date", "created_at"]

            for field_name in common_query_fields:
                try:
                    field = model._meta.get_field(field_name)

                    # 检查是否有 db_index
                    if hasattr(field, "db_index") and not field.db_index:
                        issues.append(
                            {
                                "model": model.__name__,
                                "field": field_name,
                                "severity": "info",
                                "message": "常用查询字段没有索引",
                                "recommendation": f"考虑为 {field_name} 添加索引",
                            }
                        )
                except:
                    pass

        self.issues.extend(issues)
        return issues

    def scan_all(self):
        """运行所有扫描"""
        print("开始扫描...\n")

        print("1. 扫描 Decimal 字段精度...")
        self.scan_decimal_fields()
        print(f"   发现 {len(self.issues)} 个问题\n")

        print("2. 扫描外键级联删除...")
        self.scan_foreign_key_cascades()
        print(f"   发现 {len([i for i in self.issues if i['severity'] == 'warning'])} 个警告\n")

        print("3. 扫描状态流转...")
        self.scan_status_transitions()
        print(f"   发现 {len([i for i in self.issues if i['severity'] == 'info'])} 个提示\n")

        print("4. 扫描计算方法...")
        self.scan_calculation_methods()
        print(f"   发现 {len([i for i in self.issues if i['severity'] == 'warning'])} 个警告\n")

        print("5. 扫描索引优化...")
        self.scan_index_optimization()
        print(f"   发现 {len([i for i in self.issues if i['severity'] == 'info'])} 个机会\n")

        return self.issues

    def print_report(self, issues=None):
        """打印扫描报告"""
        if issues is None:
            issues = self.issues

        if not issues:
            print("\n✅ 未发现任何问题！")
            return

        print("\n" + "=" * 80)
        print("扫描报告")
        print("=" * 80 + "\n")

        # 按严重程度分组
        errors = [i for i in issues if i["severity"] == "error"]
        warnings = [i for i in issues if i["severity"] == "warning"]
        infos = [i for i in issues if i["severity"] == "info"]

        if errors:
            print(f"❌ 错误 ({len(errors)}个):")
            for issue in errors:
                print(f"   - {issue['model']}.{issue['field']}")
                print(f"     {issue['message']}")
                print()

        if warnings:
            print(f"⚠️  警告 ({len(warnings)}个):")
            for issue in warnings:
                print(f"   - {issue['model']}.{issue['field']}")
                print(f"     {issue['message']}")
                if "recommendation" in issue:
                    print(f"     💡 建议: {issue['recommendation']}")
                print()

        if infos:
            print(f"ℹ️  提示 ({len(infos)}个):")
            for issue in infos:
                print(f"   - {issue['model']}.{issue['field']}")
                print(f"     {issue['message']}")
                if "recommendation" in issue:
                    print(f"     💡 建议: {issue['recommendation']}")
                print()

        print("=" * 80)
        print(f"总计: {len(issues)} 个问题")
        print("=" * 80)


class DataConsistencyScanner:
    """数据一致性扫描器"""

    def __init__(self):
        """初始化扫描器"""
        self.issues = []

    def scan_purchase_orders(self):
        """扫描采购订单数据一致性"""
        from django.db.models import Sum

        from apps.purchase.models import PurchaseOrder, PurchaseOrderItem

        issues = []

        orders = PurchaseOrder.objects.all()

        for order in orders:
            # 检查总金额
            calculated_total = (
                order.items.filter(is_deleted=False).aggregate(total=Sum("line_total"))["total"]
                or 0
            )

            if order.total_amount != calculated_total:
                issues.append(
                    {
                        "type": "total_amount_mismatch",
                        "order_number": order.order_number,
                        "expected": calculated_total,
                        "actual": order.total_amount,
                    }
                )

        self.issues.extend(issues)
        return issues

    def scan_sales_orders(self):
        """扫描销售订单数据一致性"""
        from django.db.models import Sum

        from apps.sales.models import SalesOrder, SalesOrderItem

        issues = []

        orders = SalesOrder.objects.all()

        for order in orders:
            # 检查总金额
            calculated_total = (
                order.items.filter(is_deleted=False).aggregate(total=Sum("line_total"))["total"]
                or 0
            )

            if order.total_amount != calculated_total:
                issues.append(
                    {
                        "type": "total_amount_mismatch",
                        "order_number": order.order_number,
                        "expected": calculated_total,
                        "actual": order.total_amount,
                    }
                )

        self.issues.extend(issues)
        return issues

    def scan_all(self):
        """运行所有数据一致性扫描"""
        print("开始扫描数据一致性...\n")

        print("1. 扫描采购订单...")
        self.scan_purchase_orders()
        print(f"   发现 {len(self.issues)} 个问题\n")

        print("2. 扫描销售订单...")
        self.scan_sales_orders()
        print(f"   发现 {len(self.issues)} 个问题\n")

        return self.issues
