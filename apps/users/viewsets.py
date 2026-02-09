"""
User viewsets for the ERP system.
"""
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from .models import Role, UserRole, Permission, UserProfile, LoginLog
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    RoleSerializer,
    UserRoleSerializer,
    PermissionSerializer,
    UserProfileSerializer,
    LoginLogSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """User viewset."""

    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "department", "gender"]
    search_fields = ["username", "email", "first_name", "last_name", "employee_id"]
    ordering_fields = ["username", "email", "date_joined", "last_login"]
    ordering = ["username"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    @action(detail=True, methods=["post"])
    def set_password(self, request, pk=None):
        """Set user password."""
        user = self.get_object()
        password = request.data.get("password")

        if not password:
            return Response({"error": "密码不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()

        return Response({"message": "密码设置成功"})

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate user."""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({"message": "用户已激活"})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Deactivate user."""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({"message": "用户已停用"})


class RoleViewSet(viewsets.ModelViewSet):
    """Role viewset."""

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["name", "code", "description"]
    ordering_fields = ["name", "code", "created_at"]
    ordering = ["name"]

    @action(detail=True, methods=["get"])
    def users(self, request, pk=None):
        """Get users with this role."""
        role = self.get_object()
        user_roles = UserRole.objects.filter(role=role, is_active=True)
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response(serializer.data)


class UserRoleViewSet(viewsets.ModelViewSet):
    """User role viewset."""

    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["user", "role", "is_active"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]


class PermissionViewSet(viewsets.ModelViewSet):
    """Permission viewset."""

    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["permission_type", "module", "is_active"]
    search_fields = ["name", "code", "description"]
    ordering_fields = ["name", "code", "module"]
    ordering = ["module", "name"]


class UserProfileViewSet(viewsets.ModelViewSet):
    """User profile viewset."""

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["user", "language", "timezone"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    @action(detail=False, methods=["get", "put"])
    def me(self, request):
        """Get or update current user's profile."""
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)

        if request.method == "GET":
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        elif request.method == "PUT":
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Login log viewset (read-only)."""

    queryset = LoginLog.objects.all()
    serializer_class = LoginLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["user", "login_type", "is_successful"]
    ordering_fields = ["login_time"]
    ordering = ["-login_time"]
