"""
Notifications Models - Alerts, Events, Reminders
"""
from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class Notification(models.Model):
    TYPE_CHOICES = [
        ('exam', 'Exam Alert'),
        ('assignment', 'Assignment Deadline'),
        ('class', 'Class Reminder'),
        ('announcement', 'Announcement'),
        ('event', 'Event'),
        ('system', 'System'),
        ('motivation', 'Motivation'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent = models.BooleanField(default=False)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.user_id} - {self.title}"

    def mark_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])


class Event(models.Model):
    EVENT_TYPES = [
        ('academic', 'Academic'),
        ('src', 'SRC Event'),
        ('holiday', 'Holiday'),
        ('faculty', 'Faculty Meeting'),
        ('exam', 'Examination'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='academic')
    date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    is_public = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'events'
        ordering = ['date']

    def __str__(self):
        return f"{self.title} - {self.date}"

    @property
    def is_upcoming(self):
        return self.date >= timezone.now().date()


class Announcement(models.Model):
    TARGET_CHOICES = [
        ('all', 'All Users'),
        ('students', 'Students Only'),
        ('staff', 'Staff Only'),
        ('level_100', 'Level 100'),
        ('level_200', 'Level 200'),
        ('level_300', 'Level 300'),
        ('level_400', 'Level 400'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    target = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'announcements'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
