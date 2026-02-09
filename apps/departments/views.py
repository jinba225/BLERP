"""
Department views for the ERP system.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone

from .models import Department, Position, DepartmentBudget


@login_required
def department_list(request):
    """
    List all departments in a tree structure.
    """
    departments = Department.objects.filter(is_deleted=False).select_related("parent", "manager")

    # Search
    search = request.GET.get("search", "")
    if search:
        departments = departments.filter(
            Q(name__icontains=search) | Q(code__icontains=search) | Q(description__icontains=search)
        )

    # Filter by active status
    is_active = request.GET.get("is_active", "")
    if is_active:
        departments = departments.filter(is_active=is_active == "true")

    # Filter by parent (root departments)
    show_root_only = request.GET.get("root_only", "")
    if show_root_only == "true":
        departments = departments.filter(parent__isnull=True)

    # Get tree structure
    if not search and not show_root_only:
        # Show full tree
        departments = Department.objects.filter(is_deleted=False).select_related(
            "parent", "manager"
        )

    context = {
        "departments": departments,
        "search": search,
        "is_active": is_active,
        "show_root_only": show_root_only,
    }
    return render(request, "modules/departments/department_list.html", context)


@login_required
def department_detail(request, pk):
    """
    Display department details with employees, positions, and sub-departments.
    """
    department = get_object_or_404(
        Department.objects.filter(is_deleted=False).select_related("parent", "manager"), pk=pk
    )

    # Get all employees in this department
    employees = department.get_all_employees()

    # Get positions in this department
    positions = Position.objects.filter(department=department, is_deleted=False)

    # Get budgets for this department
    budgets = DepartmentBudget.objects.filter(department=department, is_deleted=False).order_by(
        "-year", "-quarter", "-month"
    )[:12]

    # Get child departments
    children = department.get_children().filter(is_deleted=False)

    context = {
        "department": department,
        "employees": employees,
        "positions": positions,
        "budgets": budgets,
        "children": children,
        "employee_count": department.get_employee_count(),
    }
    return render(request, "modules/departments/department_detail.html", context)


@login_required
def department_tree(request):
    """
    Display department organization tree.
    """
    # Get root departments
    root_departments = (
        Department.objects.filter(is_deleted=False, parent__isnull=True)
        .select_related("manager")
        .prefetch_related("children")
    )

    context = {
        "root_departments": root_departments,
    }
    return render(request, "modules/departments/department_tree.html", context)


@login_required
def position_list(request):
    """
    List all positions with search and filter capabilities.
    """
    positions = Position.objects.filter(is_deleted=False).select_related("department")

    # Search
    search = request.GET.get("search", "")
    if search:
        positions = positions.filter(
            Q(name__icontains=search) | Q(code__icontains=search) | Q(description__icontains=search)
        )

    # Filter by department
    department_id = request.GET.get("department", "")
    if department_id:
        positions = positions.filter(department_id=department_id)

    # Filter by level
    level = request.GET.get("level", "")
    if level:
        positions = positions.filter(level=level)

    # Filter by active status
    is_active = request.GET.get("is_active", "")
    if is_active:
        positions = positions.filter(is_active=is_active == "true")

    # Sorting - 按创建时间降序（最新的在最上面）
    sort = request.GET.get("sort", "-created_at")
    positions = positions.order_by(sort)

    # Pagination
    paginator = Paginator(positions, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get departments for filter
    departments = Department.objects.filter(is_active=True, is_deleted=False)

    context = {
        "page_obj": page_obj,
        "search": search,
        "department_id": department_id,
        "level": level,
        "is_active": is_active,
        "departments": departments,
        "total_count": paginator.count,
    }
    return render(request, "modules/departments/position_list.html", context)


@login_required
def position_detail(request, pk):
    """
    Display position details with employees.
    """
    position = get_object_or_404(
        Position.objects.filter(is_deleted=False).select_related("department"), pk=pk
    )

    # Get employees with this position
    from users.models import User

    employees = User.objects.filter(position=position.name, is_active=True)

    context = {
        "position": position,
        "employees": employees,
        "employee_count": position.get_employee_count(),
    }
    return render(request, "modules/departments/position_detail.html", context)


@login_required
def budget_list(request):
    """
    List all department budgets.
    """
    budgets = DepartmentBudget.objects.filter(is_deleted=False).select_related(
        "department", "approved_by"
    )

    # Search
    search = request.GET.get("search", "")
    if search:
        budgets = budgets.filter(Q(department__name__icontains=search) | Q(notes__icontains=search))

    # Filter by department
    department_id = request.GET.get("department", "")
    if department_id:
        budgets = budgets.filter(department_id=department_id)

    # Filter by budget type
    budget_type = request.GET.get("budget_type", "")
    if budget_type:
        budgets = budgets.filter(budget_type=budget_type)

    # Filter by year
    year = request.GET.get("year", "")
    if year:
        budgets = budgets.filter(year=year)

    # Filter by approval status
    is_approved = request.GET.get("is_approved", "")
    if is_approved:
        budgets = budgets.filter(is_approved=is_approved == "true")

    # Sorting - 按创建时间降序（最新的在最上面）
    sort = request.GET.get("sort", "-created_at")
    budgets = budgets.order_by(sort)

    # Pagination
    paginator = Paginator(budgets, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get departments for filter
    departments = Department.objects.filter(is_active=True, is_deleted=False)

    # Calculate totals
    totals = budgets.aggregate(
        total_budget=Sum("personnel_budget")
        + Sum("operational_budget")
        + Sum("equipment_budget")
        + Sum("other_budget"),
        total_actual=Sum("personnel_actual")
        + Sum("operational_actual")
        + Sum("equipment_actual")
        + Sum("other_actual"),
    )

    context = {
        "page_obj": page_obj,
        "search": search,
        "department_id": department_id,
        "budget_type": budget_type,
        "year": year,
        "is_approved": is_approved,
        "departments": departments,
        "total_count": paginator.count,
        "totals": totals,
    }
    return render(request, "modules/departments/budget_list.html", context)


@login_required
def budget_detail(request, pk):
    """
    Display budget details with variance analysis.
    """
    budget = get_object_or_404(
        DepartmentBudget.objects.filter(is_deleted=False).select_related(
            "department", "approved_by"
        ),
        pk=pk,
    )

    context = {
        "budget": budget,
    }
    return render(request, "modules/departments/budget_detail.html", context)


@login_required
def budget_summary(request):
    """
    Display budget summary and comparison across departments.
    """
    # Get filter parameters
    year = request.GET.get("year", timezone.now().year)
    budget_type = request.GET.get("budget_type", "annual")

    # Get budgets
    budgets = DepartmentBudget.objects.filter(
        is_deleted=False, year=year, budget_type=budget_type, is_approved=True
    ).select_related("department")

    # Calculate overall totals
    overall_totals = budgets.aggregate(
        total_personnel_budget=Sum("personnel_budget"),
        total_operational_budget=Sum("operational_budget"),
        total_equipment_budget=Sum("equipment_budget"),
        total_other_budget=Sum("other_budget"),
        total_personnel_actual=Sum("personnel_actual"),
        total_operational_actual=Sum("operational_actual"),
        total_equipment_actual=Sum("equipment_actual"),
        total_other_actual=Sum("other_actual"),
    )

    context = {
        "budgets": budgets,
        "year": year,
        "budget_type": budget_type,
        "overall_totals": overall_totals,
    }
    return render(request, "modules/departments/budget_summary.html", context)


@login_required
def organization_chart(request):
    """
    Display organization chart with departments and positions.
    """
    # Get root departments
    root_departments = (
        Department.objects.filter(is_deleted=False, is_active=True, parent__isnull=True)
        .select_related("manager")
        .prefetch_related("children__manager", "positions")
    )

    context = {
        "root_departments": root_departments,
    }
    return render(request, "modules/departments/organization_chart.html", context)
