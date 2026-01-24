"""
Django settings for better_laser_erp project.
"""

import os
import secrets
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# 安全配置 - SECRET_KEY
# ============================================
# 生产环境必须提供 SECRET_KEY 环境变量
_secret_key = config('SECRET_KEY', default=None)

if _secret_key:
    # 使用环境变量中的 SECRET_KEY
    SECRET_KEY = _secret_key
else:
    # 开发环境自动生成随机 SECRET_KEY
    SECRET_KEY = secrets.token_urlsafe(50)
    if not config('DEBUG', default=True, cast=bool):
        # 生产环境必须配置 SECRET_KEY！
        raise ValueError(
            "⚠️  生产环境必须在 .env 文件中配置 SECRET_KEY！\n"
            "请运行以下命令生成随机密钥：\n"
            "  python -c 'import secrets; print(secrets.token_urlsafe(50))'"
        )

# ============================================
# 调试模式配置
# ============================================
DEBUG = config('DEBUG', default=True, cast=bool)

# 生产环境安全检查
if not DEBUG:
    # 确保生产环境配置了 ALLOWED_HOSTS
    _allowed_hosts = config('ALLOWED_HOSTS', default='')
    if not _allowed_hosts or _allowed_hosts == 'localhost,127.0.0.1':
        raise ValueError(
            "⚠️  生产环境必须配置正确的 ALLOWED_HOSTS！\n"
            "请在 .env 文件中设置您的域名，例如：\n"
            "  ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com"
        )

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'django_filters',
    'crispy_forms',
    'crispy_tailwind',
    'mptt',
    'import_export',  # 导入导出功能
    # 'taggit',  # 标签功能，暂时不需要
]

LOCAL_APPS = [
    # 📦 1. 基础数据
    'apps.products',
    'apps.customers',
    'apps.suppliers',

    # 📊 2. 业务运营
    'apps.sales',
    'apps.purchase',
    'apps.inventory',

    # 💰 3. 财务管理
    'apps.finance',

    # 👥 4. 组织架构
    'apps.departments',

    # ⚙️ 5. 系统设置
    'apps.users',
    'apps.core',
    'apps.authentication',

    # 🤖 6. AI助手
    'apps.ai_assistant',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.TimezoneMiddleware',
]

ROOT_URLCONF = 'better_laser_erp.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'better_laser_erp.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# 根据环境变量自动选择数据库引擎
DB_ENGINE = config('DB_ENGINE', default='django.db.backends.sqlite3')

if DB_ENGINE == 'django.db.backends.sqlite3':
    # 开发环境使用 SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # 生产环境使用 MySQL
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': config('DB_NAME', default='django_erp'),
            'USER': config('DB_USER', default='django_user'),
            'PASSWORD': config('DB_PASSWORD', default='django_password'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES', "
                                "SET time_zone='+08:00', "
                                "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci",
                # 连接池配置
                'connect_timeout': 10,
                'read_timeout': 30,
                'write_timeout': 30,
                # SSL 配置 (可选，生产环境推荐)
                # 'ssl': {
                #     'ca': '/path/to/ca-cert.pem',
                #     'cert': '/path/to/client-cert.pem',
                #     'key': '/path/to/client-key.pem',
                # },
            },
            'CONN_MAX_AGE': 600,  # 连接池：连接存活时间 (秒)
            'ATOMIC_REQUESTS': True,  # 自动事务包装
        }
    }

# Cache Configuration
# 根据环境变量自动选择缓存后端
REDIS_HOST = config('REDIS_HOST', default=None)

if REDIS_HOST:
    # 生产环境使用 Redis 缓存
    REDIS_PASSWORD = config('REDIS_PASSWORD', default='')
    REDIS_PORT = config('REDIS_PORT', default='6379')

    # 构建 Redis URL
    if REDIS_PASSWORD:
        REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/1"
    else:
        REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
            },
            'KEY_PREFIX': 'blbs_erp',
            'TIMEOUT': 300,  # 默认缓存过期时间 (秒)
        }
    }
else:
    # 开发环境使用本地内存缓存
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

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

