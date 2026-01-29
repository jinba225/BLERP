"""
Django settings for better_laser_erp project.
"""

import os
import secrets
from pathlib import Path
from decouple import config
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# Django Core Settings
# ============================================
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=lambda x: [s.strip() for s in x.split(',')] if x else [])
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# Installed Applications
# ============================================
INSTALLED_APPS = [
    # Django Default Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # 友好的数据格式化（如日期、数字）
    
    # Admin 美化
    'jazzmin',  # Django Admin 现代化主题（必须在 admin 之前）
    
    # Third Party Apps
    'rest_framework',
    'django_filters',
    'corsheaders',
    'crispy_forms',
    
    # Project Apps
    'apps.core',
    'apps.users',
    'apps.authentication',
    'apps.customers',
    'apps.products',
    'apps.inventory',
    'apps.sales',
    'apps.purchase',
    'apps.suppliers',
    'apps.departments',
    'apps.finance',
    'apps.ai_assistant',
    'apps.ecomm_sync',
]

# ============================================
# Middleware Configuration
# ============================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Templates Configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.jazzmin_config',
            ],
        },
    },
]

# Static Files Configuration
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media Files Configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# WSGI Configuration
WSGI_APPLICATION = 'better_laser_erp.wsgi.application'
ROOT_URLCONF = 'better_laser_erp.urls'

# ============================================
# Database Settings
# ============================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Redis Configuration
REDIS_HOST = config('REDIS_HOST', default=None)
REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)
REDIS_PASSWORD = config('REDIS_PASSWORD', default=None)

# Caching Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

if REDIS_HOST:
    CACHES['default'] = {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}',
    }

# ============================================
# Authentication settings
# ============================================
AUTH_USER_MODEL = 'users.User'

# Custom Authentication Backend
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'apps.authentication.backends.CustomBackend',
]

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'apps.authentication.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

# Security Settings
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# JWT Settings
JWT_SECRET_KEY = config('JWT_SECRET_KEY', default=SECRET_KEY)
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = 86400  # 24 hours

# DeepSeek AI API Key
DEEPSEEK_API_KEY = 'sk-ffee6eadd5aa4548aad1a4b51ce2e5fc'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'better_laser_erp': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)
SERVER_EMAIL = config('SERVER_EMAIL', default=EMAIL_HOST_USER)

# Frontend URL for password reset links
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

# Celery Configuration
# 根据环境变量自动配置 Celery
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default=None)

if CELERY_BROKER_URL:
    # 生产环境启用 Celery
    CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default=CELERY_BROKER_URL)
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
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
    'cleanup-expired-conversations': {
        'task': 'apps.ai_assistant.tasks.cleanup_expired_conversations',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨 2 点
    },
    'cleanup-old-logs': {
        'task': 'apps.ai_assistant.tasks.cleanup_old_logs',
        'schedule': crontab(hour=3, minute=0),  # 每天凌晨 3 点
    },
}

# AI Assistant Configuration
# AI助手异步处理配置
AI_ASSISTANT_USE_ASYNC = config('AI_ASSISTANT_USE_ASYNC', default=False, cast=bool)

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB

# ============================================
# 安全配置 - HTTPS 和安全头部
# ============================================

# 基础安全头部（开发和生产环境都启用）
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'  # 允许在相同域名下使用 iframe
SESSION_COOKIE_HTTPONLY = True  # 防止 JavaScript 访问 session cookie
CSRF_COOKIE_HTTPONLY = True  # 防止 JavaScript 访问 CSRF cookie

# 生产环境 HTTPS 强化配置
if not DEBUG:
    # 强制 HTTPS 重定向
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1年
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Cookie 安全
    SESSION_COOKIE_SECURE = True  # 仅通过 HTTPS 传输 session cookie
    CSRF_COOKIE_SECURE = True  # 仅通过 HTTPS 传输 CSRF cookie
    SESSION_COOKIE_SAMESITE = 'Strict'  # 防止 CSRF 攻击
    CSRF_COOKIE_SAMESITE = 'Strict'

    # Session 安全
    SESSION_COOKIE_AGE = 86400  # 24小时后过期
    SESSION_SAVE_EVERY_REQUEST = True  # 每次请求刷新 session
    SESSION_EXPIRE_AT_BROWSER_CLOSE = False

    # 其他安全设置
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

    # 日志级别调整
    LOGGING['root']['level'] = 'WARNING'
    LOGGING['loggers']['django']['level'] = 'WARNING'
    LOGGING['loggers']['better_laser_erp']['level'] = 'INFO'

# ============================================
# 会话配置
# ============================================
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # 使用数据库存储 session

# 如果启用 Redis,可以使用 Redis 存储 session (性能更好)
# 开发环境不使用 Redis，避免依赖
# if REDIS_HOST:
#     SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
#     SESSION_CACHE_ALIAS = 'default'

# Authentication URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# ============================================
# AI助手配置
# ============================================
# API Key加密密钥（请在.env中设置，生产环境必须配置）
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', None)

# ============================================
# Django Jazzmin 美化配置
# ============================================

def get_jazzmin_settings():
    """
    获取 Jazzmin 配置（支持动态主题）
    """
    from apps.core.models import SystemConfig
    from apps.core.utils.theme_config import THEME_COLORS, DEFAULT_THEME
    
    # 获取当前主题
    try:
        theme_config = SystemConfig.objects.filter(
            key='ui.theme',
            is_active=True
        ).first()
        
        if theme_config:
            current_theme = theme_config.value
        else:
            current_theme = DEFAULT_THEME
    except:
        current_theme = DEFAULT_THEME
    
    # 获取 Logo
    try:
        logo_config = SystemConfig.objects.filter(
            key='ui.logo',
            is_active=True
        ).first()
        
        logo_url = logo_config.value if logo_config else ''
    except:
        logo_url = ''
    
    # 获取颜色配置
    colors = THEME_COLORS.get(current_theme, THEME_COLORS[DEFAULT_THEME])
    
    # 构建配置
    config = {
        # 基础配置
        "site_title": "BetterLaser ERP",
        "site_header": "BetterLaser ERP 管理后台",
        "site_icon": logo_url,
        "login_logo": logo_url,
        "welcome_sign": "欢迎来到 BetterLaser ERP",
        
        # 布局设置
        "language_chooser_display": "show",
        "show_ui_builder": False,
        "navigation_expanded": True,
        "show_sidebar": True,
        
        # 主题颜色（动态）
        "theme": {
            "primary": colors['primary'],
            "success": colors['success'],
            "warning": colors['warning'],
            "danger": colors['danger'],
            "info": colors['info'],
            "sidebar_bg": colors['sidebar_bg'],
            "sidebar_header_bg": colors['sidebar_bg'],
            "sidebar_link_active_bg": colors['sidebar_link_active_bg'],
            "sidebar_link_active_color": colors['sidebar_link_active_color'],
            "sidebar_link_color": colors['sidebar_link_color'],
            "header_bg": colors['header_bg'],
            "header_text": colors['header_text'],
        },
        
        # 用户菜单
        "usermenu": [
            {
                "title": "返回系统",
                "url": "/",
                "icon": "fas fa-home",
                "order": 100,
            },
            {
                "title": "系统设置",
                "url": "/admin/core/systemconfig/",
                "icon": "fas fa-cogs",
                "order": 110,
            },
            {
                "title": "切换主题",
                "url": "/admin/core/systemconfig/?action=switch_theme",
                "icon": "fas fa-palette",
                "order": 115,
            },
            {
                "title": "退出登录",
                "url": "/logout/",
                "icon": "fas fa-sign-out-alt",
                "order": 999,
            },
        ],
        
        # 自定义链接
        "custom_links": {
            "links": [
                {
                    "name": "官方网站",
                    "url": "https://betterlaser.com",
                    "icon": "fas fa-globe",
                    "model": "SystemConfig",
                    "new_window": True,
                    "order": 100,
                }
            ]
        },
        
        # 隐藏不需要的模型
        "hide_models": {
            "auth": ["Group"],  # 隐藏 Group 模型
            "core": ["AuditLog"],  # 可选：隐藏审计日志
        },
        
        # 其他设置
        "show_relative_dates": False,
        "date_format": "Y-m-d H:i:s",
        "datetime_format": "Y-m-d H:i:s",
        "time_format": "H:i:s",
        
        # 侧边栏菜单（按应用分组）
        "custom_menu": {
            "menu": [
                {
                    "app": "core",
                    "label": "系统管理",
                    "icon": "fas fa-cogs",
                    "models": [
                        {"model": "Company"},
                        {"model": "SystemConfig"},
                        {"model": "PrintTemplate"},
                        {"model": "Notification"},
                        {"model": "Attachment"},
                    ]
                },
                {
                    "app": "users",
                    "label": "用户管理",
                    "icon": "fas fa-users",
                    "models": [
                        {"model": "User"},
                        {"model": "Role"},
                        {"model": "Permission"},
                    ]
                },
                {
                    "app": "customers",
                    "label": "客户管理",
                    "icon": "fas fa-user-friends",
                    "models": [
                        {"model": "Customer"},
                        {"model": "Contact"},
                    ]
                },
                {
                    "app": "products",
                    "label": "产品管理",
                    "icon": "fas fa-box",
                    "models": [
                        {"model": "Product"},
                        {"model": "ProductCategory"},
                    ]
                },
                {
                    "app": "inventory",
                    "label": "库存管理",
                    "icon": "fas fa-warehouse",
                    "models": [
                        {"model": "Warehouse"},
                        {"model": "Stock"},
                        {"model": "InboundOrder"},
                        {"model": "OutboundOrder"},
                        {"model": "StockAdjustment"},
                        {"model": "StockTransfer"},
                        {"model": "StockCount"},
                    ]
                },
                {
                    "app": "sales",
                    "label": "销售管理",
                    "icon": "fas fa-shopping-cart",
                    "models": [
                        {"model": "Quote"},
                        {"model": "SalesOrder"},
                        {"model": "Delivery"},
                        {"model": "SalesReturn"},
                        {"model": "SalesLoan"},
                    ]
                },
                {
                    "app": "purchase",
                    "label": "采购管理",
                    "icon": "fas fa-truck",
                    "models": [
                        {"model": "PurchaseRequest"},
                        {"model": "PurchaseOrder"},
                        {"model": "Supplier"},
                        {"model": "PurchaseReceipt"},
                        {"model": "PurchaseReturn"},
                        {"model": "PurchaseBorrow"},
                        {"model": "PurchaseInquiry"},
                        {"model": "SupplierQuotation"},
                    ]
                },
                {
                    "app": "suppliers",
                    "label": "供应商管理",
                    "icon": "fas fa-building",
                    "models": [
                        {"model": "Supplier"},
                        {"model": "SupplierContact"},
                    ]
                },
                {
                    "app": "finance",
                    "label": "财务管理",
                    "icon": "fas fa-dollar-sign",
                    "models": [
                        {"model": "Account"},
                        {"model": "Payment"},
                        {"model": "Receivable"},
                        {"model": "Invoice"},
                        {"model": "PaymentOrder"},
                    ]
                },
                {
                    "app": "departments",
                    "label": "部门管理",
                    "icon": "fas fa-sitemap",
                    "models": [
                        {"model": "Department"},
                        {"model": "Employee"},
                    ]
                },
                {
                    "app": "ai_assistant",
                    "label": "AI 助手",
                    "icon": "fas fa-robot",
                    "models": [
                        {"model": "AIConversation"},
                        {"model": "AIModelConfig"},
                        {"model": "AITool"},
                    ]
                },
                {
                    "app": "ecomm_sync",
                    "label": "电商同步",
                    "icon": "fas fa-sync",
                    "models": [
                        {"model": "EcommPlatform"},
                        {"model": "EcommProduct"},
                        {"model": "SyncLog"},
                        {"model": "SyncStrategy"},
                        {"model": "WooShopConfig"},
                    ]
                },
            ]
        },
    }
    
    return config


# 延迟加载 JAZZMIN_SETTINGS（在 Apps 加载后才能访问数据库）
JAZZMIN_SETTINGS = None

# Django Jazzmin 美化配置
# ============================================

# Jazzmin 配置（简化版本，不依赖数据库）
JAZZMIN_SETTINGS = {
    # 基础配置
    "site_title": "BetterLaser ERP",
    "site_header": "BetterLaser ERP 管理后台",
    "site_icon": "",
    "login_logo": "",
    "welcome_sign": "欢迎来到 BetterLaser ERP",
    
    # 布局设置
    "language_chooser_display": "show",
    "show_ui_builder": False,
    "navigation_expanded": True,
    "show_sidebar": True,
    
    # 默认主题（不依赖数据库）
    "theme": {
        "primary": "#3b82f6",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "info": "#3b82f6",
        "sidebar_bg": "#1e293b",
        "sidebar_header_bg": "#0f172a",
        "sidebar_link_active_bg": "#3b82f6",
        "sidebar_link_active_color": "#ffffff",
        "sidebar_link_color": "#94a3b8",
        "header_bg": "#ffffff",
        "header_text": "#1e293b",
    },
    
    # 用户菜单
    "usermenu": [
        {
            "title": "返回系统",
            "url": "/",
            "icon": "fas fa-home",
            "order": 100,
        },
        {
            "title": "系统设置",
            "url": "/admin/core/systemconfig/",
            "icon": "fas fa-cogs",
            "order": 110,
        },
        {
            "title": "切换主题",
            "url": "/admin/core/systemconfig/?action=switch_theme",
            "icon": "fas fa-palette",
            "order": 115,
        },
        {
            "title": "退出登录",
            "url": "/logout/",
            "icon": "fas fa-sign-out-alt",
            "order": 999,
        },
    ],
    
    # 自定义链接
    "custom_links": {
        "links": [
            {
                "name": "官方网站",
                "url": "https://betterlaser.com",
                "icon": "fas fa-globe",
                "model": "SystemConfig",
                "new_window": True,
                "order": 100,
            }
        ]
    },
    
    # 隐藏不需要的模型
    "hide_models": {
        "auth": ["Group"],
        "core": ["AuditLog"],
    },
    
    # 其他设置
    "show_relative_dates": False,
    "date_format": "Y-m-d H:i:s",
    "datetime_format": "Y-m-d H:i:s",
    "time_format": "H:i:s",
    
    # 侧边栏菜单（按应用分组）
    "custom_menu": {
        "menu": [
            {
                "app": "core",
                "label": "系统管理",
                "icon": "fas fa-cogs",
                "models": [
                    {"model": "Company"},
                    {"model": "SystemConfig"},
                    {"model": "PrintTemplate"},
                    {"model": "Notification"},
                    {"model": "Attachment"},
                ]
            },
            {
                    "app": "users",
                    "label": "用户管理",
                    "icon": "fas fa-users",
                    "models": [
                        {"model": "User"},
                        {"model": "Role"},
                        {"model": "Permission"},
                    ]
                },
            {
                    "app": "customers",
                    "label": "客户管理",
                    "icon": "fas fa-user-friends",
                    "models": [
                        {"model": "Customer"},
                        {"model": "Contact"},
                    ]
                },
            {
                    "app": "products",
                    "label": "产品管理",
                    "icon": "fas fa-box",
                    "models": [
                        {"model": "Product"},
                        {"model": "ProductCategory"},
                    ]
                },
            {
                    "app": "inventory",
                    "label": "库存管理",
                    "icon": "fas fa-warehouse",
                    "models": [
                        {"model": "Warehouse"},
                        {"model": "Stock"},
                        {"model": "InboundOrder"},
                        {"model": "OutboundOrder"},
                        {"model": "StockAdjustment"},
                        {"model": "StockTransfer"},
                        {"model": "StockCount"},
                    ]
                },
            {
                    "app": "sales",
                    "label": "销售管理",
                    "icon": "fas fa-shopping-cart",
                    "models": [
                        {"model": "Quote"},
                        {"model": "SalesOrder"},
                        {"model": "Delivery"},
                        {"model": "SalesReturn"},
                        {"model": "SalesLoan"},
                    ]
                },
            {
                    "app": "purchase",
                    "label": "采购管理",
                    "icon": "fas fa-truck",
                    "models": [
                        {"model": "PurchaseRequest"},
                        {"model": "PurchaseOrder"},
                        {"model": "Supplier"},
                        {"model": "PurchaseReceipt"},
                        {"model": "PurchaseReturn"},
                        {"model": "PurchaseBorrow"},
                        {"model": "PurchaseInquiry"},
                        {"model": "SupplierQuotation"},
                    ]
                },
            {
                    "app": "suppliers",
                    "label": "供应商管理",
                    "icon": "fas fa-building",
                    "models": [
                        {"model": "Supplier"},
                        {"model": "SupplierContact"},
                    ]
                },
            {
                    "app": "finance",
                    "label": "财务管理",
                    "icon": "fas fa-dollar-sign",
                    "models": [
                        {"model": "Account"},
                        {"model": "Payment"},
                        {"model": "Receivable"},
                        {"model": "Invoice"},
                        {"model": "PaymentOrder"},
                    ]
                },
            {
                    "app": "departments",
                    "label": "部门管理",
                    "icon": "fas fa-sitemap",
                    "models": [
                        {"model": "Department"},
                        {"model": "Employee"},
                    ]
                },
            {
                    "app": "ai_assistant",
                    "label": "AI 助手",
                    "icon": "fas fa-robot",
                    "models": [
                        {"model": "AIConversation"},
                        {"model": "AIModelConfig"},
                        {"model": "AITool"},
                    ]
                },
                {
                    "app": "ecomm_sync",
                    "label": "电商同步",
                    "icon": "fas fa-sync",
                    "models": [
                        {"model": "EcommPlatform"},
                        {"model": "EcommProduct"},
                        {"model": "SyncLog"},
                        {"model": "SyncStrategy"},
                        {"model": "WooShopConfig"},
                    ]
                },
            ]
        },
    }

# 构建配置（使用默认值，不访问数据库）
# 主题配置将在 apps/core/apps.py 的 ready() 方法中动态更新
from apps.core.utils.theme_config import THEME_COLORS, DEFAULT_THEME

# 使用默认主题
current_theme = DEFAULT_THEME
logo_url = ''
colors = THEME_COLORS[current_theme]

JAZZMIN_SETTINGS = {
        "site_title": "BetterLaser ERP",
        "site_header": "BetterLaser ERP 管理后台",
        "site_icon": logo_url,
        "login_logo": logo_url,
        "welcome_sign": "欢迎来到 BetterLaser ERP",
        
        "language_chooser_display": "show",
        "show_ui_builder": False,
        "navigation_expanded": True,
        "show_sidebar": True,
        
        "theme": {
            "primary": colors['primary'],
            "success": colors['success'],
            "warning": colors['warning'],
            "danger": colors['danger'],
            "info": colors['info'],
            "sidebar_bg": colors['sidebar_bg'],
            "sidebar_header_bg": colors['sidebar_bg'],
            "sidebar_link_active_bg": colors['sidebar_link_active_bg'],
            "sidebar_link_active_color": colors['sidebar_link_active_color'],
            "sidebar_link_color": colors['sidebar_link_color'],
            "header_bg": colors['header_bg'],
            "header_text": colors['header_text'],
        },
        
        "usermenu": [
            {
                "title": "返回系统",
                "url": "/",
                "icon": "fas fa-home",
                "order": 100,
            },
            {
                "title": "系统设置",
                "url": "/admin/core/systemconfig/",
                "icon": "fas fa-cogs",
                "order": 110,
            },
            {
                "title": "切换主题",
                "url": "/admin/core/systemconfig/?action=switch_theme",
                "icon": "fas fa-palette",
                "order": 115,
            },
            {
                "title": "退出登录",
                "url": "/logout/",
                "icon": "fas fa-sign-out-alt",
                "order": 999,
            },
        ],
        
        "custom_links": {
            "links": [
                {
                    "name": "官方网站",
                    "url": "https://betterlaser.com",
                    "icon": "fas fa-globe",
                    "model": "SystemConfig",
                    "new_window": True,
                    "order": 100,
                }
            ]
        },
        
        "hide_models": {
            "auth": ["Group"],
            "core": ["AuditLog"],
        },
        
        "show_relative_dates": False,
        "date_format": "Y-m-d H:i:s",
        "datetime_format": "Y-m-d H:i:s",
        "time_format": "H:i:s",
        
        "custom_menu": {
            "menu": [
                {
                    "app": "core",
                    "label": "系统管理",
                    "icon": "fas fa-cogs",
                    "models": [
                        {"model": "Company"},
                        {"model": "SystemConfig"},
                        {"model": "PrintTemplate"},
                        {"model": "Notification"},
                        {"model": "Attachment"},
                    ]
                },
                {
                    "app": "users",
                    "label": "用户管理",
                    "icon": "fas fa-users",
                    "models": [
                        {"model": "User"},
                        {"model": "Role"},
                        {"model": "Permission"},
                    ]
                },
                {
                    "app": "customers",
                    "label": "客户管理",
                    "icon": "fas fa-user-friends",
                    "models": [
                        {"model": "Customer"},
                        {"model": "Contact"},
                    ]
                },
                {
                    "app": "products",
                    "label": "产品管理",
                    "icon": "fas fa-box",
                    "models": [
                        {"model": "Product"},
                        {"model": "ProductCategory"},
                    ]
                },
                {
                    "app": "inventory",
                    "label": "库存管理",
                    "icon": "fas fa-warehouse",
                    "models": [
                        {"model": "Warehouse"},
                        {"model": "Stock"},
                        {"model": "InboundOrder"},
                        {"model": "OutboundOrder"},
                        {"model": "StockAdjustment"},
                        {"model": "StockTransfer"},
                        {"model": "StockCount"},
                    ]
                },
                {
                    "app": "sales",
                    "label": "销售管理",
                    "icon": "fas fa-shopping-cart",
                    "models": [
                        {"model": "Quote"},
                        {"model": "SalesOrder"},
                        {"model": "Delivery"},
                        {"model": "SalesReturn"},
                        {"model": "SalesLoan"},
                    ]
                },
                {
                    "app": "purchase",
                    "label": "采购管理",
                    "icon": "fas fa-truck",
                    "models": [
                        {"model": "PurchaseRequest"},
                        {"model": "PurchaseOrder"},
                        {"model": " Supplier"},
                        {"model": "PurchaseReceipt"},
                        {"model": "PurchaseReturn"},
                        {"model": "PurchaseBorrow"},
                        {"model": "PurchaseInquiry"},
                        {"model": "SupplierQuotation"},
                    ]
                },
                {
                    "app": "suppliers",
                    "label": "供应商管理",
                    "icon": "fas fa-building",
                    "models": [
                        {"model": "Supplier"},
                        {"model": "SupplierContact"},
                    ]
                },
                {
                    "app": "finance",
                    "label": "财务管理",
                    "icon": "fas fa-dollar-sign",
                    "models": [
                        {"model": "Account"},
                        {"model": "Payment"},
                        {"model": "Receivable"},
                        {"model": "Invoice"},
                        {"model": "PaymentOrder"},
                    ]
                },
                {
                    "app": "departments",
                    "label": "部门管理",
                    "icon": "fas fa-sitemap",
                    "models": [
                        {"model": "Department"},
                        {"model": "Employee"},
                    ]
                },
                {
                    "app": "ai_assistant",
                    "label": "AI 助手",
                    "icon": "fas fa-robot",
                    "models": [
                        {"model": "AIConversation"},
                        {"model": "AIModelConfig"},
                        {"model": "AITool"},
                    ]
                },
                {
                    "app": "ecomm_sync",
                    "label": "电商同步",
                    "icon": "fas fa-sync",
                    "models": [
                        {"model": "EcommPlatform"},
                        {"model": "EcommProduct"},
                        {"model": "SyncLog"},
                        {"model": "SyncStrategy"},
                        {"model": "WooShopConfig"},
                    ]
                },
            ]
        },
    }


