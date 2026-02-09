"""
AI助手数据模型
"""

from core.models import BaseModel
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class CustomerAIConfig(BaseModel):
    """客户级别的 AI 助手配置"""

    PERMISSION_CHOICES = [
        ("read_only", "只读"),
        ("read_write", "读写"),
        ("full_access", "完全访问"),
    ]

    # 关联客户
    customer = models.OneToOneField(
        "customers.Customer",
        verbose_name="客户",
        on_delete=models.CASCADE,
        related_name="ai_config",
        unique=True,
    )

    # 模型配置（客户级别，优先级高于全局）
    model_config = models.ForeignKey(
        "AIModelConfig",
        verbose_name="AI 模型配置",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_configs",
        help_text="留空则使用全局默认配置",
    )

    # 系统提示词自定义
    system_prompt = models.TextField("系统提示词", blank=True, help_text="自定义系统提示词，留空则使用默认提示词")

    # 权限配置
    permission_level = models.CharField(
        "权限级别",
        max_length=20,
        choices=PERMISSION_CHOICES,
        default="read_only",
        help_text="客户 AI 助手的权限级别",
    )

    # 工具权限控制
    allowed_tools = models.JSONField(
        "允许的工具", default=list, blank=True, help_text="允许客户 AI 助手使用的工具列表，留空则使用默认工具集"
    )

    blocked_tools = models.JSONField(
        "阻止的工具", default=list, blank=True, help_text="明确阻止的工具列表，优先级高于 allowed_tools"
    )

    # 参数配置
    max_conversation_turns = models.IntegerField("最大对话轮数", default=50, help_text="单次会话的最大对话轮数")

    max_conversation_duration = models.IntegerField(
        "最大会话时长(分钟)", default=60, help_text="单次会话的最长持续时间"
    )

    # 功能开关
    enable_tool_calling = models.BooleanField("启用工具调用", default=True, help_text="是否允许 AI 助手调用工具")

    enable_data_query = models.BooleanField("启用数据查询", default=True, help_text="是否允许查询客户数据")

    enable_data_modification = models.BooleanField(
        "启用数据修改", default=False, help_text="是否允许修改客户数据（需要 full_access 权限）"
    )

    # 状态管理
    is_active = models.BooleanField("是否启用", default=True)

    # 使用统计
    total_conversations = models.IntegerField("总会话数", default=0)
    total_messages = models.IntegerField("总消息数", default=0)
    last_used_at = models.DateTimeField("最后使用时间", null=True, blank=True)

    class Meta:
        db_table = "customer_ai_config"
        verbose_name = "客户 AI 配置"
        verbose_name_plural = "客户 AI 配置"
        ordering = ["customer__name"]
        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["permission_level"]),
        ]

    def __str__(self):
        return f"{self.customer.name} - AI 配置"

    def get_effective_model_config(self):
        """获取有效的模型配置（客户配置 > 全局默认，带缓存）"""
        from ai_assistant.services.cache_service import AIModelConfigCache

        # 1. 优先使用客户级别的配置
        if self.model_config:
            return self.model_config

        # 2. 尝试从缓存获取默认配置
        cached_config = AIModelConfigCache.get_default_config()
        if cached_config:
            return cached_config

        # 3. 从数据库查询并缓存
        default_config = AIModelConfig.objects.filter(
            is_default=True, is_active=True, is_deleted=False
        ).first()

        if default_config:
            AIModelConfigCache.set_default_config(default_config)

        return default_config

    def save(self, *args, **kwargs):
        """保存配置时自动更新缓存"""
        super().save(*args, **kwargs)

        # 使相关缓存失效
        from ai_assistant.services.cache_service import AIModelConfigCache

        if self.customer:
            AIModelConfigCache.invalidate_customer_config(self.customer.id)

        # 如果修改了默认配置，也使默认配置缓存失效
        AIModelConfigCache.invalidate_default_config()

    def get_allowed_tools_list(self):
        """获取允许的工具列表（考虑阻止列表）"""
        allowed = self.allowed_tools or []
        blocked = self.blocked_tools or []
        return [tool for tool in allowed if tool not in blocked]

    def can_use_tool(self, tool_name):
        """检查是否可以使用指定工具"""
        allowed_tools = self.get_allowed_tools_list()

        # 如果有明确的允许列表，只允许列表中的工具
        if allowed_tools:
            return tool_name in allowed_tools

        # 如果有明确的阻止列表，不允许列表中的工具
        if self.blocked_tools:
            return tool_name not in self.blocked_tools

        # 默认允许
        return True

    def can_modify_data(self):
        """检查是否可以修改数据"""
        return (
            self.is_active
            and self.enable_data_modification
            and self.permission_level == "full_access"
        )

    def can_query_data(self):
        """检查是否可以查询数据"""
        return (
            self.is_active
            and self.enable_data_query
            and self.permission_level in ["read_write", "full_access"]
        )


class AIModelConfig(BaseModel):
    """大模型API配置"""

    PROVIDER_CHOICES = [
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic Claude"),
        ("baidu", "百度文心一言"),
        ("aliyun", "阿里通义千问"),
        ("tencent", "腾讯混元"),
        ("zhipu", "智谱AI"),
        ("moonshot", "Moonshot"),
        ("deepseek", "DeepSeek"),
        ("mock", "Mock（测试用）"),
        ("google", "Google Gemini"),
        ("azure_openai", "Microsoft Azure OpenAI"),
        ("aws_bedrock", "AWS Bedrock"),
        ("groq", "Groq"),
        ("huggingface", "Hugging Face"),
        ("cohere", "Cohere"),
        ("mistral", "Mistral"),
        ("perplexity", "Perplexity"),
        ("together", "Together AI"),
        ("openrouter", "OpenRouter"),
    ]

    # 基本信息
    name = models.CharField("配置名称", max_length=100)
    provider = models.CharField("提供商", max_length=50, choices=PROVIDER_CHOICES)

    # API配置
    api_key = models.CharField("API Key", max_length=500, help_text="将被加密存储")
    api_base = models.CharField(
        "API Base URL", max_length=500, blank=True, help_text="自定义API地址，留空使用默认"
    )
    model_name = models.CharField(
        "模型名称", max_length=100, help_text="如: gpt-4, claude-3-5-sonnet, ernie-bot-4.0"
    )

    # 参数配置
    temperature = models.DecimalField(
        "Temperature", max_digits=3, decimal_places=2, default=0.7, help_text="控制输出随机性，0-1之间"
    )
    max_tokens = models.IntegerField("Max Tokens", default=2000, help_text="最大生成Token数")
    timeout = models.IntegerField("超时时间(秒)", default=60)

    # 状态管理
    is_active = models.BooleanField("是否启用", default=True)
    is_default = models.BooleanField("是否默认", default=False, help_text="默认配置将被优先使用")
    priority = models.IntegerField("优先级", default=0, help_text="数字越大优先级越高")

    # 使用统计
    total_requests = models.IntegerField("总请求数", default=0)
    total_tokens = models.IntegerField("总Token数", default=0)
    last_used_at = models.DateTimeField("最后使用时间", null=True, blank=True)

    class Meta:
        db_table = "ai_model_config"
        verbose_name = "AI模型配置"
        verbose_name_plural = "AI模型配置"
        ordering = ["-priority", "-is_default", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_provider_display()})"

    def save(self, *args, **kwargs):
        # 如果设置为默认，取消其他配置的默认状态
        if self.is_default:
            AIModelConfig.objects.filter(is_default=True).exclude(pk=self.pk).update(
                is_default=False
            )
        super().save(*args, **kwargs)

        # 使缓存失效
        from ai_assistant.services.cache_service import AIModelConfigCache

        AIModelConfigCache.invalidate_default_config()


class AIConversation(BaseModel):
    """AI对话会话"""

    CHANNEL_CHOICES = [
        ("web", "Web界面"),
        ("wechat", "微信"),
        ("dingtalk", "钉钉"),
        ("telegram", "Telegram"),
    ]

    STATUS_CHOICES = [
        ("active", "活跃"),
        ("ended", "已结束"),
    ]

    conversation_id = models.CharField("会话ID", max_length=100, unique=True, db_index=True)
    user = models.ForeignKey(
        User, verbose_name="用户", on_delete=models.CASCADE, related_name="ai_conversations"
    )
    channel = models.CharField("渠道", max_length=20, choices=CHANNEL_CHOICES)
    channel_user_id = models.CharField(
        "渠道用户ID", max_length=200, help_text="微信openid或钉钉userid", blank=True
    )

    # 会话状态
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="active")

    # 会话元信息
    title = models.CharField("会话标题", max_length=200, blank=True)
    context_summary = models.TextField("上下文摘要", blank=True, help_text="用于上下文压缩")

    # 统计信息
    message_count = models.IntegerField("消息数", default=0)
    last_message_at = models.DateTimeField("最后消息时间", null=True, blank=True)

    class Meta:
        db_table = "ai_conversation"
        verbose_name = "AI对话会话"
        verbose_name_plural = "AI对话会话"
        ordering = ["-last_message_at"]
        indexes = [
            models.Index(fields=["user", "channel", "status"]),
            models.Index(fields=["conversation_id"]),
        ]

    def __str__(self):
        return f"{self.conversation_id} - {self.user.username}"


class AIMessage(BaseModel):
    """AI对话消息"""

    ROLE_CHOICES = [
        ("user", "用户"),
        ("assistant", "AI助手"),
        ("system", "系统"),
        ("tool", "工具调用"),
    ]

    CONTENT_TYPE_CHOICES = [
        ("text", "文本"),
        ("image", "图片"),
        ("file", "文件"),
    ]

    conversation = models.ForeignKey(
        AIConversation, verbose_name="会话", on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField("角色", max_length=20, choices=ROLE_CHOICES)

    # 消息内容
    content = models.TextField("消息内容")
    content_type = models.CharField(
        "内容类型", max_length=20, choices=CONTENT_TYPE_CHOICES, default="text"
    )

    # 工具调用记录
    tool_calls = models.JSONField("工具调用", null=True, blank=True, help_text="记录AI调用的工具和参数")
    tool_results = models.JSONField("工具结果", null=True, blank=True)

    # 模型信息
    model_config = models.ForeignKey(
        AIModelConfig, verbose_name="使用的模型", on_delete=models.SET_NULL, null=True, blank=True
    )
    tokens_used = models.IntegerField("消耗Token数", default=0)
    response_time = models.DecimalField(
        "响应时间(秒)", max_digits=10, decimal_places=3, null=True, blank=True
    )

    class Meta:
        db_table = "ai_message"
        verbose_name = "AI对话消息"
        verbose_name_plural = "AI对话消息"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}"


class AITool(BaseModel):
    """AI可调用的ERP工具"""

    CATEGORY_CHOICES = [
        ("sales", "销售管理"),
        ("purchase", "采购管理"),
        ("inventory", "库存管理"),
        ("finance", "财务管理"),
        ("report", "报表查询"),
        ("system", "系统管理"),
    ]

    tool_name = models.CharField("工具名称", max_length=100, unique=True, db_index=True)
    display_name = models.CharField("显示名称", max_length=200)
    category = models.CharField("分类", max_length=50, choices=CATEGORY_CHOICES)

    # 工具描述（给AI看的）
    description = models.TextField("工具描述", help_text="描述工具的功能，AI会根据此决定是否调用")

    # 参数定义（JSON Schema格式）
    parameters = models.JSONField("参数定义", help_text="JSON Schema格式定义工具参数")

    # 执行配置
    handler_path = models.CharField(
        "处理器路径", max_length=200, help_text="如: ai_assistant.tools.sales.SearchCustomerTool"
    )
    requires_approval = models.BooleanField("需要审批", default=False, help_text="高风险操作需要用户确认")

    # 权限控制
    required_permissions = models.JSONField("所需权限", default=list, help_text="用户需要的权限列表")

    # 状态
    is_active = models.BooleanField("是否启用", default=True)

    # 使用统计
    call_count = models.IntegerField("调用次数", default=0)
    success_count = models.IntegerField("成功次数", default=0)
    last_called_at = models.DateTimeField("最后调用时间", null=True, blank=True)

    class Meta:
        db_table = "ai_tool"
        verbose_name = "AI工具定义"
        verbose_name_plural = "AI工具定义"
        ordering = ["category", "tool_name"]

    def __str__(self):
        return f"{self.display_name} ({self.get_category_display()})"


class WeChatConfig(BaseModel):
    """微信企业号配置"""

    corp_id = models.CharField("企业ID", max_length=100)
    corp_secret = models.CharField("应用Secret", max_length=500, help_text="将被加密存储")
    agent_id = models.CharField("应用AgentID", max_length=100)
    token = models.CharField("Token", max_length=100)
    encoding_aes_key = models.CharField("EncodingAESKey", max_length=500)

    is_active = models.BooleanField("是否启用", default=True)

    class Meta:
        db_table = "wechat_config"
        verbose_name = "微信配置"
        verbose_name_plural = "微信配置"

    def __str__(self):
        return f"微信企业号 - {self.corp_id}"


class DingTalkConfig(BaseModel):
    """钉钉企业应用配置"""

    app_key = models.CharField("AppKey", max_length=100)
    app_secret = models.CharField("AppSecret", max_length=500, help_text="将被加密存储")
    agent_id = models.CharField("AgentID", max_length=100)

    is_active = models.BooleanField("是否启用", default=True)

    class Meta:
        db_table = "dingtalk_config"
        verbose_name = "钉钉配置"
        verbose_name_plural = "钉钉配置"

    def __str__(self):
        return f"钉钉应用 - {self.app_key}"


class TelegramConfig(BaseModel):
    """Telegram Bot配置"""

    bot_token = models.CharField(
        "Bot Token", max_length=500, help_text="从 @BotFather 获取的Token，将被加密存储"
    )
    bot_username = models.CharField("Bot用户名", max_length=100, blank=True, help_text="机器人的@username")
    webhook_url = models.CharField(
        "Webhook URL", max_length=500, blank=True, help_text="Telegram回调地址"
    )

    # 功能开关
    allow_groups = models.BooleanField("允许群组", default=False, help_text="是否允许在群组中使用")
    command_prefix = models.CharField("命令前缀", max_length=10, default="/", help_text="命令前缀，默认为/")

    is_active = models.BooleanField("是否启用", default=True)

    class Meta:
        db_table = "telegram_config"
        verbose_name = "Telegram配置"
        verbose_name_plural = "Telegram配置"

    def __str__(self):
        return f"Telegram Bot - {self.bot_username or 'Unknown'}"


class AIToolExecutionLog(BaseModel):
    """AI工具执行日志"""

    # 工具信息
    tool_name = models.CharField("工具名称", max_length=100)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="执行用户", related_name="ai_tool_executions"
    )

    # 执行参数和结果
    parameters = models.JSONField("执行参数", default=dict, help_text="工具调用时传入的参数")
    result = models.JSONField("执行结果", default=dict, help_text="工具返回的结果")

    # 执行状态
    success = models.BooleanField("是否成功", default=True)
    error_message = models.TextField("错误信息", blank=True)

    # 时间记录
    executed_at = models.DateTimeField("执行时间", auto_now_add=True)
    execution_time = models.FloatField("执行耗时(秒)", null=True, blank=True)

    # 关联会话（可选）
    conversation = models.ForeignKey(
        "AIConversation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="关联会话",
        related_name="tool_executions",
    )

    class Meta:
        db_table = "ai_tool_execution_log"
        verbose_name = "AI工具执行日志"
        verbose_name_plural = "AI工具执行日志"
        ordering = ["-executed_at"]
        indexes = [
            models.Index(fields=["tool_name", "-executed_at"]),
            models.Index(fields=["user", "-executed_at"]),
            models.Index(fields=["success", "-executed_at"]),
        ]

    def __str__(self):
        status = "成功" if self.success else "失败"
        return f"{self.tool_name} - {self.user.username} - {status}"


class ChannelUserMapping(BaseModel):
    """渠道用户身份映射"""

    CHANNEL_CHOICES = [
        ("wechat", "微信"),
        ("dingtalk", "钉钉"),
        ("telegram", "Telegram"),
    ]

    # 渠道信息
    channel = models.CharField("渠道", max_length=20, choices=CHANNEL_CHOICES)
    external_user_id = models.CharField(
        "外部用户ID", max_length=200, help_text="微信OpenID、钉钉UserID或Telegram ChatID"
    )
    external_username = models.CharField(
        "外部用户名", max_length=200, blank=True, help_text="外部平台的用户名或昵称"
    )

    # 系统用户
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="系统用户", related_name="channel_mappings"
    )

    # 状态
    is_active = models.BooleanField("是否启用", default=True)

    # 元数据
    metadata = models.JSONField("元数据", default=dict, blank=True, help_text="存储额外的用户信息")

    class Meta:
        db_table = "channel_user_mapping"
        verbose_name = "渠道用户映射"
        verbose_name_plural = "渠道用户映射"
        unique_together = [["channel", "external_user_id"]]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["channel", "external_user_id"]),
            models.Index(fields=["user", "channel"]),
        ]

    def __str__(self):
        return f"{self.get_channel_display()} \
            {self.external_username or self.external_user_id} → {self.user.username}"
