"""
Quick script to check if Exams models are registered in admin
Run: python check_admin_registration.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kaaf.settings')
django.setup()

from django.contrib import admin
from apps.exams.models import Exam, Question, ExamAttempt, ExamCategory, Answer, PastQuestionFile

print("=" * 60)
print("CHECKING ADMIN REGISTRATION")
print("=" * 60)

models_to_check = [
    ('ExamCategory', ExamCategory),
    ('Exam', Exam),
    ('Question', Question),
    ('ExamAttempt', ExamAttempt),
    ('Answer', Answer),
    ('PastQuestionFile', PastQuestionFile),
]

all_registered = True

for model_name, model_class in models_to_check:
    is_registered = model_class in admin.site._registry
    status = "✅ REGISTERED" if is_registered else "❌ NOT REGISTERED"
    print(f"{model_name:20} {status}")
    if not is_registered:
        all_registered = False

print("=" * 60)

if all_registered:
    print("✅ ALL MODELS ARE REGISTERED!")
    print("\nAdmin should be visible at:")
    print("http://127.0.0.1:8000/admin/")
    print("\nLook for 'EXAMINATION SYSTEM' section")
else:
    print("❌ SOME MODELS ARE NOT REGISTERED")
    print("\nTry restarting the Django server:")
    print("1. Stop server (Ctrl+C)")
    print("2. Run: .\\venv\\Scripts\\python.exe manage.py runserver 8000")

print("=" * 60)
