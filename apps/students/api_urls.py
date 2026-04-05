from django.urls import path
from . import api_views

urlpatterns = [
    path('results/', api_views.ResultsAPIView.as_view(), name='api_results'),
    path('timetable/', api_views.TimetableAPIView.as_view(), name='api_timetable'),
    path('gpa/', api_views.GPAAPIView.as_view(), name='api_gpa'),
]
