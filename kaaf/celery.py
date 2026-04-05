"""Celery configuration for background tasks"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kaaf.settings')

app = Celery('kaaf')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks schedule
app.conf.beat_schedule = {
    # Send class reminders every hour
    'send-class-reminders': {
        'task': 'apps.notifications.tasks.send_class_reminders',
        'schedule': crontab(minute=0),  # every hour
    },
    # Check assignment deadlines daily at 8am
    'check-assignment-deadlines': {
        'task': 'apps.notifications.tasks.check_assignment_deadlines',
        'schedule': crontab(hour=8, minute=0),
    },
    # Send motivational quotes daily at 7am
    'send-daily-motivation': {
        'task': 'apps.notifications.tasks.send_daily_motivation',
        'schedule': crontab(hour=7, minute=0),
    },
}
