"""
AI Assistant 视图函数

提供AI模型配置管理的Web界面
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from .models import AIModelConfig
from .services import AIService
from .utils import encrypt_api_key, decrypt_api_key


@login_required
def model_config_list(request):
    """
    AI模型配置列表页

    显示所有AI模型配置，支持筛选和搜索
    """
    # 获取筛选参数
    provider = request.GET.get('provider', '')
    is_active = request.GET.get('is_active', '')
    search = request.GET.get('search', '')

    # 基础查询
    configs = AIModelConfig.objects.filter(is_deleted=False)

    # 应用筛选
    if provider:
        configs = configs.filter(provider=provider)

    if is_active:
        configs = configs.filter(is_active=(is_active == 'true'))

    if search:
        configs = configs.filter(name__icontains=search)

    # 排序（默认配置优先，然后按优先级）
    configs = configs.order_by('-is_default', '-priority', '-created_at')

    # 分页
    paginator = Paginator(configs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # 统计数据
    total_count = AIModelConfig.objects.filter(is_deleted=False).count()
    active_count = AIModelConfig.objects.filter(is_deleted=False, is_active=True).count()
    default_config = AIModelConfig.objects.filter(is_deleted=False, is_default=True).first()

    # Provider选项（用于筛选）
    provider_choices = AIModelConfig.PROVIDER_CHOICES

    context = {
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'default_config': default_config,
        'provider_choices': provider_choices,
        'current_provider': provider,
        'current_is_active': is_active,
        'search': search,
    }

    return render(request, 'ai_assistant/model_config_list.html', context)


@login_required
def model_config_create(request):
    """
    创建AI模型配置

    支持所有Provider类型的配置创建
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 获取表单数据
                name = request.POST.get('name')
                provider = request.POST.get('provider')
                api_key = request.POST.get('api_key')
                api_base = request.POST.get('api_base', '').strip()
                model_name = request.POST.get('model_name')
                temperature = request.POST.get('temperature', '0.7')
                max_tokens = request.POST.get('max_tokens', '2000')
                timeout = request.POST.get('timeout', '60')
                priority = request.POST.get('priority', '0')
                is_active = request.POST.get('is_active') == 'on'
                is_default = request.POST.get('is_default') == 'on'
                description = request.POST.get('description', '')

                # 验证必填字段
                if not all([name, provider, api_key, model_name]):
                    messages.error(request, '请填写所有必填字段 (>_<)')
                    return redirect('ai_assistant:model_config_create')

                # 如果设置为默认，取消其他配置的默认状态
                if is_default:
                    AIModelConfig.objects.filter(is_default=True).update(is_default=False)

                # 加密API Key
                encrypted_key = encrypt_api_key(api_key)

                # 创建配置
                config = AIModelConfig.objects.create(
                    name=name,
                    provider=provider,
                    api_key=encrypted_key,
                    api_base=api_base if api_base else None,
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=int(max_tokens),
                    timeout=int(timeout),
                    priority=int(priority),
                    is_active=is_active,
                    is_default=is_default,
                    description=description,
                    created_by=request.user,
                )

                messages.success(request, f'AI模型配置 "{name}" 创建成功喵～ o(*￣︶￣*)o')
                return redirect('ai_assistant:model_config_list')

        except Exception as e:
            messages.error(request, f'创建失败: {str(e)} (>_<)')
            return redirect('ai_assistant:model_config_create')

    # GET 请求：显示表单
    provider_choices = AIModelConfig.PROVIDER_CHOICES

    # 预设的模型名称建议
    model_suggestions = {
        'openai': ['gpt-4', 'gpt-4-turbo-preview', 'gpt-3.5-turbo'],
        'anthropic': ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
        'baidu': ['ernie-bot-4.0', 'ernie-bot-turbo', 'ernie-bot'],
        'aliyun': ['qwen-max', 'qwen-plus', 'qwen-turbo'],
    }

    context = {
        'provider_choices': provider_choices,
        'model_suggestions': model_suggestions,
    }

    return render(request, 'ai_assistant/model_config_form.html', context)


@login_required
def model_config_edit(request, pk):
    """
    编辑AI模型配置

    允许修改配置参数，API Key需要重新输入
    """
    config = get_object_or_404(AIModelConfig, pk=pk, is_deleted=False)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 获取表单数据
                name = request.POST.get('name')
                provider = request.POST.get('provider')
                api_key = request.POST.get('api_key', '').strip()
                api_base = request.POST.get('api_base', '').strip()
                model_name = request.POST.get('model_name')
                temperature = request.POST.get('temperature', '0.7')
                max_tokens = request.POST.get('max_tokens', '2000')
                timeout = request.POST.get('timeout', '60')
                priority = request.POST.get('priority', '0')
                is_active = request.POST.get('is_active') == 'on'
                is_default = request.POST.get('is_default') == 'on'
                description = request.POST.get('description', '')

                # 验证必填字段
                if not all([name, provider, model_name]):
                    messages.error(request, '请填写所有必填字段 (>_<)')
                    return redirect('ai_assistant:model_config_edit', pk=pk)

                # 如果设置为默认，取消其他配置的默认状态
                if is_default and not config.is_default:
                    AIModelConfig.objects.filter(is_default=True).update(is_default=False)

                # 更新基本信息
                config.name = name
                config.provider = provider
                config.model_name = model_name
                config.temperature = temperature
                config.max_tokens = int(max_tokens)
                config.timeout = int(timeout)
                config.priority = int(priority)
                config.is_active = is_active
                config.is_default = is_default
                config.description = description
                config.api_base = api_base if api_base else None

                # 如果提供了新的API Key，更新它
                if api_key:
                    config.api_key = encrypt_api_key(api_key)

                config.save()

                messages.success(request, f'AI模型配置 "{name}" 更新成功喵～ ヽ(✿ﾟ▽ﾟ)ノ')
                return redirect('ai_assistant:model_config_list')

        except Exception as e:
            messages.error(request, f'更新失败: {str(e)} (>_<)')
            return redirect('ai_assistant:model_config_edit', pk=pk)

    # GET 请求：显示表单
    provider_choices = AIModelConfig.PROVIDER_CHOICES

    # 预设的模型名称建议
    model_suggestions = {
        'openai': ['gpt-4', 'gpt-4-turbo-preview', 'gpt-3.5-turbo'],
        'anthropic': ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
        'baidu': ['ernie-bot-4.0', 'ernie-bot-turbo', 'ernie-bot'],
        'aliyun': ['qwen-max', 'qwen-plus', 'qwen-turbo'],
    }

    context = {
        'config': config,
        'provider_choices': provider_choices,
        'model_suggestions': model_suggestions,
        'is_edit': True,
    }

    return render(request, 'ai_assistant/model_config_form.html', context)


@login_required
@require_POST
def model_config_delete(request, pk):
    """
    删除AI模型配置（软删除）

    注意：默认配置不能删除
    """
    config = get_object_or_404(AIModelConfig, pk=pk, is_deleted=False)

    try:
        # 检查是否是默认配置
        if config.is_default:
            messages.error(request, '默认配置不能删除，请先设置其他配置为默认 (`д′)')
            return redirect('ai_assistant:model_config_list')

        # 软删除
        config.delete()

        messages.success(request, f'AI模型配置 "{config.name}" 已删除 (๑ˉ∀ˉ๑)')

    except Exception as e:
        messages.error(request, f'删除失败: {str(e)} (>_<)')

    return redirect('ai_assistant:model_config_list')


@login_required
def model_config_test(request, pk):
    """
    测试AI模型配置连接

    发送测试消息验证配置是否正确
    """
    config = get_object_or_404(AIModelConfig, pk=pk, is_deleted=False)

    if request.method == 'POST':
        try:
            # 使用AIService测试连接
            success, message = AIService.test_config(config)

            if success:
                return JsonResponse({
                    'success': True,
                    'message': message,
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': message,
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'测试失败: {str(e)}',
            })

    # GET 请求：显示测试页面
    context = {
        'config': config,
    }

    return render(request, 'ai_assistant/model_config_test.html', context)


@login_required
@require_POST
def model_config_set_default(request, pk):
    """
    设置指定配置为默认配置

    会自动取消其他配置的默认状态
    """
    config = get_object_or_404(AIModelConfig, pk=pk, is_deleted=False)

    try:
        with transaction.atomic():
            # 取消所有配置的默认状态
            AIModelConfig.objects.filter(is_default=True).update(is_default=False)

            # 设置当前配置为默认
            config.is_default = True
            config.is_active = True  # 默认配置必须是启用状态
            config.save()

            messages.success(request, f'已将 "{config.name}" 设置为默认配置喵～ ฅ\'ω\'ฅ')

    except Exception as e:
        messages.error(request, f'设置失败: {str(e)} (>_<)')

    return redirect('ai_assistant:model_config_list')
