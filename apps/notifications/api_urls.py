from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.NotificationsAPIView.as_view(), name='api_notifications'),
    path('events/', api_views.EventsAPIView.as_view(), name='api_events'),
]
