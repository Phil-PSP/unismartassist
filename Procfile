web: daphne kaaf.asgi:application --port $PORT --bind 0.0.0.0
worker: celery -A kaaf worker -l info
beat: celery -A kaaf beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
