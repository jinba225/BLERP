"""
Core app URLs.
"""
from django.urls import path


# 导入数据库管理视图
from .views_database import (
    database_management,
    add_test_data as database_add_test_data,
    clear_test_data as database_clear_test_data,
    backup_database as database_backup_database,
    restore_database as database_restore_database,
    download_backup as database_download_backup,
)

# 导入打印模板视图
from .views_template import (
    template_list,
    template_create,
    template_edit,
    template_delete,
    template_preview,
    template_set_default,
    template_duplicate,
    template_export,
    template_import,
    template_update_category,
)

app_name = 'core'




urlpatterns = [
    # ============================================
    # Print Templates (打印模板管理)
    # ============================================
    path('print-templates/', template_list, name='print_template_list'),
    path('print-templates/create/', template_create, name='print_template_create'),
    path('print-templates/<int:pk>/edit/', template_edit, name='print_template_edit'),
    path('print-templates/<int:pk>/delete/', template_delete, name='print_template_delete'),
    path('print-templates/<int:pk>/preview/', template_preview, name='print_template_preview'),
    path('print-templates/<int:pk>/set-default/', template_set_default, name='print_template_set_default'),
    path('print-templates/<int:pk>/duplicate/', template_duplicate, name='print_template_duplicate'),
    path('print-templates/export/', template_export, name='print_template_export'),
    path('print-templates/import/', template_import, name='print_template_import'),
    path('print-templates/<int:pk>/update-category/', template_update_category, name='print_template_update_category'),

    # ============================================
    # Database Management (数据库管理)
    # ============================================
    path('database/', database_management, name='database_management'),
    path('database/add-test-data/', database_add_test_data, name='database_add_test_data'),
    path('database/client-test-data/', database_clear_test_data, name='database_clear_test_data'),
    path('database/backup/', database_backup_database, name='database_backup'),
    path('database/restore/', database_restore_database, name='database_restore_database'),
    path('database/download/<str:filename>/', database_download_backup, name='database_download_backup'),
]
