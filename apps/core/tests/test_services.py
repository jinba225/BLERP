"""
Core模块 - 服务层测试
测试DocumentNumberGenerator单据号生成服务
"""
import threading
import unittest
from datetime import date

from core.utils.document_number import DocumentNumberGenerator
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase

from apps.core.models import DocumentNumberSequence, SystemConfig

User = get_user_model()


# 检测是否使用SQLite数据库
def is_sqlite_database():
    """检测当前是否使用SQLite数据库"""
    return "sqlite" in settings.DATABASES["default"]["ENGINE"]


class DocumentNumberGeneratorTestCase(TestCase):
    """DocumentNumberGenerator基础功能测试"""

    def setUp(self):
        """测试前准备 - 创建测试用户和配置"""
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            employee_id="EMP001",
        )

        # 创建默认配置（使用get_or_create避免唯一性冲突）
        SystemConfig.objects.get_or_create(
            key="document_prefix_sales_order",
            defaults={
                "value": "SO",
                "config_type": "business",
                "description": "销售订单前缀",
                "is_active": True,
            },
        )
        SystemConfig.objects.get_or_create(
            key="document_number_date_format",
            defaults={
                "value": "YYMMDD",
                "config_type": "business",
                "description": "单据号日期格式",
                "is_active": True,
            },
        )
        SystemConfig.objects.get_or_create(
            key="document_number_sequence_digits",
            defaults={
                "value": "3",
                "config_type": "business",
                "description": "单据号序号位数",
                "is_active": True,
            },
        )

    def test_generate_basic_document_number(self):
        """测试基础单据号生成"""
        doc_number = DocumentNumberGenerator.generate("sales_order")

        # 验证格式：SO + YYMMDD + 001
        self.assertTrue(doc_number.startswith("SO"))
        self.assertEqual(len(doc_number), 11)  # SO(2) + YYMMDD(6) + 001(3) = 11
        self.assertTrue(doc_number[2:].isdigit())  # 除前缀外都是数字

    def test_generate_with_custom_date(self):
        """测试使用自定义日期生成单据号"""
        test_date = date(2025, 11, 8)
        doc_number = DocumentNumberGenerator.generate("sales_order", test_date)

        # 验证日期部分 (251108)
        self.assertIn("251108", doc_number)
        self.assertEqual(doc_number, "SO251108001")

    def test_sequence_increment(self):
        """测试序号自动递增"""
        test_date = date(2025, 11, 8)

        doc1 = DocumentNumberGenerator.generate("sales_order", test_date)
        doc2 = DocumentNumberGenerator.generate("sales_order", test_date)
        doc3 = DocumentNumberGenerator.generate("sales_order", test_date)

        self.assertEqual(doc1, "SO251108001")
        self.assertEqual(doc2, "SO251108002")
        self.assertEqual(doc3, "SO251108003")

    def test_sequence_reset_on_different_date(self):
        """测试不同日期序号重置"""
        date1 = date(2025, 11, 8)
        date2 = date(2025, 11, 9)

        doc1 = DocumentNumberGenerator.generate("sales_order", date1)
        doc2 = DocumentNumberGenerator.generate("sales_order", date1)
        doc3 = DocumentNumberGenerator.generate("sales_order", date2)

        self.assertEqual(doc1, "SO251108001")
        self.assertEqual(doc2, "SO251108002")
        self.assertEqual(doc3, "SO251109001")  # 日期变化，序号重置为001

    def test_different_prefixes_independent_sequences(self):
        """测试不同前缀的序号独立"""
        # 创建报价单前缀配置（使用get_or_create避免唯一性冲突）
        SystemConfig.objects.get_or_create(
            key="document_prefix_quotation",
            defaults={"value": "QT", "config_type": "business", "is_active": True},
        )

        test_date = date(2025, 11, 8)

        so1 = DocumentNumberGenerator.generate("sales_order", test_date)
        qt1 = DocumentNumberGenerator.generate("quotation", test_date)
        so2 = DocumentNumberGenerator.generate("sales_order", test_date)
        qt2 = DocumentNumberGenerator.generate("quotation", test_date)

        self.assertEqual(so1, "SO251108001")
        self.assertEqual(qt1, "QT251108001")  # 不同前缀，序号独立
        self.assertEqual(so2, "SO251108002")
        self.assertEqual(qt2, "QT251108002")

    def test_legacy_prefix_support(self):
        """测试旧前缀兼容性"""
        test_date = date(2025, 11, 8)

        # 使用旧前缀直接生成（兼容模式）
        doc_number = DocumentNumberGenerator.generate("SO", test_date)

        # 应该正常工作，并使用配置中的前缀
        self.assertTrue(doc_number.startswith("SO"))
        self.assertIn("251108", doc_number)


class DocumentNumberGeneratorDateFormatTestCase(TestCase):
    """DocumentNumberGenerator日期格式测试"""

    def setUp(self):
        """测试前准备"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", employee_id="EMP001"
        )

        # 清理DocumentNumberSequence表（确保测试隔离）
        DocumentNumberSequence.objects.all().delete()

        # 创建销售订单前缀配置
        SystemConfig.objects.create(
            key="document_prefix_sales_order", value="SO", config_type="business", is_active=True
        )
        SystemConfig.objects.create(
            key="document_number_sequence_digits", value="3", config_type="business", is_active=True
        )

    def test_date_format_yyyymmdd(self):
        """测试YYYYMMDD日期格式"""
        SystemConfig.objects.create(
            key="document_number_date_format",
            value="YYYYMMDD",
            config_type="business",
            is_active=True,
        )

        test_date = date(2025, 11, 8)
        doc_number = DocumentNumberGenerator.generate("sales_order", test_date)

        # SO + 20251108 + 001 = SO20251108001 (13位)
        self.assertEqual(doc_number, "SO20251108001")
        self.assertEqual(len(doc_number), 13)

    def test_date_format_yymmdd(self):
        """测试YYMMDD日期格式"""
        SystemConfig.objects.create(
            key="document_number_date_format",
            value="YYMMDD",
            config_type="business",
            is_active=True,
        )

        test_date = date(2025, 11, 8)
        doc_number = DocumentNumberGenerator.generate("sales_order", test_date)

        # SO + 251108 + 001 = SO251108001 (11位)
        self.assertEqual(doc_number, "SO251108001")
        self.assertEqual(len(doc_number), 11)

    def test_date_format_yymm(self):
        """测试YYMM日期格式"""
        SystemConfig.objects.create(
            key="document_number_date_format", value="YYMM", config_type="business", is_active=True
        )

        test_date = date(2025, 11, 8)
        doc_number = DocumentNumberGenerator.generate("sales_order", test_date)

        # SO + 2511 + 001 = SO2511001 (9位)
        self.assertEqual(doc_number, "SO2511001")
        self.assertEqual(len(doc_number), 9)

    def test_format_date_helper(self):
        """测试format_date辅助方法"""
        test_date = date(2025, 11, 8)

        yyyymmdd = DocumentNumberGenerator.format_date(test_date, "YYYYMMDD")
        yymmdd = DocumentNumberGenerator.format_date(test_date, "YYMMDD")
        yymm = DocumentNumberGenerator.format_date(test_date, "YYMM")

        self.assertEqual(yyyymmdd, "20251108")
        self.assertEqual(yymmdd, "251108")
        self.assertEqual(yymm, "2511")


class DocumentNumberGeneratorSequenceDigitsTestCase(TestCase):
    """DocumentNumberGenerator序号位数测试"""

    def setUp(self):
        """测试前准备"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", employee_id="EMP001"
        )

        SystemConfig.objects.create(
            key="document_prefix_sales_order", value="SO", config_type="business", is_active=True
        )
        SystemConfig.objects.create(
            key="document_number_date_format",
            value="YYMMDD",
            config_type="business",
            is_active=True,
        )

    def test_sequence_digits_3(self):
        """测试3位序号"""
        SystemConfig.objects.create(
            key="document_number_sequence_digits", value="3", config_type="business", is_active=True
        )

        test_date = date(2025, 11, 8)
        doc_number = DocumentNumberGenerator.generate("sales_order", test_date)

        # SO251108001 - 序号部分是001（3位）
        self.assertEqual(doc_number, "SO251108001")
        self.assertTrue(doc_number.endswith("001"))

    def test_sequence_digits_4(self):
        """测试4位序号"""
        SystemConfig.objects.create(
            key="document_number_sequence_digits", value="4", config_type="business", is_active=True
        )

        test_date = date(2025, 11, 8)
        doc_number = DocumentNumberGenerator.generate("sales_order", test_date)

        # SO2511080001 - 序号部分是0001（4位）
        self.assertEqual(doc_number, "SO2511080001")
        self.assertTrue(doc_number.endswith("0001"))

    def test_sequence_digits_5(self):
        """测试5位序号"""
        SystemConfig.objects.create(
            key="document_number_sequence_digits", value="5", config_type="business", is_active=True
        )

        test_date = date(2025, 11, 8)
        doc_number = DocumentNumberGenerator.generate("sales_order", test_date)

        # SO25110800001 - 序号部分是00001（5位）
        self.assertEqual(doc_number, "SO25110800001")
        self.assertTrue(doc_number.endswith("00001"))

    def test_large_sequence_number(self):
        """测试大序号（超过位数）"""
        SystemConfig.objects.create(
            key="document_number_sequence_digits", value="3", config_type="business", is_active=True
        )

        test_date = date(2025, 11, 8)

        # 创建1000个单据号
        for i in range(1, 1001):
            doc = DocumentNumberGenerator.generate("sales_order", test_date)

        # 第1000个应该是SO2511081000（即使配置是3位，也能正常工作）
        self.assertEqual(doc, "SO2511081000")


class DocumentNumberGeneratorValidationTestCase(TestCase):
    """DocumentNumberGenerator验证和解析测试"""

    def test_validate_number_valid(self):
        """测试验证有效的单据号"""
        self.assertTrue(DocumentNumberGenerator.validate_number("SO251108001", "SO"))
        self.assertTrue(DocumentNumberGenerator.validate_number("QT20251108001", "QT"))
        self.assertTrue(DocumentNumberGenerator.validate_number("PO2511001", "PO"))

    def test_validate_number_invalid_prefix(self):
        """测试验证无效前缀"""
        self.assertFalse(DocumentNumberGenerator.validate_number("SO251108001", "QT"))
        self.assertFalse(DocumentNumberGenerator.validate_number("ABC251108001", "SO"))

    def test_validate_number_invalid_format(self):
        """测试验证无效格式"""
        # 非数字字符
        self.assertFalse(DocumentNumberGenerator.validate_number("SO25110800A", "SO"))

        # 太短
        self.assertFalse(DocumentNumberGenerator.validate_number("SO123", "SO"))

        # 太长
        self.assertFalse(DocumentNumberGenerator.validate_number("SO" + "1" * 20, "SO"))

    def test_parse_number_yymmdd_format(self):
        """测试解析YYMMDD格式的单据号"""
        result = DocumentNumberGenerator.parse_number("SO251108001", "SO", "YYMMDD", 3)

        self.assertIsNotNone(result)
        self.assertEqual(result["prefix"], "SO")
        self.assertEqual(result["date"], date(2025, 11, 8))
        self.assertEqual(result["sequence"], 1)

    def test_parse_number_yyyymmdd_format(self):
        """测试解析YYYYMMDD格式的单据号"""
        result = DocumentNumberGenerator.parse_number("QT20251108001", "QT", "YYYYMMDD", 3)

        self.assertIsNotNone(result)
        self.assertEqual(result["prefix"], "QT")
        self.assertEqual(result["date"], date(2025, 11, 8))
        self.assertEqual(result["sequence"], 1)

    def test_parse_number_yymm_format(self):
        """测试解析YYMM格式的单据号"""
        result = DocumentNumberGenerator.parse_number("PO2511001", "PO", "YYMM", 3)

        self.assertIsNotNone(result)
        self.assertEqual(result["prefix"], "PO")
        self.assertEqual(result["date"], date(2025, 11, 1))  # YYMM默认是1号
        self.assertEqual(result["sequence"], 1)

    def test_parse_number_invalid(self):
        """测试解析无效单据号"""
        result = DocumentNumberGenerator.parse_number("INVALID", "SO", "YYMMDD", 3)

        self.assertIsNone(result)


class DocumentNumberGeneratorPrefixTestCase(TestCase):
    """DocumentNumberGenerator前缀管理测试"""

    def setUp(self):
        """测试前准备"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", employee_id="EMP001"
        )

    def test_get_prefix_from_config(self):
        """测试从配置获取前缀"""
        SystemConfig.objects.create(
            key="document_prefix_sales_order", value="SO", config_type="business", is_active=True
        )

        prefix = DocumentNumberGenerator.get_prefix("sales_order")
        self.assertEqual(prefix, "SO")

    def test_get_prefix_custom_value(self):
        """测试自定义前缀值"""
        SystemConfig.objects.create(
            key="document_prefix_sales_order",
            value="ORDER",  # 自定义前缀
            config_type="business",
            is_active=True,
        )

        prefix = DocumentNumberGenerator.get_prefix("sales_order")
        self.assertEqual(prefix, "ORDER")

    def test_get_prefix_legacy_mapping(self):
        """测试旧前缀映射"""
        SystemConfig.objects.create(
            key="document_prefix_sales_order", value="SO", config_type="business", is_active=True
        )

        # 使用旧前缀'SO'应该映射到'sales_order'配置
        prefix = DocumentNumberGenerator.get_prefix("SO")
        self.assertEqual(prefix, "SO")

    def test_get_prefix_fallback_to_legacy(self):
        """测试配置不存在时回退到旧前缀"""
        # 不创建任何配置

        # 使用旧前缀应该返回原值
        prefix = DocumentNumberGenerator.get_prefix("SO")
        self.assertEqual(prefix, "SO")

    def test_get_prefix_direct_string(self):
        """测试直接传入前缀字符串"""
        # 传入不在映射中的字符串
        prefix = DocumentNumberGenerator.get_prefix("CUSTOM")
        self.assertEqual(prefix, "CUSTOM")


class DocumentNumberGeneratorConfigTestCase(TestCase):
    """DocumentNumberGenerator配置读取测试"""

    def setUp(self):
        """测试前准备"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", employee_id="EMP001"
        )

    def test_get_date_format_from_config(self):
        """测试从配置获取日期格式"""
        SystemConfig.objects.create(
            key="document_number_date_format",
            value="YYYYMMDD",
            config_type="business",
            is_active=True,
        )

        date_format = DocumentNumberGenerator.get_date_format()
        self.assertEqual(date_format, "YYYYMMDD")

    def test_get_date_format_default(self):
        """测试日期格式默认值"""
        # 不创建配置
        date_format = DocumentNumberGenerator.get_date_format()
        self.assertEqual(date_format, "YYMMDD")  # 默认值

    def test_get_sequence_digits_from_config(self):
        """测试从配置获取序号位数"""
        SystemConfig.objects.create(
            key="document_number_sequence_digits", value="4", config_type="business", is_active=True
        )

        digits = DocumentNumberGenerator.get_sequence_digits()
        self.assertEqual(digits, 4)

    def test_get_sequence_digits_default(self):
        """测试序号位数默认值"""
        # 不创建配置
        digits = DocumentNumberGenerator.get_sequence_digits()
        self.assertEqual(digits, 3)  # 默认值

    def test_get_sequence_digits_invalid_value(self):
        """测试无效序号位数配置"""
        SystemConfig.objects.create(
            key="document_number_sequence_digits",
            value="invalid",  # 无效值
            config_type="business",
            is_active=True,
        )

        digits = DocumentNumberGenerator.get_sequence_digits()
        self.assertEqual(digits, 3)  # 应该返回默认值


class DocumentNumberGeneratorConcurrencyTestCase(TransactionTestCase):
    """DocumentNumberGenerator并发安全测试

    注意: SQLite数据库不支持真正的并发写入，会出现table locked错误。
    这些测试在SQLite环境下会被跳过，仅在MySQL/PostgreSQL等真正支持并发的数据库上运行。
    """

    def setUp(self):
        """测试前准备"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", employee_id="EMP001"
        )

        SystemConfig.objects.create(
            key="document_prefix_sales_order", value="SO", config_type="business", is_active=True
        )
        SystemConfig.objects.create(
            key="document_number_date_format",
            value="YYMMDD",
            config_type="business",
            is_active=True,
        )
        SystemConfig.objects.create(
            key="document_number_sequence_digits", value="3", config_type="business", is_active=True
        )

    @unittest.skipIf(is_sqlite_database(), "SQLite不支持并发写入，跳过此测试")
    def test_concurrent_generation(self):
        """测试并发生成单据号的唯一性"""
        test_date = date(2025, 11, 8)
        generated_numbers = []
        errors = []

        def generate_number():
            """线程函数：生成单据号"""
            try:
                doc_number = DocumentNumberGenerator.generate("sales_order", test_date)
                generated_numbers.append(doc_number)
            except Exception as e:
                errors.append(str(e))

        # 创建10个线程并发生成单据号
        threads = []
        for i in range(10):
            thread = threading.Thread(target=generate_number)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证：没有错误发生
        self.assertEqual(len(errors), 0, f"生成过程中出现错误: {errors}")

        # 验证：生成了10个单据号
        self.assertEqual(len(generated_numbers), 10)

        # 验证：所有单据号都是唯一的（没有重复）
        unique_numbers = set(generated_numbers)
        self.assertEqual(len(unique_numbers), 10, f"发现重复的单据号！生成的号码: {sorted(generated_numbers)}")

        # 验证：所有单据号都符合预期格式
        for doc_number in generated_numbers:
            self.assertTrue(doc_number.startswith("SO251108"))
            self.assertEqual(len(doc_number), 11)

    @unittest.skipIf(is_sqlite_database(), "SQLite不支持并发写入，跳过此测试")
    def test_concurrent_different_dates(self):
        """测试不同日期的并发生成"""
        date1 = date(2025, 11, 8)
        date2 = date(2025, 11, 9)
        generated_numbers = {"date1": [], "date2": []}

        def generate_for_date1():
            doc_number = DocumentNumberGenerator.generate("sales_order", date1)
            generated_numbers["date1"].append(doc_number)

        def generate_for_date2():
            doc_number = DocumentNumberGenerator.generate("sales_order", date2)
            generated_numbers["date2"].append(doc_number)

        # 创建10个线程交替生成不同日期的单据号
        threads = []
        for i in range(10):
            thread1 = threading.Thread(target=generate_for_date1)
            thread2 = threading.Thread(target=generate_for_date2)
            threads.extend([thread1, thread2])
            thread1.start()
            thread2.start()

        for thread in threads:
            thread.join()

        # 验证：每个日期都生成了10个唯一的单据号
        self.assertEqual(len(set(generated_numbers["date1"])), 10)
        self.assertEqual(len(set(generated_numbers["date2"])), 10)

        # 验证：不同日期的单据号不冲突
        all_numbers = set(generated_numbers["date1"] + generated_numbers["date2"])
        self.assertEqual(len(all_numbers), 20)


class DocumentNumberGeneratorEdgeCaseTestCase(TestCase):
    """DocumentNumberGenerator边界条件测试"""

    def setUp(self):
        """测试前准备"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", employee_id="EMP001"
        )

        SystemConfig.objects.create(
            key="document_prefix_sales_order", value="SO", config_type="business", is_active=True
        )
        SystemConfig.objects.create(
            key="document_number_date_format",
            value="YYMMDD",
            config_type="business",
            is_active=True,
        )
        SystemConfig.objects.create(
            key="document_number_sequence_digits", value="3", config_type="business", is_active=True
        )

    def test_year_2000_handling(self):
        """测试2000年（Y2K）的处理"""
        test_date = date(2000, 1, 1)
        doc_number = DocumentNumberGenerator.generate("sales_order", test_date)

        # YY格式：00 (表示2000年)
        self.assertIn("000101", doc_number)
        self.assertEqual(doc_number, "SO000101001")

    def test_year_2099_handling(self):
        """测试2099年的处理"""
        test_date = date(2099, 12, 31)
        doc_number = DocumentNumberGenerator.generate("sales_order", test_date)

        # YY格式：99 (表示2099年)
        self.assertIn("991231", doc_number)
        self.assertEqual(doc_number, "SO991231001")

    def test_leap_year_handling(self):
        """测试闰年2月29日"""
        test_date = date(2024, 2, 29)  # 2024是闰年
        doc_number = DocumentNumberGenerator.generate("sales_order", test_date)

        self.assertIn("240229", doc_number)
        self.assertEqual(doc_number, "SO240229001")

    def test_month_boundaries(self):
        """测试月份边界（1月和12月）"""
        jan_date = date(2025, 1, 1)
        dec_date = date(2025, 12, 31)

        jan_doc = DocumentNumberGenerator.generate("sales_order", jan_date)
        dec_doc = DocumentNumberGenerator.generate("sales_order", dec_date)

        self.assertEqual(jan_doc, "SO250101001")
        self.assertEqual(dec_doc, "SO251231001")

    def test_very_long_prefix(self):
        """测试很长的前缀"""
        SystemConfig.objects.create(
            key="document_prefix_sales_contract",
            value="SALES_CONTRACT",  # 很长的前缀
            config_type="business",
            is_active=True,
        )

        test_date = date(2025, 11, 8)
        doc_number = DocumentNumberGenerator.generate("sales_contract", test_date)

        self.assertTrue(doc_number.startswith("SALES_CONTRACT"))
        self.assertIn("251108", doc_number)

    def test_empty_prefix(self):
        """测试空前缀"""
        SystemConfig.objects.create(
            key="document_prefix_quotation", value="", config_type="business", is_active=True  # 空前缀
        )

        test_date = date(2025, 11, 8)
        doc_number = DocumentNumberGenerator.generate("quotation", test_date)

        # 空前缀应该只包含日期和序号
        self.assertEqual(doc_number, "251108001")

    def test_sequence_overflow(self):
        """测试序号溢出（超过配置位数）"""
        test_date = date(2025, 11, 8)

        # 生成999个单据号
        for i in range(999):
            DocumentNumberGenerator.generate("sales_order", test_date)

        # 第1000个单据号（超过3位）
        doc_1000 = DocumentNumberGenerator.generate("sales_order", test_date)

        # 应该是SO2511081000（自动扩展位数）
        self.assertEqual(doc_1000, "SO2511081000")

    def test_parse_number_with_no_config(self):
        """测试没有配置时的解析（使用默认值）"""
        # 清除所有配置
        SystemConfig.objects.all().delete()

        # 使用默认配置解析
        result = DocumentNumberGenerator.parse_number("SO251108001", "SO")

        self.assertIsNotNone(result)
        self.assertEqual(result["prefix"], "SO")
        self.assertEqual(result["date"], date(2025, 11, 8))
        self.assertEqual(result["sequence"], 1)
