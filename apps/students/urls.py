from django.urls import path
from . import views

urlpatterns = [
    path('results/', views.results_view, name='results'),
    path('timetable/', views.timetable_view, name='timetable'),
    path('gpa/', views.gpa_dashboard_view, name='gpa_dashboard'),
    path('documents/', views.documents_view, name='documents'),
    path('documents/<int:doc_id>/', views.document_detail_view, name='document_detail'),
    # AJAX endpoints
    path('api/gpa-trend/', views.api_gpa_trend, name='api_gpa_trend'),
    path('api/today-schedule/', views.api_today_schedule, name='api_today_schedule'),
]
