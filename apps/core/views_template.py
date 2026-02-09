"""
Print template editor views (moved from sales module).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from .models import PrintTemplate


@login_required
def template_list(request):
    """List all print templates."""
    # 获取类别过滤参数
    category_filter = request.GET.get("category", "")

    # 基础查询
    templates = PrintTemplate.objects.filter(is_deleted=False)

    # 应用类别过滤
    if category_filter:
        templates = templates.filter(template_category=category_filter)

    templates = templates.order_by("template_category", "name")

    # 计算统计数据
    total_count = templates.count()
    active_count = templates.filter(is_active=True).count()

    # 统计不同类别的数量
    template_categories = templates.values("template_category").distinct().count()

    # 获取所有类别选项
    category_choices = PrintTemplate.CATEGORY_CHOICES

    context = {
        "templates": templates,
        "total_count": total_count,
        "active_count": active_count,
        "template_categories": template_categories,
        "category_choices": category_choices,
        "current_category": category_filter,
    }
    return render(request, "modules/sales/template_list.html", context)


@login_required
def template_create(request):
    """Create a new print template."""
    if request.method == "POST":
        try:
            template = PrintTemplate(
                name=request.POST.get("name"),
                template_category=request.POST.get("template_category", "sales"),
                is_active=request.POST.get("is_active", "on") == "on",
                company_name=request.POST.get("company_name", "BetterLaser 激光科技有限公司"),
                company_address=request.POST.get("company_address", ""),
                company_phone=request.POST.get("company_phone", ""),
                company_email=request.POST.get("company_email", ""),
                custom_css=request.POST.get("custom_css", ""),
                notes=request.POST.get("notes", ""),
                created_by=request.user,
            )

            # Get default layout config for template category
            template.layout_config = PrintTemplate.get_default_layout_config(
                template.template_category
            )

            # Parse and save layout_config from JSON if provided
            layout_json = request.POST.get("layout_config")
            if layout_json:
                try:
                    template.layout_config = json.loads(layout_json)
                except json.JSONDecodeError:
                    messages.error(request, "布局配置JSON格式错误")
                    return redirect("core:print_template_create")

            template.save()
            messages.success(request, f"模板 {template.name} 创建成功！")
            return redirect("core:print_template_edit", pk=template.pk)
        except Exception as e:
            messages.error(request, f"创建失败：{str(e)}")

    # GET request
    context = {
        "action": "create",
        "template_categories": PrintTemplate.CATEGORY_CHOICES,
    }
    return render(request, "modules/sales/template_form.html", context)


@login_required
def template_edit(request, pk):
    """Edit an existing print template with drag-and-drop editor."""
    template = get_object_or_404(PrintTemplate, pk=pk, is_deleted=False)

    if request.method == "POST":
        try:
            template.name = request.POST.get("name")
            template.template_category = request.POST.get("template_category", "sales")
            template.is_active = request.POST.get("is_active") == "on"
            template.company_name = request.POST.get("company_name", "BetterLaser 激光科技有限公司")
            template.company_address = request.POST.get("company_address", "")
            template.company_phone = request.POST.get("company_phone", "")
            template.company_email = request.POST.get("company_email", "")
            template.custom_css = request.POST.get("custom_css", "")
            template.notes = request.POST.get("notes", "")
            template.updated_by = request.user

            # Parse and save layout_config from JSON
            layout_json = request.POST.get("layout_config")
            if layout_json:
                try:
                    template.layout_config = json.loads(layout_json)
                except json.JSONDecodeError:
                    messages.error(request, "布局配置JSON格式错误")
                    return redirect("core:print_template_edit", pk=pk)

            template.save()
            messages.success(request, f"模板 {template.name} 更新成功！")
            return redirect("core:print_template_edit", pk=pk)
        except Exception as e:
            messages.error(request, f"更新失败：{str(e)}")

    # GET request - Load template configuration
    # Initialize empty template for HiPrint if layout_config is empty
    if not template.layout_config or template.layout_config == {}:
        template.layout_config = {}

    context = {
        "template": template,
        "action": "edit",
        "template_categories": PrintTemplate.CATEGORY_CHOICES,
        "layout_config_json": json.dumps(template.layout_config, ensure_ascii=False),
    }
    return render(request, "modules/sales/template_editor_hiprint_standalone.html", context)


@login_required
@require_POST
def template_delete(request, pk):
    """Delete (soft delete) a print template."""
    template = get_object_or_404(PrintTemplate, pk=pk, is_deleted=False)

    from django.utils import timezone

    template.is_deleted = True
    template.deleted_at = timezone.now()
    template.deleted_by = request.user
    template.save()

    messages.success(request, f"模板 {template.name} 已删除")
    return redirect("core:print_template_list")


@login_required
@require_POST
def template_set_default(request, pk):
    """
    Set a template as the default for specific document types.
    This function now redirects to the admin page for DefaultTemplateMapping.
    """
    template = get_object_or_404(PrintTemplate, pk=pk, is_deleted=False)

    # 提示用户使用Admin后台配置默认模板
    messages.info(
        request,
        f"模板 {template.name} 属于 {template.get_template_category_display()} 类别。"
        f'请前往 Admin 后台的"单据默认模板配置"页面,为具体的单据类型(如"报价单-国内"、"报价单-海外")设置默认模板。',
    )

    # 重定向到 Admin 的 DefaultTemplateMapping 列表页
    return redirect("/admin/core/defaulttemplatemapping/")


@login_required
@require_POST
def template_duplicate(request, pk):
    """Duplicate an existing template."""
    original = get_object_or_404(PrintTemplate, pk=pk, is_deleted=False)

    # Create a copy
    template = PrintTemplate(
        name=f"{original.name} (副本)",
        template_category=original.template_category,
        suitable_for=original.suitable_for.copy() if original.suitable_for else [],
        is_active=True,
        company_name=original.company_name,
        company_address=original.company_address,
        company_phone=original.company_phone,
        company_email=original.company_email,
        layout_config=original.layout_config.copy() if original.layout_config else {},
        custom_css=original.custom_css,
        notes=original.notes,
        created_by=request.user,
    )
    template.save()

    messages.success(request, f"模板已复制为: {template.name}")
    return redirect("core:print_template_edit", pk=template.pk)


@login_required
def template_export(request, pk):
    """Export a template as JSON file."""
    import json
    from django.http import HttpResponse
    from django.utils import timezone

    template = get_object_or_404(PrintTemplate, pk=pk, is_deleted=False)

    # Prepare export data
    export_data = {
        "name": template.name,
        "template_category": template.template_category,
        "suitable_for": template.suitable_for,
        "company_name": template.company_name,
        "company_address": template.company_address,
        "company_phone": template.company_phone,
        "company_email": template.company_email,
        "layout_config": template.layout_config,
        "custom_css": template.custom_css,
        "notes": template.notes,
        "export_version": "1.0",
        "export_date": str(timezone.now()),
    }

    # Create response
    response = HttpResponse(
        json.dumps(export_data, ensure_ascii=False, indent=2), content_type="application/json"
    )
    filename = (
        f"{template.name}_{template.template_category}_{timezone.now().strftime('%Y%m%d')}.json"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    messages.success(request, f"模板 {template.name} 已导出")
    return response


@login_required
def template_import(request):
    """Import a template from JSON file."""
    if request.method == "POST":
        try:
            import_file = request.FILES.get("import_file")
            if not import_file:
                messages.error(request, "请选择要导入的文件")
                return redirect("core:print_template_list")

            # Read and parse JSON
            import_data = json.loads(import_file.read().decode("utf-8"))

            # Validate required fields
            required_fields = ["name", "template_category", "layout_config"]
            for field in required_fields:
                if field not in import_data:
                    messages.error(request, f"导入文件缺少必需字段: {field}")
                    return redirect("core:print_template_list")

            # Create template
            template = PrintTemplate(
                name=import_data["name"] + " (导入)",
                template_category=import_data.get("template_category", "sales"),
                suitable_for=import_data.get("suitable_for", []),
                is_active=True,
                company_name=import_data.get("company_name", "BetterLaser 激光科技有限公司"),
                company_address=import_data.get("company_address", ""),
                company_phone=import_data.get("company_phone", ""),
                company_email=import_data.get("company_email", ""),
                layout_config=import_data.get("layout_config", {}),
                custom_css=import_data.get("custom_css", ""),
                notes=import_data.get("notes", ""),
                created_by=request.user,
            )
            template.save()

            messages.success(request, f"模板 {template.name} 导入成功！")
            return redirect("core:print_template_edit", pk=template.pk)

        except json.JSONDecodeError:
            messages.error(request, "文件格式错误，请上传有效的JSON文件")
        except Exception as e:
            messages.error(request, f"导入失败：{str(e)}")

        return redirect("core:print_template_list")

    # GET request - show import form
    return render(request, "modules/sales/template_import.html")


@login_required
def template_preview(request, pk):
    """Preview a template with sample data."""
    template = get_object_or_404(PrintTemplate, pk=pk, is_deleted=False)

    context = {
        "template": template,
        "layout_config_json": json.dumps(template.layout_config, ensure_ascii=False),
    }
    return render(request, "modules/sales/template_preview.html", context)


@login_required
@require_POST
def template_update_category(request, pk):
    """Update template category via AJAX."""
    try:
        template = get_object_or_404(PrintTemplate, pk=pk, is_deleted=False)
        new_category = request.POST.get("category")

        # 验证类别是否有效
        valid_categories = [choice[0] for choice in PrintTemplate.CATEGORY_CHOICES]
        if new_category not in valid_categories:
            return JsonResponse({"success": False, "error": "无效的模板类别"}, status=400)

        # 更新类别
        template.template_category = new_category
        template.updated_by = request.user
        template.save()

        return JsonResponse(
            {
                "success": True,
                "message": f"模板类别已更新为：{template.get_template_category_display()}",
                "category": new_category,
                "category_display": template.get_template_category_display(),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
