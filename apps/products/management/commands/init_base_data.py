"""
Django管理命令：初始化基础数据

这个命令会创建：
1. 常用计量单位
2. 默认仓库
3. 示例产品分类

运行方式：
python manage.py init_base_data
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.products.models import Unit, ProductCategory
from apps.inventory.models import Warehouse


class Command(BaseCommand):
    help = '初始化ERP系统基础数据（计量单位、仓库、产品分类）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新创建数据（如果已存在）',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options.get('force', False)

        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('开始初始化基础数据...'))
        self.stdout.write(self.style.SUCCESS('=' * 50))

        # 初始化计量单位
        self._create_units(force)

        # 初始化默认仓库
        self._create_warehouses(force)

        # 初始化产品分类示例
        self._create_categories(force)

        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('基础数据初始化完成！'))
        self.stdout.write(self.style.SUCCESS('=' * 50))

    def _create_units(self, force):
        """创建常用计量单位"""
        self.stdout.write('\n正在创建计量单位...')

        units_data = [
            # 基本单位
            {'name': '个', 'symbol': '个', 'unit_type': 'count', 'description': '基本计数单位'},
            {'name': '件', 'symbol': '件', 'unit_type': 'count', 'description': '产品件数'},
            {'name': '台', 'symbol': '台', 'unit_type': 'count', 'description': '设备台数'},
            {'name': '套', 'symbol': '套', 'unit_type': 'count', 'description': '成套产品'},
            {'name': '只', 'symbol': '只', 'unit_type': 'count', 'description': '计数单位'},
            {'name': '支', 'symbol': '支', 'unit_type': 'count', 'description': '计数单位'},
            {'name': '张', 'symbol': '张', 'unit_type': 'count', 'description': '平面物品'},
            {'name': '盒', 'symbol': '盒', 'unit_type': 'count', 'description': '包装单位'},
            {'name': '箱', 'symbol': '箱', 'unit_type': 'count', 'description': '包装单位'},

            # 重量单位
            {'name': '吨', 'symbol': 't', 'unit_type': 'weight', 'description': '公吨'},
            {'name': '公斤', 'symbol': 'kg', 'unit_type': 'weight', 'description': '千克'},
            {'name': '克', 'symbol': 'g', 'unit_type': 'weight', 'description': '克'},
            {'name': '毫克', 'symbol': 'mg', 'unit_type': 'weight', 'description': '毫克'},
            {'name': '磅', 'symbol': 'lb', 'unit_type': 'weight', 'description': '英制重量单位'},

            # 长度单位
            {'name': '米', 'symbol': 'm', 'unit_type': 'length', 'description': '米'},
            {'name': '厘米', 'symbol': 'cm', 'unit_type': 'length', 'description': '厘米'},
            {'name': '毫米', 'symbol': 'mm', 'unit_type': 'length', 'description': '毫米'},
            {'name': '千米', 'symbol': 'km', 'unit_type': 'length', 'description': '千米'},
            {'name': '英寸', 'symbol': 'in', 'unit_type': 'length', 'description': '英制长度单位'},
            {'name': '英尺', 'symbol': 'ft', 'unit_type': 'length', 'description': '英制长度单位'},

            # 面积单位
            {'name': '平方米', 'symbol': 'm²', 'unit_type': 'area', 'description': '平方米'},
            {'name': '平方厘米', 'symbol': 'cm²', 'unit_type': 'area', 'description': '平方厘米'},
            {'name': '平方毫米', 'symbol': 'mm²', 'unit_type': 'area', 'description': '平方毫米'},

            # 体积单位
            {'name': '立方米', 'symbol': 'm³', 'unit_type': 'volume', 'description': '立方米'},
            {'name': '升', 'symbol': 'L', 'unit_type': 'volume', 'description': '升'},
            {'name': '毫升', 'symbol': 'mL', 'unit_type': 'volume', 'description': '毫升'},

            # 时间单位
            {'name': '小时', 'symbol': 'h', 'unit_type': 'time', 'description': '小时'},
            {'name': '分钟', 'symbol': 'min', 'unit_type': 'time', 'description': '分钟'},
            {'name': '秒', 'symbol': 's', 'unit_type': 'time', 'description': '秒'},
            {'name': '天', 'symbol': '天', 'unit_type': 'time', 'description': '天'},
            {'name': '月', 'symbol': '月', 'unit_type': 'time', 'description': '月'},
            {'name': '年', 'symbol': '年', 'unit_type': 'time', 'description': '年'},
        ]

        created_count = 0
        skipped_count = 0

        for unit_data in units_data:
            unit, created = Unit.objects.get_or_create(
                symbol=unit_data['symbol'],
                defaults=unit_data
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ 创建单位: {unit.name} ({unit.symbol})'))
            else:
                skipped_count += 1
                if force:
                    for key, value in unit_data.items():
                        setattr(unit, key, value)
                    unit.save()
                    self.stdout.write(self.style.WARNING(f'  ↻ 更新单位: {unit.name} ({unit.symbol})'))

        self.stdout.write(self.style.SUCCESS(f'\n计量单位创建完成: 新建 {created_count} 个, 跳过 {skipped_count} 个'))

    def _create_warehouses(self, force):
        """创建默认仓库"""
        self.stdout.write('\n正在创建默认仓库...')

        warehouses_data = [
            {
                'name': '总仓库',
                'code': 'WH001',
                'warehouse_type': 'main',
                'address': '待设置',
                'is_active': True,
            },
            {
                'name': '次品仓',
                'code': 'WH_DMG',
                'warehouse_type': 'damaged',
                'address': '待设置',
                'is_active': True,
            },
            {
                'name': '虚拟仓',
                'code': 'WH_VIR',
                'warehouse_type': 'virtual',
                'address': '虚拟仓库',
                'is_active': True,
            },
        ]

        created_count = 0
        skipped_count = 0

        for warehouse_data in warehouses_data:
            warehouse, created = Warehouse.objects.get_or_create(
                code=warehouse_data['code'],
                defaults=warehouse_data
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ 创建仓库: {warehouse.name} ({warehouse.code})'))
            else:
                skipped_count += 1
                if force:
                    for key, value in warehouse_data.items():
                        setattr(warehouse, key, value)
                    warehouse.save()
                    self.stdout.write(self.style.WARNING(f'  ↻ 更新仓库: {warehouse.name} ({warehouse.code})'))

        self.stdout.write(self.style.SUCCESS(f'\n仓库创建完成: 新建 {created_count} 个, 跳过 {skipped_count} 个'))

    def _create_categories(self, force):
        """创建产品分类示例"""
        self.stdout.write('\n正在创建产品分类示例...')

        categories_data = [
            {'name': '激光设备', 'code': 'CAT_LASER', 'description': '激光切割、焊接等设备'},
            {'name': '原材料', 'code': 'CAT_RAW', 'description': '生产用原材料'},
            {'name': '配件耗材', 'code': 'CAT_PARTS', 'description': '设备配件和耗材'},
            {'name': '成品', 'code': 'CAT_FINISHED', 'description': '最终产品'},
            {'name': '半成品', 'code': 'CAT_SEMI', 'description': '半成品'},
        ]

        created_count = 0
        skipped_count = 0

        for category_data in categories_data:
            category, created = ProductCategory.objects.get_or_create(
                code=category_data['code'],
                defaults=category_data
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ 创建分类: {category.name} ({category.code})'))
            else:
                skipped_count += 1
                if force:
                    for key, value in category_data.items():
                        if key != 'code':  # 不更新 code
                            setattr(category, key, value)
                    category.save()
                    self.stdout.write(self.style.WARNING(f'  ↻ 更新分类: {category.name} ({category.code})'))

        self.stdout.write(self.style.SUCCESS(f'\n产品分类创建完成: 新建 {created_count} 个, 跳过 {skipped_count} 个'))
