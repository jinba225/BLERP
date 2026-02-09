"""
Core views for the ERP system.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import datetime, timedelta


@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        remember_me = request.POST.get("remember_me")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Set session expiry
            if not remember_me:
                request.session.set_expiry(0)  # Session expires when browser closes
            else:
                request.session.set_expiry(1209600)  # 2 weeks

            # Redirect to next page or dashboard
            next_url = request.GET.get("next", "/")
            return redirect(next_url)
        else:
            messages.error(request, "用户名或密码错误")

    return render(request, "modules/core/login.html")


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, "您已成功退出登录")
    return redirect("login")


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard view.
    """

    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get current date and calculate periods
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

        # Sales statistics
        try:
            from sales.models import SalesOrder

            # Current month sales
            current_month_sales = SalesOrder.objects.filter(
                order_date__gte=current_month_start,
                status__in=["confirmed", "shipped", "delivered", "completed"],
            ).aggregate(total=Sum("total_amount"), count=Count("id"))

            # Last month sales for comparison
            last_month_sales = SalesOrder.objects.filter(
                order_date__gte=last_month_start,
                order_date__lt=current_month_start,
                status__in=["confirmed", "shipped", "delivered", "completed"],
            ).aggregate(total=Sum("total_amount"))

            # Pending orders
            pending_orders = SalesOrder.objects.filter(
                status__in=["draft", "pending", "confirmed"]
            ).count()

            context.update(
                {
                    "current_month_sales": current_month_sales["total"] or 0,
                    "sales_orders_count": current_month_sales["count"] or 0,
                    "pending_orders": pending_orders,
                    "last_month_sales": last_month_sales["total"] or 0,
                }
            )

        except ImportError:
            context.update(
                {
                    "current_month_sales": 0,
                    "sales_orders_count": 0,
                    "pending_orders": 0,
                    "last_month_sales": 0,
                }
            )

        # Inventory statistics
        try:
            from inventory.models import InventoryStock
            from products.models import Product

            # Low stock items
            low_stock_items = (
                Product.objects.filter(stocks__quantity__lte=F("min_stock"), is_active=True)
                .distinct()
                .count()
            )

            context["low_stock_items"] = low_stock_items

        except ImportError:
            context["low_stock_items"] = 0

        # Customer statistics
        try:
            from customers.models import Customer

            # New customers this month
            new_customers = Customer.objects.filter(created_at__gte=current_month_start).count()

            context["new_customers"] = new_customers

        except ImportError:
            context["new_customers"] = 0

        # Recent orders for dashboard
        try:
            from sales.models import SalesOrder

            recent_orders = SalesOrder.objects.select_related("customer").order_by("-created_at")[
                :5
            ]

            context["recent_orders"] = recent_orders

        except ImportError:
            context["recent_orders"] = []

        return context


@login_required
def dashboard_view(request):
    """
    Simple function-based dashboard view.
    """
    context = {
        "title": "仪表盘",
        "user": request.user,
    }
    return render(request, "index.html", context)


@login_required
def page_refresh_demo_view(request):
    """
    页面自动刷新功能演示视图
    """
    # 自定义页面刷新配置（演示用）
    request.page_refresh_config = {
        "interval": 15,  # 演示页面使用较短间隔
        "show_notifications": True,  # 启用Toast通知
    }

    context = {
        "title": "页面刷新功能演示",
        "user": request.user,
    }
    return render(request, "modules/core/page_refresh_demo.html", context)
