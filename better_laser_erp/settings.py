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
# Authentication settings
# ============================================
AUTH_USER_MODEL = 'users.User'

# Custom Authentication Backend
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'authentication.backends.CustomBackend',
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

# JWT Settings
JWT_SECRET_KEY = config('JWT_SECRET_KEY', default=SECRET_KEY)
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = 86400  # 24 hours

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

# 如果启用了 Redis,可以使用 Redis 存储 session (性能更好)
if REDIS_HOST:
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'

# Authentication URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# ============================================
# AI助手配置
# ============================================
# API Key加密密钥（请在.env中设置，生产环境必须配置）
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', None)

