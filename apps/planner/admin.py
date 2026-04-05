from django.contrib import admin
from .models import Task, StudySession


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'task_type', 'priority', 'due_date', 'is_completed']
    list_filter = ['task_type', 'priority', 'is_completed']
    search_fields = ['user__user_id', 'title']


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject', 'duration_minutes', 'started_at', 'completed']
    list_filter = ['completed']
