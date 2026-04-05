from django.urls import path
from . import api_views

urlpatterns = [
    path('tasks/', api_views.TasksAPIView.as_view(), name='api_tasks'),
]
