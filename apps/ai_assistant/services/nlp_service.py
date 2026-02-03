"""
自然语言处理服务

使用 AI 模型进行意图识别和实体提取，支持自然语言创建/审核文档。

支持的意图:
- create_order: 创建销售订单
- approve_order: 审核订单
- reject_order: 拒绝订单
- query_customer: 查询客户信息
- query_product: 查询产品信息
- query_inventory: 查询库存信息
- create_quote: 创建报价单
- query_order: 查询订单状态
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import re

from ai_assistant.providers import BaseAIProvider, AIResponse


class Intent(Enum):
    """意图枚举"""
    CREATE_ORDER = "create_order"
    APPROVE_ORDER = "approve_order"
    REJECT_ORDER = "reject_order"
    QUERY_CUSTOMER = "query_customer"
    QUERY_PRODUCT = "query_product"
    QUERY_INVENTORY = "query_inventory"
    CREATE_QUOTE = "create_quote"
    QUERY_ORDER = "query_order"
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    """意图识别结果"""
    intent: Intent
    confidence: float
    entities: Dict[str, Any]
    original_text: str


class NLPService:
    """自然语言处理服务"""
    
    def __init__(self, ai_provider: BaseAIProvider):
        self.ai_provider = ai_provider
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一个 ERP 系统的智能助手，负责理解用户的自然语言请求。

你的任务是:
1. 识别用户的意图（从以下选项中选择）:
   - create_order: 创建销售订单
   - approve_order: 审核订单
   - reject_order: 拒绝订单
   - query_customer: 查询客户信息
   - query_product: 查询产品信息
   - query_inventory: 查询库存信息
   - create_quote: 创建报价单
   - query_order: 查询订单状态

2. 提取关键实体信息，包括:
   - customer_name: 客户名称
   - customer_code: 客户代码
   - product_name: 产品名称
   - product_code: 产品代码
   - quantity: 数量
   - amount: 金额
   - order_number: 订单号
   - warehouse_name: 仓库名称
   - delivery_address: 交付地址
   - remark: 备注

3. 返回 JSON 格式，包含以下字段:
   {
     "intent": "意图名称",
     "confidence": 0.95,  // 置信度 0-1
     "entities": {
       "customer_name": "客户名称",
       "product_name": "产品名称",
       // 其他提取的实体...
     },
     "reasoning": "简要说明识别意图的理由"
   }

示例:

用户输入: "给北京科技有限公司创建一个订单，100 个笔记本电脑，金额 50 万"
输出:
{
  "intent": "create_order",
  "confidence": 0.98,
  "entities": {
    "customer_name": "北京科技有限公司",
    "product_name": "笔记本电脑",
    "quantity": 100,
    "amount": 500000
  },
  "reasoning": "用户明确提到创建订单，并提供了客户、产品和数量信息"
}

用户输入: "查询订单 SO2025010001 的状态"
输出:
{
  "intent": "query_order",
  "confidence": 0.99,
  "entities": {
    "order_number": "SO2025010001"
  },
  "reasoning": "用户明确要求查询订单状态，并提供了订单号"
}

请只返回 JSON 格式，不要包含其他文字。"""
    
    def parse_user_input(self, user_input: str) -> IntentResult:
        """解析用户输入"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response = self.ai_provider.chat(messages)
        
        try:
            result = self._parse_ai_response(response.content)
            return IntentResult(
                intent=result["intent"],
                confidence=result["confidence"],
                entities=result["entities"],
                original_text=user_input
            )
        except Exception as e:
            return self._fallback_parse(user_input)
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """解析 AI 响应"""
        # 尝试提取 JSON（改进的正则表达式，只匹配第一个完整的 JSON 对象）
        json_match = re.search(r'\{[^{}]*\{[^{}]*\}(?:[^{}]*\{[^{}]*\})*[^{}]*\}', response_text)
        if json_match:
            try:
                result = json.loads(json_match.group())

                # 验证和转换 intent
                intent_str = result.get("intent", "unknown")
                try:
                    result["intent"] = Intent(intent_str)
                except ValueError:
                    result["intent"] = Intent.UNKNOWN

                # 确保必要字段存在
                result.setdefault("confidence", 0.0)
                result.setdefault("entities", {})
                result.setdefault("reasoning", "")

                return result
            except json.JSONDecodeError:
                pass

        # 如果没有找到有效的 JSON，尝试从头提取
        try:
            # 从开头尝试解析 JSON
            json_start = response_text.find('{')
            if json_start >= 0:
                # 查找匹配的闭合括号
                brace_count = 0
                end_pos = json_start + 1
                for i, char in enumerate(response_text[json_start + 1:], start=json_start + 1):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break

                json_str = response_text[json_start:end_pos]
                result = json.loads(json_str)

                # 验证和转换 intent
                intent_str = result.get("intent", "unknown")
                try:
                    result["intent"] = Intent(intent_str)
                except ValueError:
                    result["intent"] = Intent.UNKNOWN

                # 确保必要字段存在
                result.setdefault("confidence", 0.0)
                result.setdefault("entities", {})
                result.setdefault("reasoning", "")

                return result
        except (json.JSONDecodeError, ValueError):
            pass

        raise ValueError("无法解析 AI 响应")
    
    def _fallback_parse(self, user_input: str) -> IntentResult:
        """备用解析方法（基于规则）"""
        user_input_lower = user_input.lower()
        
        # 简单的基于规则的意图识别
        intent = Intent.UNKNOWN
        confidence = 0.5
        
        if any(keyword in user_input_lower for keyword in ["创建订单", "新建订单", "增加订单", "create order"]):
            intent = Intent.CREATE_ORDER
            confidence = 0.7
        elif any(keyword in user_input_lower for keyword in ["审核订单", "批准订单", "approve order"]):
            intent = Intent.APPROVE_ORDER
            confidence = 0.7
        elif any(keyword in user_input_lower for keyword in ["拒绝订单", "驳回订单", "reject order"]):
            intent = Intent.REJECT_ORDER
            confidence = 0.7
        elif any(keyword in user_input_lower for keyword in ["查询客户", "查看客户", "query customer"]):
            intent = Intent.QUERY_CUSTOMER
            confidence = 0.7
        elif any(keyword in user_input_lower for keyword in ["查询产品", "查看产品", "query product"]):
            intent = Intent.QUERY_PRODUCT
            confidence = 0.7
        elif any(keyword in user_input_lower for keyword in ["查询库存", "查看库存", "query inventory"]):
            intent = Intent.QUERY_INVENTORY
            confidence = 0.7
        elif any(keyword in user_input_lower for keyword in ["创建报价", "新建报价", "create quote"]):
            intent = Intent.CREATE_QUOTE
            confidence = 0.7
        elif any(keyword in user_input_lower for keyword in ["查询订单", "查看订单", "query order"]):
            intent = Intent.QUERY_ORDER
            confidence = 0.7
        
        # 提取实体
        entities = self._extract_entities(user_input)
        
        return IntentResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            original_text=user_input
        )
    
    def _extract_entities(self, user_input: str) -> Dict[str, Any]:
        """从用户输入中提取实体"""
        entities = {}
        
        # 提取数量（数字）
        quantity_pattern = r'(\d+)\s*(个|台|件|套|箱|kg|kg)'
        quantity_match = re.search(quantity_pattern, user_input)
        if quantity_match:
            entities["quantity"] = int(quantity_match.group(1))
        
        # 提取金额（中文或数字）
        amount_pattern = r'(\d+(?:\.\d+)?)\s*(万|元|块|USD|USD)'
        amount_match = re.search(amount_pattern, user_input)
        if amount_match:
            amount = float(amount_match.group(1))
            unit = amount_match.group(2)
            if unit == "万":
                amount *= 10000
            entities["amount"] = amount
        
        # 提取订单号（SO 开头）
        order_number_pattern = r'(SO\d{10,})'
        order_match = re.search(order_number_pattern, user_input)
        if order_match:
            entities["order_number"] = order_match.group(1)
        
        # 提取客户名称（公司名称通常较长）
        customer_patterns = [
            r'([^\s,，。]+(?:有限公司|股份公司|集团|科技公司|贸易公司)[^\s,，。]*)',
            r'(北京|上海|广州|深圳|杭州|成都|武汉)[^\s,，。]+?(?:公司|集团)',
        ]
        for pattern in customer_patterns:
            customer_match = re.search(pattern, user_input)
            if customer_match:
                entities["customer_name"] = customer_match.group(1)
                break
        
        return entities
    
    def extract_missing_entities(self, intent_result: IntentResult, required_fields: List[str]) -> List[str]:
        """提取缺失的实体"""
        missing = []
        for field in required_fields:
            if field not in intent_result.entities or not intent_result.entities[field]:
                missing.append(field)
        return missing
    
    def clarify_missing_info(self, intent_result: IntentResult, missing_fields: List[str]) -> str:
        """生成追问问题，收集缺失信息"""
        field_questions = {
            "customer_name": "请问客户名称是什么？",
            "customer_code": "请问客户代码是什么？",
            "product_name": "请问产品名称是什么？",
            "product_code": "请问产品代码是什么？",
            "quantity": "请问数量是多少？",
            "amount": "请问金额是多少？",
            "order_number": "请问订单号是什么？",
            "warehouse_name": "请问从哪个仓库发货？",
            "delivery_address": "请问交付地址是什么？",
            "remark": "有什么备注信息吗？",
        }
        
        questions = [field_questions.get(field, f"请提供 {field} 信息") for field in missing_fields]
        
        if len(questions) == 1:
            return questions[0]
        else:
            return "我需要了解以下信息：\n" + "\n".join(f"- {q}" for q in questions)
