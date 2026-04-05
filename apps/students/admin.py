from django.contrib import admin
from .models import Department, Programme, StudentProfile, Course, CourseRegistration, Result, GPARecord, Timetable, Document


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'faculty']
    search_fields = ['name', 'code']


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'duration_years']


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'programme', 'level', 'semester', 'cumulative_gpa']
    list_filter = ['level', 'semester', 'programme']
    search_fields = ['user__user_id', 'user__first_name', 'user__last_name']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'credit_hours', 'level', 'semester']
    list_filter = ['level', 'semester', 'department']
    search_fields = ['code', 'name']


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'academic_year', 'semester', 'score', 'grade']
    list_filter = ['academic_year', 'semester', 'grade']
    search_fields = ['student__user__user_id', 'course__code']


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ['course', 'day', 'start_time', 'end_time', 'venue', 'entry_type']
    list_filter = ['day', 'entry_type', 'academic_year']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['student', 'title', 'file_type', 'processed', 'uploaded_at']
    list_filter = ['processed', 'file_type']
