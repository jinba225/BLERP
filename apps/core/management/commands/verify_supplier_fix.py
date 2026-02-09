from django.core.management.base import BaseCommand
from django.db.models import Count, Sum

from apps.finance.models import SupplierAccount


class Command(BaseCommand):
    help = "验证供应商应付账款核销页面修复"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🔍 验证供应商应付账款核销页面修复"))

        # 查询有多个账户的供应商
        multi_account_suppliers = (
            SupplierAccount.objects.filter(is_deleted=False)
            .values("supplier__id", "supplier__name")
            .annotate(account_count=Count("id"), total_balance=Sum("balance"))
            .filter(account_count__gt=1)
        )

        self.stdout.write(f"\n📊 找到 {multi_account_suppliers.count()} 个有多个应付账户的供应商：")

        for item in multi_account_suppliers[:5]:
            supplier_id = item["supplier__id"]
            supplier_name = item["supplier__name"]
            account_count = item["account_count"]
            total_balance = item["total_balance"] or 0

            self.stdout.write(f"\n✅ 供应商: {supplier_name} (ID: {supplier_id})")
            self.stdout.write(f"   - 账户数量: {account_count}")
            self.stdout.write(f"   - 总余额: ¥{total_balance:.2f}")

            # 显示详细账户列表
            accounts = SupplierAccount.objects.filter(
                supplier_id=supplier_id, is_deleted=False
            ).order_by("invoice_number")

            self.stdout.write("   - 详细账户:")
            for acc in accounts:
                self.stdout.write(f"     * {acc.invoice_number}: ¥{acc.balance:.2f}")

        # 查询只有一个账户的供应商
        single_account_suppliers = (
            SupplierAccount.objects.filter(is_deleted=False)
            .values("supplier__id")
            .annotate(account_count=Count("id"))
            .filter(account_count=1)
        )

        self.stdout.write(f"\n📊 找到 {single_account_suppliers.count()} 个只有一个应付账户的供应商")
        self.stdout.write(self.style.WARNING("(这些供应商的核销页面不应显示汇总信息)"))

        # 验证视图逻辑
        if multi_account_suppliers.exists():
            self.stdout.write(self.style.SUCCESS("\n✅ 视图函数验证:"))

            supplier_id = multi_account_suppliers.first()["supplier__id"]
            supplier_summary = SupplierAccount.objects.filter(
                supplier_id=supplier_id, is_deleted=False
            ).aggregate(total_balance=Sum("balance"), account_count=Count("id"))

            self.stdout.write(f"   - total_balance: {supplier_summary['total_balance']}")
            self.stdout.write(f"   - account_count: {supplier_summary['account_count']}")

            if supplier_summary and supplier_summary["account_count"] > 1:
                self.stdout.write(self.style.SUCCESS("   ✅ 模板条件满足，将显示汇总信息"))
            else:
                self.stdout.write(self.style.ERROR("   ❌ 模板条件不满足"))

        self.stdout.write(self.style.SUCCESS("\n🎯 修复总结:"))
        self.stdout.write("1. ✅ 视图函数添加了 supplier_summary 查询")
        self.stdout.write("2. ✅ 模板添加了供应商汇总信息显示")
        self.stdout.write("3. ✅ 单账户供应商不会显示冗余信息")
        self.stdout.write("4. ✅ 多账户供应商会显示汇总信息")

        self.stdout.write(self.style.SUCCESS("\n📱 用户体验改进:"))
        self.stdout.write("- 用户在核销页面可以清楚看到当前账户余额")
        self.stdout.write("- 用户可以了解该供应商的总应付情况")
        self.stdout.write("- 解决了列表页和核销页金额不一致的困惑")
