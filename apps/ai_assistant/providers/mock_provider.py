"""
Mock AI Provider - 用于测试

模拟AI响应，无需真实API Key
"""

import time
import json
from typing import List, Dict, Any, Optional
from .base import BaseAIProvider, AIResponse


class MockAIProvider(BaseAIProvider):
    """
    Mock AI Provider - 模拟AI响应

    用于测试和开发环境，不需要真实的API Key
    """

    provider_name = "mock"

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AIResponse:
        """
        模拟AI对话

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            tools: 工具列表（可选）

        Returns:
            AIResponse对象
        """
        # 模拟处理时间
        time.sleep(0.5)

        # 获取最后一条用户消息
        last_message = messages[-1] if messages else {"role": "user", "content": ""}
        message_content = last_message.get("content", "")

        # 检查是否需要工具调用
        if tools and self._should_use_tool(message_content):
            return self._mock_tool_call(message_content, tools)

        # 普通对话响应
        content = self._generate_mock_response(message_content)

        return AIResponse(
            content=content,
            finish_reason="stop",
            tokens_used=len(message_content.split()) * 2 + len(content.split()) * 2,
            tool_calls=None,
            model=self.model_name
        )

    def _should_use_tool(self, message: str) -> bool:
        """
        判断消息是否需要调用工具
        """
        tool_keywords = [
            '查询', '搜索', '查看', '创建', '生成',
            '库存', '订单', '客户', '供应商', '报表',
            'search', 'query', 'create', 'check', 'find'
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in tool_keywords)

    def _mock_tool_call(self, message: str, tools: List[Dict[str, Any]]) -> AIResponse:
        """
        模拟工具调用
        """
        # 根据消息内容选择合适的工具
        selected_tool = self._select_tool(message, tools)

        if not selected_tool:
            # 没有合适的工具，返回普通响应
            return AIResponse(
                content=self._generate_mock_response(message),
                finish_reason="stop",
                tokens_used=50,
                tool_calls=None,
                model=self.model_name
            )

        # 生成工具调用参数
        tool_params = self._generate_tool_params(message, selected_tool)

        tool_calls = [{
            'id': f'mock_tool_call_{int(time.time())}',
            'type': 'function',
            'function': {
                'name': selected_tool['function']['name'],
                'arguments': json.dumps(tool_params, ensure_ascii=False)
            }
        }]

        return AIResponse(
            content="",  # 工具调用时内容为空
            finish_reason="tool_calls",
            tokens_used=40,
            tool_calls=tool_calls,
            model=self.model_name
        )

    def _select_tool(self, message: str, tools: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        根据消息内容选择合适的工具
        """
        message_lower = message.lower()

        # 工具选择规则
        tool_rules = {
            'search_customer': ['客户', 'customer', '查客户', '找客户'],
            'search_supplier': ['供应商', 'supplier', '查供应商', '找供应商'],
            'query_sales_orders': ['订单', 'order', '查订单', '销售订单'],
            'check_inventory': ['库存', 'inventory', 'stock', '查库存'],
            'search_product': ['产品', 'product', '查产品', '物料'],
            'generate_sales_report': ['销售报表', 'sales report', '销售统计'],
            'generate_inventory_report': ['库存报表', 'inventory report', '库存统计'],
        }

        # 遍历所有工具，找到匹配的
        for tool in tools:
            tool_name = tool['function']['name']
            if tool_name in tool_rules:
                keywords = tool_rules[tool_name]
                if any(keyword in message_lower for keyword in keywords):
                    return tool

        # 默认返回第一个工具
        return tools[0] if tools else None

    def _generate_tool_params(self, message: str, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据消息和工具生成参数
        """
        tool_name = tool['function']['name']

        # 不同工具的默认参数
        params_map = {
            'search_customer': {'keyword': self._extract_keyword(message)},
            'search_supplier': {'keyword': self._extract_keyword(message)},
            'query_sales_orders': {'status': 'all', 'limit': 10},
            'check_inventory': {'product_name': self._extract_keyword(message)},
            'search_product': {'keyword': self._extract_keyword(message)},
            'generate_sales_report': {'period': 'month'},
            'generate_inventory_report': {'warehouse_id': None},
        }

        return params_map.get(tool_name, {})

    def _extract_keyword(self, message: str) -> str:
        """
        从消息中提取关键词
        """
        # 移除常见的查询词
        remove_words = ['查询', '搜索', '查看', '找', '帮我', '请',
                       'search', 'find', 'query', 'check']

        words = message.split()
        keywords = [w for w in words if w not in remove_words]

        return ' '.join(keywords) if keywords else message

    def _generate_mock_response(self, message: str) -> str:
        """
        生成模拟的对话响应
        """
        message_lower = message.lower()

        # 问候语响应
        if any(word in message_lower for word in ['你好', 'hello', 'hi', '嗨']):
            return "你好喵～浮浮酱是ERP AI助手，可以帮你管理销售、采购、库存等业务哦！有什么需要帮助的吗？(๑•̀ㅂ•́)✧"

        # 帮助响应
        if any(word in message_lower for word in ['帮助', 'help', '能做什么', '功能']):
            return """浮浮酱可以帮你：
✓ 查询客户和供应商信息
✓ 查看销售订单和采购订单
✓ 检查库存状态
✓ 生成各类报表
✓ 创建销售报价单

试试问我"查询库存"或"最近的订单"吧～ (´｡• ᵕ •｡`) ♡"""

        # 感谢响应
        if any(word in message_lower for word in ['谢谢', 'thanks', 'thank you', '太好了']):
            return "不客气喵～很高兴能帮到你！还有什么需要吗？ฅ'ω'ฅ"

        # 默认响应
        return f"浮浮酱收到了你的消息：「{message}」\n\n这是一个测试响应喵～在真实环境中，我会调用AI模型来生成更智能的回复哦！(..•˘_˘•..)"

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ):
        """
        流式对话（Mock版本不支持流式）

        Args:
            messages: 消息列表
            tools: 工具列表（可选）

        Yields:
            文本片段
        """
        # Mock Provider 不支持流式，直接返回完整响应
        response = self.chat(messages, tools)
        yield response.content
