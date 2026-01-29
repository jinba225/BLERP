"""
对话流管理器

管理多轮对话，逐步收集用户信息，创建/审核文档。

主要功能:
1. 维护对话状态
2. 根据缺失信息生成追问
3. 验证数据有效性
4. 执行业务操作
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from apps.ai_assistant.services.nlp_service import NLPService, Intent, IntentResult


class ConversationState(Enum):
    """对话状态"""
    GREETING = "greeting"
    COLLECTING_INFO = "collecting_info"
    CONFIRMING = "confirming"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    user_id: int
    state: ConversationState = ConversationState.GREETING
    intent: Optional[Intent] = None
    collected_data: Dict[str, Any] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None


class ConversationFlowManager:
    """对话流管理器"""
    
    def __init__(self, nlp_service: NLPService):
        self.nlp_service = nlp_service
        self.contexts: Dict[str, ConversationContext] = {}
        
        # 每个意图的必需字段
        self.intent_required_fields = {
            Intent.CREATE_ORDER: ["customer_name", "product_name", "quantity"],
            Intent.CREATE_QUOTE: ["customer_name", "product_name", "quantity"],
            Intent.APPROVE_ORDER: ["order_number"],
            Intent.REJECT_ORDER: ["order_number"],
            Intent.QUERY_CUSTOMER: ["customer_name"],
            Intent.QUERY_PRODUCT: ["product_name"],
            Intent.QUERY_INVENTORY: [],
            Intent.QUERY_ORDER: ["order_number"],
        }
    
    def create_context(self, session_id: str, user_id: int) -> ConversationContext:
        """创建新的对话上下文"""
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            state=ConversationState.GREETING
        )
        self.contexts[session_id] = context
        return context
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """获取对话上下文"""
        return self.contexts.get(session_id)
    
    def process_message(
        self, 
        session_id: str, 
        user_id: int, 
        user_message: str
    ) -> Tuple[str, bool]:
        """处理用户消息，返回 AI 回复和是否完成
        
        Returns:
            (reply, is_completed): AI 回复和是否完成对话
        """
        # 获取或创建上下文
        context = self.get_context(session_id)
        if not context:
            context = self.create_context(session_id, user_id)
        
        # 记录对话历史
        context.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # 根据状态处理消息
        try:
            if context.state == ConversationState.GREETING:
                return self._handle_greeting(context, user_message)
            elif context.state == ConversationState.COLLECTING_INFO:
                return self._handle_collecting_info(context, user_message)
            elif context.state == ConversationState.CONFIRMING:
                return self._handle_confirming(context, user_message)
            elif context.state == ConversationState.EXECUTING:
                return self._handle_executing(context, user_message)
            else:
                return self._handle_completed_or_error(context)
        except Exception as e:
            context.state = ConversationState.ERROR
            context.error_message = str(e)
            context.updated_at = datetime.now()
            return f"处理过程中发生错误: {str(e)}", False
    
    def _handle_greeting(self, context: ConversationContext, user_message: str) -> Tuple[str, bool]:
        """处理初始问候消息"""
        # 解析意图
        intent_result = self.nlp_service.parse_user_input(user_message)
        
        context.intent = intent_result.intent
        context.collected_data.update(intent_result.entities)
        
        # 如果意图未知，请求澄清
        if context.intent == Intent.UNKNOWN:
            reply = "我不太理解您的需求。您是想创建订单、查询客户、查询产品，还是有其他需求？"
            context.updated_at = datetime.now()
            return reply, False
        
        # 检查缺失字段
        required_fields = self.intent_required_fields.get(context.intent, [])
        missing_fields = self.nlp_service.extract_missing_entities(intent_result, required_fields)
        
        context.missing_fields = missing_fields
        
        if not missing_fields:
            # 所有必需信息都已收集，进入确认阶段
            context.state = ConversationState.CONFIRMING
            return self._generate_confirmation(context)
        else:
            # 进入收集信息阶段
            context.state = ConversationState.COLLECTING_INFO
            reply = self.nlp_service.clarify_missing_info(intent_result, missing_fields)
            context.updated_at = datetime.now()
            return reply, False
    
    def _handle_collecting_info(self, context: ConversationContext, user_message: str) -> Tuple[str, bool]:
        """处理收集信息阶段的消息"""
        # 在收集信息阶段，直接使用 MockAIProvider 的实体提取逻辑
        # 这样可以避免 NLP 服务的意图识别干扰实体提取

        # 直接调用 MockAIProvider 的 _extract_intent_entities 方法
        entities = {}
        try:
            if hasattr(self.nlp_service.ai_provider, '_extract_intent_entities'):
                entities = self.nlp_service.ai_provider._extract_intent_entities(user_message)
                # 调试信息
                # print(f"DEBUG: _handle_collecting_info - 提取到的实体: {entities}")
        except Exception as e:
            # print(f"DEBUG: _handle_collecting_info - 实体提取失败: {str(e)}")
            entities = {}

        # 更新收集的数据
        for key, value in entities.items():
            if value:
                context.collected_data[key] = value

        # 检查缺失字段
        required_fields = self.intent_required_fields.get(context.intent, [])
        missing_fields = [
            field for field in required_fields
            if field not in context.collected_data or not context.collected_data.get(field)
        ]

        context.missing_fields = missing_fields

        # 自动进入确认阶段（当所有字段都已收集时）
        if not missing_fields:
            # 所有必需信息都已收集，进入确认阶段
            context.state = ConversationState.CONFIRMING
            return self._generate_confirmation(context)

        # 如果还在收集信息阶段，检查是否有确认指令
        if missing_fields:
            if any(word in user_message.lower() for word in ['确认', '是', '好的', 'OK', '没问题']):
                # 用户确认，进入确认阶段
                context.state = ConversationState.CONFIRMING
                return self._generate_confirmation(context)
            elif any(word in user_message.lower() for word in ['取消', '重来', '重新开始']):
                # 用户取消，重新开始
                context.state = ConversationState.GREETING
                context.collected_data = {}
                context.missing_fields = []
                return "好的，已取消当前操作。请问您想做什么？", False

        # 继续收集信息
        reply = self.nlp_service.clarify_missing_info(
            IntentResult(intent=context.intent, confidence=0.85, entities={}, original_text=user_message),
            missing_fields
        )
        context.updated_at = datetime.now()
        return reply, False
    
    def _generate_confirmation(self, context: ConversationContext) -> Tuple[str, bool]:
        """生成确认消息"""
        intent_name = {
            Intent.CREATE_ORDER: "创建销售订单",
            Intent.CREATE_QUOTE: "创建报价单",
            Intent.APPROVE_ORDER: "审核订单",
            Intent.REJECT_ORDER: "拒绝订单",
            Intent.QUERY_CUSTOMER: "查询客户",
            Intent.QUERY_PRODUCT: "查询产品",
            Intent.QUERY_INVENTORY: "查询库存",
            Intent.QUERY_ORDER: "查询订单",
        }.get(context.intent, "未知操作")
        
        reply = f"确认要执行以下操作：\n\n"
        reply += f"操作类型: {intent_name}\n"
        
        # 显示收集的数据
        for key, value in context.collected_data.items():
            reply += f"{key}: {value}\n"
        
        reply += '\n请确认是否继续？（回复"确认"或"取消"）'
        context.updated_at = datetime.now()
        return reply, False
    
    def _handle_confirming(self, context: ConversationContext, user_message: str) -> Tuple[str, bool]:
        """处理确认阶段的消息"""
        user_message_lower = user_message.lower()

        # 首先检查是否还有缺失的必需信息
        required_fields = self.intent_required_fields.get(context.intent, [])
        missing_fields = [
            field for field in required_fields
            if field not in context.collected_data or not context.collected_data.get(field)
        ]

        # 如果还有缺失信息，回到收集信息阶段
        if missing_fields:
            # 还有缺失信息，回到收集信息阶段
            context.state = ConversationState.COLLECTING_INFO
            reply = f"以下信息还未提供：{', '.join(missing_fields)}。请补充这些信息。"
            context.updated_at = datetime.now()
            return reply, False

        # 检查确认或取消指令
        if "确认" in user_message_lower or "是" in user_message_lower or "好的" in user_message_lower or "OK" in user_message_lower or "没问题":
            # 用户确认，执行操作
            context.state = ConversationState.EXECUTING
            return self._execute_operation(context)
        elif "取消" in user_message_lower or "否" in user_message_lower:
            # 用户取消
            context.state = ConversationState.COMPLETED
            reply = "操作已取消。"
            context.updated_at = datetime.now()
            return reply, True
        else:
            # 用户没有明确回答，重新确认
            return self._generate_confirmation(context)
    
    def _execute_operation(self, context: ConversationContext) -> Tuple[str, bool]:
        """执行业务操作"""
        try:
            # 根据意图执行相应操作
            if context.intent == Intent.CREATE_ORDER:
                result = self._create_order(context)
            elif context.intent == Intent.CREATE_QUOTE:
                result = self._create_quote(context)
            elif context.intent == Intent.APPROVE_ORDER:
                result = self._approve_order(context)
            elif context.intent == Intent.REJECT_ORDER:
                result = self._reject_order(context)
            elif context.intent == Intent.QUERY_CUSTOMER:
                result = self._query_customer(context)
            elif context.intent == Intent.QUERY_PRODUCT:
                result = self._query_product(context)
            elif context.intent == Intent.QUERY_INVENTORY:
                result = self._query_inventory(context)
            elif context.intent == Intent.QUERY_ORDER:
                result = self._query_order(context)
            else:
                raise ValueError(f"未知意图: {context.intent}")
            
            context.state = ConversationState.COMPLETED
            context.updated_at = datetime.now()
            
            # 记录 AI 回复
            context.conversation_history.append({
                "role": "assistant",
                "content": result,
                "timestamp": datetime.now().isoformat()
            })
            
            return result, True
        
        except Exception as e:
            context.state = ConversationState.ERROR
            context.error_message = str(e)
            context.updated_at = datetime.now()
            return f"执行操作时发生错误: {str(e)}", False
    
    def _handle_executing(self, context: ConversationContext, user_message: str) -> Tuple[str, bool]:
        """处理执行阶段的消息（不应该到达这里）"""
        return self._generate_confirmation(context)
    
    def _handle_completed_or_error(self, context: ConversationContext) -> Tuple[str, bool]:
        """处理已完成或错误的对话"""
        if context.state == ConversationState.COMPLETED:
            return "操作已完成。如需继续，请重新开始。", True
        else:
            return f"操作失败: {context.error_message}。如需继续，请重新开始。", False
    
    def _create_order(self, context: ConversationContext) -> str:
        """创建销售订单（示例实现）"""
        # 这里应该调用实际的业务逻辑
        customer_name = context.collected_data.get("customer_name", "")
        product_name = context.collected_data.get("product_name", "")
        quantity = context.collected_data.get("quantity", "")
        
        return f"✅ 成功创建销售订单！\n客户: {customer_name}\n产品: {product_name}\n数量: {quantity}\n\n订单号: SO{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _create_quote(self, context: ConversationContext) -> str:
        """创建报价单（示例实现）"""
        customer_name = context.collected_data.get("customer_name", "")
        product_name = context.collected_data.get("product_name", "")
        quantity = context.collected_data.get("quantity", "")
        
        return f"✅ 成功创建报价单！\n客户: {customer_name}\n产品: {product_name}\n数量: {quantity}\n\n报价单号: QT{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _approve_order(self, context: ConversationContext) -> str:
        """审核订单（示例实现）"""
        order_number = context.collected_data.get("order_number", "")
        return f"✅ 成功审核订单 {order_number}！"
    
    def _reject_order(self, context: ConversationContext) -> str:
        """拒绝订单（示例实现）"""
        order_number = context.collected_data.get("order_number", "")
        return f"❌ 已拒绝订单 {order_number}。"
    
    def _query_customer(self, context: ConversationContext) -> str:
        """查询客户（示例实现）"""
        customer_name = context.collected_data.get("customer_name", "")
        return f"📋 客户信息:\n客户名称: {customer_name}\n客户代码: CUST001\n联系人: 张三\n电话: 13800138000\n地址: 北京市朝阳区"
    
    def _query_product(self, context: ConversationContext) -> str:
        """查询产品（示例实现）"""
        product_name = context.collected_data.get("product_name", "")
        return f"📦 产品信息:\n产品名称: {product_name}\n产品代码: PROD001\n单价: ¥5,000.00\n库存: 100"
    
    def _query_inventory(self, context: ConversationContext) -> str:
        """查询库存（示例实现）"""
        return f"📊 库存信息:\n笔记本电脑: 100 台\n显示器: 50 台\n键盘: 200 个"
    
    def _query_order(self, context: ConversationContext) -> str:
        """查询订单（示例实现）"""
        order_number = context.collected_data.get("order_number", "")
        return f"📋 订单信息:\n订单号: {order_number}\n状态: 已审核\n总金额: ¥50,000.00\n创建时间: 2025-01-26"
    
    def reset_context(self, session_id: str) -> None:
        """重置对话上下文"""
        if session_id in self.contexts:
            del self.contexts[session_id]
