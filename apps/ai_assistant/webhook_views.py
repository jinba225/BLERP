"""
渠道Webhook视图函数

处理来自各个渠道的Webhook请求
"""

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

from .models import WeChatConfig, DingTalkConfig, TelegramConfig, ChannelUserMapping
from .channels import (
    WeChatChannel,
    DingTalkChannel,
    TelegramChannel,
)

# from .services import ChannelAIService  # 暂时注释，ChannelAIService尚未实现
from .channels.base_channel import IncomingMessage, OutgoingMessage


# 判断是否启用异步处理
USE_ASYNC_PROCESSING = (
    getattr(settings, "AI_ASSISTANT_USE_ASYNC", False)
    and hasattr(settings, "CELERY_BROKER_URL")
    and settings.CELERY_BROKER_URL
)


def _process_message_sync(user, message):
    """
    同步处理消息

    Args:
        user: 用户对象
        message: IncomingMessage对象

    Returns:
        OutgoingMessage对象
    """
    # TODO: 实现ChannelAIService后取消注释
    # from .services import ChannelAIService
    # ai_service = ChannelAIService(user, message.channel)
    # return ai_service.process_message(message)

    # 临时返回一个模拟响应
    return OutgoingMessage(content="⚠️ AI助手服务正在开发中，请稍后再试。", message_type="text")


def _process_message_async(user, message):
    """
    异步处理消息

    Args:
        user: 用户对象
        message: IncomingMessage对象

    Returns:
        None（消息将异步处理）
    """
    from .tasks import process_message_async

    # 序列化消息数据
    message_data = {
        "message_id": message.message_id,
        "channel": message.channel,
        "external_user_id": message.external_user_id,
        "content": message.content,
        "timestamp": message.timestamp.isoformat() if message.timestamp else None,
        "message_type": message.message_type,
        "conversation_id": message.conversation_id,
        "raw_data": message.raw_data,
    }

    # 提交异步任务
    process_message_async.delay(message_data, user.id)

    # 返回"正在处理"的响应
    from .channels import OutgoingMessage

    return OutgoingMessage(content="收到消息，正在处理中喵～ (..•˘_˘•..)", message_type="text")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def wechat_webhook(request):
    """
    微信企业号Webhook

    GET: 验证URL
    POST: 接收消息
    """
    try:
        # 获取微信配置
        config = WeChatConfig.objects.filter(is_active=True, is_deleted=False).first()

        if not config:
            return HttpResponse("微信配置不存在", status=404)

        # 初始化渠道
        channel = WeChatChannel(config)

        # 验证请求
        if not channel.verify_webhook(request):
            return HttpResponse("签名验证失败", status=403)

        # GET请求：返回echostr
        if request.method == "GET":
            echostr = request.GET.get("echostr", "")
            # TODO: 需要解密echostr
            return HttpResponse(echostr)

        # POST请求：处理消息
        message = channel.parse_message(request)
        if not message:
            return HttpResponse("OK")

        # 获取用户映射
        user = channel.get_or_create_user_mapping(message.external_user_id)
        if not user:
            # 发送提示消息
            channel.send_message(
                message.external_user_id,
                type(
                    "OutgoingMessage", (), {"content": "您还未绑定系统账号，请联系管理员", "message_type": "text"}
                )(),
            )
            return HttpResponse("OK")

        # 处理消息（同步或异步）
        if USE_ASYNC_PROCESSING:
            response = _process_message_async(user, message)
        else:
            response = _process_message_sync(user, message)

        # 发送回复
        channel.send_message(message.external_user_id, response)

        return HttpResponse("OK")

    except Exception as e:
        print(f"微信Webhook处理失败: {str(e)}")
        return HttpResponse("Internal Server Error", status=500)


@csrf_exempt
@require_http_methods(["POST"])
def dingtalk_webhook(request):
    """
    钉钉企业应用Webhook

    POST: 接收消息
    """
    try:
        # 获取钉钉配置
        config = DingTalkConfig.objects.filter(is_active=True, is_deleted=False).first()

        if not config:
            return JsonResponse({"error": "钉钉配置不存在"}, status=404)

        # 初始化渠道
        channel = DingTalkChannel(config)

        # 验证请求
        if not channel.verify_webhook(request):
            return JsonResponse({"error": "签名验证失败"}, status=403)

        # 解析消息
        message = channel.parse_message(request)
        if not message:
            return JsonResponse({"success": True})

        # 获取用户映射
        user = channel.get_or_create_user_mapping(message.external_user_id)
        if not user:
            # 发送提示消息
            channel.send_message(
                message.external_user_id,
                type(
                    "OutgoingMessage", (), {"content": "您还未绑定系统账号，请联系管理员", "message_type": "text"}
                )(),
            )
            return JsonResponse({"success": True})

        # 处理消息（同步或异步）
        if USE_ASYNC_PROCESSING:
            response = _process_message_async(user, message)
        else:
            response = _process_message_sync(user, message)

        # 发送回复
        channel.send_message(message.external_user_id, response)

        return JsonResponse({"success": True})

    except Exception as e:
        print(f"钉钉Webhook处理失败: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def telegram_webhook(request):
    """
    Telegram Bot Webhook

    POST: 接收消息
    """
    try:
        # 获取Telegram配置
        config = TelegramConfig.objects.filter(is_active=True, is_deleted=False).first()

        if not config:
            return JsonResponse({"error": "Telegram配置不存在"}, status=404)

        # 初始化渠道
        channel = TelegramChannel(config)

        # 验证请求
        if not channel.verify_webhook(request):
            return JsonResponse({"error": "请求验证失败"}, status=403)

        # 解析消息
        message = channel.parse_message(request)
        if not message:
            return JsonResponse({"ok": True})

        # 获取用户映射
        user = channel.get_or_create_user_mapping(message.external_user_id)
        if not user:
            # 获取chat_id（用于发送消息）
            chat_id = message.raw_data.get("chat_id", message.external_user_id)

            # 发送提示消息
            from .channels import OutgoingMessage

            channel.send_message(
                str(chat_id),
                OutgoingMessage(content="你还未绑定系统账号，请联系管理员绑定 (>_<)", message_type="text"),
            )
            return JsonResponse({"ok": True})

        # 处理消息（同步或异步）
        if USE_ASYNC_PROCESSING:
            response = _process_message_async(user, message)
        else:
            response = _process_message_sync(user, message)

        # 发送回复（使用chat_id）
        chat_id = message.raw_data.get("chat_id", message.external_user_id)
        channel.send_message(str(chat_id), response)

        return JsonResponse({"ok": True})

    except Exception as e:
        print(f"Telegram Webhook处理失败: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
