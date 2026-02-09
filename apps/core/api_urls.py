from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import CompanyViewSet, SystemConfigViewSet, AttachmentViewSet, AuditLogViewSet

app_name = "core_api"

router = DefaultRouter()
router.register(r"companies", CompanyViewSet)
router.register(r"system-configs", SystemConfigViewSet)
router.register(r"attachments", AttachmentViewSet)
router.register(r"audit-logs", AuditLogViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
