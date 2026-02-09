"""
AI助手异步任务

提供消息处理、会话清理等异步任务
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_message_async(self, message_data: dict, user_id: int):
    """
    异步处理消息

    Args:
        message_data: 消息数据字典
        user_id: 用户ID

    Returns:
        处理结果
    """
    try:
        from datetime import datetime

        from ai_assistant.channels.base_channel import IncomingMessage
        from ai_assistant.channels.message_handler import MessageHandler
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # 获取用户
        try:
            user = User.objects.get(id=user_id, is_deleted=False)
        except User.DoesNotExist:
            logger.error(f"用户不存在: user_id={user_id}")
            return {"success": False, "error": "用户不存在"}

        # 重建 IncomingMessage 对象
        message = IncomingMessage(
            message_id=message_data.get("message_id", ""),
            channel=message_data.get("channel", ""),
            external_user_id=message_data.get("external_user_id", ""),
            content=message_data.get("content", ""),
            timestamp=datetime.fromisoformat(message_data.get("timestamp"))
            if message_data.get("timestamp")
            else timezone.now(),
            message_type=message_data.get("message_type", "text"),
            conversation_id=message_data.get("conversation_id"),
            raw_data=message_data.get("raw_data", {}),
        )

        # 处理消息
        handler = MessageHandler(user)
        response = handler.handle_message(message)

        logger.info(f"异步消息处理成功: message_id={message.message_id}")

        return {
            "success": True,
            "response_content": response.content,
            "message_type": response.message_type,
        }

    except Exception as e:
        logger.error(f"异步消息处理失败: {str(e)}", exc_info=True)

        # 重试机制
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"消息处理达到最大重试次数: message_id={message_data.get('message_id')}")
            return {"success": False, "error": str(e)}


@shared_task(bind=True, max_retries=2)
def execute_tool_async(self, tool_name: str, user_id: int, parameters: dict):
    """
    异步执行工具

    Args:
        tool_name: 工具名称
        user_id: 用户ID
        parameters: 工具参数

    Returns:
        工具执行结果
    """
    try:
        from ai_assistant.tools.registry import ToolRegistry
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # 获取用户
        try:
            user = User.objects.get(id=user_id, is_deleted=False)
        except User.DoesNotExist:
            logger.error(f"用户不存在: user_id={user_id}")
            return {"success": False, "error": "用户不存在"}

        # 获取工具
        tool = ToolRegistry.get_tool(tool_name, user)
        if not tool:
            logger.error(f"工具不存在: tool_name={tool_name}")
            return {"success": False, "error": f"工具 {tool_name} 不存在"}

        # 执行工具
        result = tool.run(**parameters)

        logger.info(f"异步工具执行成功: tool={tool_name}, user={user.username}")

        return result.to_dict()

    except Exception as e:
        logger.error(f"异步工具执行失败: {str(e)}", exc_info=True)

        # 重试机制
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"工具执行达到最大重试次数: tool={tool_name}")
            return {"success": False, "error": str(e)}


@shared_task
def cleanup_expired_conversations():
    """
    清理过期会话（定时任务）

    删除30天未活跃的会话
    """
    try:
        from ai_assistant.models import AIConversation

        # 计算过期时间（30天前）
        expire_time = timezone.now() - timedelta(days=30)

        # 查找过期会话
        expired_conversations = AIConversation.objects.filter(
            last_message_at__lt=expire_time, status="active", is_deleted=False
        )

        count = expired_conversations.count()

        # 软删除过期会话
        for conversation in expired_conversations:
            conversation.status = "ended"
            conversation.save()
            conversation.delete()  # 软删除

        logger.info(f"清理了 {count} 个过期会话")

        return {"success": True, "count": count}

    except Exception as e:
        logger.error(f"清理过期会话失败: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


@shared_task
def cleanup_old_logs():
    """
    清理旧日志（定时任务）

    删除90天前的工具执行日志
    """
    try:
        from ai_assistant.models import AIToolExecutionLog

        # 计算过期时间（90天前）
        expire_time = timezone.now() - timedelta(days=90)

        # 查找旧日志
        old_logs = AIToolExecutionLog.objects.filter(executed_at__lt=expire_time, is_deleted=False)

        count = old_logs.count()

        # 软删除旧日志
        for log in old_logs:
            log.delete()  # 软删除

        logger.info(f"清理了 {count} 条旧日志")

        return {"success": True, "count": count}

    except Exception as e:
        logger.error(f"清理旧日志失败: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


@shared_task
def refresh_access_token(channel: str, app_id: str):
    """
    刷新Access Token（定时任务）

    提前刷新即将过期的Access Token

    Args:
        channel: 渠道类型 (wechat/dingtalk)
        app_id: 应用ID
    """
    try:
        from ai_assistant.utils.cache import AIAssistantCache

        # 删除缓存，下次获取时会自动刷新
        AIAssistantCache.delete_access_token(channel, app_id)

        logger.info(f"已触发Access Token刷新: channel={channel}, app_id={app_id}")

        return {"success": True}

    except Exception as e:
        logger.error(f"刷新Access Token失败: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}
