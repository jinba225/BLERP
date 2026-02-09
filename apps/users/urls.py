"""
Users app URLs.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import (
    UserViewSet,
    RoleViewSet,
    UserRoleViewSet,
    PermissionViewSet,
    UserProfileViewSet,
    LoginLogViewSet,
)
from . import views

app_name = "users"

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"roles", RoleViewSet)
router.register(r"user-roles", UserRoleViewSet)
router.register(r"permissions", PermissionViewSet)
router.register(r"profiles", UserProfileViewSet)
router.register(r"login-logs", LoginLogViewSet)

urlpatterns = [
    # Frontend views - User Management
    path("", views.user_list, name="user_list"),
    path("create/", views.user_create, name="user_create"),
    path("<int:pk>/", views.user_detail, name="user_detail"),
    path("<int:pk>/edit/", views.user_update, name="user_update"),
    path("<int:pk>/delete/", views.user_delete, name="user_delete"),
    path("<int:pk>/toggle-status/", views.user_toggle_status, name="user_toggle_status"),
    # Frontend views - Role Management
    path("roles/", views.role_list, name="role_list"),
    path("roles/create/", views.role_create, name="role_create"),
    path("roles/<int:pk>/", views.role_detail, name="role_detail"),
    path("roles/<int:pk>/edit/", views.role_update, name="role_update"),
    path("roles/<int:pk>/delete/", views.role_delete, name="role_delete"),
    path("roles/<int:pk>/permissions/", views.role_permissions, name="role_permissions"),
    path("roles/<int:pk>/assign-users/", views.role_assign_users, name="role_assign_users"),
    path(
        "roles/<int:pk>/remove-user/<int:user_id>/", views.role_remove_user, name="role_remove_user"
    ),
    # Frontend views - Login Logs
    path("login-logs/", views.login_log_list, name="login_log_list"),
    # API routes
    path("api/", include(router.urls)),
]
