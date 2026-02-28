"""
Django management command to initialize default print templates.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.sales.models import PrintTemplate

User = get_user_model()


class Command(BaseCommand):
    help = "初始化默认打印模板"

    def handle(self, *args, **options):
        self.stdout.write("开始创建默认打印模板...")

        # Get or create system user for template creation
        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            self.stdout.write(self.style.WARNING("警告：未找到超级用户，将使用 None 作为创建者"))

        templates_created = 0

        # Create default template for domestic quotes
        if not PrintTemplate.objects.filter(
            template_type="quote_domestic", is_deleted=False
        ).exists():
            domestic_template = PrintTemplate.objects.create(
                name="标准国内报价单",
                template_type="quote_domestic",
                is_default=True,
                is_active=True,
                company_name="BetterLaser 激光科技有限公司",
                company_address="",
                company_phone="",
                company_email="",
                layout_config=PrintTemplate.get_default_layout_config("quote_domestic"),
                notes="系统默认国内报价单模板",
                created_by=system_user,
            )
            templates_created += 1
            self.stdout.write(self.style.SUCCESS(f"✓ 创建国内报价单模板: {domestic_template.name}"))

        # Create default template for overseas quotes
        if not PrintTemplate.objects.filter(
            template_type="quote_overseas", is_deleted=False
        ).exists():
            overseas_template = PrintTemplate.objects.create(
                name="标准海外报价单",
                template_type="quote_overseas",
                is_default=True,
                is_active=True,
                company_name="BetterLaser Laser Technology Co., Ltd.",
                company_address="",
                company_phone="",
                company_email="",
                layout_config=PrintTemplate.get_default_layout_config("quote_overseas"),
                notes="系统默认海外报价单模板",
                created_by=system_user,
            )
            templates_created += 1
            self.stdout.write(self.style.SUCCESS(f"✓ 创建海外报价单模板: {overseas_template.name}"))

        if templates_created > 0:
            self.stdout.write(self.style.SUCCESS(f"\n成功创建 {templates_created} 个默认模板！"))
        else:
            self.stdout.write(self.style.WARNING("所有默认模板已存在，无需创建"))
