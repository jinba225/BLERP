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
        self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None
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
            model=self.model_name,
        )

    def _should_use_tool(self, message: str) -> bool:
        """
        判断消息是否需要调用工具
        """
        tool_keywords = [
            "查询",
            "搜索",
            "查看",
            "创建",
            "生成",
            "库存",
            "订单",
            "客户",
            "供应商",
            "报表",
            "search",
            "query",
            "create",
            "check",
            "find",
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
                model=self.model_name,
            )

        # 生成工具调用参数
        tool_params = self._generate_tool_params(message, selected_tool)

        tool_calls = [
            {
                "id": f"mock_tool_call_{int(time.time())}",
                "type": "function",
                "function": {
                    "name": selected_tool["function"]["name"],
                    "arguments": json.dumps(tool_params, ensure_ascii=False),
                },
            }
        ]

        return AIResponse(
            content="",  # 工具调用时内容为空
            finish_reason="tool_calls",
            tokens_used=40,
            tool_calls=tool_calls,
            model=self.model_name,
        )

    def _select_tool(self, message: str, tools: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        根据消息内容选择合适的工具
        """
        message_lower = message.lower()

        # 工具选择规则
        tool_rules = {
            "search_customer": ["客户", "customer", "查客户", "找客户"],
            "search_supplier": ["供应商", "supplier", "查供应商", "找供应商"],
            "query_sales_orders": ["订单", "order", "查订单", "销售订单"],
            "check_inventory": ["库存", "inventory", "stock", "查库存"],
            "search_product": ["产品", "product", "查产品", "物料"],
            "generate_sales_report": ["销售报表", "sales report", "销售统计"],
            "generate_inventory_report": ["库存报表", "inventory report", "库存统计"],
        }

        # 遍历所有工具，找到匹配的
        for tool in tools:
            tool_name = tool["function"]["name"]
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
        tool_name = tool["function"]["name"]

        # 不同工具的默认参数
        params_map = {
            "search_customer": {"keyword": self._extract_keyword(message)},
            "search_supplier": {"keyword": self._extract_keyword(message)},
            "query_sales_orders": {"status": "all", "limit": 10},
            "check_inventory": {"product_name": self._extract_keyword(message)},
            "search_product": {"keyword": self._extract_keyword(message)},
            "generate_sales_report": {"period": "month"},
            "generate_inventory_report": {"warehouse_id": None},
        }

        return params_map.get(tool_name, {})

    def _extract_keyword(self, message: str) -> str:
        """
        从消息中提取关键词
        """
        # 移除常见的查询词
        remove_words = ["查询", "搜索", "查看", "找", "帮我", "请", "search", "find", "query", "check"]

        words = message.split()
        keywords = [w for w in words if w not in remove_words]

        return " ".join(keywords) if keywords else message

    def _generate_mock_response(self, message: str) -> str:
        """
        生成模拟的对话响应

        如果消息看起来像是意图识别请求（system prompt要求JSON格式），则返回JSON
        否则返回普通对话响应
        """
        message_lower = message.lower()

        # 检查是否是意图识别请求（包含JSON相关关键词或意图相关关键词）
        intent_keywords = ["意图", "intent", "识别", "用户需求", "用户想要"]
        if any(keyword in message_lower for keyword in intent_keywords):
            return self._generate_intent_response(message)

        # 问候语响应
        if any(word in message_lower for word in ["你好", "hello", "hi", "嗨"]):
            return "你好喵～浮浮酱是ERP AI助手，可以帮你管理销售、采购、库存等业务哦！有什么需要帮助的吗？(๑•̀ㅂ•́)✧"

        # 帮助响应
        if any(word in message_lower for word in ["帮助", "help", "能做什么", "功能"]):
            return """浮浮酱可以帮你：
✓ 查询客户和供应商信息
✓ 查看销售订单和采购订单
✓ 检查库存状态
✓ 生成各类报表
✓ 创建销售报价单

试试问我"查询库存"或"最近的订单"吧～ (´｡• ᵕ •｡`) ♡"""

        # 感谢响应
        if any(word in message_lower for word in ["谢谢", "thanks", "thank you", "太好了"]):
            return "不客气喵～很高兴能帮到你！还有什么需要吗？ฅ'ω'ฅ"

        # 确认响应
        if any(word in message_lower for word in ["确认", "是", "好的", "OK", "没问题"]):
            return "好的，我将按照你的要求执行操作～ ✓"

        # 默认响应（如果包含任何业务关键词，也尝试识别意图）
        business_keywords = ["订单", "客户", "产品", "库存", "查询", "创建", "报价", "审核", "拒绝"]
        if any(keyword in message_lower for keyword in business_keywords):
            return self._generate_intent_response(message)

        # 完全默认响应
        return f"浮浮酱收到了你的消息：「{message}」\n\n这是一个测试响应喵～在真实环境中，我会调用AI模型来生成更智能的回复哦！(..•˘_˘•..)"

    def _generate_intent_response(self, message: str) -> str:
        """
        生成意图识别响应（JSON格式）
        """
        message_lower = message.lower()

        # 识别意图（按优先级排序）
        intent_map = [
            # 创建订单（最高优先级）
            {
                "intent": "create_order",
                "keywords": [
                    "创建订单",
                    "新建订单",
                    "增加订单",
                    "添加订单",
                    "创建一个订单",
                    "新建一个订单",
                    "create order",
                    "add order",
                    "add order",
                    "create sales order",
                ],
                "confidence": 0.95,
            },
            # 查询订单（优先级较高）
            {
                "intent": "query_order",
                "keywords": [
                    "查询订单",
                    "查看订单",
                    "query order",
                    "查订单",
                    "订单状态",
                    "订单详情",
                ],
                "confidence": 0.85,
            },
            # 审核订单
            {
                "intent": "approve_order",
                "keywords": [
                    "审核订单",
                    "批准订单",
                    "approve order",
                    "通过订单",
                    "确认订单",
                ],
                "confidence": 0.90,
            },
            # 拒绝订单
            {
                "intent": "reject_order",
                "keywords": [
                    "拒绝订单",
                    "驳回订单",
                    "reject order",
                    "不同意订单",
                    "取消订单",
                ],
                "confidence": 0.90,
            },
            # 查询客户（优先级中等）
            {
                "intent": "query_customer",
                "keywords": [
                    "查询客户",
                    "查看客户",
                    "query customer",
                    "找客户",
                    "客户信息",
                ],
                "confidence": 0.85,
            },
            # 查询产品
            {
                "intent": "query_product",
                "keywords": [
                    "查询产品",
                    "查看产品",
                    "query product",
                    "查产品",
                    "产品信息",
                ],
                "confidence": 0.85,
            },
            # 查询库存
            {
                "intent": "query_inventory",
                "keywords": [
                    "查询库存",
                    "查看库存",
                    "query inventory",
                    "查库存",
                    "库存信息",
                ],
                "confidence": 0.85,
            },
            # 创建报价
            {
                "intent": "create_quote",
                "keywords": [
                    "创建报价",
                    "新建报价",
                    "增加报价",
                    "add quote",
                    "创建报价单",
                ],
                "confidence": 0.9,
            },
            # 查询订单（备用关键词）
            {
                "intent": "query_order",
                "keywords": [
                    "订单号是什么",
                    "订单详情",
                    "查看订单",
                    "订单状态",
                ],
                "confidence": 0.8,
            },
        ]

        # 识别意图
        intent = "unknown"
        confidence = 0.5
        reasoning = "无法识别明确的意图"

        for intent_info in intent_map:
            for keyword in intent_info["keywords"]:
                if keyword in message_lower:
                    intent = intent_info["intent"]
                    confidence = intent_info["confidence"]
                    reasoning = f"识别到关键词: '{keyword}'"
                    break
            if intent != "unknown":
                break

        # 返回 JSON
        result = {
            "intent": intent,
            "confidence": confidence,
            "entities": {},
            "reasoning": reasoning,
        }

        return json.dumps(result, ensure_ascii=False)

    def _extract_intent_entities(self, message: str) -> dict:
        """
        从消息中提取实体
        """
        import re

        entities = {}

        # 提取客户名称
        customer_patterns = [
            r"客户[是为：是]\s*([^\s,，。]+)",  # 客户是/为/为 xxx
            r"([^\s,，。]+?(?:有限公司|股份公司|集团|科技公司|贸易公司))",  # xxx 有限公司等
            r"(北京|上海|广州|深圳|杭州|成都|武汉|南京)[^\s,，。]+?(?:公司|集团)",  # 北京xxx公司
        ]
        for pattern in customer_patterns:
            match = re.search(pattern, message)
            if match:
                customer_name = match.group(1)
                # 去掉前缀的动词
                for prefix in ["给", "为", "向", "客户是", "客户为", "客户为"]:
                    if customer_name.startswith(prefix):
                        customer_name = customer_name[len(prefix) :]
                        break
                if customer_name and len(customer_name) > 1:
                    entities["customer_name"] = customer_name
                    break

        # 提取产品名称（简化版，直接匹配产品列表）
        product_keywords = [
            "笔记本电脑",
            "台式机",
            "显示器",
            "打印机",
            "复印机",
            "服务器",
            "鼠标",
            "键盘",
            "电脑",
            "设备",
            "笔记本电脑电脑",
        ]
        for keyword in product_keywords:
            if keyword in message:
                entities["product_name"] = keyword
                break

        # 提取数量
        quantity_patterns = [
            r"数量[是为：是]\s*(\d+)",  # 数量是/为/为 xxx
            r"(\d+)\s*(个|台|件|套|箱|kg|KG|台)",  # xxx 个/台/件
        ]
        for pattern in quantity_patterns:
            match = re.search(pattern, message)
            if match:
                try:
                    quantity = int(match.group(1))
                    if quantity > 0:
                        entities["quantity"] = quantity
                        break
                except ValueError:
                    pass

        # 提取金额
        amount_patterns = [
            r"金额[是为：是]\s*(\d+(?:\.\d+)?)",  # 金额是/为/为 xxx
            r"(\d+(?:\.\d+)?)\s*(万|元|块|USD|CNY)",  # xxx 万/元/块
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, message)
            if match:
                try:
                    amount = float(match.group(1))
                    unit = match.group(2)
                    if unit == "万":
                        amount *= 10000
                    if amount > 0:
                        entities["amount"] = amount
                        break
                except (ValueError, IndexError):
                    pass

        # 提取订单号
        order_patterns = [
            r"订单号[是为：是]\s*([A-Z]+\d+)",  # 订单号是/为/为 SOxxx
            r"([A-Z]+\d{10,})",  # SOxxx (10位以上数字)
        ]
        for pattern in order_patterns:
            match = re.search(pattern, message)
            if match:
                order_number = match.group(1)
                if order_number:
                    entities["order_number"] = order_number
                    break

        return entities

        # 提取产品名称
        product_keywords = ["笔记本电脑", "台式机", "显示器", "打印机", "复印机", "服务器", "鼠标", "键盘", "电脑", "设备"]
        for keyword in product_keywords:
            if keyword in message:
                entities["product_name"] = keyword
                break

        # 提取数量
        quantity_match = re.search(r"(\d+)\s*(个|台|件|套|箱|kg|台)", message)
        if quantity_match:
            try:
                quantity = int(quantity_match.group(1))
                if quantity > 0:
                    entities["quantity"] = quantity
            except (ValueError, AttributeError):
                pass

        # 提取金额
        amount_match = re.search(r"(\d+(?:\.\d+)?)\s*(万|元|块|USD)", message)
        if amount_match:
            try:
                amount = float(amount_match.group(1))
                unit = amount_match.group(2)
                if unit == "万":
                    amount *= 10000
                if amount > 0:
                    entities["amount"] = amount
            except (ValueError, AttributeError):
                pass

        # 提取订单号
        order_match = re.search(r"(SO[A-Z0-9]{10,})", message)
        if order_match:
            entities["order_number"] = order_match.group(1)

        return entities

    def stream_chat(
        self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None
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
