"""
Core app URLs.
"""
from django.urls import path

from . import views
from . import views_database as db_views
from . import views_template as tpl_views

app_name = "core"

urlpatterns = [
    path("", db_views.database_management, name="settings_root"),
    path("print-templates/", tpl_views.template_list, name="print_template_list"),
    path("print-templates/create/", tpl_views.template_create, name="print_template_create"),
    path("print-templates/<int:pk>/edit/", tpl_views.template_edit, name="print_template_edit"),
    path(
        "print-templates/<int:pk>/delete/", tpl_views.template_delete, name="print_template_delete"
    ),
    path(
        "print-templates/<int:pk>/preview/",
        tpl_views.template_preview,
        name="print_template_preview",
    ),
    path(
        "print-templates/<int:pk>/set-default/",
        tpl_views.template_set_default,
        name="print_template_set_default",
    ),
    path(
        "print-templates/<int:pk>/duplicate/",
        tpl_views.template_duplicate,
        name="print_template_duplicate",
    ),
    path("print-templates/export/", tpl_views.template_export, name="print_template_export"),
    path("print-templates/import/", tpl_views.template_import, name="print_template_import"),
    path(
        "print-templates/<int:pk>/update-category/",
        tpl_views.template_update_category,
        name="print_template_update_category",
    ),
    path("database/", db_views.database_management, name="database_management"),
    path("database/add-test-data/", db_views.add_test_data, name="database_add_test_data"),
    path("database/clear-test-data/", db_views.clear_test_data, name="database_clear_test_data"),
    path("database/backup/", db_views.backup_database, name="database_backup"),
    path("database/restore/", db_views.restore_database, name="database_restore_database"),
    path(
        "database/download/<str:filename>/",
        db_views.download_backup,
        name="database_download_backup",
    ),
    path("page-refresh-demo/", views.page_refresh_demo_view, name="page_refresh_demo"),
]
