"""
数据迁移命令：更新现有模板数据到新的分类结构

功能：
1. 将现有模板的 template_category 设置为正确的大类
2. 为现有模板设置 suitable_for 字段
3. 创建默认模板映射
"""
from django.core.management.base import BaseCommand
from sales.models import DefaultTemplateMapping, PrintTemplate


class Command(BaseCommand):
    help = "将现有打印模板数据迁移到新的分类结构"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只显示将要执行的操作，不实际修改数据",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 Dry-run 模式：只显示操作，不修改数据\n"))
        else:
            self.stdout.write(self.style.SUCCESS("🚀 开始数据迁移\n"))

        # 获取所有现有模板
        templates = PrintTemplate.objects.filter(is_deleted=False)
        template_count = templates.count()

        self.stdout.write(f"📊 找到 {template_count} 个模板需要处理\n")

        if template_count == 0:
            self.stdout.write(self.style.WARNING("⚠️  没有找到需要迁移的模板"))
            return

        # 显示现有模板
        self.stdout.write("=" * 80)
        self.stdout.write("现有模板列表：")
        for t in templates:
            self.stdout.write(f"  - ID={t.pk}: {t.name}")
            self.stdout.write(f"    template_category: {t.template_category}")
            self.stdout.write(f"    suitable_for: {t.suitable_for}")
        self.stdout.write("=" * 80 + "\n")

        # 迁移计划
        migration_plan = {
            # ID: (name, template_category, suitable_for, default_for)
            1: ("标准国内报价单", "sales", ["quote"], ["quote_domestic"]),
            2: ("标准海外报价单", "sales", ["quote"], ["quote_overseas"]),
        }

        updated_count = 0
        created_mappings_count = 0

        for template in templates:
            if template.pk in migration_plan:
                name, category, suitable_for, default_for = migration_plan[template.pk]

                self.stdout.write(f"\n处理模板 ID={template.pk}: {template.name}")

                # 1. 更新模板字段
                changes = []
                if template.template_category != category:
                    changes.append(
                        f"  template_category: {template.template_category} → {category}"
                    )
                    if not dry_run:
                        template.template_category = category

                if template.suitable_for != suitable_for:
                    changes.append(f"  suitable_for: {template.suitable_for} → {suitable_for}")
                    if not dry_run:
                        template.suitable_for = suitable_for

                if changes:
                    for change in changes:
                        self.stdout.write(self.style.WARNING(change))

                    if not dry_run:
                        template.save()
                        updated_count += 1
                        self.stdout.write(self.style.SUCCESS("  ✅ 模板已更新"))
                else:
                    self.stdout.write("  ℹ️  无需更新")

                # 2. 创建默认模板映射
                for doc_type in default_for:
                    existing_mapping = DefaultTemplateMapping.objects.filter(
                        document_type=doc_type, is_deleted=False
                    ).first()

                    if existing_mapping:
                        self.stdout.write(
                            f"  ⚠️  默认映射已存在: {doc_type} → {existing_mapping.template.name}"
                        )
                    else:
                        self.stdout.write(f"  📝 创建默认映射: {doc_type} → {template.name}")
                        if not dry_run:
                            DefaultTemplateMapping.objects.create(
                                document_type=doc_type, template=template
                            )
                            created_mappings_count += 1
                            self.stdout.write(self.style.SUCCESS("  ✅ 默认映射已创建"))
            else:
                self.stdout.write(f"\n⚠️  模板 ID={template.pk} ({template.name}) 不在迁移计划中，跳过")

        # 总结
        self.stdout.write("\n" + "=" * 80)
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 Dry-run 完成，以上是将要执行的操作"))
            self.stdout.write(
                self.style.WARNING("💡 执行 python manage.py migrate_template_data 进行实际迁移")
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ 数据迁移完成！"))
            self.stdout.write(f"  - 更新模板: {updated_count} 个")
            self.stdout.write(f"  - 创建默认映射: {created_mappings_count} 个")
        self.stdout.write("=" * 80)
