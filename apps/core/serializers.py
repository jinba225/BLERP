"""
Core serializers for ERP system.
"""
from typing import Any
from rest_framework import serializers
from .models import Company, SystemConfig, Attachment, AuditLog


class CompanySerializer(serializers.ModelSerializer):
    """Company serializer."""

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "code",
            "legal_representative",
            "registration_number",
            "tax_number",
            "address",
            "phone",
            "fax",
            "email",
            "website",
            "logo",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SystemConfigSerializer(serializers.ModelSerializer):
    """System configuration serializer."""

    class Meta:
        model = SystemConfig
        fields = [
            "id",
            "key",
            "value",
            "config_type",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AttachmentSerializer(serializers.ModelSerializer):
    """Attachment serializer."""

    def get_file_size_display(self, obj: Attachment) -> str:
        """Get formatted file size."""
        return obj.file_size_display if hasattr(obj, "file_size_display") else ""

    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = [
            "id",
            "name",
            "file",
            "file_type",
            "file_size",
            "file_size_display",
            "mime_type",
            "description",
            "content_type",
            "object_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "file_size", "created_at", "updated_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer."""

    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "user_name",
            "action",
            "model_name",
            "object_id",
            "object_repr",
            "changes",
            "ip_address",
            "user_agent",
            "timestamp",
        ]
        read_only_fields = ["id", "timestamp"]
