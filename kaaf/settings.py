"""
KAAF University Chatbot - Django Settings
"""
import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-kaaf-dev-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'channels',
    'corsheaders',
    # Local apps
    'apps.accounts',
    'apps.students',
    'apps.staff',
    'apps.chatbot',
    'apps.notifications',
    'apps.planner',
    'apps.analytics',
    'apps.management',
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

# Database - SQLite for local dev (change to PostgreSQL for production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Auth
AUTH_USER_MODEL = 'accounts.User'
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
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# Channels - in-memory for local dev (use Redis layer in production)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Celery
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
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

# Email
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
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app',
    'https://*.ngrok.io',
]

# Session
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

# In-memory cache for fast repeated lookups (system prompts, dashboard data)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 300,  # 5 minutes
    }
}

# File upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
