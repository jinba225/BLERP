"""
Departments app URLs.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "departments"

router = DefaultRouter()

urlpatterns = [
    # API routes
    path("api/", include(router.urls)),
    # Department URLs
    path("", views.department_list, name="department_list"),
    path("<int:pk>/", views.department_detail, name="department_detail"),
    path("tree/", views.department_tree, name="department_tree"),
    path("organization-chart/", views.organization_chart, name="organization_chart"),
    # Position URLs
    path("positions/", views.position_list, name="position_list"),
    path("positions/<int:pk>/", views.position_detail, name="position_detail"),
    # Budget URLs
    path("budgets/", views.budget_list, name="budget_list"),
    path("budgets/<int:pk>/", views.budget_detail, name="budget_detail"),
    path("budgets/summary/", views.budget_summary, name="budget_summary"),
]
