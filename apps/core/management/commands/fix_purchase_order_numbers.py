"""
Django管理命令：修复采购订单号连续性问题

使用方法：
    python manage.py fix_purchase_order_numbers
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "修复采购订单号连续性问题 - 重置序列号使新订单重用已删除编号"

    def add_arguments(self, parser):
        parser.add_argument(
            "--auto",
            action="store_true",
            dest="auto",
            help="自动修复（重置序列号为当前最大订单号）",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            dest="reset",
            help="重置序列号为0",
        )
        parser.add_argument(
            "--set",
            type=int,
            dest="set_value",
            help="设置序列号为指定值",
        )

    def handle(self, *args, **options):
        # 延迟导入，避免模块加载时的循环依赖问题
        from core.models import DocumentNumberSequence

        from apps.purchase.models import PurchaseOrder

        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("修复采购订单号连续性"))
        self.stdout.write(self.style.SUCCESS("=" * 70))

        # 获取今天的日期字符串
        today = timezone.now().date()
        date_str = today.strftime("%y%m%d")  # YYMMDD 格式

        # 获取所有未删除的采购订单
        all_orders = PurchaseOrder.objects.filter(is_deleted=False).order_by("created_at")
        today_orders = all_orders.filter(created_at__date=today)

        self.stdout.write(f"\n找到 {all_orders.count()} 个未删除的采购订单（总计）")
        self.stdout.write(f"其中今天创建的订单: {today_orders.count()} 个")

        # 检查今天的订单编号
        today_numbers = []
        for order in today_orders:
            try:
                # 提取单号中的数字部分 - 格式: POYYMMDDXXX
                if order.order_number.startswith("PO"):
                    # 跳过前缀 "PO" 和日期部分 (6位)
                    num_part = order.order_number[8:]  # PO(2) + YYMMDD(6) = 8
                    today_numbers.append(int(num_part))
            except (ValueError, IndexError):
                pass

        if today_numbers:
            max_num = max(today_numbers)
            expected_count = max_num
            actual_count = len(today_numbers)

            self.stdout.write(f"\n当前最大单号: PO{date_str}{max_num:03d}")
            self.stdout.write(f"预期数量: {expected_count}")
            self.stdout.write(f"实际数量: {actual_count}")
            self.stdout.write(f"缺失单号: {expected_count - actual_count} 个")

            # 找出缺失的编号
            missing_numbers = sorted(set(range(1, max_num + 1)) - set(today_numbers))
            if missing_numbers:
                self.stdout.write(f"缺失的具体编号: {missing_numbers}")
        else:
            self.stdout.write(f"\n今天还没有采购订单")
            # 检查数据库中的序列记录
            try:
                sequence = DocumentNumberSequence.objects.filter(
                    prefix="PO", date_str=date_str
                ).first()

                if sequence:
                    self.stdout.write(f"数据库中记录的当前序号: {sequence.current_number}")
                else:
                    self.stdout.write(f"数据库中还没有今天(PO{date_str})的序列记录")
            except Exception as e:
                self.stdout.write(f"查询序列记录失败: {e}")

        # 处理命令行选项
        if options["auto"]:
            # 自动重置为当前最大编号
            if today_numbers:
                new_sequence = max(today_numbers)
                self.stdout.write(f"\n将序列号设置为 {new_sequence}")
                with transaction.atomic():
                    (
                        sequence,
                        created,
                    ) = DocumentNumberSequence.objects.select_for_update().get_or_create(
                        prefix="PO",
                        date_str=date_str,
                        defaults={"current_number": new_sequence},
                    )
                    if not created:
                        sequence.current_number = new_sequence
                        sequence.save()
                self.stdout.write(self.style.SUCCESS(f"\n✅ 序列号已重置为 {new_sequence}"))
                self.stdout.write(
                    self.style.SUCCESS(f"下一个采购订单号将是: PO{date_str}{new_sequence + 1:03d}")
                )
            else:
                self.stdout.write(self.style.WARNING("\n今天没有订单，无法确定最大编号"))

        elif options["reset"]:
            # 重置为0
            self.stdout.write(f"\n将序列号设置为 0")
            with transaction.atomic():
                (
                    sequence,
                    created,
                ) = DocumentNumberSequence.objects.select_for_update().get_or_create(
                    prefix="PO", date_str=date_str, defaults={"current_number": 0}
                )
                if not created:
                    sequence.current_number = 0
                    sequence.save()
            self.stdout.write(self.style.SUCCESS(f"\n✅ 序列号已重置为 0"))
            self.stdout.write(self.style.SUCCESS(f"下一个采购订单号将是: PO{date_str}001"))

        elif options["set_value"] is not None:
            # 设置为指定值
            new_sequence = options["set_value"]
            if new_sequence < 0:
                self.stdout.write(self.style.ERROR("序列号不能为负数"))
                return

            self.stdout.write(f"\n将序列号设置为 {new_sequence}")
            with transaction.atomic():
                (
                    sequence,
                    created,
                ) = DocumentNumberSequence.objects.select_for_update().get_or_create(
                    prefix="PO",
                    date_str=date_str,
                    defaults={"current_number": new_sequence},
                )
                if not created:
                    sequence.current_number = new_sequence
                    sequence.save()
            self.stdout.write(self.style.SUCCESS(f"\n✅ 序列号已设置为 {new_sequence}"))
            self.stdout.write(self.style.SUCCESS(f"下一个采购订单号将是: PO{date_str}{new_sequence + 1:03d}"))

        else:
            # 交互式菜单
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write("修复选项:")
            self.stdout.write("=" * 70)
            self.stdout.write("1. 重置序列号为当前最大订单号（新订单将连续编号）")
            self.stdout.write("2. 将序列号设置为0（从头开始）")
            self.stdout.write("3. 自定义序列号")
            self.stdout.write("4. 显示使用帮助")
            self.stdout.write("0. 取消操作")

            choice = input("\n请选择修复选项 (0-4): ").strip()

            if choice == "1":
                # 重置为当前最大编号
                if today_numbers:
                    new_sequence = max(today_numbers)
                    self.stdout.write(f"\n将序列号设置为 {new_sequence}")
                    confirm = input("确认? (yes/no): ").strip().lower()
                    if confirm == "yes":
                        with transaction.atomic():
                            (
                                sequence,
                                created,
                            ) = DocumentNumberSequence.objects.select_for_update().get_or_create(
                                prefix="PO",
                                date_str=date_str,
                                defaults={"current_number": new_sequence},
                            )
                            if not created:
                                sequence.current_number = new_sequence
                                sequence.save()
                        self.stdout.write(self.style.SUCCESS(f"\n✅ 序列号已重置为 {new_sequence}"))
                        self.stdout.write(
                            self.style.SUCCESS(f"下一个采购订单号将是: PO{date_str}{new_sequence + 1:03d}")
                        )
                    else:
                        self.stdout.write("\n操作已取消")
                else:
                    self.stdout.write(self.style.WARNING("\n今天没有订单，无法确定最大编号"))

            elif choice == "2":
                # 重置为0
                self.stdout.write(f"\n将序列号设置为 0")
                self.stdout.write(self.style.WARNING("⚠️ 警告：如果今天已有订单，这可能导致编号冲突！"))
                confirm = input("确认? (输入 'RESET' 继续): ").strip()
                if confirm == "RESET":
                    with transaction.atomic():
                        (
                            sequence,
                            created,
                        ) = DocumentNumberSequence.objects.select_for_update().get_or_create(
                            prefix="PO",
                            date_str=date_str,
                            defaults={"current_number": 0},
                        )
                        if not created:
                            sequence.current_number = 0
                            sequence.save()
                    self.stdout.write(self.style.SUCCESS(f"\n✅ 序列号已重置为 0"))
                    self.stdout.write(self.style.SUCCESS(f"下一个采购订单号将是: PO{date_str}001"))
                else:
                    self.stdout.write("\n操作已取消")

            elif choice == "3":
                # 自定义序列号
                custom_value = input("\n请输入新的序列号值: ").strip()
                try:
                    new_sequence = int(custom_value)
                    if new_sequence < 0:
                        self.stdout.write(self.style.ERROR("序列号不能为负数"))
                        return

                    self.stdout.write(f"\n将序列号设置为 {new_sequence}")
                    confirm = input("确认? (yes/no): ").strip().lower()
                    if confirm == "yes":
                        with transaction.atomic():
                            (
                                sequence,
                                created,
                            ) = DocumentNumberSequence.objects.select_for_update().get_or_create(
                                prefix="PO",
                                date_str=date_str,
                                defaults={"current_number": new_sequence},
                            )
                            if not created:
                                sequence.current_number = new_sequence
                                sequence.save()
                        self.stdout.write(self.style.SUCCESS(f"\n✅ 序列号已设置为 {new_sequence}"))
                        self.stdout.write(
                            self.style.SUCCESS(f"下一个采购订单号将是: PO{date_str}{new_sequence + 1:03d}")
                        )
                    else:
                        self.stdout.write("\n操作已取消")
                except ValueError:
                    self.stdout.write(self.style.ERROR("输入的不是有效的数字"))

            elif choice == "4":
                self.stdout.write("\n命令行选项:")
                self.stdout.write("  --auto    自动重置为当前最大订单号")
                self.stdout.write("  --reset   重置序列号为0")
                self.stdout.write("  --set N   设置序列号为指定值 N")
                self.stdout.write("\n示例:")
                self.stdout.write("  python manage.py fix_purchase_order_numbers --auto")
                self.stdout.write("  python manage.py fix_purchase_order_numbers --reset")
                self.stdout.write("  python manage.py fix_purchase_order_numbers --set 5")

            else:
                self.stdout.write("\n操作已取消")

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS("操作完成"))
        self.stdout.write(self.style.SUCCESS("=" * 70))
