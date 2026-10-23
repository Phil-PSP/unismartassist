from django.contrib import admin
from .models import (
    ExamCategory, Exam, Question, QuestionOption,
    ExamAttempt, Answer, PastQuestionFile
)

# Debug: Print when admin module is loaded
print("=" * 60)
print("🔧 LOADING EXAMS ADMIN MODULE")
print("=" * 60)


@admin.register(ExamCategory)
class ExamCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


print("✅ Registered: ExamCategory")

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4
    fields = ['option_text', 'is_correct', 'order']


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    fields = ['question_text', 'question_type', 'marks', 'order']
    show_change_link = True


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'exam_type', 'total_marks', 'duration_minutes', 'is_published', 'created_at']
    list_filter = ['exam_type', 'is_published', 'is_active', 'difficulty', 'course__department']
    search_fields = ['title', 'course__name', 'course__code']
    inlines = [QuestionInline]
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'course', 'category', 'exam_type', 'difficulty', 'description', 'instructions')
        }),
        ('Timing', {
            'fields': ('duration_minutes', 'start_time', 'end_time')
        }),
        ('Scoring', {
            'fields': ('total_marks', 'pass_mark')
        }),
        ('Settings', {
            'fields': ('shuffle_questions', 'shuffle_options', 'show_results_immediately', 'allow_review', 'max_attempts')
        }),
        ('Past Question Info', {
            'fields': ('academic_year', 'semester'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_published', 'created_by')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


print("✅ Registered: Exam")

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'exam', 'question_type', 'marks', 'order']
    list_filter = ['question_type', 'exam__course']
    search_fields = ['question_text', 'exam__title']
    inlines = [QuestionOptionInline]
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'attempt_number', 'status', 'score', 'percentage', 'passed', 'started_at']
    list_filter = ['status', 'passed', 'exam__course']
    search_fields = ['student__first_name', 'student__last_name', 'exam__title']
    readonly_fields = ['id', 'started_at', 'submitted_at', 'graded_at']
    
    fieldsets = (
        ('Attempt Info', {
            'fields': ('exam', 'student', 'attempt_number', 'status')
        }),
        ('Timing', {
            'fields': ('started_at', 'submitted_at', 'time_taken_minutes')
        }),
        ('Scoring', {
            'fields': ('score', 'percentage', 'passed')
        }),
        ('Grading', {
            'fields': ('feedback', 'graded_by', 'graded_at')
        }),
    )


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'is_correct', 'marks_awarded', 'answered_at']
    list_filter = ['is_correct', 'question__question_type']
    search_fields = ['attempt__student__first_name', 'attempt__student__last_name', 'question__question_text']
    readonly_fields = ['answered_at']


@admin.register(PastQuestionFile)
class PastQuestionFileAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'academic_year', 'semester', 'exam_type', 'downloads', 'uploaded_at']
    list_filter = ['academic_year', 'semester', 'exam_type', 'file_type', 'is_active']
    search_fields = ['title', 'course__name', 'course__code']
    readonly_fields = ['id', 'uploaded_at', 'downloads']


print("✅ Registered: Question")
print("✅ Registered: ExamAttempt")
print("✅ Registered: Answer")
print("✅ Registered: PastQuestionFile")
print("=" * 60)
print("🎉 ALL EXAMS ADMIN MODELS REGISTERED!")
print("=" * 60)
