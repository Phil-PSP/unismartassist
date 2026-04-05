from django.urls import path
from . import views

urlpatterns = [
    path('', views.planner_view, name='planner'),
    path('add/', views.add_task_view, name='add_task'),
    path('<int:task_id>/complete/', views.complete_task_view, name='complete_task'),
    path('<int:task_id>/delete/', views.delete_task_view, name='delete_task'),
    path('timer/', views.study_timer_view, name='study_timer'),
    path('timer/start/', views.start_session_view, name='start_session'),
    path('timer/<int:session_id>/finish/', views.finish_session_view, name='finish_session'),
]
