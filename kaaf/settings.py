"""
KAAF University Chatbot - Django Settings
"""
import os
import dj_database_url
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='')
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith('replace-with-') or SECRET_KEY == 'django-insecure-kaaf-dev-key-change-in-production':
    raise RuntimeError('Set a unique, high-entropy SECRET_KEY (at least 50 characters) in the environment.')

DEBUG = config('DEBUG', default=False, cast=bool)
if DEBUG and not config('DJANGO_ALLOW_INSECURE_DEBUG', default=False, cast=bool):
    raise RuntimeError('DEBUG=True requires DJANGO_ALLOW_INSECURE_DEBUG=True; never enable this in production.')

# Allow Railway's auto-generated domain + any custom domains
_allowed = config('ALLOWED_HOSTS', default='localhost,127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in _allowed.split(',') if host.strip()]
if not DEBUG and '*' in ALLOWED_HOSTS:
    raise RuntimeError('Wildcard ALLOWED_HOSTS is not permitted when DEBUG=False.')
# Railway injects RAILWAY_PUBLIC_DOMAIN automatically
_railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '')
if _railway_domain and _railway_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_railway_domain)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'channels',
    'corsheaders',
    # Local apps
    'apps.accounts.apps.AccountsConfig',
    'apps.students',
    'apps.staff',
    'apps.chatbot',
    'apps.notifications',
    'apps.planner',
    'apps.analytics',
    'apps.management',
    'apps.exams',  # New examination system
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.accounts.middleware.ActivityLogMiddleware',
]

ROOT_URLCONF = 'kaaf.urls'

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
                'apps.chatbot.context_processors.chat_sessions',
                'apps.chatbot.context_processors.admin_nav',
            ],
        },
    },
]

# ASGI for WebSockets
ASGI_APPLICATION = 'kaaf.asgi.application'
WSGI_APPLICATION = 'kaaf.wsgi.application'

# Database — uses DATABASE_URL on Railway, falls back to SQLite locally
_db_url = os.environ.get('DATABASE_URL', f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
DATABASES = {
    'default': dj_database_url.config(
        default=_db_url,
        conn_max_age=0,
    )
}
# SQLite-specific: 30s busy timeout to prevent "database is locked"
if 'sqlite' in _db_url:
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS']['timeout'] = 30

# Auth
AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Accra'
USE_I18N = True
USE_TZ = True

# Static & Media
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.accounts.jwt_auth.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.ScopedRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {
        'auth': '5/minute',
        'mfa': '5/minute',
        'chat': '20/minute',
    },
}

# Channels — uses Redis on Railway, falls back to in-memory locally
_redis_url = config('REDIS_URL', default='')
if _redis_url:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [_redis_url],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# Celery — uses REDIS_URL on Railway
CELERY_BROKER_URL = config('REDIS_URL', default=config('CELERY_BROKER_URL', default='redis://localhost:6379/0'))
CELERY_RESULT_BACKEND = config('REDIS_URL', default=config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0'))
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat Schedule
try:
    from celery.schedules import crontab
    CELERY_BEAT_SCHEDULE = {
        'morning-briefing': {
            'task': 'apps.notifications.tasks.send_morning_briefing',
            'schedule': crontab(hour=7, minute=0),
        },
        'class-reminders': {
            'task': 'apps.notifications.tasks.send_class_reminders',
            'schedule': crontab(minute=0),
        },
        'assignment-deadlines': {
            'task': 'apps.notifications.tasks.check_assignment_deadlines',
            'schedule': crontab(hour=8, minute=0),
        },
        'daily-motivation': {
            'task': 'apps.notifications.tasks.send_daily_motivation',
            'schedule': crontab(hour=6, minute=30),
        },
        'at-risk-check': {
            'task': 'apps.notifications.tasks.check_at_risk_students',
            'schedule': crontab(hour=9, minute=0, day_of_week=1),
        },
        'grade-reminders': {
            'task': 'apps.notifications.tasks.send_grade_submission_reminders',
            'schedule': crontab(hour=10, minute=0, day_of_week=5),
        },
        'leaderboard-shoutouts': {
            'task': 'apps.notifications.tasks.check_leaderboard_shoutouts',
            'schedule': crontab(hour=18, minute=0),
        },
        'update-memories': {
            'task': 'apps.notifications.tasks.update_all_user_memories',
            'schedule': crontab(hour=2, minute=0),
        },
        'exam-countdown-alerts': {
            'task': 'apps.notifications.tasks.send_exam_countdown_alerts',
            'schedule': crontab(hour=8, minute=30),
        },
        'daily-challenge': {
            'task': 'apps.notifications.tasks.send_daily_challenge',
            'schedule': crontab(hour=7, minute=30),  # 7:30am daily
        },
        'streak-milestones': {
            'task': 'apps.notifications.tasks.check_streak_milestones',
            'schedule': crontab(hour=20, minute=0),  # 8pm daily
        },
    }
except ImportError:
    pass  # Celery not installed — tasks run manually or via Redis when available

# Email — use SMTP in production if env vars are set
if config('EMAIL_HOST_USER', default=''):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)

# OpenAI (optional)
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')

# Google Gemini
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')

# CORS
# Use explicit trusted origins; do not trust wildcard tunnel or platform domains.
_cors_origins = config('CORS_ALLOWED_ORIGINS', default='http://localhost:8000,http://127.0.0.1:8000')
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins.split(',') if origin.strip()]
_csrf_origins = config('CSRF_TRUSTED_ORIGINS', default='')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _csrf_origins.split(',') if origin.strip()]
if _railway_domain:
    production_origin = f'https://{_railway_domain}'
    if production_origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(production_origin)
    if production_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(production_origin)

# Session — database backend
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True

# Shared cache: Redis in deployed environments, per-process fallback for local development.
if _redis_url:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _redis_url,
            'TIMEOUT': 300,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'kaaf-local-cache',
            'TIMEOUT': 300,
        }
    }

# File upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024


# Production security defaults. Enable only after HTTPS and proxy configuration are verified.
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=not DEBUG, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=not DEBUG, cast=bool)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=not DEBUG, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=False, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if config('TRUST_X_FORWARDED_PROTO', default=False, cast=bool) else None
