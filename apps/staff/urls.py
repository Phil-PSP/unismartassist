from django.urls import path
from . import views

urlpatterns = [
    path('', views.staff_dashboard_view, name='staff_dashboard'),
    path('performance/', views.student_performance_view, name='student_performance'),
]
