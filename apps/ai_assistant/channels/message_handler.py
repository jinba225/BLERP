"""
统一消息处理器

处理来自各个渠道的消息，调用AI服务，执行工具
"""

import json

from django.contrib.auth import get_user_model

from ..services import AIService
from ..tools import ToolRegistry
from ..utils.logger import AIAssistantLogger, log_channel_message, log_error, log_tool_execution
from .base_channel import IncomingMessage, OutgoingMessage

User = get_user_model()

# 获取日志记录器
logger = AIAssistantLogger.get_logger(__name__)


class MessageHandler:
    """统一消息处理器"""

    def __init__(self, user: User):
        """
        初始化处理器

        Args:
            user: 系统用户
        """
        self.user = user

    def handle_message(self, message: IncomingMessage) -> OutgoingMessage:
        """
        处理入站消息

        Args:
            message: 入站消息

        Returns:
            出站消息
        """
        try:
            # 记录入站消息
            log_channel_message(
                logger,
                message.channel,
                message.external_user_id,
                message.content,
                direction="incoming",
            )

            # 初始化AI服务
            ai_service = AIService(user=self.user)

            # 获取用户可用的工具列表
            tools = ToolRegistry.to_openai_functions(self.user)

            # 调用AI服务（使用会话ID保持上下文）
            conversation_id = message.conversation_id or self._generate_conversation_id(message)

            response = ai_service.chat(
                message=message.content,
                conversation_id=conversation_id,
                channel=message.channel,
                tools=tools if tools else None,
            )

            # 检查是否需要调用工具
            if response.tool_calls:
                logger.info(f"🔧 Detected {len(response.tool_calls)} tool call(s)")

                # 执行工具调用
                tool_results = []
                for tool_call in response.tool_calls:
                    result = self._execute_tool(tool_call)
                    tool_results.append(result)

                # 如果有工具执行结果，可能需要再次调用AI
                if tool_results:
                    # 构建工具执行结果消息
                    tool_message = self._format_tool_results(tool_results)

                    logger.debug(f"Tool results: {tool_message[:200]}...")

                    # 再次调用AI，让它根据工具结果生成回复
                    final_response = ai_service.chat(
                        message=tool_message,
                        conversation_id=conversation_id,
                        channel=message.channel,
                    )

                    content = final_response.content
                else:
                    content = response.content
            else:
                content = response.content

            # 记录出站消息
            log_channel_message(
                logger, message.channel, message.external_user_id, content, direction="outgoing"
            )

            return OutgoingMessage(content=content, message_type="text")

        except Exception as e:
            # 记录错误
            log_error(
                logger,
                e,
                context={
                    "channel": message.channel,
                    "user_id": message.external_user_id,
                    "message_id": message.message_id,
                },
            )

            # 错误处理
            error_message = f"处理消息时出错: {str(e)} (>_<)"
            return OutgoingMessage(content=error_message, message_type="text")

    def _generate_conversation_id(self, message: IncomingMessage) -> str:
        """
        生成会话ID

        Args:
            message: 入站消息

        Returns:
            会话ID
        """
        # 使用渠道+外部用户ID作为会话标识
        return f"{message.channel}_{message.external_user_id}"

    def _execute_tool(self, tool_call: dict) -> dict:
        """
        执行工具调用

        Args:
            tool_call: 工具调用信息

        Returns:
            工具执行结果
        """
        import time

        start_time = time.time()

        try:
            # 解析工具调用
            tool_name = tool_call.get("function", {}).get("name")
            arguments_str = tool_call.get("function", {}).get("arguments", "{}")

            logger.info(f"🔧 Executing tool: {tool_name}")

            # 解析参数
            try:
                arguments = (
                    json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                )
            except json.JSONDecodeError as e:
                execution_time = time.time() - start_time
                error_msg = f"参数解析失败: {arguments_str}"
                logger.error(f"❌ Tool {tool_name} - {error_msg}")

                log_tool_execution(
                    logger,
                    tool_name or "unknown",
                    self.user.username,
                    {},
                    success=False,
                    execution_time=execution_time,
                    error=error_msg,
                )

                return {"success": False, "error": error_msg}

            # 获取工具实例
            tool = ToolRegistry.get_tool(tool_name, self.user)
            if not tool:
                execution_time = time.time() - start_time
                error_msg = f"工具 {tool_name} 不存在"
                logger.error(f"❌ {error_msg}")

                log_tool_execution(
                    logger,
                    tool_name or "unknown",
                    self.user.username,
                    arguments,
                    success=False,
                    execution_time=execution_time,
                    error=error_msg,
                )

                return {"success": False, "error": error_msg}

            # 执行工具
            logger.debug(f"Tool params: {arguments}")
            result = tool.run(**arguments)

            execution_time = time.time() - start_time

            # 记录工具执行
            log_tool_execution(
                logger,
                tool_name,
                self.user.username,
                arguments,
                success=result.success,
                execution_time=execution_time,
                error=result.error if not result.success else None,
            )

            return result.to_dict()

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"工具执行失败: {str(e)}"

            logger.error(f"❌ Tool execution error: {str(e)}")
            log_error(logger, e, context={"tool_call": tool_call})

            log_tool_execution(
                logger,
                tool_name if "tool_name" in locals() else "unknown",
                self.user.username,
                arguments if "arguments" in locals() else {},
                success=False,
                execution_time=execution_time,
                error=error_msg,
            )

            return {"success": False, "error": error_msg}

    def _format_tool_results(self, tool_results: list) -> str:
        """
        格式化工具执行结果

        Args:
            tool_results: 工具执行结果列表

        Returns:
            格式化的消息
        """
        messages = []
        for result in tool_results:
            if result.get("success"):
                messages.append(f"✅ 操作成功: {result.get('message', '')}")
                if result.get("data"):
                    messages.append(
                        f"结果: {json.dumps(result['data'], ensure_ascii=False, indent=2)}"
                    )
            else:
                messages.append(f"❌ 操作失败: {result.get('error', '未知错误')}")

        return "\n\n".join(messages) if messages else "工具执行完成"
