from django.contrib import admin
from .models import ChatSession, ChatMessage, ChatFeedback


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'mode', 'started_at', 'last_activity', 'is_active']
    list_filter = ['mode', 'is_active']
    search_fields = ['user__user_id']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'sender', 'message', 'intent', 'confidence', 'timestamp']
    list_filter = ['sender', 'intent']
    search_fields = ['message', 'session__user__user_id']


@admin.register(ChatFeedback)
class ChatFeedbackAdmin(admin.ModelAdmin):
    list_display = ['message', 'rating', 'comment', 'created_at']
    list_filter = ['rating']
