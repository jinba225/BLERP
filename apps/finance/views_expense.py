"""
费用管理视图

提供费用报销的完整流程：
- 费用创建和编辑
- 费用提交审批
- 费用审批（通过/拒绝）
- 费用支付
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from datetime import date

from .models import Expense, Account
from core.utils.document_number import DocumentNumberGenerator

logger = logging.getLogger(__name__)


@login_required
def expense_list(request):
    """费用列表"""
    # 基础查询（只显示未删除的费用）
    expenses = Expense.objects.filter(is_deleted=False).select_related(
        "applicant", "department", "approved_by", "paid_by"
    )

    # 搜索过滤
    search = request.GET.get("search", "")
    if search:
        expenses = expenses.filter(
            Q(expense_number__icontains=search)
            | Q(description__icontains=search)
            | Q(applicant__username__icontains=search)
        )

    # 状态过滤
    status = request.GET.get("status", "")
    if status:
        expenses = expenses.filter(status=status)

    # 费用类别过滤
    category = request.GET.get("category", "")
    if category:
        expenses = expenses.filter(category=category)

    # 日期范围过滤
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    if date_from:
        expenses = expenses.filter(expense_date__gte=date_from)
    if date_to:
        expenses = expenses.filter(expense_date__lte=date_to)

    # 排序
    sort = request.GET.get("sort", "-expense_date")
    expenses = expenses.order_by(sort)

    # 统计
    stats = expenses.aggregate(
        total_amount=Sum("amount"),
        draft_count=Sum("status", filter=Q(status="draft")),
        submitted_count=Sum("status", filter=Q(status="submitted")),
        approved_count=Sum("status", filter=Q(status="approved")),
        paid_count=Sum("status", filter=Q(status="paid")),
    )

    # 分页
    paginator = Paginator(expenses, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search": search,
        "status": status,
        "category": category,
        "date_from": date_from,
        "date_to": date_to,
        "total_count": paginator.count,
        "stats": stats,
        "status_choices": Expense.EXPENSE_STATUS,
        "category_choices": Expense.EXPENSE_CATEGORY,
    }
    return render(request, "modules/finance/expense_list.html", context)


@login_required
@transaction.atomic
def expense_create(request):
    """创建费用"""
    if request.method == "POST":
        try:
            # 生成费用单号
            expense_number = DocumentNumberGenerator.generate("expense")

            # 创建费用记录
            expense = Expense.objects.create(
                expense_number=expense_number,
                expense_date=request.POST.get("expense_date"),
                applicant=request.user,
                department_id=request.POST.get("department")
                if request.POST.get("department")
                else None,
                category=request.POST.get("category"),
                amount=request.POST.get("amount"),
                payment_method=request.POST.get("payment_method"),
                project=request.POST.get("project", ""),
                reference_number=request.POST.get("reference_number", ""),
                description=request.POST.get("description"),
                notes=request.POST.get("notes", ""),
                created_by=request.user,
                updated_by=request.user,
            )

            messages.success(request, f"费用单 {expense.expense_number} 创建成功！")
            return redirect("finance:expense_detail", pk=expense.pk)

        except Exception as e:
            logger.exception(f"创建费用失败: {str(e)}")
            messages.error(request, f"创建费用失败：{str(e)}")

    # GET请求 - 显示表单
    context = {
        "category_choices": Expense.EXPENSE_CATEGORY,
        "payment_method_choices": Expense.PAYMENT_METHOD,
        "default_date": date.today(),
    }
    return render(request, "modules/finance/expense_form.html", context)


@login_required
def expense_detail(request, pk):
    """费用详情"""
    expense = get_object_or_404(
        Expense.objects.filter(is_deleted=False).select_related(
            "applicant", "department", "approved_by", "paid_by", "payment_account", "journal"
        ),
        pk=pk,
    )

    context = {
        "expense": expense,
    }
    return render(request, "modules/finance/expense_detail.html", context)


@login_required
@transaction.atomic
def expense_edit(request, pk):
    """编辑费用"""
    expense = get_object_or_404(Expense.objects.filter(is_deleted=False), pk=pk)

    # 只有草稿状态的费用可以编辑
    if expense.status != "draft":
        messages.error(request, "只有草稿状态的费用单才能编辑！")
        return redirect("finance:expense_detail", pk=pk)

    if request.method == "POST":
        try:
            expense.expense_date = request.POST.get("expense_date")
            if request.POST.get("department"):
                expense.department_id = request.POST.get("department")
            expense.category = request.POST.get("category")
            expense.amount = request.POST.get("amount")
            expense.payment_method = request.POST.get("payment_method")
            expense.project = request.POST.get("project", "")
            expense.reference_number = request.POST.get("reference_number", "")
            expense.description = request.POST.get("description")
            expense.notes = request.POST.get("notes", "")
            expense.updated_by = request.user
            expense.save()

            messages.success(request, f"费用单 {expense.expense_number} 更新成功！")
            return redirect("finance:expense_detail", pk=pk)

        except Exception as e:
            logger.exception(f"更新费用失败: {str(e)}")
            messages.error(request, f"更新费用失败：{str(e)}")

    context = {
        "expense": expense,
        "category_choices": Expense.EXPENSE_CATEGORY,
        "payment_method_choices": Expense.PAYMENT_METHOD,
        "is_edit": True,
    }
    return render(request, "modules/finance/expense_form.html", context)


@login_required
@transaction.atomic
def expense_delete(request, pk):
    """删除费用（软删除）"""
    expense = get_object_or_404(Expense.objects.filter(is_deleted=False), pk=pk)

    # 只有草稿和已拒绝状态的费用可以删除
    if expense.status not in ["draft", "rejected"]:
        messages.error(request, "只有草稿和已拒绝状态的费用单才能删除！")
        return redirect("finance:expense_detail", pk=pk)

    if request.method == "POST":
        try:
            expense.delete()  # BaseModel的软删除
            messages.success(request, f"费用单 {expense.expense_number} 已删除！")
            return redirect("finance:expense_list")

        except Exception as e:
            logger.exception(f"删除费用失败: {str(e)}")
            messages.error(request, f"删除费用失败：{str(e)}")

    context = {
        "expense": expense,
    }
    return render(request, "modules/finance/expense_confirm_delete.html", context)


@login_required
@transaction.atomic
def expense_submit(request, pk):
    """提交费用审批"""
    expense = get_object_or_404(Expense.objects.filter(is_deleted=False), pk=pk)

    if request.method == "POST":
        try:
            expense.submit(user=request.user)
            messages.success(request, f"费用单 {expense.expense_number} 已提交审批！")
            return redirect("finance:expense_detail", pk=pk)

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.exception(f"提交费用失败: {str(e)}")
            messages.error(request, f"提交费用失败：{str(e)}")

    context = {
        "expense": expense,
    }
    return render(request, "modules/finance/expense_confirm_submit.html", context)


@login_required
@transaction.atomic
def expense_approve(request, pk):
    """审批费用（通过）"""
    expense = get_object_or_404(Expense.objects.filter(is_deleted=False), pk=pk)

    if request.method == "POST":
        try:
            expense.approve(approved_by_user=request.user)
            messages.success(request, f"费用单 {expense.expense_number} 审批通过！")
            return redirect("finance:expense_detail", pk=pk)

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.exception(f"审批费用失败: {str(e)}")
            messages.error(request, f"审批费用失败：{str(e)}")

    context = {
        "expense": expense,
    }
    return render(request, "modules/finance/expense_confirm_approve.html", context)


@login_required
@transaction.atomic
def expense_reject(request, pk):
    """审批费用（拒绝）"""
    expense = get_object_or_404(Expense.objects.filter(is_deleted=False), pk=pk)

    if request.method == "POST":
        try:
            reason = request.POST.get("reason", "")
            if not reason:
                messages.error(request, "请输入拒绝原因！")
                return redirect("finance:expense_reject", pk=pk)

            expense.reject(rejected_by_user=request.user, reason=reason)
            messages.success(request, f"费用单 {expense.expense_number} 已拒绝！")
            return redirect("finance:expense_detail", pk=pk)

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.exception(f"拒绝费用失败: {str(e)}")
            messages.error(request, f"拒绝费用失败：{str(e)}")

    context = {
        "expense": expense,
    }
    return render(request, "modules/finance/expense_confirm_reject.html", context)


@login_required
@transaction.atomic
def expense_pay(request, pk):
    """支付费用"""
    expense = get_object_or_404(Expense.objects.filter(is_deleted=False), pk=pk)

    if request.method == "POST":
        try:
            # 获取支付科目
            payment_account_id = request.POST.get("payment_account")
            payment_account = None
            if payment_account_id:
                payment_account = Account.objects.get(pk=payment_account_id, is_deleted=False)

            # 是否自动生成会计凭证
            auto_create_journal = request.POST.get("auto_create_journal") == "on"

            # 标记为已支付
            journal = expense.mark_paid(
                paid_by_user=request.user,
                payment_account=payment_account,
                auto_create_journal=auto_create_journal,
            )

            if journal:
                messages.success(
                    request,
                    f"费用单 {expense.expense_number} 已支付！会计凭证 {journal.journal_number} 已自动生成。",
                )
            else:
                messages.success(request, f"费用单 {expense.expense_number} 已支付！")

            return redirect("finance:expense_detail", pk=pk)

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.exception(f"支付费用失败: {str(e)}")
            messages.error(request, f"支付费用失败：{str(e)}")

    # GET请求 - 显示支付表单
    # 获取可用的支付科目（现金和银行存款）
    payment_accounts = Account.objects.filter(
        Q(code__startswith="1001") | Q(code__startswith="1002"),  # 库存现金、银行存款
        is_deleted=False,
        is_active=True,
    )

    context = {
        "expense": expense,
        "payment_accounts": payment_accounts,
    }
    return render(request, "modules/finance/expense_pay.html", context)
