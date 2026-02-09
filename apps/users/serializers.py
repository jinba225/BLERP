"""
User serializers for ERP system.
"""
from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import LoginLog, Permission, Role, UserProfile, UserRole

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User serializer."""

    def get_full_name(self, obj: User) -> str:
        """Get full name of user."""
        return obj.get_full_name() if hasattr(obj, "get_full_name") else ""

    def get_display_name(self, obj: User) -> str:
        """Get display name for user."""
        return obj.display_name if hasattr(obj, "display_name") else ""

    full_name = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "display_name",
            "phone",
            "avatar",
            "gender",
            "birth_date",
            "employee_id",
            "hire_date",
            "department",
            "department_name",
            "position",
            "manager",
            "is_active",
            "last_login",
            "date_joined",
        ]
        read_only_fields = ["id", "last_login", "date_joined"]
        extra_kwargs = {"password": {"write_only": True}}


class UserCreateSerializer(serializers.ModelSerializer):
    """User creation serializer."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone",
            "employee_id",
            "department",
            "position",
            "manager",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("密码不匹配")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class RoleSerializer(serializers.ModelSerializer):
    """Role serializer."""

    def get_permissions_count(self, obj: Role) -> int:
        """Get permissions count for role."""
        return obj.permissions.count()

    permissions_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "code",
            "description",
            "is_active",
            "permissions",
            "permissions_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserRoleSerializer(serializers.ModelSerializer):
    """User role serializer."""

    user_name = serializers.CharField(source="user.username", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = UserRole
        fields = [
            "id",
            "user",
            "user_name",
            "role",
            "role_name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PermissionSerializer(serializers.ModelSerializer):
    """Permission serializer."""

    class Meta:
        model = Permission
        fields = [
            "id",
            "name",
            "code",
            "permission_type",
            "module",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer."""

    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "user_name",
            "id_card",
            "address",
            "emergency_contact",
            "emergency_phone",
            "salary",
            "bank_account",
            "bank_name",
            "language",
            "timezone",
            "theme",
            "email_notifications",
            "sms_notifications",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LoginLogSerializer(serializers.ModelSerializer):
    """Login log serializer."""

    def get_session_duration(self, obj: LoginLog) -> str:
        """Get formatted session duration."""
        duration = obj.session_duration if hasattr(obj, "session_duration") else None
        if duration:
            return str(duration)
        return ""

    user_name = serializers.CharField(source="user.username", read_only=True)
    session_duration = serializers.SerializerMethodField()

    class Meta:
        model = LoginLog
        fields = [
            "id",
            "user",
            "user_name",
            "login_type",
            "ip_address",
            "user_agent",
            "location",
            "is_successful",
            "failure_reason",
            "login_time",
            "logout_time",
            "session_duration",
        ]
        read_only_fields = ["id", "login_time"]
