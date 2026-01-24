"""
财务报表生成器

自动生成各类财务报表，包括：
- 资产负债表
- 利润表
- 现金流量表
- 科目余额表
- 科目明细账
"""
import logging
from decimal import Decimal
from datetime import date
from django.db.models import Sum, Q
from django.utils import timezone

from .models import Account, Journal, JournalEntry, FinancialReport

logger = logging.getLogger(__name__)


class FinancialReportGenerator:
    """
    财务报表生成器基类
    """

    def __init__(self):
        self.accounts_cache = {}  # 科目缓存

    def get_account_balance(self, account_code, report_date, start_date=None):
        """
        计算指定日期的科目余额

        Args:
            account_code: 科目代码
            report_date: 报表日期
            start_date: 开始日期（用于利润表等期间报表）

        Returns:
            dict: {
                'opening_balance': 期初余额,
                'debit': 借方发生额,
                'credit': 贷方发生额,
                'ending_balance': 期末余额
            }
        """
        try:
            account = Account.objects.get(code=account_code, is_deleted=False)
        except Account.DoesNotExist:
            logger.warning(f'Account {account_code} not found')
            return {
                'opening_balance': Decimal('0'),
                'debit': Decimal('0'),
                'credit': Decimal('0'),
                'ending_balance': Decimal('0')
            }

        # 获取期初余额
        opening_balance = account.opening_balance

        # 计算发生额（只统计已过账的凭证）
        entries = JournalEntry.objects.filter(
            account=account,
            journal__status='posted',
            journal__journal_date__lte=report_date,
            is_deleted=False
        )

        # 如果指定了开始日期，只统计期间内的发生额
        if start_date:
            entries = entries.filter(journal__journal_date__gte=start_date)

        aggregation = entries.aggregate(
            total_debit=Sum('debit_amount'),
            total_credit=Sum('credit_amount')
        )

        debit = aggregation['total_debit'] or Decimal('0')
        credit = aggregation['total_credit'] or Decimal('0')

        # 计算期末余额
        # 资产类、费用类、成本类：余额在借方，借增贷减
        # 负债类、权益类、收入类：余额在贷方，贷增借减
        if account.account_type in ['asset', 'expense', 'cost']:
            ending_balance = opening_balance + debit - credit
        else:  # liability, equity, revenue
            ending_balance = opening_balance + credit - debit

        return {
            'opening_balance': opening_balance,
            'debit': debit,
            'credit': credit,
            'ending_balance': ending_balance
        }

    def get_accounts_by_type(self, account_type):
        """
        获取指定类型的所有末级科目

        Args:
            account_type: 科目类型 (asset/liability/equity/revenue/expense/cost)

        Returns:
            QuerySet: 科目查询集
        """
        return Account.objects.filter(
            account_type=account_type,
            is_leaf=True,  # 只获取末级科目
            is_active=True,
            is_deleted=False
        )

    def save_report(self, report_type, report_date, report_data, user=None, **kwargs):
        """
        保存报表数据

        Args:
            report_type: 报表类型
            report_date: 报表日期
            report_data: 报表数据（dict）
            user: 生成人
            **kwargs: 其他字段（start_date, end_date等）

        Returns:
            FinancialReport: 保存的报表对象
        """
        report = FinancialReport.objects.create(
            report_type=report_type,
            report_date=report_date,
            report_data=report_data,
            generated_by=user,
            **kwargs
        )

        logger.info(
            f'Financial report generated: {report.get_report_type_display()} '
            f'for date {report_date} by user {user.username if user else "System"}'
        )

        return report


class BalanceSheetGenerator(FinancialReportGenerator):
    """
    资产负债表生成器

    资产负债表反映企业在某一特定日期的财务状况。
    会计恒等式：资产 = 负债 + 所有者权益
    """

    def generate(self, report_date, user=None):
        """
        生成资产负债表

        Args:
            report_date: 报表日期（截止日期）
            user: 生成人

        Returns:
            FinancialReport: 生成的报表对象
        """
        logger.info(f'Generating Balance Sheet for date {report_date}')

        # 1. 资产
        assets = self._calculate_assets(report_date)

        # 2. 负债
        liabilities = self._calculate_liabilities(report_date)

        # 3. 所有者权益
        equity = self._calculate_equity(report_date)

        # 4. 验证平衡
        total_assets = assets['total']
        total_liabilities = liabilities['total']
        total_equity = equity['total']
        total_liabilities_and_equity = total_liabilities + total_equity

        is_balanced = abs(total_assets - total_liabilities_and_equity) < Decimal('0.01')

        if not is_balanced:
            logger.warning(
                f'Balance Sheet not balanced! Assets: {total_assets}, '
                f'Liabilities + Equity: {total_liabilities_and_equity}'
            )

        # 5. 构建报表数据
        report_data = {
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'is_balanced': is_balanced,
            'balance_difference': float(total_assets - total_liabilities_and_equity)
        }

        # 6. 保存报表
        report = self.save_report(
            report_type='balance_sheet',
            report_date=report_date,
            report_data=report_data,
            user=user,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=total_equity
        )

        return report

    def _calculate_assets(self, report_date):
        """计算资产"""
        accounts = self.get_accounts_by_type('asset')

        current_assets = []  # 流动资产
        fixed_assets = []  # 固定资产
        other_assets = []  # 其他资产

        total = Decimal('0')

        for account in accounts:
            balance_data = self.get_account_balance(account.code, report_date)
            ending_balance = balance_data['ending_balance']

            if ending_balance == 0:
                continue  # 跳过余额为0的科目

            item = {
                'code': account.code,
                'name': account.name,
                'amount': float(ending_balance)
            }

            # 根据科目分类归类
            if account.category == 'current_asset':
                current_assets.append(item)
            elif account.category == 'fixed_asset':
                fixed_assets.append(item)
            else:
                other_assets.append(item)

            total += ending_balance

        return {
            'current_assets': current_assets,
            'current_assets_total': float(sum(Decimal(str(item['amount'])) for item in current_assets)),
            'fixed_assets': fixed_assets,
            'fixed_assets_total': float(sum(Decimal(str(item['amount'])) for item in fixed_assets)),
            'other_assets': other_assets,
            'other_assets_total': float(sum(Decimal(str(item['amount'])) for item in other_assets)),
            'total': float(total)
        }

    def _calculate_liabilities(self, report_date):
        """计算负债"""
        accounts = self.get_accounts_by_type('liability')

        current_liabilities = []  # 流动负债
        long_term_liabilities = []  # 长期负债
        other_liabilities = []  # 其他负债

        total = Decimal('0')

        for account in accounts:
            balance_data = self.get_account_balance(account.code, report_date)
            ending_balance = balance_data['ending_balance']

            if ending_balance == 0:
                continue

            item = {
                'code': account.code,
                'name': account.name,
                'amount': float(ending_balance)
            }

            if account.category == 'current_liability':
                current_liabilities.append(item)
            elif account.category == 'long_term_liability':
                long_term_liabilities.append(item)
            else:
                other_liabilities.append(item)

            total += ending_balance

        return {
            'current_liabilities': current_liabilities,
            'current_liabilities_total': float(sum(Decimal(str(item['amount'])) for item in current_liabilities)),
            'long_term_liabilities': long_term_liabilities,
            'long_term_liabilities_total': float(sum(Decimal(str(item['amount'])) for item in long_term_liabilities)),
            'other_liabilities': other_liabilities,
            'other_liabilities_total': float(sum(Decimal(str(item['amount'])) for item in other_liabilities)),
            'total': float(total)
        }

    def _calculate_equity(self, report_date):
        """计算所有者权益"""
        accounts = self.get_accounts_by_type('equity')

        items = []
        total = Decimal('0')

        for account in accounts:
            balance_data = self.get_account_balance(account.code, report_date)
            ending_balance = balance_data['ending_balance']

            if ending_balance == 0:
                continue

            items.append({
                'code': account.code,
                'name': account.name,
                'amount': float(ending_balance)
            })

            total += ending_balance

        return {
            'items': items,
            'total': float(total)
        }


class IncomeStatementGenerator(FinancialReportGenerator):
    """
    利润表生成器

    利润表反映企业在一定期间的经营成果。
    利润 = 收入 - 成本 - 费用
    """

    def generate(self, start_date, end_date, user=None):
        """
        生成利润表

        Args:
            start_date: 开始日期
            end_date: 结束日期
            user: 生成人

        Returns:
            FinancialReport: 生成的报表对象
        """
        logger.info(f'Generating Income Statement from {start_date} to {end_date}')

        # 1. 营业收入
        revenue = self._calculate_revenue(start_date, end_date)

        # 2. 营业成本
        cost = self._calculate_cost(start_date, end_date)

        # 3. 费用
        expenses = self._calculate_expenses(start_date, end_date)

        # 4. 计算利润
        gross_profit = revenue['total'] - cost['total']  # 毛利润
        operating_profit = gross_profit - expenses['total']  # 营业利润
        net_profit = operating_profit  # 净利润（简化版，未考虑营业外收支和所得税）

        # 5. 构建报表数据
        report_data = {
            'revenue': revenue,
            'cost': cost,
            'expenses': expenses,
            'gross_profit': float(gross_profit),
            'operating_profit': float(operating_profit),
            'net_profit': float(net_profit)
        }

        # 6. 保存报表
        report = self.save_report(
            report_type='income_statement',
            report_date=end_date,
            start_date=start_date,
            end_date=end_date,
            report_data=report_data,
            user=user,
            net_profit=net_profit
        )

        return report

    def _calculate_revenue(self, start_date, end_date):
        """计算收入"""
        accounts = self.get_accounts_by_type('revenue')

        items = []
        total = Decimal('0')

        for account in accounts:
            balance_data = self.get_account_balance(account.code, end_date, start_date)
            # 收入类科目，贷方表示收入增加
            amount = balance_data['credit'] - balance_data['debit']

            if amount == 0:
                continue

            items.append({
                'code': account.code,
                'name': account.name,
                'amount': float(amount)
            })

            total += amount

        return {
            'items': items,
            'total': float(total)
        }

    def _calculate_cost(self, start_date, end_date):
        """计算成本"""
        accounts = self.get_accounts_by_type('cost')

        items = []
        total = Decimal('0')

        for account in accounts:
            balance_data = self.get_account_balance(account.code, end_date, start_date)
            # 成本类科目，借方表示成本增加
            amount = balance_data['debit'] - balance_data['credit']

            if amount == 0:
                continue

            items.append({
                'code': account.code,
                'name': account.name,
                'amount': float(amount)
            })

            total += amount

        return {
            'items': items,
            'total': float(total)
        }

    def _calculate_expenses(self, start_date, end_date):
        """计算费用"""
        accounts = self.get_accounts_by_type('expense')

        items = []
        total = Decimal('0')

        for account in accounts:
            balance_data = self.get_account_balance(account.code, end_date, start_date)
            # 费用类科目，借方表示费用增加
            amount = balance_data['debit'] - balance_data['credit']

            if amount == 0:
                continue

            items.append({
                'code': account.code,
                'name': account.name,
                'amount': float(amount)
            })

            total += amount

        return {
            'items': items,
            'total': float(total)
        }


class CashFlowGenerator(FinancialReportGenerator):
    """
    现金流量表生成器

    现金流量表反映企业一定期间现金和现金等价物的流入和流出情况。
    分为三大活动：经营活动、投资活动、筹资活动
    """

    def generate(self, start_date, end_date, user=None):
        """
        生成现金流量表

        Args:
            start_date: 开始日期
            end_date: 结束日期
            user: 生成人

        Returns:
            FinancialReport: 生成的报表对象
        """
        logger.info(f'Generating Cash Flow Statement from {start_date} to {end_date}')

        # 简化版：只计算现金类科目的变动
        # 完整版需要根据凭证的业务类型分类到不同活动

        # 1. 获取现金类科目（库存现金、银行存款）
        cash_accounts = Account.objects.filter(
            Q(code__startswith='1001') | Q(code__startswith='1002'),  # 库存现金、银行存款
            is_deleted=False,
            is_active=True
        )

        total_cash_inflow = Decimal('0')
        total_cash_outflow = Decimal('0')

        cash_items = []

        for account in cash_accounts:
            balance_data = self.get_account_balance(account.code, end_date, start_date)

            cash_inflow = balance_data['debit']  # 现金流入
            cash_outflow = balance_data['credit']  # 现金流出

            cash_items.append({
                'code': account.code,
                'name': account.name,
                'inflow': float(cash_inflow),
                'outflow': float(cash_outflow),
                'net': float(cash_inflow - cash_outflow)
            })

            total_cash_inflow += cash_inflow
            total_cash_outflow += cash_outflow

        net_cash_flow = total_cash_inflow - total_cash_outflow

        # 构建报表数据（简化版）
        report_data = {
            'cash_items': cash_items,
            'total_inflow': float(total_cash_inflow),
            'total_outflow': float(total_cash_outflow),
            'net_cash_flow': float(net_cash_flow),
            'note': '简化版现金流量表，仅统计现金类科目变动'
        }

        # 保存报表
        report = self.save_report(
            report_type='cash_flow',
            report_date=end_date,
            start_date=start_date,
            end_date=end_date,
            report_data=report_data,
            user=user
        )

        return report


class TrialBalanceGenerator(FinancialReportGenerator):
    """
    科目余额表生成器

    科目余额表列示所有科目的期初余额、本期发生额、期末余额。
    """

    def generate(self, start_date, end_date, user=None):
        """
        生成科目余额表

        Args:
            start_date: 开始日期
            end_date: 结束日期
            user: 生成人

        Returns:
            FinancialReport: 生成的报表对象
        """
        logger.info(f'Generating Trial Balance from {start_date} to {end_date}')

        # 获取所有末级科目
        accounts = Account.objects.filter(
            is_leaf=True,
            is_active=True,
            is_deleted=False
        ).order_by('code')

        items = []
        total_opening_debit = Decimal('0')
        total_opening_credit = Decimal('0')
        total_debit = Decimal('0')
        total_credit = Decimal('0')
        total_ending_debit = Decimal('0')
        total_ending_credit = Decimal('0')

        for account in accounts:
            balance_data = self.get_account_balance(account.code, end_date, start_date)

            opening_balance = balance_data['opening_balance']
            debit = balance_data['debit']
            credit = balance_data['credit']
            ending_balance = balance_data['ending_balance']

            # 判断借贷方向
            if account.account_type in ['asset', 'expense', 'cost']:
                # 借方余额
                opening_debit = max(opening_balance, Decimal('0'))
                opening_credit = Decimal('0')
                ending_debit = max(ending_balance, Decimal('0'))
                ending_credit = Decimal('0')
            else:
                # 贷方余额
                opening_debit = Decimal('0')
                opening_credit = max(opening_balance, Decimal('0'))
                ending_debit = Decimal('0')
                ending_credit = max(ending_balance, Decimal('0'))

            # 如果全部为0，跳过
            if (opening_debit == 0 and opening_credit == 0 and
                debit == 0 and credit == 0 and
                ending_debit == 0 and ending_credit == 0):
                continue

            items.append({
                'code': account.code,
                'name': account.name,
                'account_type': account.get_account_type_display(),
                'opening_debit': float(opening_debit),
                'opening_credit': float(opening_credit),
                'debit': float(debit),
                'credit': float(credit),
                'ending_debit': float(ending_debit),
                'ending_credit': float(ending_credit)
            })

            total_opening_debit += opening_debit
            total_opening_credit += opening_credit
            total_debit += debit
            total_credit += credit
            total_ending_debit += ending_debit
            total_ending_credit += ending_credit

        # 构建报表数据
        report_data = {
            'items': items,
            'totals': {
                'opening_debit': float(total_opening_debit),
                'opening_credit': float(total_opening_credit),
                'debit': float(total_debit),
                'credit': float(total_credit),
                'ending_debit': float(total_ending_debit),
                'ending_credit': float(total_ending_credit)
            }
        }

        # 保存报表
        report = self.save_report(
            report_type='trial_balance',
            report_date=end_date,
            start_date=start_date,
            end_date=end_date,
            report_data=report_data,
            user=user
        )

        return report


# 便捷函数
def generate_balance_sheet(report_date=None, user=None):
    """生成资产负债表"""
    if report_date is None:
        report_date = date.today()
    generator = BalanceSheetGenerator()
    return generator.generate(report_date, user)


def generate_income_statement(start_date, end_date, user=None):
    """生成利润表"""
    generator = IncomeStatementGenerator()
    return generator.generate(start_date, end_date, user)


def generate_cash_flow(start_date, end_date, user=None):
    """生成现金流量表"""
    generator = CashFlowGenerator()
    return generator.generate(start_date, end_date, user)


def generate_trial_balance(start_date, end_date, user=None):
    """生成科目余额表"""
    generator = TrialBalanceGenerator()
    return generator.generate(start_date, end_date, user)
