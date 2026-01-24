"""
Core viewsets for the ERP system.
"""
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Company, SystemConfig, Attachment, AuditLog
from .serializers import (
    CompanySerializer, SystemConfigSerializer, 
    AttachmentSerializer, AuditLogSerializer
)


class CompanyViewSet(viewsets.ModelViewSet):
    """Company viewset."""
    
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'legal_representative']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']


class SystemConfigViewSet(viewsets.ModelViewSet):
    """System configuration viewset."""
    
    queryset = SystemConfig.objects.all()
    serializer_class = SystemConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['config_type', 'is_active']
    search_fields = ['key', 'value', 'description']
    ordering_fields = ['key', 'config_type', 'created_at']
    ordering = ['key']
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get configurations by type."""
        config_type = request.query_params.get('type')
        if not config_type:
            return Response({'error': 'Type parameter is required'}, status=400)
        
        configs = self.queryset.filter(config_type=config_type, is_active=True)
        serializer = self.get_serializer(configs, many=True)
        return Response(serializer.data)


class AttachmentViewSet(viewsets.ModelViewSet):
    """Attachment viewset."""
    
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['file_type', 'content_type']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'file_size', 'created_at']
    ordering = ['-created_at']


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit log viewset (read-only)."""
    
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'model_name', 'user']
    search_fields = ['object_repr', 'model_name']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']