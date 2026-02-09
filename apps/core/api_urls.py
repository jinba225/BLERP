from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import AttachmentViewSet, AuditLogViewSet, CompanyViewSet, SystemConfigViewSet

app_name = "core_api"

router = DefaultRouter()
router.register(r"companies", CompanyViewSet)
router.register(r"system-configs", SystemConfigViewSet)
router.register(r"attachments", AttachmentViewSet)
router.register(r"audit-logs", AuditLogViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
