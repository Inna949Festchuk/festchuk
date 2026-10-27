"""
Django settings for Festchuk project.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / '.env')


# ============================================================
# Core Settings
# ============================================================

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-in-production')
DEBUG = os.getenv('DJANGO_DEBUG', '1') == '1'
if DEBUG:
    # Local dev: allow any Host (Docker service names like `backend`, localhost, etc.).
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [
        h.strip()
        for h in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
        if h.strip()
    ]

# ============================================================
# Applications
# ============================================================

INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'corsheaders',
    'django_celery_beat',
    'channels',

    # Local apps
    'apps.core',
    'apps.projects',
    'apps.blog',
    'apps.analytics',
    'apps.ai_agent',
]

# ============================================================
# Middleware
# ============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# ============================================================
# Templates
# ============================================================

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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ============================================================
# Database — PostgreSQL + pgvector
# ============================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'festchuk'),
        'USER': os.getenv('POSTGRES_USER', 'festchuk'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'festchuk'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

# ============================================================
# Cache — Redis
# ============================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/{os.getenv('REDIS_DB', '0')}",
    }
}

# ============================================================
# Celery
# ============================================================

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Moscow'

# Celery Beat schedule
CELERY_BEAT_SCHEDULE = {
    'sync-github-readmes': {
        'task': 'apps.ai_agent.tasks.sync_all_projects_readme',
        'schedule': 86400.0,  # Daily
    },
}

# ============================================================
# REST Framework
# ============================================================

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
    },
}

# ============================================================
# CORS
# ============================================================

CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:3000,http://127.0.0.1:3000'
    ).split(',')
]
CORS_ALLOW_CREDENTIALS = True

# ============================================================
# Channels (WebSockets)
# ============================================================

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# ============================================================
# RouterAI
# ============================================================

ROUTERAI_API_KEY = os.getenv('ROUTERAI_API_KEY', '')
ROUTERAI_BASE_URL = os.getenv('ROUTERAI_BASE_URL', 'https://api.routerai.ru/v1')
ROUTERAI_LLM_MODEL = os.getenv('ROUTERAI_LLM_MODEL', 'qwen-2.5-plus')
ROUTERAI_EMBEDDINGS_MODEL = os.getenv('ROUTERAI_EMBEDDINGS_MODEL', 'bge-m3')
ROUTERAI_TTS_MODEL = os.getenv('ROUTERAI_TTS_MODEL', 'tts-1-hd')
ROUTERAI_STT_MODEL = os.getenv('ROUTERAI_STT_MODEL', 'whisper-large-v3')

# ============================================================
# AI Agent
# ============================================================

CHAT_SESSION_TTL = 4 * 3600  # 4 hours
MAX_CHAT_HISTORY = 50  # messages to keep in context
RAG_TOP_K = 5  # number of similar documents to retrieve

# ============================================================
# Analytics
# ============================================================

LIKES_TTL = 86400  # 24 hours
VIEWS_TTL = 86400  # 24 hours

# ============================================================
# Static & Media
# ============================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================================
# i18n
# ============================================================

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# ============================================================
# Security (Production)
# ============================================================

if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv('HTTPS_ENABLED', 'false') == 'true'
    SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
    CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ============================================================
# Logging
# ============================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
