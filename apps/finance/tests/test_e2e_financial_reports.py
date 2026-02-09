"""
Django ERP 财务报表端到端测试

完整测试财务报表业务流程:
1. 资产负债表生成和验证
2. 利润表生成和验证
3. 现金流量表生成和验证
4. 报表间数据一致性验证

关键验证:
- 会计凭证的借贷平衡
- 报表数据的准确计算
- 三大报表间的勾稽关系
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from core.tests.test_fixtures import FixtureFactory
from django.utils import timezone
from finance.models import Account, Journal, JournalEntry
from finance.report_generator import FinancialReportGenerator


@pytest.mark.django_db
@pytest.mark.e2e
class TestFinancialReportsE2E:
    """财务报表端到端测试"""

    def setup_accounts(self):
        """
        创建标准会计科目体系

        资产类:
        - 1001: 库存现金
        - 1122: 应收账款
        - 1403: 原材料
        - 1601: 固定资产

        负债类:
        - 2202: 应付账款
        - 2221: 应付职工薪酬

        权益类:
        - 4001: 实收资本
        - 4103: 本年利润

        成本类:
        - 5001: 生产成本

        收入类:
        - 6001: 主营业务收入

        费用类:
        - 6601: 销售费用
        - 6602: 管理费用
        """
        # 资产类科目
        self.cash_account = Account.objects.create(
            code="1001",
            name="库存现金",
            account_type="asset",
            category="current_asset",
            opening_balance=Decimal("100000.00"),
        )

        self.ar_account = Account.objects.create(
            code="1122",
            name="应收账款",
            account_type="asset",
            category="current_asset",
            opening_balance=Decimal("50000.00"),
        )

        self.material_account = Account.objects.create(
            code="1403",
            name="原材料",
            account_type="asset",
            category="current_asset",
            opening_balance=Decimal("80000.00"),
        )

        self.fixed_asset_account = Account.objects.create(
            code="1601",
            name="固定资产",
            account_type="asset",
            category="fixed_asset",
            opening_balance=Decimal("500000.00"),
        )

        # 负债类科目
        self.ap_account = Account.objects.create(
            code="2202",
            name="应付账款",
            account_type="liability",
            category="current_liability",
            opening_balance=Decimal("30000.00"),
        )

        self.payroll_account = Account.objects.create(
            code="2221",
            name="应付职工薪酬",
            account_type="liability",
            category="current_liability",
            opening_balance=Decimal("20000.00"),
        )

        # 权益类科目
        self.capital_account = Account.objects.create(
            code="4001",
            name="实收资本",
            account_type="equity",
            opening_balance=Decimal("600000.00"),
        )

        self.profit_account = Account.objects.create(
            code="4103",
            name="本年利润",
            account_type="equity",
            opening_balance=Decimal("80000.00"),
        )

        # 成本类科目
        self.cost_account = Account.objects.create(
            code="5001",
            name="生产成本",
            account_type="cost",
            opening_balance=Decimal("0"),
        )

        # 收入类科目
        self.revenue_account = Account.objects.create(
            code="6001",
            name="主营业务收入",
            account_type="revenue",
            opening_balance=Decimal("0"),
        )

        # 费用类科目
        self.sales_expense_account = Account.objects.create(
            code="6601",
            name="销售费用",
            account_type="expense",
            opening_balance=Decimal("0"),
        )

        self.admin_expense_account = Account.objects.create(
            code="6602",
            name="管理费用",
            account_type="expense",
            opening_balance=Decimal("0"),
        )

    def create_journal_entry(self, user, journal_date, entries_data, description="测试凭证"):
        """
        创建会计凭证

        Args:
            user: 创建用户
            journal_date: 凭证日期
            entries_data: 分录列表
                [{
                    'account': Account实例,
                    'debit_amount': 借方金额,
                    'credit_amount': 贷方金额,
                    'description': 摘要
                }]
            description: 凭证摘要

        Returns:
            Journal: 创建的凭证
        """
        # 验证借贷平衡
        total_debit = sum(item["debit_amount"] for item in entries_data)
        total_credit = sum(item["credit_amount"] for item in entries_data)

        if total_debit != total_credit:
            raise ValueError(f"借贷不平衡: 借方={total_debit}, 贷方={total_credit}")

        # 创建凭证
        journal = Journal.objects.create(
            journal_number=f'JE-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}',
            journal_type="general",
            status="posted",  # 直接过账
            journal_date=journal_date,
            period=f"{journal_date.year}-{journal_date.month:02d}",
            description=description,
            created_by=user,
        )

        # 创建分录
        for entry_data in entries_data:
            JournalEntry.objects.create(
                journal=journal,
                account=entry_data["account"],
                debit_amount=entry_data["debit_amount"],
                credit_amount=entry_data["credit_amount"],
                description=entry_data.get("description", ""),
            )

        return journal

    def test_balance_sheet_generation(self, test_users):
        """
        测试: 资产负债表生成和验证

        流程:
        1. 创建标准会计科目
        2. 创建会计凭证并过账
        3. 生成资产负债表
        4. 验证: 资产总计 = 负债总计 + 所有者权益总计
        """
        # 准备数据
        admin = test_users["admin"]
        report_date = date(2026, 1, 31)

        # 1. 创建会计科目
        self.setup_accounts()

        # 2. 创建会计凭证
        # 凭证1: 销售商品（应收账款增加，收入增加）
        self.create_journal_entry(
            user=admin,
            journal_date=date(2026, 1, 15),
            entries_data=[
                {
                    "account": self.ar_account,
                    "debit_amount": Decimal("50000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "销售商品A",
                },
                {
                    "account": self.revenue_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal("50000.00"),
                    "description": "销售商品A",
                },
            ],
            description="销售商品",
        )

        # 凭证2: 支付销售费用
        self.create_journal_entry(
            user=admin,
            journal_date=date(2026, 1, 20),
            entries_data=[
                {
                    "account": self.sales_expense_account,
                    "debit_amount": Decimal("5000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "支付广告费",
                },
                {
                    "account": self.cash_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal("5000.00"),
                    "description": "支付广告费",
                },
            ],
            description="支付广告费",
        )

        # 凭证3: 支付管理费用
        self.create_journal_entry(
            user=admin,
            journal_date=date(2026, 1, 25),
            entries_data=[
                {
                    "account": self.admin_expense_account,
                    "debit_amount": Decimal("3000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "支付办公费",
                },
                {
                    "account": self.cash_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal("3000.00"),
                    "description": "支付办公费",
                },
            ],
            description="支付办公费",
        )

        # 3. 使用报表生成器计算科目余额
        generator = FinancialReportGenerator()

        # 计算资产类科目余额
        cash_balance = generator.get_account_balance("1001", report_date)
        ar_balance = generator.get_account_balance("1122", report_date)
        material_balance = generator.get_account_balance("1403", report_date)
        fixed_asset_balance = generator.get_account_balance("1601", report_date)

        # 计算负债类科目余额
        ap_balance = generator.get_account_balance("2202", report_date)
        payroll_balance = generator.get_account_balance("2221", report_date)

        # 计算权益类科目余额
        capital_balance = generator.get_account_balance("4001", report_date)
        profit_balance = generator.get_account_balance("4103", report_date)

        # 计算收入和费用科目余额（期间发生额）
        revenue_balance = generator.get_account_balance(
            "6001", report_date, start_date=date(2026, 1, 1)
        )
        sales_expense_balance = generator.get_account_balance(
            "6601", report_date, start_date=date(2026, 1, 1)
        )
        admin_expense_balance = generator.get_account_balance(
            "6602", report_date, start_date=date(2026, 1, 1)
        )

        # 4. 验证资产负债表平衡
        # 资产总计
        total_assets = (
            cash_balance["ending_balance"]
            + ar_balance["ending_balance"]
            + material_balance["ending_balance"]
            + fixed_asset_balance["ending_balance"]
        )

        # 负债总计
        total_liabilities = ap_balance["ending_balance"] + payroll_balance["ending_balance"]

        # 权益总计（包含本期利润）
        net_income = (
            revenue_balance["credit"]
            - sales_expense_balance["debit"]  # 收入贷方发生额
            - admin_expense_balance["debit"]  # 费用借方发生额
        )

        total_equity = (
            capital_balance["ending_balance"]
            + profit_balance["ending_balance"]
            + net_income  # 本期净利润增加所有者权益
        )

        # 验证: 资产 = 负债 + 权益
        assert abs(total_assets - (total_liabilities + total_equity)) < Decimal(
            "0.01"
        ), f"资产负债表不平衡: 资产={total_assets}, 负债+权益={total_liabilities + total_equity}"

        # 验证具体数值
        assert cash_balance["ending_balance"] == Decimal("92000.00")  # 100000 - 5000 - 3000
        assert ar_balance["ending_balance"] == Decimal("100000.00")  # 50000 + 50000
        assert net_income == Decimal("42000.00")  # 50000 - 5000 - 3000

    def test_income_statement_generation(self, test_users):
        """
        测试: 利润表生成和验证

        流程:
        1. 创建会计科目
        2. 创建会计凭证（收入、成本、费用）
        3. 生成利润表
        4. 验证: 收入 - 成本 - 费用 = 利润
        """
        # 准备数据
        admin = test_users["admin"]
        report_date = date(2026, 1, 31)
        start_date = date(2026, 1, 1)

        # 1. 创建会计科目
        self.setup_accounts()

        # 2. 创建会计凭证
        # 凭证1: 确认收入100000元
        self.create_journal_entry(
            user=admin,
            journal_date=date(2026, 1, 10),
            entries_data=[
                {
                    "account": self.ar_account,
                    "debit_amount": Decimal("100000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "销售商品",
                },
                {
                    "account": self.revenue_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal("100000.00"),
                    "description": "销售商品",
                },
            ],
            description="确认销售收入",
        )

        # 凭证2: 确认销售成本60000元
        self.create_journal_entry(
            user=admin,
            journal_date=date(2026, 1, 10),
            entries_data=[
                {
                    "account": self.cost_account,
                    "debit_amount": Decimal("60000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "结转销售成本",
                },
                {
                    "account": self.material_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal("60000.00"),
                    "description": "结转销售成本",
                },
            ],
            description="结转销售成本",
        )

        # 凭证3: 支付销售费用10000元
        self.create_journal_entry(
            user=admin,
            journal_date=date(2026, 1, 15),
            entries_data=[
                {
                    "account": self.sales_expense_account,
                    "debit_amount": Decimal("10000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "广告费",
                },
                {
                    "account": self.cash_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal("10000.00"),
                    "description": "广告费",
                },
            ],
            description="支付广告费",
        )

        # 凭证4: 支付管理费用8000元
        self.create_journal_entry(
            user=admin,
            journal_date=date(2026, 1, 20),
            entries_data=[
                {
                    "account": self.admin_expense_account,
                    "debit_amount": Decimal("8000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "办公费",
                },
                {
                    "account": self.cash_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal("8000.00"),
                    "description": "办公费",
                },
            ],
            description="支付办公费",
        )

        # 3. 使用报表生成器计算期间发生额
        generator = FinancialReportGenerator()

        # 计算收入
        revenue_balance = generator.get_account_balance("6001", report_date, start_date=start_date)
        operating_revenue = revenue_balance["credit"]  # 收入科目贷方发生额

        # 计算成本
        cost_balance = generator.get_account_balance("5001", report_date, start_date=start_date)
        operating_cost = cost_balance["debit"]  # 成本科目借方发生额

        # 计算费用
        sales_expense_balance = generator.get_account_balance(
            "6601", report_date, start_date=start_date
        )
        sales_expense = sales_expense_balance["debit"]

        admin_expense_balance = generator.get_account_balance(
            "6602", report_date, start_date=start_date
        )
        admin_expense = admin_expense_balance["debit"]

        total_expenses = sales_expense + admin_expense

        # 4. 计算利润
        gross_profit = operating_revenue - operating_cost  # 毛利
        operating_profit = gross_profit - total_expenses  # 营业利润
        net_profit = operating_profit  # 净利润（简化计算）

        # 验证利润计算
        assert operating_revenue == Decimal("100000.00"), f"收入错误: {operating_revenue}"
        assert operating_cost == Decimal("60000.00"), f"成本错误: {operating_cost}"
        assert sales_expense == Decimal("10000.00"), f"销售费用错误: {sales_expense}"
        assert admin_expense == Decimal("8000.00"), f"管理费用错误: {admin_expense}"

        assert gross_profit == Decimal("40000.00"), f"毛利错误: {gross_profit}"
        assert net_profit == Decimal("22000.00"), f"净利润错误: {net_profit}"

        # 验证公式: 收入 - 成本 - 费用 = 利润
        calculated_profit = operating_revenue - operating_cost - total_expenses
        assert abs(calculated_profit - net_profit) < Decimal(
            "0.01"
        ), f"利润计算错误: {calculated_profit} != {net_profit}"

    def test_cash_flow_statement_generation(self, test_users):
        """
        测试: 现金流量表生成和验证

        流程:
        1. 创建会计科目
        2. 创建现金收付凭证
        3. 生成现金流量表
        4. 验证: 现金净增加额 = 期末现金 - 期初现金
        """
        # 准备数据
        admin = test_users["admin"]
        report_date = date(2026, 1, 31)
        start_date = date(2026, 1, 1)

        # 1. 创建会计科目
        self.setup_accounts()

        # 期初现金余额
        opening_cash = Decimal("100000.00")

        # 2. 创建现金收付凭证
        # 现金流入: 收回应收账款30000元
        self.create_journal_entry(
            user=admin,
            journal_date=date(2026, 1, 10),
            entries_data=[
                {
                    "account": self.cash_account,
                    "debit_amount": Decimal("30000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "收回货款",
                },
                {
                    "account": self.ar_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal("30000.00"),
                    "description": "收回货款",
                },
            ],
            description="收回货款",
        )

        # 现金流出: 支付应付账款20000元
        self.create_journal_entry(
            user=admin,
            journal_date=date(2026, 1, 15),
            entries_data=[
                {
                    "account": self.ap_account,
                    "debit_amount": Decimal("20000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "支付货款",
                },
                {
                    "account": self.cash_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal("20000.00"),
                    "description": "支付货款",
                },
            ],
            description="支付货款",
        )

        # 现金流出: 支付工资15000元
        self.create_journal_entry(
            user=admin,
            journal_date=date(2026, 1, 25),
            entries_data=[
                {
                    "account": self.payroll_account,
                    "debit_amount": Decimal("15000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "支付工资",
                },
                {
                    "account": self.cash_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal("15000.00"),
                    "description": "支付工资",
                },
            ],
            description="支付工资",
        )

        # 3. 计算现金流量
        generator = FinancialReportGenerator()
        cash_balance = generator.get_account_balance("1001", report_date, start_date=start_date)

        # 期间现金变动
        cash_inflow = cash_balance["debit"]  # 借方发生额（现金流入）
        cash_outflow = cash_balance["credit"]  # 贷方发生额（现金流出）
        net_cash_change = cash_inflow - cash_outflow  # 现金净增加额

        # 期末现金余额
        ending_cash = cash_balance["ending_balance"]

        # 4. 验证现金流量
        assert cash_inflow == Decimal("30000.00"), f"现金流入错误: {cash_inflow}"
        assert cash_outflow == Decimal("35000.00"), f"现金流出错误: {cash_outflow}"
        assert net_cash_change == Decimal("-5000.00"), f"现金净增加额错误: {net_cash_change}"

        # 验证: 期末现金 = 期初现金 + 现金净增加额
        expected_ending_cash = opening_cash + net_cash_change
        assert abs(ending_cash - expected_ending_cash) < Decimal(
            "0.01"
        ), f"期末现金计算错误: {ending_cash} != {expected_ending_cash}"

    def test_report_data_consistency(self, test_users):
        """
        测试: 报表间数据一致性验证

        验证三大报表之间的勾稽关系:
        1. 资产负债表中的未分配利润变动 = 利润表中的净利润
        2. 现金流量表中的现金变动 = 资产负债表中的货币资金变动
        3. 利润表中的收入 = 相关科目期间发生额
        """
        # 准备数据
        admin = test_users["admin"]
        report_date = date(2026, 1, 31)
        start_date = date(2026, 1, 1)

        # 1. 创建会计科目
        self.setup_accounts()

        # 2. 创建综合业务凭证
        # 销售商品: 收入80000元，成本50000元
        self.create_journal_entry(
            user=admin,
            journal_date=date(2026, 1, 10),
            entries_data=[
                {
                    "account": self.ar_account,
                    "debit_amount": Decimal("80000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "销售商品",
                },
                {
                    "account": self.revenue_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal("80000.00"),
                    "description": "销售商品",
                },
            ],
            description="销售商品",
        )

        self.create_journal_entry(
            user=admin,
            journal_date=date(2026, 1, 10),
            entries_data=[
                {
                    "account": self.cost_account,
                    "debit_amount": Decimal("50000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "结转成本",
                },
                {
                    "account": self.material_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal("50000.00"),
                    "description": "结转成本",
                },
            ],
            description="结转成本",
        )

        # 支付费用
        self.create_journal_entry(
            user=admin,
            journal_date=date(2026, 1, 15),
            entries_data=[
                {
                    "account": self.sales_expense_account,
                    "debit_amount": Decimal("8000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "销售费用",
                },
                {
                    "account": self.admin_expense_account,
                    "debit_amount": Decimal("5000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "管理费用",
                },
                {
                    "account": self.cash_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal("13000.00"),
                    "description": "支付费用",
                },
            ],
            description="支付费用",
        )

        # 收回应收账款
        self.create_journal_entry(
            user=admin,
            journal_date=date(2026, 1, 20),
            entries_data=[
                {
                    "account": self.cash_account,
                    "debit_amount": Decimal("40000.00"),
                    "credit_amount": Decimal("0"),
                    "description": "收款",
                },
                {
                    "account": self.ar_account,
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal("40000.00"),
                    "description": "收款",
                },
            ],
            description="收回应收账款",
        )

        # 3. 计算各报表数据
        generator = FinancialReportGenerator()

        # 资产负债表数据
        cash_balance = generator.get_account_balance("1001", report_date)
        ar_balance = generator.get_account_balance("1122", report_date)
        profit_balance = generator.get_account_balance("4103", report_date)

        # 利润表数据
        revenue_balance = generator.get_account_balance("6001", report_date, start_date=start_date)
        cost_balance = generator.get_account_balance("5001", report_date, start_date=start_date)
        sales_expense_balance = generator.get_account_balance(
            "6601", report_date, start_date=start_date
        )
        admin_expense_balance = generator.get_account_balance(
            "6602", report_date, start_date=start_date
        )

        # 现金流量数据
        cash_flow = generator.get_account_balance("1001", report_date, start_date=start_date)

        # 4. 验证勾稽关系

        # 验证1: 净利润计算正确性
        net_income = (
            revenue_balance["credit"]
            - cost_balance["debit"]
            - sales_expense_balance["debit"]
            - admin_expense_balance["debit"]
        )
        assert net_income == Decimal("17000.00"), f"净利润错误: {net_income}"

        # 验证2: 现金变动 = 流入 - 流出
        net_cash_change = cash_flow["debit"] - cash_flow["credit"]
        expected_cash_change = Decimal("40000.00") - Decimal("13000.00")  # 40000流入 - 13000流出
        assert abs(net_cash_change - expected_cash_change) < Decimal(
            "0.01"
        ), f"现金变动错误: {net_cash_change} != {expected_cash_change}"

        # 验证3: 应收账款余额 = 期初 + 借方 - 贷方
        expected_ar = Decimal("50000.00") + Decimal("80000.00") - Decimal("40000.00")
        assert abs(ar_balance["ending_balance"] - expected_ar) < Decimal(
            "0.01"
        ), f"应收账款错误: {ar_balance['ending_balance']} != {expected_ar}"

        # 验证4: 现金余额 = 期初 + 借方 - 贷方
        expected_cash = Decimal("100000.00") + Decimal("40000.00") - Decimal("13000.00")
        assert abs(cash_balance["ending_balance"] - expected_cash) < Decimal(
            "0.01"
        ), f"现金余额错误: {cash_balance['ending_balance']} != {expected_cash}"

        # 验证5: 资产负债平衡
        total_assets = (
            cash_balance["ending_balance"]
            + ar_balance["ending_balance"]
            + generator.get_account_balance("1403", report_date)["ending_balance"]
            + generator.get_account_balance("1601", report_date)["ending_balance"]
        )

        total_liabilities = (
            generator.get_account_balance("2202", report_date)["ending_balance"]
            + generator.get_account_balance("2221", report_date)["ending_balance"]
        )

        total_equity = (
            generator.get_account_balance("4001", report_date)["ending_balance"]
            + profit_balance["ending_balance"]
            + net_income  # 本期净利润
        )

        assert abs(total_assets - (total_liabilities + total_equity)) < Decimal(
            "0.01"
        ), f"资产负债不平衡: 资产={total_assets}, 负债+权益={total_liabilities + total_equity}"
