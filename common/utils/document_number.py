"""
Document number generator utility.

Generates unique document numbers with format: PREFIX + YYYYMMDD + 4-digit sequence
Example: SO20251108001

前缀支持系统配置，可在后台修改
"""
from datetime import date

from django.db import transaction
from django.utils import timezone


class DocumentNumberGenerator:
    """
    Unified document number generator for all document types.

    Document number format: PREFIX + YYYYMMDD + 4-digit sequence number

    前缀配置键名映射表（新）：

    【销售流程】
    - quotation: document_prefix_quotation (SQ - 报价单)
    - sales_order: document_prefix_sales_order (SO - 销售订单)
    - sales_loan: document_prefix_sales_loan (LO - 销售借用)

    【采购流程】
    - purchase_request: document_prefix_purchase_request (PR - 采购申请)
    - purchase_inquiry: document_prefix_purchase_inquiry (RFQ - 采购询价)
    - purchase_order: document_prefix_purchase_order (PO - 采购订单)
    - borrow: document_prefix_borrow (BO - 采购借用)

    【入库单据 - 统一前缀 IN】
    - receipt: document_prefix_receipt (IN - 采购收货单)
    - stock_in: document_prefix_stock_in (IN - 入库单)
    - sales_return: document_prefix_sales_return (IN - 销售退货)
    - material_return: document_prefix_material_return (IN - 退料单)

    【出库单据 - 统一前缀 OUT】
    - delivery: document_prefix_delivery (OUT - 销售发货单)
    - stock_out: document_prefix_stock_out (OUT - 出库单)
    - purchase_return: document_prefix_purchase_return (OUT - 采购退货)
    - material_requisition: document_prefix_material_requisition (OUT - 领料单)

    【库存管理】
    - stock_transfer: document_prefix_stock_transfer (INT - 调拨单)
    - stock_picking: document_prefix_stock_picking (PICK - 盘点单)
    - stock_adjustment: document_prefix_stock_adjustment (ADJ - 库存调整)
    - quality_inspection: document_prefix_quality_inspection (QC - 质检单)

    【合同管理】
    - sales_contract: document_prefix_sales_contract (SC - 销售合同)
    - purchase_contract: document_prefix_purchase_contract (PC - 采购合同)
    - loan_contract: document_prefix_loan_contract (LC - 借用合同)

    【生产管理】
    - production_plan: document_prefix_production_plan (PP - 生产计划)
    - work_order: document_prefix_work_order (MO - 生产工单)

    【财务管理】
    - payment_receipt: document_prefix_payment_receipt (PAY - 收款单)
    - payment: document_prefix_payment (BILL - 付款单)
    - invoice: document_prefix_invoice (INV - 发票)
    - refund: document_prefix_refund (RINV - 退款单)
    - expense: document_prefix_expense (EXP - 报销单)

    注意：所有入库单据使用统一前缀 IN，所有出库单据使用统一前缀 OUT，
         通过 transaction_type 或 reference_type 区分具体的单据类型。

    兼容旧前缀（直接传入前缀字符串）：
    - QT,
    SO,
    SD,
    SR,
    PI,
    PO,
    PR,
    PT,
    SI,
    ST,
    SA,
    SP,
    QI,
    SC,
    PC,
    LC,
    PP,
    WO,
    MR,
    MT,
    PM,
    PY,
    IV,
    EX,
    DL, RF
    """

    # 前缀配置键名映射表
    PREFIX_CONFIG_MAP = {
        "quotation": "document_prefix_quotation",
        "sales_order": "document_prefix_sales_order",
        "delivery": "document_prefix_delivery",
        "sales_return": "document_prefix_sales_return",
        "sales_loan": "document_prefix_sales_loan",  # 销售借用单
        "purchase_request": "document_prefix_purchase_request",  # 采购申请单
        "purchase_inquiry": "document_prefix_purchase_inquiry",
        "purchase_order": "document_prefix_purchase_order",
        "receipt": "document_prefix_receipt",
        "purchase_return": "document_prefix_purchase_return",
        "borrow": "document_prefix_borrow",  # 采购借用单
        "stock_in": "document_prefix_stock_in",
        "stock_out": "document_prefix_stock_out",
        "stock_transfer": "document_prefix_stock_transfer",
        "stock_picking": "document_prefix_stock_picking",
        "stock_adjustment": "document_prefix_stock_adjustment",
        "quality_inspection": "document_prefix_quality_inspection",
        "sales_contract": "document_prefix_sales_contract",
        "purchase_contract": "document_prefix_purchase_contract",
        "loan_contract": "document_prefix_loan_contract",
        "production_plan": "document_prefix_production_plan",
        "work_order": "document_prefix_work_order",
        "material_requisition": "document_prefix_material_requisition",
        "material_return": "document_prefix_material_return",
        "payment_receipt": "document_prefix_payment_receipt",
        "payment": "document_prefix_payment",
        "invoice": "document_prefix_invoice",
        "refund": "document_prefix_refund",
        "expense": "document_prefix_expense",
        "account_detail": "document_prefix_account_detail",  # 应付明细/应收明细
        "supplier_account": "document_prefix_supplier_account",  # 应付主单
    }

    # 旧前缀到配置键名的映射（兼容性）
    LEGACY_PREFIX_MAP = {
        "QT": "quotation",
        "SQ": "quotation",  # 新的报价单前缀
        "SO": "sales_order",
        "SD": "delivery",  # 旧的发货单前缀
        "DL": "delivery",  # 另一种旧的发货单前缀
        "SR": "sales_return",
        "LO": "sales_loan",  # 销售借用单
        "PR": "purchase_request",  # 采购申请单
        "PI": "purchase_inquiry",
        "RFQ": "purchase_inquiry",  # Odoo 标准
        "PO": "purchase_order",
        "IN": "receipt",  # 收货单
        "PT": "purchase_return",
        "BO": "borrow",  # 采购借用单
        "SI": "stock_in",
        "ST": "stock_out",
        "SA": "stock_adjustment",
        "INT": "stock_transfer",
        "SP": "stock_picking",
        "QI": "quality_inspection",
        "QC": "quality_inspection",
        "SC": "sales_contract",
        "PC": "purchase_contract",
        "LC": "loan_contract",
        "PP": "production_plan",
        "WO": "work_order",
        "MO": "work_order",  # Odoo 标准
        "MR": "material_requisition",
        "MT": "material_return",
        "MTR": "material_return",
        "PM": "payment_receipt",
        "PY": "payment",
        "IV": "invoice",
        "EX": "expense",
        "RF": "refund",
        "RINV": "refund",
    }

    @staticmethod
    def get_prefix(prefix_key):
        """
        Get the actual prefix from system configuration.

        Args:
            prefix_key (str): Prefix key name (e.g., 'sales_order') or legacy prefix (e.g., 'SO')

        Returns:
            str: Actual prefix from configuration or fallback to default

        Example:
            >>> DocumentNumberGenerator.get_prefix('sales_order')
            'SO'
            >>> DocumentNumberGenerator.get_prefix('SO')  # Legacy support
            'SO'
        """
        from core.models import SystemConfig

        # 如果是配置键名，直接获取
        if prefix_key in DocumentNumberGenerator.PREFIX_CONFIG_MAP:
            config_key = DocumentNumberGenerator.PREFIX_CONFIG_MAP[prefix_key]
        # 如果是旧前缀，先映射到配置键名
        elif prefix_key in DocumentNumberGenerator.LEGACY_PREFIX_MAP:
            config_key_name = DocumentNumberGenerator.LEGACY_PREFIX_MAP[prefix_key]
            config_key = DocumentNumberGenerator.PREFIX_CONFIG_MAP.get(config_key_name)
            # 如果找不到配置，直接返回旧前缀（向后兼容）
            if not config_key:
                return prefix_key
        else:
            # 如果都不是，假设这是一个直接传入的前缀字符串（向后兼容）
            return prefix_key

        # 从数据库获取配置
        try:
            config = SystemConfig.objects.get(key=config_key, is_active=True)
            return config.value
        except SystemConfig.DoesNotExist:
            # 如果配置不存在，尝试返回旧前缀，否则返回原始输入
            for legacy_prefix, mapped_key in DocumentNumberGenerator.LEGACY_PREFIX_MAP.items():
                if DocumentNumberGenerator.PREFIX_CONFIG_MAP.get(mapped_key) == config_key:
                    return legacy_prefix
            return prefix_key

    @staticmethod
    def get_date_format():
        """
        Get date format from system configuration.

        Returns:
            str: Date format string (YYYYMMDD, YYMMDD, or YYMM)

        Example:
            >>> DocumentNumberGenerator.get_date_format()
            'YYMMDD'
        """
        from core.models import SystemConfig

        try:
            config = SystemConfig.objects.get(key="document_number_date_format", is_active=True)
            return config.value
        except SystemConfig.DoesNotExist:
            # Default to YYMMDD if not configured
            return "YYMMDD"

    @staticmethod
    def get_sequence_digits():
        """
        Get sequence number digits from system configuration.

        Returns:
            int: Number of digits for sequence (default: 3)

        Example:
            >>> DocumentNumberGenerator.get_sequence_digits()
            3
        """
        from core.models import SystemConfig

        try:
            config = SystemConfig.objects.get(key="document_number_sequence_digits", is_active=True)
            return int(config.value)
        except (SystemConfig.DoesNotExist, ValueError):
            # Default to 3 digits if not configured or invalid
            return 3

    @staticmethod
    def format_date(date_value, date_format):
        """
        Format date according to the specified format.

        Args:
            date_value (date): Date to format
            date_format (str): Format string (YYYYMMDD, YYMMDD, or YYMM)

        Returns:
            str: Formatted date string

        Example:
            >>> from datetime import date
            >>> DocumentNumberGenerator.format_date(date(2025, 11, 8), 'YYMMDD')
            '251108'
            >>> DocumentNumberGenerator.format_date(date(2025, 11, 8), 'YYYYMMDD')
            '20251108'
            >>> DocumentNumberGenerator.format_date(date(2025, 11, 8), 'YYMM')
            '2511'
        """
        if date_format == "YYYYMMDD":
            return date_value.strftime("%Y%m%d")
        elif date_format == "YYMMDD":
            return date_value.strftime("%y%m%d")
        elif date_format == "YYMM":
            return date_value.strftime("%y%m")
        else:
            # Default to YYMMDD
            return date_value.strftime("%y%m%d")

    @staticmethod
    def generate(prefix_key, date_value=None, check_deleted=True, model_class=None):
        """
        Generate a unique document number with configurable format.

        Args:
            prefix_key (str): Document type key (e.g., 'sales_order', 'purchase_order')
                             or legacy prefix string (e.g., 'SO', 'PO')
            date_value (date, optional): Date for the document. Defaults to today.
            check_deleted (bool): Whether to check for deleted documents and reuse their numbers
            model_class (Model, optional): Model class to check for deleted documents

        Returns:
            str: Generated document number

        Example:
            >>> DocumentNumberGenerator.generate('sales_order')
            'SO251108001'  # With default YYMMDD + 3 digits
            >>> DocumentNumberGenerator.generate('SO')  # Legacy support
            'SO251108001'
        """
        if date_value is None:
            date_value = timezone.now().date()

        # Get actual prefix from configuration
        prefix = DocumentNumberGenerator.get_prefix(prefix_key)

        # Get date format and sequence digits from configuration
        date_format = DocumentNumberGenerator.get_date_format()
        sequence_digits = DocumentNumberGenerator.get_sequence_digits()

        # Format date according to configuration
        date_str = DocumentNumberGenerator.format_date(date_value, date_format)

        # Get or create document number sequence
        sequence = DocumentNumberGenerator._get_next_sequence(
            prefix, date_str, model_class, check_deleted
        )

        # Format sequence with leading zeros (configurable digits)
        sequence_str = str(sequence).zfill(sequence_digits)

        # Combine to create full document number
        document_number = f"{prefix}{date_str}{sequence_str}"

        return document_number

    @staticmethod
    def _get_next_sequence(prefix, date_str, model_class=None, check_deleted=True):
        """
        Get the next sequence number for the given prefix and date.

        Uses database-level locking to ensure uniqueness in concurrent environments.

        Args:
            prefix (str): Document type prefix
            date_str (str): Date string in YYYYMMDD format
            model_class (Model, optional): Model class to check for deleted documents
            check_deleted (bool): Whether to check for deleted documents and reuse their numbers

        Returns:
            int: Next sequence number
        """
        from core.models import DocumentNumberSequence

        with transaction.atomic():
            # Get or create sequence record with database lock
            (
                sequence_obj,
                created,
            ) = DocumentNumberSequence.objects.select_for_update().get_or_create(
                prefix=prefix, date_str=date_str, defaults={"current_number": 0}
            )

            # If requested, try to find deleted documents with reusable numbers
            if check_deleted and model_class is not None:
                # 自动检测单据号字段名
                number_field = None
                for field in model_class._meta.get_fields():
                    if field.name.endswith("_number") and hasattr(field, "max_length"):
                        number_field = field.name
                        break

                if number_field:
                    # Get active document numbers
                    active_numbers = set()
                    active_docs = model_class.objects.filter(
                        **{f"{number_field}__startswith": f"{prefix}{date_str}"}, is_deleted=False
                    )

                    for doc in active_docs:
                        try:
                            doc_number = getattr(doc, number_field)
                            number_part = doc_number[len(prefix) + len(date_str) :]
                            import re

                            match = re.search(r"(\d+)$", number_part)
                            if match:
                                seq = int(match.group(1))
                                active_numbers.add(seq)
                        except (ValueError, AttributeError):
                            pass

                    # Find missing numbers (gaps in the sequence)
                    if active_numbers:
                        max_active = max(active_numbers)
                        # Find all numbers from 1 to max_active that are not in active_numbers
                        missing_numbers = sorted(set(range(1, max_active + 1)) - active_numbers)

                        # Filter to only include missing numbers that are >= current sequence
                        # This prevents reusing numbers that were already used and the sequence has moved past
                        reusable_missing = [
                            num for num in missing_numbers if num >= sequence_obj.current_number
                        ]

                        if reusable_missing:
                            # Reuse the smallest missing number that hasn't been passed by the sequence
                            reusable_number = reusable_missing[0]
                            # Update sequence to this number (next call will increment)
                            sequence_obj.current_number = reusable_number
                            sequence_obj.save()
                            return reusable_number

            # Increment and save
            sequence_obj.current_number += 1
            sequence_obj.save()

            return sequence_obj.current_number

    @staticmethod
    def validate_number(document_number, prefix):
        """
        Validate if a document number matches the expected format (flexible validation).

        Note: This method now validates flexibly to support different date formats
        and sequence lengths. It checks if the non-prefix part contains only digits.

        Args:
            document_number (str): Document number to validate
            prefix (str): Expected prefix

        Returns:
            bool: True if valid, False otherwise

        Example:
            >>> DocumentNumberGenerator.validate_number('SO251108001', 'SO')
            True
            >>> DocumentNumberGenerator.validate_number('QT20251108001', 'QT')
            True
        """
        if not document_number or not document_number.startswith(prefix):
            return False

        # Get the part after prefix
        number_part = document_number[len(prefix) :]

        # Must be all digits
        if not number_part.isdigit():
            return False

        # Minimum length: 6 (YYMMDD) + 1 (at least 1 digit sequence) = 7
        # Maximum length: 8 (YYYYMMDD) + 5 (max sequence digits) = 13
        if len(number_part) < 7 or len(number_part) > 13:
            return False

        return True

    @staticmethod
    def parse_number(document_number, prefix, date_format=None, sequence_digits=None):
        """
        Parse a document number into its components.

        Args:
            document_number (str): Document number to parse
            prefix (str): Document prefix
            date_format (str, optional): Expected date format. If None, reads from config.
            sequence_digits (int, optional): Expected sequence digits. If None, reads from config.

        Returns:
            dict: Dictionary with 'prefix', 'date', 'sequence' keys, or None if invalid

        Example:
            >>> DocumentNumberGenerator.parse_number('SO251108001', 'SO')
            {'prefix': 'SO', 'date': date(2025, 11, 8), 'sequence': 1}
            >>> DocumentNumberGenerator.parse_number('QT20251108001', 'QT', 'YYYYMMDD', 3)
            {'prefix': 'QT', 'date': date(2025, 11, 8), 'sequence': 1}
        """
        if not DocumentNumberGenerator.validate_number(document_number, prefix):
            return None

        # Get config if not provided
        if date_format is None:
            date_format = DocumentNumberGenerator.get_date_format()
        if sequence_digits is None:
            sequence_digits = DocumentNumberGenerator.get_sequence_digits()

        # Determine date length based on format
        date_lengths = {
            "YYYYMMDD": 8,
            "YYMMDD": 6,
            "YYMM": 4,
        }
        date_length = date_lengths.get(date_format, 6)

        # Extract date and sequence parts
        date_str = document_number[len(prefix) : len(prefix) + date_length]
        sequence_str = document_number[len(prefix) + date_length :]

        try:
            # Parse date based on format
            if date_format == "YYYYMMDD":
                year = int(date_str[0:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
            elif date_format == "YYMMDD":
                year = 2000 + int(date_str[0:2])
                month = int(date_str[2:4])
                day = int(date_str[4:6])
            elif date_format == "YYMM":
                year = 2000 + int(date_str[0:2])
                month = int(date_str[2:4])
                day = 1  # Default to 1st day of month
            else:
                return None

            document_date = date(year, month, day)
            sequence = int(sequence_str)

            return {
                "prefix": prefix,
                "date": document_date,
                "sequence": sequence,
            }
        except (ValueError, TypeError):
            return None
