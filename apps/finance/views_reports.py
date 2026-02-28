"""
Financial Report Views for the ERP system.
"""

import logging
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import FinancialReport

logger = logging.getLogger(__name__)


@login_required
def financial_report_list(request):
    """
    列出所有已生成的财务报表。
    """
    reports = FinancialReport.objects.filter(is_deleted=False).select_related(
        "generated_by"
    )

    # Search
    search = request.GET.get("search", "")
    if search:
        reports = reports.filter(Q(notes__icontains=search))

    # Filter by report type
    report_type = request.GET.get("report_type", "")
    if report_type:
        reports = reports.filter(report_type=report_type)

    # Date range filter
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    if date_from:
        reports = reports.filter(report_date__gte=date_from)
    if date_to:
        reports = reports.filter(report_date__lte=date_to)

    # Sorting
    sort = request.GET.get("sort", "-report_date")
    reports = reports.order_by(sort)

    # Pagination
    paginator = Paginator(reports, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search": search,
        "report_type": report_type,
        "date_from": date_from,
        "date_to": date_to,
        "total_count": paginator.count,
        "report_type_choices": FinancialReport.REPORT_TYPES,
    }
    return render(request, "modules/finance/report_list.html", context)


@login_required
def financial_report_detail(request, pk):
    """
    显示财务报表详情。
    """
    report = get_object_or_404(
        FinancialReport.objects.filter(is_deleted=False).select_related("generated_by"),
        pk=pk,
    )

    # 根据报表类型选择不同的模板
    template_name = f"modules/finance/report_{report.report_type}.html"

    context = {
        "report": report,
    }
    return render(request, template_name, context)


@login_required
def financial_report_generator(request):
    """
    财务报表生成器主页面。
    """
    context = {
        "report_type_choices": FinancialReport.REPORT_TYPES,
    }
    return render(request, "modules/finance/report_generator.html", context)


@login_required
@transaction.atomic
def generate_balance_sheet(request):
    """
    生成资产负债表。
    """
    from .report_generator import generate_balance_sheet as generate_bs

    if request.method == "POST":
        try:
            # 获取报表日期
            report_date_str = request.POST.get("report_date")
            if not report_date_str:
                messages.error(request, "请选择报表日期！")
                return redirect("finance:report_generator")

            report_date = date.fromisoformat(report_date_str)

            # 生成报表
            logger.info(
                f"User {request.user.username} generating balance sheet for date {report_date}"
            )

            report = generate_bs(report_date=report_date, user=request.user)

            logger.info(
                f"Balance sheet generated successfully: report_id={report.id}, "
                f'total_assets={
                    report.total_assets}, is_balanced={
                    report.report_data.get("is_balanced")}'
            )

            messages.success(
                request,
                f"资产负债表生成成功！报表日期：{report_date}，"
                f"总资产：¥{report.total_assets:,.2f}，"
                f'资产负债平衡：{"是" if report.report_data.get("is_balanced") else "否"}',
            )
            return redirect("finance:report_detail", pk=report.pk)

        except Exception as e:
            logger.exception(f"Error generating balance sheet: {str(e)}")
            messages.error(request, f"生成资产负债表失败：{str(e)}")
            return redirect("finance:report_generator")

    # GET request - show form
    context = {
        "report_type": "balance_sheet",
        "report_type_name": "资产负债表",
        "default_date": date.today(),
    }
    return render(request, "modules/finance/report_form_balance_sheet.html", context)


@login_required
@transaction.atomic
def generate_income_statement(request):
    """
    生成利润表。
    """
    from .report_generator import generate_income_statement as generate_is

    if request.method == "POST":
        try:
            # 获取日期范围
            start_date_str = request.POST.get("start_date")
            end_date_str = request.POST.get("end_date")

            if not start_date_str or not end_date_str:
                messages.error(request, "请选择开始日期和结束日期！")
                return redirect("finance:report_generator")

            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)

            if start_date > end_date:
                messages.error(request, "开始日期不能晚于结束日期！")
                return redirect("finance:report_generator")

            # 生成报表
            logger.info(
                f"User {request.user.username} generating income statement "
                f"from {start_date} to {end_date}"
            )

            report = generate_is(
                start_date=start_date, end_date=end_date, user=request.user
            )

            logger.info(
                f"Income statement generated successfully: report_id={report.id}, "
                f"net_profit={report.net_profit}"
            )

            messages.success(
                request,
                f"利润表生成成功！期间：{start_date} 至 {end_date}，"
                f"净利润：¥{report.net_profit:,.2f}",
            )
            return redirect("finance:report_detail", pk=report.pk)

        except Exception as e:
            logger.exception(f"Error generating income statement: {str(e)}")
            messages.error(request, f"生成利润表失败：{str(e)}")
            return redirect("finance:report_generator")

    # GET request - show form
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)

    context = {
        "report_type": "income_statement",
        "report_type_name": "利润表",
        "default_start_date": first_day_of_month,
        "default_end_date": today,
    }
    return render(request, "modules/finance/report_form_income_statement.html", context)


@login_required
@transaction.atomic
def generate_cash_flow(request):
    """
    生成现金流量表。
    """
    from .report_generator import generate_cash_flow as generate_cf

    if request.method == "POST":
        try:
            # 获取日期范围
            start_date_str = request.POST.get("start_date")
            end_date_str = request.POST.get("end_date")

            if not start_date_str or not end_date_str:
                messages.error(request, "请选择开始日期和结束日期！")
                return redirect("finance:report_generator")

            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)

            if start_date > end_date:
                messages.error(request, "开始日期不能晚于结束日期！")
                return redirect("finance:report_generator")

            # 生成报表
            logger.info(
                f"User {request.user.username} generating cash flow statement "
                f"from {start_date} to {end_date}"
            )

            report = generate_cf(
                start_date=start_date, end_date=end_date, user=request.user
            )

            net_cash_flow = report.report_data.get("net_cash_flow", 0)

            logger.info(
                f"Cash flow statement generated successfully: report_id={report.id}, "
                f"net_cash_flow={net_cash_flow}"
            )

            messages.success(
                request,
                f"现金流量表生成成功！期间：{start_date} 至 {end_date}，"
                f"现金净增加额：¥{net_cash_flow:,.2f}",
            )
            return redirect("finance:report_detail", pk=report.pk)

        except Exception as e:
            logger.exception(f"Error generating cash flow statement: {str(e)}")
            messages.error(request, f"生成现金流量表失败：{str(e)}")
            return redirect("finance:report_generator")

    # GET request - show form
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)

    context = {
        "report_type": "cash_flow",
        "report_type_name": "现金流量表",
        "default_start_date": first_day_of_month,
        "default_end_date": today,
    }
    return render(request, "modules/finance/report_form_cash_flow.html", context)


@login_required
@transaction.atomic
def generate_trial_balance(request):
    """
    生成科目余额表。
    """
    from .report_generator import generate_trial_balance as generate_tb

    if request.method == "POST":
        try:
            # 获取日期范围
            start_date_str = request.POST.get("start_date")
            end_date_str = request.POST.get("end_date")

            if not start_date_str or not end_date_str:
                messages.error(request, "请选择开始日期和结束日期！")
                return redirect("finance:report_generator")

            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)

            if start_date > end_date:
                messages.error(request, "开始日期不能晚于结束日期！")
                return redirect("finance:report_generator")

            # 生成报表
            logger.info(
                f"User {request.user.username} generating trial balance "
                f"from {start_date} to {end_date}"
            )

            report = generate_tb(
                start_date=start_date, end_date=end_date, user=request.user
            )

            totals = report.report_data.get("totals", {})

            logger.info(
                f"Trial balance generated successfully: report_id={report.id}, "
                f'account_count={len(report.report_data.get("items", []))}'
            )

            messages.success(
                request,
                f"科目余额表生成成功！期间：{start_date} 至 {end_date}，"
                f'科目数：{len(report.report_data.get("items", []))} 个',
            )
            return redirect("finance:report_detail", pk=report.pk)

        except Exception as e:
            logger.exception(f"Error generating trial balance: {str(e)}")
            messages.error(request, f"生成科目余额表失败：{str(e)}")
            return redirect("finance:report_generator")

    # GET request - show form
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)

    context = {
        "report_type": "trial_balance",
        "report_type_name": "科目余额表",
        "default_start_date": first_day_of_month,
        "default_end_date": today,
    }
    return render(request, "modules/finance/report_form_trial_balance.html", context)
