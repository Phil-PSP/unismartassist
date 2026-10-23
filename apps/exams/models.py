"""
Examination System Models
Supports online exams, past questions, and student attempts
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User
from apps.students.models import Course
import uuid


class ExamCategory(models.Model):
    """Categories for organizing exams (e.g., Mid-Semester, End-of-Semester, Quiz)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Exam Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Exam(models.Model):
    """Main exam model - can be a quiz, mid-sem, or final exam"""
    EXAM_TYPES = [
        ('quiz', 'Quiz'),
        ('mid_sem', 'Mid-Semester'),
        ('final', 'Final Exam'),
        ('past_question', 'Past Question'),
        ('practice', 'Practice Test'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    category = models.ForeignKey(ExamCategory, on_delete=models.SET_NULL, null=True, blank=True)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES, default='practice')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS, default='medium')
    
    description = models.TextField(blank=True)
    instructions = models.TextField(default="Read each question carefully and select the best answer.")
    
    # Timing
    duration_minutes = models.IntegerField(default=60, help_text="Duration in minutes")
    start_time = models.DateTimeField(null=True, blank=True, help_text="When exam becomes available")
    end_time = models.DateTimeField(null=True, blank=True, help_text="When exam closes")
    
    # Settings
    total_marks = models.IntegerField(default=100)
    pass_mark = models.IntegerField(default=50)
    shuffle_questions = models.BooleanField(default=True)
    shuffle_options = models.BooleanField(default=True)
    show_results_immediately = models.BooleanField(default=False)
    allow_review = models.BooleanField(default=True, help_text="Allow students to review after submission")
    max_attempts = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='exams_created')
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Past question specific
    academic_year = models.CharField(max_length=20, blank=True, help_text="e.g., 2023/2024")
    semester = models.IntegerField(null=True, blank=True, choices=[(1, 'First'), (2, 'Second')])
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'is_published']),
            models.Index(fields=['exam_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.course.code} - {self.title}"
    
    @property
    def total_questions(self):
        return self.questions.count()
    
    @property
    def is_available(self):
        """Check if exam is currently available"""
        from django.utils import timezone
        now = timezone.now()
        if not self.is_published or not self.is_active:
            return False
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True


class Question(models.Model):
    """Individual question in an exam"""
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('fill_blank', 'Fill in the Blank'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    
    marks = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    order = models.IntegerField(default=0)
    
    # Optional: Add image support
    image = models.ImageField(upload_to='exam_questions/', null=True, blank=True)
    
    # For short answer/essay questions
    expected_answer = models.TextField(blank=True, help_text="For auto-grading or reference")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


class QuestionOption(models.Model):
    """Options for multiple choice questions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.option_text[:30]} ({'✓' if self.is_correct else '✗'})"


class ExamAttempt(models.Model):
    """Student's attempt at an exam"""
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_attempts')
    
    attempt_number = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_taken_minutes = models.IntegerField(null=True, blank=True)
    
    # Scoring
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    
    # Feedback
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='exams_graded')
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        unique_together = ['exam', 'student', 'attempt_number']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['exam', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.exam.title} (Attempt {self.attempt_number})"
    
    def calculate_score(self):
        """Calculate total score from answers"""
        total_score = 0
        total_possible = 0
        
        for answer in self.answers.all():
            total_possible += answer.question.marks
            if answer.is_correct:
                total_score += answer.marks_awarded or answer.question.marks
        
        self.score = total_score
        self.percentage = (total_score / total_possible * 100) if total_possible > 0 else 0
        self.passed = self.score >= self.exam.pass_mark
        self.save()
        
        return self.score


class Answer(models.Model):
    """Student's answer to a question"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    
    # For multiple choice
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.SET_NULL, null=True, blank=True)
    
    # For text-based answers
    answer_text = models.TextField(blank=True)
    
    # Grading
    is_correct = models.BooleanField(null=True, blank=True)
    marks_awarded = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"Answer to {self.question}"
    
    def check_answer(self):
        """Auto-check answer for multiple choice, true/false, and fill_blank"""
        if self.question.question_type in ['multiple_choice', 'true_false']:
            if self.selected_option:
                self.is_correct = self.selected_option.is_correct
                self.marks_awarded = self.question.marks if self.is_correct else 0
                self.save()
        elif self.question.question_type == 'fill_blank':
            if self.answer_text and self.question.expected_answer:
                # Case-insensitive comparison, strip whitespace
                student_answer = self.answer_text.strip().lower()
                correct_answer = self.question.expected_answer.strip().lower()
                self.is_correct = student_answer == correct_answer
                self.marks_awarded = self.question.marks if self.is_correct else 0
                self.save()
        return self.is_correct


class PastQuestionFile(models.Model):
    """Uploaded past question papers (PDF, images, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='past_question_files')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    file = models.FileField(upload_to='past_questions/')
    file_type = models.CharField(max_length=10, choices=[
        ('pdf', 'PDF'),
        ('image', 'Image'),
        ('doc', 'Document'),
    ])
    
    academic_year = models.CharField(max_length=20)
    semester = models.IntegerField(choices=[(1, 'First'), (2, 'Second')])
    exam_type = models.CharField(max_length=20, choices=Exam.EXAM_TYPES)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    downloads = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-academic_year', '-semester']
    
    def __str__(self):
        return f"{self.course.code} - {self.title} ({self.academic_year})"
