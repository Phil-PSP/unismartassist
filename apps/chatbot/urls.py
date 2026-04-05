from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chatbot'),
    path('send/', views.send_message_view, name='chat_send'),
    path('feedback/', views.feedback_view, name='chat_feedback'),
    path('history/', views.chat_history_view, name='chat_history'),
    path('new-session/', views.new_session_view, name='chat_new_session'),
    path('delete-session/<int:session_id>/', views.delete_session_view, name='chat_delete_session'),
    path('delete-all/', views.delete_all_sessions_view, name='chat_delete_all'),
]
