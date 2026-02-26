"""
Django settings for django_erp project.
"""

import os
import secrets
import sys
from pathlib import Path

try:
    from celery.schedules import crontab
except ImportError:
    crontab = None
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# 路径配置 - 添加 apps/ 到 Python 路径
# ============================================
# 将 apps/ 目录添加到 Python 路径，以便 Django 能找到所有应用
# 注意：所有 Django 应用已从根目录迁移至 apps/ 目录
APPS_DIR = BASE_DIR / "apps"
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

# 将 common/ 目录添加到 Python 路径
# common/ 包含共享的工具函数、mixins、装饰器等
COMMON_DIR = BASE_DIR / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

# 环境变量文件位置（已迁移至 config/environment/）
# python-decouple 会自动查找 .env 文件
# 备份位置：config/environment/.env

# ============================================
# Django Core Settings
# ============================================
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda x: [s.strip() for s in x.split(",")] if x else [],
)
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ============================================
# Installed Applications
# ============================================
INSTALLED_APPS = [
    # Django Default Apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",  # 友好的数据格式化（如日期、数字）
    # Third Party Apps
    "rest_framework",
    "django_filters",
    "corsheaders",
    "crispy_forms",
    "drf_spectacular",  # OpenAPI 3.x documentation
    # Project Apps
    "core",
    "users",
    "authentication",
    "customers",
    "products",
    "inventory",
    "sales",
    "purchase",
    "suppliers",
    "departments",
    "finance",
    "ai_assistant",
    "ecomm_sync",
    "collect",
    "logistics",
    "bi",
]

# ============================================
# Middleware Configuration
# ============================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Templates Configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.company_info",
            ],
        },
    },
]

# Static Files Configuration
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media Files Configuration
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# WSGI Configuration
WSGI_APPLICATION = "django_erp.wsgi.application"
ROOT_URLCONF = "django_erp.urls"

# ============================================
# Database Settings
# ============================================
DB_ENGINE = config("DB_ENGINE", default="django.db.backends.sqlite3")
DB_NAME = config("DB_NAME", default=BASE_DIR / "db.sqlite3")
DB_USER = config("DB_USER", default=None)
DB_PASSWORD = config("DB_PASSWORD", default=None)
DB_HOST = config("DB_HOST", default=None)
DB_PORT = config(
    "DB_PORT", default=None, cast=lambda v: int(v) if v and v.lower() != "none" else None
)

DATABASES = {
    "default": {
        "ENGINE": DB_ENGINE,
        "NAME": DB_NAME if isinstance(DB_NAME, str) else str(DB_NAME),
    }
}

if DB_ENGINE == "django.db.backends.postgresql":
    DATABASES["default"].update(
        {
            "USER": DB_USER,
            "PASSWORD": DB_PASSWORD,
            "HOST": DB_HOST,
            "PORT": DB_PORT,
            "CONN_MAX_AGE": 600,  # 10分钟连接重用（实现简单的连接池）
            "OPTIONS": {
                "connect_timeout": 10,
                "options": "-c statement_timeout=30000",  # 30秒查询超时
            },
        }
    )

# Redis Configuration
REDIS_HOST = config("REDIS_HOST", default=None)
REDIS_PORT = config("REDIS_PORT", default=6379, cast=int)
REDIS_PASSWORD = config("REDIS_PASSWORD", default=None)

# 确保 REDIS_HOST 不是字符串 'None'
if REDIS_HOST == "None":
    REDIS_HOST = None

# Caching Configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

if REDIS_HOST:
    CACHES["default"] = {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
        "KEY_PREFIX": "django_erp",
        "TIMEOUT": 300,  # 5分钟缓存超时
        "VERSION": 1,
    }

# Cache timeout settings
CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = 60  # 1分钟缓存超时（降低以支持实时刷新）
CACHE_MIDDLEWARE_KEY_PREFIX = ""
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

# ============================================
# Authentication settings
# ============================================
AUTH_USER_MODEL = "users.User"

# Custom Authentication Backend
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "authentication.backends.CustomBackend",
]

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "authentication.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "burst": "1000/day",
    },
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

# Security Settings
SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-this-in-production")

# JWT Settings
JWT_SECRET_KEY = config("JWT_SECRET_KEY", default=None)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DELTA = 86400  # 24 hours

# DeepSeek AI API Key
DEEPSEEK_API_KEY = config("DEEPSEEK_API_KEY", default=None)

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Logging
LOGGING = {
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
            "filename": BASE_DIR / "logs" / "django.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
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
    },
}

# ============================================
# Sentry错误监控（生产环境）
# ============================================
if not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    SENTRY_DSN = config("SENTRY_DSN", default=None)

    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(),
                CeleryIntegration(),
            ],
            traces_sample_rate=0.1,  # 10%的性能追踪采样率
            environment=config("ENVIRONMENT", default="production"),
            send_default_pii=False,  # 不发送个人身份信息
            before_send_transaction=lambda event: event,  # 可选：添加事务过滤器
        )

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)
SERVER_EMAIL = config("SERVER_EMAIL", default=EMAIL_HOST_USER)

# Frontend URL for password reset links
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000")

# Celery Configuration
# 根据环境变量自动配置 Celery
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default=None)

if CELERY_BROKER_URL:
    # 生产环境启用 Celery
    CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default=CELERY_BROKER_URL)
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TASK_SERIALIZER = "json"
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_TIMEZONE = TIME_ZONE
    CELERY_ENABLE_UTC = False
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 30 * 60  # 30分钟超时
    CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25分钟软超时
    CELERY_WORKER_PREFETCH_MULTIPLIER = 4
    CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Worker 重启阈值
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
    CELERY_RESULT_EXPIRES = 3600  # 结果保留1小时

# Celery Beat 定时任务配置
CELERY_BEAT_SCHEDULE = {
    # AI助手定时任务
    "cleanup-expired-conversations": {
        "task": "ai_assistant.tasks.cleanup_expired_conversations",
        "schedule": crontab(hour=2, minute=0),  # 每天凌晨 2 点
    },
    "cleanup-old-logs": {
        "task": "ai_assistant.tasks.cleanup_old_logs",
        "schedule": crontab(hour=3, minute=0),  # 每天凌晨 3 点
    },
    # 电商同步定时任务
    "sync-ecommerce-incremental": {
        "task": "ecomm_sync.tasks.sync_platform_products_task",
        "schedule": crontab(hour=2, minute=0),
        "options": {"expires": 3600},
    },
    "sync-ecommerce-full": {
        "task": "ecomm_sync.tasks.sync_platform_products_task",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),
        "options": {"expires": 7200},
    },
    "monitor-price-changes": {
        "task": "ecomm_sync.tasks.sync_price_changes_task",
        "schedule": crontab(minute=0),
        "options": {"expires": 300},
    },
    # 物流同步定时任务
    "track-shipping-batch": {
        "task": "ecomm_sync.tasks.batch_track_shipping_task",
        "schedule": crontab(minute="*/5"),  # 每5分钟
        "options": {"expires": 300},
    },
    # 采购同步定时任务
    "sync-purchase-order-to-platform": {
        "task": "ecomm_sync.tasks.link_purchase_order_to_platform_task",
        "schedule": crontab(minute=30),  # 每30分钟
        "options": {"expires": 1800},
    },
    "sync-purchase-order-to-platform-status": {
        "task": "ecomm_sync.tasks.sync_purchase_order_to_platform_task",
        "schedule": crontab(hour=1, minute=0),  # 每天凌晨1点
        "options": {"expires": 3600},
    },
    "sync-purchase-items-to-platform": {
        "task": "ecomm_sync.tasks.sync_purchase_items_to_platform_task",
        "schedule": crontab(minute="*/10"),  # 每10分钟
        "options": {"expires": 600},
    },
    "sync-purchase-status-to-platform": {
        "task": "ecomm_sync.tasks.sync_purchase_status_to_platform_task",
        "schedule": crontab(minute="*/15"),  # 每15分钟
        "options": {"expires": 900},
    },
    "process-purchase-sync-queue": {
        "task": "ecomm_sync.tasks.process_purchase_sync_queue_task",
        "schedule": crontab(minute="*/2"),  # 每2分钟
        "options": {"expires": 120},
    },
    # 自动补货提醒
    "auto-restock-alert": {
        "task": "ecomm_sync.tasks.auto_restock_alert_task",
        "schedule": crontab(hour=8, minute=0),  # 每天早上8点
        "options": {"expires": 3600},
    },
    # Jumia平台同步
    "sync-jumia-products": {
        "task": "ecomm_sync.tasks.sync_jumia_products_task",
        "schedule": crontab(minute=0),  # 每小时
        "options": {"expires": 3600},
    },
    "sync-jumia-orders": {
        "task": "ecomm_sync.tasks.sync_jumia_orders_task",
        "schedule": crontab(minute="*/30"),  # 每30分钟
        "options": {"expires": 1800},
    },
    # Cdiscount平台同步
    "sync-cdiscount-products": {
        "task": "ecomm_sync.tasks.sync_cdiscount_products_task",
        "schedule": crontab(minute=0),  # 每小时
        "options": {"expires": 3600},
    },
    "sync-cdiscount-orders": {
        "task": "ecomm_sync.tasks.sync_cdiscount_orders_task",
        "schedule": crontab(minute="*/30"),  # 每30分钟
        "options": {"expires": 1800},
    },
    # Shopee平台同步
    "sync-shopee-products": {
        "task": "ecomm_sync.tasks.sync_shopee_products_task",
        "schedule": crontab(minute=0),  # 每小时
        "options": {"expires": 3600},
    },
    "sync-shopee-orders": {
        "task": "ecomm_sync.tasks.sync_shopee_orders_task",
        "schedule": crontab(minute="*/30"),  # 每30分钟
        "options": {"expires": 1800},
    },
    # TikTok Shop平台同步
    "sync-tiktok-products": {
        "task": "ecomm_sync.tasks.sync_tiktok_products_task",
        "schedule": crontab(minute=0),  # 每小时
        "options": {"expires": 3600},
    },
    "sync-tiktok-orders": {
        "task": "ecomm_sync.tasks.sync_tiktok_orders_task",
        "schedule": crontab(minute="*/30"),  # 每30分钟
        "options": {"expires": 1800},
    },
    # Temu平台同步
    "sync-temu-products": {
        "task": "ecomm_sync.tasks.sync_temu_products_task",
        "schedule": crontab(minute=0),  # 每小时
        "options": {"expires": 3600},
    },
    "sync-temu-orders": {
        "task": "ecomm_sync.tasks.sync_temu_orders_task",
        "schedule": crontab(minute="*/30"),  # 每30分钟
        "options": {"expires": 1800},
    },
    # Wish平台同步
    "sync-wish-products": {
        "task": "ecomm_sync.tasks.sync_wish_products_task",
        "schedule": crontab(minute=0),  # 每小时
        "options": {"expires": 3600},
    },
    "sync-wish-orders": {
        "task": "ecomm_sync.tasks.sync_wish_orders_task",
        "schedule": crontab(minute="*/30"),  # 每30分钟
        "options": {"expires": 1800},
    },
    # MercadoLibre平台同步
    "sync-mercadolibre-products": {
        "task": "ecomm_sync.tasks.sync_mercadolibre_products_task",
        "schedule": crontab(minute=0),  # 每小时
        "options": {"expires": 3600},
    },
    "sync-mercadolibre-orders": {
        "task": "ecomm_sync.tasks.sync_mercadolibre_orders_task",
        "schedule": crontab(minute="*/30"),  # 每30分钟
        "options": {"expires": 1800},
    },
}

# AI Assistant Configuration
# AI助手异步处理配置
AI_ASSISTANT_USE_ASYNC = config("AI_ASSISTANT_USE_ASYNC", default=False, cast=bool)

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB

# ============================================
# 安全配置 - HTTPS 和安全头部
# ============================================

# 基础安全头部（开发和生产环境都启用）
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"  # 禁止在 iframe 中嵌入
SESSION_COOKIE_HTTPONLY = True  # 防止 JavaScript 访问 session cookie
CSRF_COOKIE_HTTPONLY = True  # 防止 JavaScript 访问 CSRF cookie

# 生产环境 HTTPS 强化配置
if not DEBUG:
    # 强制 HTTPS 重定向
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1年
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Cookie 安全
    SESSION_COOKIE_SECURE = True  # 仅通过 HTTPS 传输 session cookie
    CSRF_COOKIE_SECURE = True  # 仅通过 HTTPS 传输 CSRF cookie
    SESSION_COOKIE_SAMESITE = "Strict"  # 防止 CSRF 攻击
    CSRF_COOKIE_SAMESITE = "Strict"

    # Session 安全
    SESSION_COOKIE_AGE = 86400  # 24小时后过期
    SESSION_SAVE_EVERY_REQUEST = True  # 每次请求刷新 session
    SESSION_EXPIRE_AT_BROWSER_CLOSE = False

    # 其他安全设置
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

    # 日志级别调整
    LOGGING["root"]["level"] = "WARNING"
    LOGGING["loggers"]["django"]["level"] = "WARNING"
    LOGGING["loggers"]["django_erp"]["level"] = "INFO"

# ============================================
# 会话配置
# ============================================
SESSION_ENGINE = "django.contrib.sessions.backends.db"  # 使用数据库存储 session

# 如果启用 Redis,可以使用 Redis 存储 session (性能更好)
# 开发环境不使用 Redis，避免依赖
# if REDIS_HOST:
#     SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
#     SESSION_CACHE_ALIAS = 'default'

# Authentication URLs
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

# ============================================
# AI助手配置
# API Key加密密钥（请在.env中设置，生产环境必须配置）
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", None)

# ============================================
# OpenAPI/Swagger Documentation Settings
# ============================================
SPECTACULAR_SETTINGS = {
    "TITLE": "BetterLaser ERP API",
    "DESCRIPTION": "ERP系统API文档",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/",
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        {"name": "Authentication", "description": "用户认证相关接口"},
        {"name": "Core", "description": "核心功能接口"},
        {"name": "Users", "description": "用户管理接口"},
        {"name": "Customers", "description": "客户管理接口"},
        {"name": "Suppliers", "description": "供应商管理接口"},
        {"name": "Products", "description": "产品管理接口"},
        {"name": "Inventory", "description": "库存管理接口"},
        {"name": "Sales", "description": "销售管理接口"},
        {"name": "Purchase", "description": "采购管理接口"},
        {"name": "Finance", "description": "财务管理接口"},
        {"name": "Departments", "description": "部门管理接口"},
        {"name": "AI Assistant", "description": "AI助手接口"},
    ],
    "SERVERS": [
        {"url": "http://localhost:8000", "description": "开发环境"},
        {"url": "https://erp.example.com", "description": "生产环境"},
    ],
    "SCHEMA_COERCE_PATH_PK": True,
    "SCHEMA_COERCE_METHOD_NAMES": {
        "retrieve": "read",
        "destroy": "delete",
    },
    "POSTPROCESSING_HOOKS": [],
}

# ============================================
# Rate Limiting Settings
# ============================================
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = "default"
RATELIMIT_VIEW = "rest_framework.throttling.Throttled"

# Rate limit configuration for different types of requests
RATELIMIT_RATE = "1000/h"  # Default rate limit
