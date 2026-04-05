from django.urls import path
from . import api_views

urlpatterns = [
    path('send/', api_views.ChatAPIView.as_view(), name='api_chat_send'),
    path('history/', api_views.ChatHistoryAPIView.as_view(), name='api_chat_history'),
]
