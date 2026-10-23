from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    # Exam URLs
    path('', views.exam_list, name='exam_list'),
    path('<uuid:exam_id>/', views.exam_detail, name='exam_detail'),
    path('<uuid:exam_id>/start/', views.start_exam, name='start_exam'),
    path('attempt/<uuid:attempt_id>/', views.take_exam, name='take_exam'),
    path('attempt/<uuid:attempt_id>/save/', views.save_answer, name='save_answer'),
    path('attempt/<uuid:attempt_id>/submit/', views.submit_exam, name='submit_exam'),
    path('attempt/<uuid:attempt_id>/result/', views.exam_result, name='exam_result'),
    
    # AI Exam Generation URLs
    path('ai/generate/', views.ai_exam_generator, name='ai_exam_generator'),
    path('ai/my-exams/', views.my_ai_exams, name='my_ai_exams'),
    
    # Past Questions URLs
    path('past-questions/', views.past_questions_list, name='past_questions_list'),
    path('past-questions/<uuid:file_id>/download/', views.download_past_question, name='download_past_question'),
    path('past-questions/upload/', views.upload_past_question, name='upload_past_question'),
    
    # Bulk Question Upload URLs
    path('questions/bulk-upload/', views.bulk_question_upload, name='bulk_question_upload'),
    path('questions/template/<str:format_type>/', views.download_question_template, name='download_question_template'),
]
