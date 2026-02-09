"""
核心配置文件
包含平台限流配置、告警规则、缓存策略等
"""

# ============================================
# 平台API限流配置
# ============================================
# 令牌桶算法参数：
# - rate: 每秒生成的令牌数（平均速率）
# - burst: 桶的容量（突发流量上限）
from enum import Enum

PLATFORM_RATE_LIMITS = {
    # 采集平台
    "taobao": {
        "rate": 10,  # 10次/秒
        "burst": 20,  # 突发20次
    },
    "1688": {
        "rate": 8,
        "burst": 15,
    },
    "pdd": {
        "rate": 5,  # 拼多多限制更严格
        "burst": 10,
    },
    "aliexpress": {
        "rate": 3,
        "burst": 5,
    },
    # 跨境同步平台
    "amazon": {
        "rate": 10,
        "burst": 20,
    },
    "ebay": {
        "rate": 8,
        "burst": 15,
    },
    "aliexpress_sync": {
        "rate": 5,
        "burst": 10,
    },
    "lazada": {
        "rate": 8,
        "burst": 15,
    },
    "shopify": {
        "rate": 10,
        "burst": 20,
    },
    "woo": {
        "rate": 10,
        "burst": 20,
    },
    "jumia": {
        "rate": 5,
        "burst": 10,
    },
    "cdiscount": {
        "rate": 5,
        "burst": 10,
    },
    "shopee": {
        "rate": 8,
        "burst": 15,
    },
    "tiktok": {
        "rate": 5,
        "burst": 10,
    },
    "temu": {
        "rate": 5,
        "burst": 10,
    },
    "wish": {
        "rate": 5,
        "burst": 10,
    },
    "mercadolibre": {
        "rate": 5,
        "burst": 10,
    },
}

# 默认限流配置（未配置的平台使用此配置）
DEFAULT_RATE_LIMIT = {
    "rate": 5,
    "burst": 10,
}


# ============================================
# 重试配置
# ============================================
RETRY_CONFIG = {
    "max_retries": 3,  # 最大重试次数
    "base_delay": 1,  # 基础退避时间（秒）
    "max_delay": 60,  # 最大退避时间（秒）
    "jitter": True,  # 是否添加随机抖动
    # 可重试的错误类型
    "retryable_errors": [
        "timeout",
        "connection_error",
        "rate_limit",
        "server_error_5xx",
        "network_unreachable",
    ],
    # 不可重试的错误类型
    "non_retryable_errors": [
        "authentication_failed",
        "permission_denied",
        "invalid_request",
        "not_found",
    ],
}


# ============================================
# 缓存策略配置
# ============================================
CACHE_STRATEGIES = {
    "product_info": {
        "ttl": 3600,  # 1小时
        "strategy": "write_through",  # 写透缓存
        "invalidation": "version_based",  # 版本号失效
        "enable_local_cache": True,
    },
    "inventory": {
        "ttl": 300,  # 5分钟
        "strategy": "write_back",  # 写回缓存
        "invalidation": "event_based",  # 事件驱动失效
        "enable_local_cache": True,
    },
    "category_list": {
        "ttl": 86400,  # 24小时
        "strategy": "cache_aside",  # 旁路缓存
        "invalidation": "ttl_based",  # TTL过期
        "enable_local_cache": True,
    },
    "order_list": {
        "ttl": 180,  # 3分钟
        "strategy": "cache_aside",
        "invalidation": "ttl_based",
        "enable_local_cache": False,  # 订单数据不使用本地缓存
    },
    "shop_info": {
        "ttl": 7200,  # 2小时
        "strategy": "write_through",
        "invalidation": "version_based",
        "enable_local_cache": True,
    },
}

# 本地缓存配置
LOCAL_CACHE_CONFIG = {
    "max_size": 1000,  # 最大缓存项数
    "ttl": 300,  # 默认过期时间（秒）
    "eviction_policy": "lru",  # LRU淘汰策略
}


# ============================================
# 监控配置
# ============================================
MONITOR_CONFIG = {
    # 指标保留时间
    "metrics_retention_days": 30,
    # 性能指标分位数
    "percentiles": [50, 95, 99],  # P50, P95, P99
    # 告警阈值
    "alert_thresholds": {
        "error_rate": 0.1,  # 错误率 > 10% 触发告警
        "p95_latency": 5000,  # P95延迟 > 5秒 触发告警
        "success_rate": 0.9,  # 成功率 < 90% 触发告警
    },
    # 监控数据聚合粒度
    "aggregation_intervals": [
        "1m",  # 1分钟
        "5m",  # 5分钟
        "1h",  # 1小时
        "1d",  # 1天
    ],
}


# ============================================
# 告警配置
# ============================================
ALERT_RULES = {
    "high_error_rate": {
        "name": "高错误率告警",
        "condition": "error_rate > 0.1",  # 错误率 > 10%
        "severity": "critical",
        "cooldown": 300,  # 5分钟冷却期
        "enabled": True,
        "channels": ["dingtalk", "email"],  # 通知渠道
    },
    "slow_response": {
        "name": "响应缓慢告警",
        "condition": "p95_latency > 5000",  # P95延迟 > 5秒
        "severity": "warning",
        "cooldown": 600,  # 10分钟冷却期
        "enabled": True,
        "channels": ["dingtalk"],
    },
    "low_success_rate": {
        "name": "成功率低告警",
        "condition": "success_rate < 0.9",  # 成功率 < 90%
        "severity": "critical",
        "cooldown": 300,
        "enabled": True,
        "channels": ["dingtalk", "email"],
    },
    "api_quota_exceeded": {
        "name": "API配额超限告警",
        "condition": "quota_usage > 0.9",  # 配额使用 > 90%
        "severity": "warning",
        "cooldown": 1800,  # 30分钟冷却期
        "enabled": True,
        "channels": ["dingtalk"],
    },
}

# 钉钉告警配置
DINGTALK_CONFIG = {
    "webhook_url": None,  # 从环境变量读取
    "secret": None,  # 加签密钥（可选）
    "msg_type": "markdown",
}

# 邮件告警配置
EMAIL_ALERT_CONFIG = {
    "enabled": True,
    "recipients": [],  # 告警接收人列表
    "subject_prefix": "[ERP告警]",
}


# ============================================
# 分布式锁配置
# ============================================
DISTRIBUTED_LOCK_CONFIG = {
    "default_ttl": 30,  # 默认锁过期时间（秒）
    "auto_renewal": True,  # 自动续期
    "renewal_interval": 10,  # 续期间隔（秒）
    "max_lock_time": 300,  # 最大锁持有时长（秒）
}


# ============================================
# 数据冲突解决策略配置
# ============================================


class ResolutionStrategy(Enum):
    """冲突解决策略枚举"""

    LAST_WRITE_WINS = "last_write_wins"  # 最后写入胜出
    LOCAL_PRIORITY = "local_priority"  # 本地优先
    REMOTE_PRIORITY = "remote_priority"  # 远程优先
    MERGE = "merge"  # 合并
    MANUAL = "manual"  # 人工处理


CONFLICT_STRATEGIES = {
    "price": ResolutionStrategy.LAST_WRITE_WINS,
    "inventory": ResolutionStrategy.LOCAL_PRIORITY,
    "status": ResolutionStrategy.REMOTE_PRIORITY,
    "title": ResolutionStrategy.MERGE,
    "description": ResolutionStrategy.MERGE,
    "images": ResolutionStrategy.MERGE,
    "sku": ResolutionStrategy.REMOTE_PRIORITY,
    "category": ResolutionStrategy.REMOTE_PRIORITY,
}


# ============================================
# 批量操作配置
# ============================================
BATCH_OPERATION_CONFIG = {
    "batch_sizes": {
        "product_create": 50,  # 批量创建商品
        "product_update": 100,  # 批量更新商品
        "inventory_update": 200,  # 批量更新库存
        "order_sync": 100,  # 批量同步订单
    },
    "max_concurrent_batches": 5,  # 最大并发批次数
    "retry_failed_items": True,  # 重试失败项
    "max_retries_per_item": 3,  # 每项最大重试次数
}


# ============================================
# 日志配置
# ============================================
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "logs/django.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django_erp": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "core.services": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
