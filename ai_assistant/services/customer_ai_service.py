"""
客户 AI 配置服务

管理客户级别的 AI 助手配置，包括模型选择、权限控制、工具管理等。
"""

from typing import Optional, List, Dict, Any
from django.db import transaction
from django.core.exceptions import PermissionDenied

from ai_assistant.models import (
    CustomerAIConfig,
    AIModelConfig,
    AITool
)


class CustomerAIService:
    """客户 AI 配置服务"""
    
    @staticmethod
    def get_or_create_customer_config(customer_id: int) -> CustomerAIConfig:
        """获取或创建客户 AI 配置"""
        config, created = CustomerAIConfig.objects.get_or_create(
            customer_id=customer_id,
            defaults={
                'is_active': True,
                'permission_level': 'read_only',
                'enable_tool_calling': True,
                'enable_data_query': True,
                'enable_data_modification': False,
            }
        )
        return config
    
    @staticmethod
    def get_effective_system_prompt(customer_id: int) -> str:
        """获取有效的系统提示词（客户配置 > 默认配置）"""
        config = CustomerAIConfig.objects.filter(
            customer_id=customer_id,
            is_active=True
        ).first()
        
        if config and config.system_prompt:
            return config.system_prompt
        
        # 返回默认系统提示词
        return """你是一个专业的 ERP 系统智能助手，帮助企业用户高效管理业务数据。

你的主要功能:
1. 协助用户创建和查询销售订单、报价单等业务单据
2. 回答关于客户、产品、库存等业务数据的问题
3. 提供数据分析和建议

注意事项:
- 严格按照用户的权限级别操作数据
- 对于重要操作，需要用户明确确认
- 保护用户隐私和商业机密
- 不确定的回答，请说明并建议用户咨询相关部门"""
    
    @staticmethod
    def get_effective_model_config(customer_id: int) -> Optional[AIModelConfig]:
        """获取有效的模型配置（客户配置 > 全局默认）"""
        config = CustomerAIConfig.objects.filter(
            customer_id=customer_id,
            is_active=True
        ).first()
        
        if config:
            effective_config = config.get_effective_model_config()
            if effective_config:
                return effective_config
        
        # 返回全局默认配置
        return AIModelConfig.objects.filter(is_default=True).first()
    
    @staticmethod
    def get_allowed_tools_for_customer(customer_id: int) -> List[str]:
        """获取客户允许使用的工具列表"""
        config = CustomerAIConfig.objects.filter(
            customer_id=customer_id,
            is_active=True
        ).first()
        
        if config:
            return config.get_allowed_tools_list()
        
        # 返回默认工具列表
        return [
            'query_customer',
            'query_product',
            'query_inventory',
            'query_order',
        ]
    
    @staticmethod
    def can_customer_use_tool(customer_id: int, tool_name: str) -> bool:
        """检查客户是否可以使用指定工具"""
        config = CustomerAIConfig.objects.filter(
            customer_id=customer_id,
            is_active=True
        ).first()
        
        if not config:
            # 没有配置的客户使用默认权限
            return tool_name in [
                'query_customer',
                'query_product',
                'query_inventory',
                'query_order',
            ]
        
        return config.can_use_tool(tool_name)
    
    @staticmethod
    def can_customer_query_data(customer_id: int) -> bool:
        """检查客户是否可以查询数据"""
        config = CustomerAIConfig.objects.filter(
            customer_id=customer_id,
            is_active=True
        ).first()
        
        if not config:
            return False
        
        return config.can_query_data()
    
    @staticmethod
    def can_customer_modify_data(customer_id: int) -> bool:
        """检查客户是否可以修改数据"""
        config = CustomerAIConfig.objects.filter(
            customer_id=customer_id,
            is_active=True
        ).first()
        
        if not config:
            return False
        
        return config.can_modify_data()
    
    @staticmethod
    def update_customer_config(
        customer_id: int,
        model_config_id: Optional[int] = None,
        system_prompt: Optional[str] = None,
        permission_level: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        blocked_tools: Optional[List[str]] = None,
        max_conversation_turns: Optional[int] = None,
        max_conversation_duration: Optional[int] = None,
        enable_tool_calling: Optional[bool] = None,
        enable_data_query: Optional[bool] = None,
        enable_data_modification: Optional[bool] = None,
    ) -> CustomerAIConfig:
        """更新客户 AI 配置"""
        config = CustomerAIService.get_or_create_customer_config(customer_id)
        
        if model_config_id is not None:
            config.model_config_id = model_config_id
        
        if system_prompt is not None:
            config.system_prompt = system_prompt
        
        if permission_level is not None:
            config.permission_level = permission_level
        
        if allowed_tools is not None:
            config.allowed_tools = allowed_tools
        
        if blocked_tools is not None:
            config.blocked_tools = blocked_tools
        
        if max_conversation_turns is not None:
            config.max_conversation_turns = max_conversation_turns
        
        if max_conversation_duration is not None:
            config.max_conversation_duration = max_conversation_duration
        
        if enable_tool_calling is not None:
            config.enable_tool_calling = enable_tool_calling
        
        if enable_data_query is not None:
            config.enable_data_query = enable_data_query
        
        if enable_data_modification is not None:
            config.enable_data_modification = enable_data_modification
        
        config.save()
        return config
    
    @staticmethod
    def reset_customer_config(customer_id: int) -> CustomerAIConfig:
        """重置客户 AI 配置为默认值"""
        config = CustomerAIService.get_or_create_customer_config(customer_id)
        
        config.model_config = None
        config.system_prompt = ''
        config.permission_level = 'read_only'
        config.allowed_tools = []
        config.blocked_tools = []
        config.max_conversation_turns = 50
        config.max_conversation_duration = 60
        config.enable_tool_calling = True
        config.enable_data_query = True
        config.enable_data_modification = False
        
        config.save()
        return config
    
    @staticmethod
    def increment_conversation_stats(customer_id: int, message_count: int = 1):
        """增加会话统计信息"""
        config = CustomerAIConfig.objects.filter(
            customer_id=customer_id,
            is_active=True
        ).first()
        
        if config:
            config.total_conversations += 1
            config.total_messages += message_count
            config.last_used_at = config.updated_at
            config.save(update_fields=['total_conversations', 'total_messages', 'last_used_at'])
    
    @staticmethod
    def get_all_available_tools() -> List[Dict[str, Any]]:
        """获取所有可用的工具"""
        tools = AITool.objects.filter(is_active=True)
        return [
            {
                'tool_name': tool.tool_name,
                'display_name': tool.display_name,
                'category': tool.category,
                'description': tool.description,
                'requires_approval': tool.requires_approval,
            }
            for tool in tools
        ]
    
    @staticmethod
    def validate_tool_permission(customer_id: int, tool_name: str, action: str = 'execute') -> bool:
        """验证工具权限"""
        config = CustomerAIConfig.objects.filter(
            customer_id=customer_id,
            is_active=True
        ).first()
        
        if not config:
            return False
        
        # 检查工具是否在允许列表中
        if not config.can_use_tool(tool_name):
            return False
        
        # 检查权限级别
        if action == 'modify' and config.permission_level != 'full_access':
            return False
        
        # 检查工具调用开关
        if not config.enable_tool_calling:
            return False
        
        return True
    
    @staticmethod
    def get_customer_permission_summary(customer_id: int) -> Dict[str, Any]:
        """获取客户权限摘要"""
        config = CustomerAIConfig.objects.filter(
            customer_id=customer_id,
            is_active=True
        ).first()
        
        if not config:
            return {
                'has_config': False,
                'permission_level': 'none',
                'can_query': False,
                'can_modify': False,
                'allowed_tools': [],
                'blocked_tools': [],
            }
        
        return {
            'has_config': True,
            'permission_level': config.permission_level,
            'can_query': config.can_query_data(),
            'can_modify': config.can_modify_data(),
            'allowed_tools': config.get_allowed_tools_list(),
            'blocked_tools': config.blocked_tools,
            'enable_tool_calling': config.enable_tool_calling,
            'total_conversations': config.total_conversations,
            'total_messages': config.total_messages,
            'last_used_at': config.last_used_at,
        }
