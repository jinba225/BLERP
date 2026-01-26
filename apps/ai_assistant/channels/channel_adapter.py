"""
渠道适配器

将 AI 响应转换为不同渠道的特定格式
"""

from typing import Dict, Any, Optional
from apps.ai_assistant.channels.base_channel import IncomingMessage, OutgoingMessage


class ChannelAdapter:
    """渠道适配器
    
    支持将 AI 响应转换为不同渠道的特定格式
    """
    
    def __init__(self, channel: str):
        """
        初始化适配器
        
        Args:
            channel: 渠道类型
        """
        self.channel = channel
    
    def format_response(self, content: str, message: IncomingMessage) -> OutgoingMessage:
        """
        格式化 AI 响应为渠道特定格式
        
        Args:
            content: AI 生成的回复内容
            message: 原始入站消息
        
        Returns:
            OutgoingMessage 对象
        """
        if self.channel == 'telegram':
            return self._format_telegram(content, message)
        elif self.channel == 'wechat':
            return self._format_wechat(content, message)
        elif self.channel == 'dingtalk':
            return self._format_dingtalk(content, message)
        elif self.channel == 'web':
            return self._format_web(content, message)
        else:
            return OutgoingMessage(content=content, message_type='text')
    
    def _format_telegram(self, content: str, message: IncomingMessage) -> OutgoingMessage:
        """
        Telegram 格式化
        
        Telegram 支持 MarkdownV2 格式
        """
        formatted = self._apply_markdown(content, platform='telegram')
        extra = {
            'parse_mode': 'MarkdownV2'
        }
        return OutgoingMessage(
            content=formatted,
            message_type='text',
            extra=extra
        )
    
    def _format_wechat(self, content: str, message: IncomingMessage) -> OutgoingMessage:
        """
        企业微信格式化
        
        企业微信支持 Markdown 格式
        """
        formatted = self._apply_markdown(content, platform='wechat')
        extra = {
            'msgtype': 'markdown',
        'markdown': {
                'content': formatted
            }
        }
        return OutgoingMessage(
            content=formatted,
            message_type='text',
            extra=extra
        )
    
    def _format_dingtalk(self, content: str, message: IncomingMessage) -> OutgoingMessage:
        """
        钉钉格式化
        
        钉钉支持 Markdown 格式
        """
        formatted = self._apply_markdown(content, platform='dingtalk')
        extra = {
            'msg': {
                'msgtype': 'markdown',
                'text': formatted
            }
        }
        return OutgoingMessage(
            content=content,
            message_type='text',
            extra=extra
        )
    
    def _format_web(self, content: str, message: IncomingMessage) -> OutgoingMessage:
        """
        Web 格式化（保持原始格式）
        
        """
        return OutgoingMessage(
            content=content,
            message_type='text'
        )
    
    def _apply_markdown(self, text: str, platform: str = 'telegram') -> str:
        """
        应用 Markdown 格式化
        
        Args:
            text: 原始文本
            platform: 平台类型
        
        Returns:
            格式化后的文本
        """
        # 转换 Markdown 符号
        formatted = text
        
        if platform == 'telegram':
            # Telegram MarkdownV2
            formatted = formatted.replace('**', '*').replace('__', '_')
        elif platform == 'wechat':
            # 企业微信 Markdown
            formatted = formatted.replace('**', '*').replace('__', '_')
        elif platform == 'dingtalk':
            # 钉钉 Markdown
            formatted = formatted.replace('**', '*').replace('__', '_')
        
        # 确保换行符正确
        formatted = formatted.replace('\n', '\n\n')
        
        return formatted
    
    def format_error_message(self, error: str, platform: str) -> OutgoingMessage:
        """
        格式化错误消息
        
        Args:
            error: 错误信息
            platform: 平台类型
        
        Returns:
            OutgoingMessage 对象
        """
        error_messages = {
            'telegram': f'❌ *错误发生*\n\n{error}',
            'wechat': f'❌ 错误发生\n\n{error}',
            'dingtalk': f'❌ 错误发生\n\n{error}',
            'web': error,
        }
        
        formatted = error_messages.get(platform, error)
        return OutgoingMessage(
            content=formatted,
            message_type='text'
        )
    
    def format_confirmation_message(self, message: str, platform: str = 'telegram') -> OutgoingMessage:
        """
        格式化确认消息
        
        Args:
            message: 确认内容
            platform: 平台类型
        
        Returns:
            OutgoingMessage 对象
        """
        if platform == 'telegram':
            return OutgoingMessage(
                content=f'✅ {message}',
                message_type='text',
                extra={'parse_mode': 'MarkdownV2'}
            )
        else:
            return OutgoingMessage(
                content=f'✅ {message}',
                message_type='text'
            )
    
    def format_tool_result(self, result: Dict[str, Any], platform: str = 'telegram') -> OutgoingMessage:
        """
        格式化工具执行结果
        
        Args:
            result: 工具执行结果
            platform: 平台类型
        
        Returns:
            Outgoing 对象
        """
        if result.get('success'):
            message = result.get('message', '操作成功')
            data = result.get('data')
            
            if data:
                content = f'✅ *{message}*\n\n'
                content += self._format_data_as_text(data)
            else:
                content = f'✅ {message}'
            
            if platform == 'telegram':
                return OutgoingMessage(
                    content=content,
                    message_type='text',
                    extra={'parse_mode': 'MarkdownV2'}
                )
            else:
                return OutgoingMessage(content=content, message_type='text')
        else:
            error = result.get('error', '操作失败')
            return self.format_error_message(error, platform)
    
    def _format_data_as_text(self, data: Any) -> str:
        """
        将数据格式化为文本
        
        Args:
            data: 数据对象
        
        Returns:
            格式化后的文本
        """
        if isinstance(data, dict):
            items = []
            for key, value in data.items():
                items.append(f'{key}: {value}')
            return '\n'.join(items)
        elif isinstance(data, list):
            return '\n'.join([str(item) for item in data])
        else:
            return str(data)
