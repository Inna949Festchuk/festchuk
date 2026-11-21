"""
Django settings for Feshchuk project.
"""
import json
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
    # Дописывает завершающий слэш /api/ путям НА МЕСТЕ (без 301) — иначе
    # Next.js-прокси ↔ Django APPEND_SLASH образуют петлю перенаправлений.
    'config.middleware.ApiTrailingSlashMiddleware',
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
        'NAME': os.getenv('POSTGRES_DB', 'feshchuk'),
        'USER': os.getenv('POSTGRES_USER', 'feshchuk'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'feshchuk'),
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
    # This API is fully anonymous (IP-based chat sessions, AllowAny everywhere).
    # DRF's DEFAULT would include SessionAuthentication, which — when the visitor
    # is logged into Django admin on the same host — authenticates the request and
    # then enforces CSRF on every POST. The SPA sends no X-CSRFToken, so chat/STT
    # would 403 while GETs pass. Disable auth entirely to remove that trap.
    'DEFAULT_AUTHENTICATION_CLASSES': (),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'config.throttling.ClientIPAnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        # Reads are cheap; the frontend fires 2+ of them per page view and the
        # whole site shares one bucket in dev (Next.js rewrites do not forward
        # X-Forwarded-For), so this has to stay well above browsing volume.
        'anon': os.getenv('THROTTLE_ANON_RATE', '2000/hour'),
        # Likes / views.
        'write': os.getenv('THROTTLE_WRITE_RATE', '120/hour'),
        # Paid AI calls — deliberately tight.
        'chat': os.getenv('THROTTLE_CHAT_RATE', '30/hour'),
        'tts': os.getenv('THROTTLE_TTS_RATE', '30/hour'),
        'stt': os.getenv('THROTTLE_STT_RATE', '30/hour'),
    },
}

# ============================================================
# Reverse proxies
# ============================================================
# Peers allowed to speak for the client via X-Forwarded-For. Private-range
# addresses (Docker bridge, nginx, the Next.js rewrite) are always trusted;
# list any public proxy here.
TRUSTED_PROXY_IPS = frozenset(
    ip.strip()
    for ip in os.getenv('TRUSTED_PROXY_IPS', '').split(',')
    if ip.strip()
)

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
ROUTERAI_BASE_URL = os.getenv('ROUTERAI_BASE_URL', 'https://routerai.ru/api/v1')
ROUTERAI_LLM_MODEL = os.getenv('ROUTERAI_LLM_MODEL', 'qwen/qwen3.7-plus')
# Low temperature improves instruction-following for module personas without
# materially increasing latency for the fast chat model.
ROUTERAI_LLM_TEMPERATURE = float(os.getenv('ROUTERAI_LLM_TEMPERATURE', '0.3'))
# qwen3.5-plus thinks by default: ~900 reasoning tokens and +10-15s even for a
# greeting. The verified RouterAI switch is reasoning={'enabled': False}
# (enable_thinking only partially suppresses it). When true, the parameter is
# not sent at all — for models without reasoning support (e.g. instruct-2507).
ROUTERAI_LLM_REASONING_ENABLED = os.getenv('ROUTERAI_LLM_REASONING_ENABLED', 'false') == 'true'
# Output is the expensive side (plus: ~193 RUB/1M) and long markdown answers
# also slow generation down. Brevity is additionally enforced in the prompt.
ROUTERAI_LLM_MAX_TOKENS = int(os.getenv('ROUTERAI_LLM_MAX_TOKENS', '1000'))
ROUTERAI_EMBEDDINGS_MODEL = os.getenv('ROUTERAI_EMBEDDINGS_MODEL', 'bge-m3')
# TTS voice names are provider-specific: minimax/speech-* take OpenAI names
# (alloy/nova/echo) while google/gemini-*-tts take Gemini names (Kore/Puck/Zephyr/...).
# A mismatched name 400s. Google TTS always returns WAV regardless of the requested format.
ROUTERAI_TTS_MODEL = os.getenv('ROUTERAI_TTS_MODEL', 'google/gemini-3.8-flash-lite-tts')
# The OpenAI SDK treats `voice` as required, so this must always be non-empty.
ROUTERAI_TTS_VOICE = os.getenv('ROUTERAI_TTS_VOICE', 'Kore')
# Must be explicit: the default is raw PCM, which a browser cannot play.
ROUTERAI_TTS_FORMAT = os.getenv('ROUTERAI_TTS_FORMAT', 'wav')
# turbo is 2.25x cheaper per second and faster than large-v3 at near-equal quality.
ROUTERAI_STT_MODEL = os.getenv('ROUTERAI_STT_MODEL', 'openai/whisper-large-v3-turbo')

# ============================================================
# AI Agent
# ============================================================

# Срок жизни сессий и истории чата в Redis (часов) с последнего действия.
# Хранилище — только Redis (152-ФЗ: ПДн не держим в PostgreSQL), удаление
# гарантирует сам движок (TTL), а не периодическая задача.
CHAT_RETENTION_HOURS = int(os.getenv('CHAT_RETENTION_HOURS', '4'))
CHAT_SESSION_TTL = CHAT_RETENTION_HOURS * 3600
# Every history message is re-sent as input tokens on each turn; 50 messages of
# long markdown answers made long dialogues expensive. 16 keeps enough context.
MAX_CHAT_HISTORY = int(os.getenv('MAX_CHAT_HISTORY', '16'))
# 5 chunks x 800 chars ~ 2k input tokens per message; top-3 suffices for the
# small corpus (projects + articles) and cuts the RAG context by ~40%.
RAG_TOP_K = int(os.getenv('RAG_TOP_K', '3'))
# Upper bound on characters handed to the synthesizer per request.
TTS_MAX_CHARS = int(os.getenv('TTS_MAX_CHARS', '4000'))
# Глобальный суточный бюджет LLM (circuit breaker): троттлинг per-IP не
# защищает от распределённого флуда (волна трафика с разных IP сливает баланс
# RouterAI). Счётчики в Redis, ключи с датой, TTL 48ч.
ROUTERAI_DAILY_MAX_REQUESTS = int(os.getenv('ROUTERAI_DAILY_MAX_REQUESTS', '1000'))
ROUTERAI_DAILY_MAX_TOKENS = int(os.getenv('ROUTERAI_DAILY_MAX_TOKENS', '5000000'))

# ============================================================
# Context7 — live library documentation for module-specific AI
# ============================================================

CONTEXT7_API_KEY = os.getenv('CONTEXT7_API_KEY', '')
CONTEXT7_BASE_URL = os.getenv('CONTEXT7_BASE_URL', 'https://context7.com/api/v1')
CONTEXT7_TIMEOUT = int(os.getenv('CONTEXT7_TIMEOUT', '15'))
# Library docs change rarely; caching them per topic removes the ~2s REST
# round-trip from almost every module message (and the repeat after a handoff).
CONTEXT7_CACHE_TTL = int(os.getenv('CONTEXT7_CACHE_TTL', '21600'))

# Module -> Context7 topic: whose library docs get auto-injected into that
# module's prompt every turn. Env override is a JSON dict ({"slug": "topic"})
# merged on top of the defaults, so a single slug can be overridden.
# quantum-shield = Django core: the security sections (CSRF/HTTPS/cookies)
# fit its stack; 'Django REST Framework' was rejected — its API docs drifted
# the persona toward HYPER DRIVE (2026-11-17).
_DEFAULT_CONTEXT7_MODULE_TOPICS = {
    'hyper-drive': 'Django 5',
    'neural-sync': 'LangChain',
    'omni-vision': 'Next.js',
    'quantum-shield': 'Django',
}
CONTEXT7_MODULE_TOPICS = dict(_DEFAULT_CONTEXT7_MODULE_TOPICS)
_context7_topics_env = os.getenv('CONTEXT7_MODULE_TOPICS', '').strip()
if _context7_topics_env:
    try:
        _context7_topics_override = json.loads(_context7_topics_env)
    except ValueError:
        _context7_topics_override = None
    if isinstance(_context7_topics_override, dict):
        CONTEXT7_MODULE_TOPICS.update(
            {str(k): str(v) for k, v in _context7_topics_override.items()}
        )

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

# Absolute base used to build media URLs in API responses. Necessary because
# in Docker the backend only sees internal proxy requests (Host: backend:8000),
# which the browser cannot resolve. Set e.g. http://localhost:8000 in .env for
# local dev; leave empty to fall back to request.build_absolute_uri().
API_BASE_URL = os.getenv('API_BASE_URL', '')

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
