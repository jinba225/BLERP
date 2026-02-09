"""
数据库管理视图
提供数据库备份、还原、测试数据管理等功能的Web界面
"""
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import FileResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .models import AuditLog
from .utils.database_helper import DatabaseHelper


def is_superuser(user):
    """检查用户是否为超级管理员"""
    return user.is_superuser


@login_required
@user_passes_test(is_superuser)
@require_http_methods(["GET"])
def database_management(request):
    """
    数据库管理主页面
    显示数据库信息、备份列表等
    """
    # 获取数据库信息
    db_info = DatabaseHelper.get_db_info()

    # 获取备份列表
    backups = DatabaseHelper.list_backups()

    context = {
        "db_info": db_info,
        "backups": backups,
        "page_title": "数据库管理",
    }

    return render(request, "modules/core/database_management.html", context)


@login_required
@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def add_test_data(request):
    """添加测试数据"""
    try:
        success, message, stats = DatabaseHelper.add_test_data()

        # 记录审计日志
        AuditLog.objects.create(
            user=request.user,
            action="create",
            model_name="DatabaseManagement",
            object_repr="添加测试数据",
            changes={"stats": stats},
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        if success:
            messages.success(request, message)
            return JsonResponse({"success": True, "message": message, "stats": stats})
        else:
            messages.error(request, message)
            return JsonResponse({"success": False, "message": message}, status=400)

    except Exception as e:
        error_msg = f"添加测试数据时发生错误: {str(e)}"
        messages.error(request, error_msg)
        return JsonResponse({"success": False, "message": error_msg}, status=500)


@login_required
@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def clear_test_data(request):
    """清除测试数据"""
    try:
        success, message, stats = DatabaseHelper.clear_test_data()

        # 记录审计日志
        AuditLog.objects.create(
            user=request.user,
            action="delete",
            model_name="DatabaseManagement",
            object_repr="清除测试数据",
            changes={"stats": stats},
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        if success:
            messages.success(request, message)
            return JsonResponse({"success": True, "message": message, "stats": stats})
        else:
            messages.error(request, message)
            return JsonResponse({"success": False, "message": message}, status=400)

    except Exception as e:
        error_msg = f"清除测试数据时发生错误: {str(e)}"
        messages.error(request, error_msg)
        return JsonResponse({"success": False, "message": error_msg}, status=500)


@login_required
@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def backup_database(request):
    """备份数据库"""
    try:
        success, message, backup_path = DatabaseHelper.backup_database()

        # 记录审计日志
        AuditLog.objects.create(
            user=request.user,
            action="export",
            model_name="DatabaseManagement",
            object_repr="备份数据库",
            changes={"backup_file": str(backup_path) if backup_path else None},
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        if success:
            messages.success(request, message)
            return JsonResponse(
                {
                    "success": True,
                    "message": message,
                    "backup_file": Path(backup_path).name if backup_path else None,
                }
            )
        else:
            messages.error(request, message)
            return JsonResponse({"success": False, "message": message}, status=400)

    except Exception as e:
        error_msg = f"备份数据库时发生错误: {str(e)}"
        messages.error(request, error_msg)
        return JsonResponse({"success": False, "message": error_msg}, status=500)


@login_required
@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def restore_database(request):
    """还原数据库"""
    try:
        backup_file = request.POST.get("backup_file")
        if not backup_file:
            return JsonResponse({"success": False, "message": "请选择备份文件"}, status=400)

        # 构建完整路径
        backup_dir = DatabaseHelper.get_backup_dir()
        backup_path = backup_dir / backup_file

        success, message = DatabaseHelper.restore_database(str(backup_path))

        # 记录审计日志
        AuditLog.objects.create(
            user=request.user,
            action="import",
            model_name="DatabaseManagement",
            object_repr="还原数据库",
            changes={"backup_file": backup_file},
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        if success:
            messages.success(request, message)
            return JsonResponse({"success": True, "message": message})
        else:
            messages.error(request, message)
            return JsonResponse({"success": False, "message": message}, status=400)

    except Exception as e:
        error_msg = f"还原数据库时发生错误: {str(e)}"
        messages.error(request, error_msg)
        return JsonResponse({"success": False, "message": error_msg}, status=500)


@login_required
@user_passes_test(is_superuser)
@require_http_methods(["GET"])
def download_backup(request, filename):
    """下载备份文件"""
    try:
        backup_dir = DatabaseHelper.get_backup_dir()
        file_path = backup_dir / filename

        if not file_path.exists():
            messages.error(request, "备份文件不存在")
            return redirect("core:database_management")

        # 记录审计日志
        AuditLog.objects.create(
            user=request.user,
            action="export",
            model_name="DatabaseManagement",
            object_repr=f"下载备份文件: {filename}",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return FileResponse(open(file_path, "rb"), as_attachment=True, filename=filename)

    except Exception as e:
        messages.error(request, f"下载备份文件时发生错误: {str(e)}")
        return redirect("core:database_management")
