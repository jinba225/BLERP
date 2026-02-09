"""
AI助手日志工具

提供统一的日志记录接口
"""

import logging
import sys
from typing import Any, Dict, Optional


class AIAssistantLogger:
    """AI助手日志记录器"""

    _loggers: Dict[str, logging.Logger] = {}

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取日志记录器

        Args:
            name: 日志记录器名称（通常使用 __name__）

        Returns:
            配置好的日志记录器
        """
        if name in cls._loggers:
            return cls._loggers[name]

        # 创建日志记录器
        logger = logging.getLogger(f"ai_assistant.{name}")

        # 如果已经配置过handler，直接返回
        if logger.handlers:
            cls._loggers[name] = logger
            return logger

        # 设置日志级别
        logger.setLevel(logging.INFO)

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # 创建格式化器
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)

        # 添加处理器
        logger.addHandler(console_handler)

        # 缓存
        cls._loggers[name] = logger

        return logger


def log_channel_message(
    logger: logging.Logger, channel: str, user_id: str, message: str, direction: str = "incoming"
):
    """
    记录渠道消息

    Args:
        logger: 日志记录器
        channel: 渠道名称
        user_id: 用户ID
        message: 消息内容
        direction: 方向（incoming/outgoing）
    """
    arrow = "➡️" if direction == "incoming" else "⬅️"
    logger.info(
        f"{arrow} [{channel}] User {user_id}: {message[:100]}{'...' if len(message) > 100 else ''}"
    )


def log_tool_execution(
    logger: logging.Logger,
    tool_name: str,
    user: str,
    params: Dict[str, Any],
    success: bool,
    execution_time: float,
    error: Optional[str] = None,
):
    """
    记录工具执行

    Args:
        logger: 日志记录器
        tool_name: 工具名称
        user: 用户名
        params: 参数
        success: 是否成功
        execution_time: 执行时间（秒）
        error: 错误信息（如果失败）
    """
    status = "✅" if success else "❌"
    logger.info(f"{status} Tool: {tool_name} | User: {user} | Time: {execution_time:.2f}s")

    if params:
        logger.debug(f"   Params: {params}")

    if error:
        logger.error(f"   Error: {error}")


def log_ai_request(
    logger: logging.Logger,
    provider: str,
    model: str,
    user: str,
    message_length: int,
    tools_count: int = 0,
):
    """
    记录AI请求

    Args:
        logger: 日志记录器
        provider: 提供商
        model: 模型名称
        user: 用户名
        message_length: 消息长度
        tools_count: 可用工具数量
    """
    logger.info(
        f"🤖 AI Request | Provider: {provider} | Model: {model} | "
        f"User: {user} | Msg Len: {message_length} | Tools: {tools_count}"
    )


def log_ai_response(
    logger: logging.Logger, tokens_used: int, response_time: float, has_tool_calls: bool = False
):
    """
    记录AI响应

    Args:
        logger: 日志记录器
        tokens_used: 使用的Token数
        response_time: 响应时间（秒）
        has_tool_calls: 是否包含工具调用
    """
    tool_indicator = "🔧" if has_tool_calls else ""
    logger.info(
        f"💬 AI Response | Tokens: {tokens_used} | " f"Time: {response_time:.2f}s {tool_indicator}"
    )


def log_error(logger: logging.Logger, error: Exception, context: Optional[Dict[str, Any]] = None):
    """
    记录错误

    Args:
        logger: 日志记录器
        error: 异常对象
        context: 上下文信息
    """
    logger.error(f"❌ Error: {type(error).__name__}: {str(error)}")

    if context:
        logger.error(f"   Context: {context}")

    # 记录完整的堆栈跟踪
    import traceback

    logger.debug(f"   Traceback:\n{traceback.format_exc()}")


def log_webhook_request(logger: logging.Logger, channel: str, method: str, verified: bool):
    """
    记录Webhook请求

    Args:
        logger: 日志记录器
        channel: 渠道名称
        method: HTTP方法
        verified: 是否验证通过
    """
    status = "✅" if verified else "❌"
    logger.info(f"{status} Webhook [{channel}] {method} - Verified: {verified}")
