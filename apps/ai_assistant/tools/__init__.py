"""
AI Assistant Tools

提供AI调用ERP系统的各类工具
"""

from .base_tool import BaseTool, ToolResult
from .registry import ToolRegistry

__all__ = ['BaseTool', 'ToolResult', 'ToolRegistry']
