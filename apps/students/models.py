"""
Students App Models - Courses, Results, GPA, Timetable
"""
from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    faculty = models.CharField(max_length=100)

    class Meta:
        db_table = 'departments'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Programme(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    duration_years = models.IntegerField(default=4)

    class Meta:
        db_table = 'programmes'

    def __str__(self):
        return self.name


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    programme = models.ForeignKey(Programme, on_delete=models.SET_NULL, null=True)
    level = models.IntegerField(default=100)  # 100, 200, 300, 400
    semester = models.IntegerField(default=1)
    academic_year = models.CharField(max_length=9, default='2024/2025')
    enrollment_date = models.DateField(default=timezone.now)
    expected_graduation = models.DateField(null=True, blank=True)
    cumulative_gpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'student_profiles'

    def __str__(self):
        return f"{self.user.user_id} - {self.programme}"

    def calculate_cumulative_gpa(self):
        """Recalculate and save cumulative GPA from all results"""
        results = Result.objects.filter(student=self, grade__isnull=False)
        if not results.exists():
            return 0.00
        total_points = sum(r.grade_points * r.course.credit_hours for r in results)
        total_credits = sum(r.course.credit_hours for r in results)
        if total_credits == 0:
            return 0.00
        gpa = round(total_points / total_credits, 2)
        self.cumulative_gpa = gpa
        self.save(update_fields=['cumulative_gpa'])
        return gpa


class Course(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=150)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    credit_hours = models.IntegerField(default=3)
    level = models.IntegerField(default=100)
    semester = models.IntegerField(default=1)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'courses'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class CourseRegistration(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='registrations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9)
    semester = models.IntegerField()
    registered_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'course_registrations'
        unique_together = ['student', 'course', 'academic_year', 'semester']

    def __str__(self):
        return f"{self.student.user.user_id} - {self.course.code}"


class Result(models.Model):
    GRADE_CHOICES = [
        ('A+', 'A+ (90-100)'), ('A', 'A (80-89)'), ('B+', 'B+ (75-79)'),
        ('B', 'B (70-74)'), ('C+', 'C+ (65-69)'), ('C', 'C (60-64)'),
        ('D+', 'D+ (55-59)'), ('D', 'D (50-54)'), ('F', 'F (0-49)'),
    ]
    GRADE_POINT_MAP = {
        'A+': 4.0, 'A': 4.0, 'B+': 3.5, 'B': 3.0,
        'C+': 2.5, 'C': 2.0, 'D+': 1.5, 'D': 1.0, 'F': 0.0,
    }

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='results')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=9)
    semester = models.IntegerField()
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=3, choices=GRADE_CHOICES, blank=True)
    grade_points = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    remarks = models.CharField(max_length=50, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'results'
        unique_together = ['student', 'course', 'academic_year', 'semester']
        ordering = ['-academic_year', 'semester']

    def save(self, *args, **kwargs):
        # Auto-assign grade from score
        if self.score is not None and not self.grade:
            self.grade = self._score_to_grade(float(self.score))
        if self.grade:
            self.grade_points = self.GRADE_POINT_MAP.get(self.grade, 0.0)
        super().save(*args, **kwargs)
        # Recalculate GPA after saving
        self.student.calculate_cumulative_gpa()

    def _score_to_grade(self, score):
        if score >= 90: return 'A+'
        elif score >= 80: return 'A'
        elif score >= 75: return 'B+'
        elif score >= 70: return 'B'
        elif score >= 65: return 'C+'
        elif score >= 60: return 'C'
        elif score >= 55: return 'D+'
        elif score >= 50: return 'D'
        return 'F'

    def __str__(self):
        return f"{self.student.user.user_id} - {self.course.code}: {self.grade}"


class GPARecord(models.Model):
    """Semester GPA history for trend analysis"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='gpa_records')
    academic_year = models.CharField(max_length=9)
    semester = models.IntegerField()
    gpa = models.DecimalField(max_digits=4, decimal_places=2)
    total_credits = models.IntegerField(default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gpa_records'
        unique_together = ['student', 'academic_year', 'semester']
        ordering = ['-academic_year', '-semester']

    def __str__(self):
        return f"{self.student.user.user_id} GPA {self.gpa} ({self.academic_year} Sem {self.semester})"


class Timetable(models.Model):
    DAYS = [
        ('MON', 'Monday'), ('TUE', 'Tuesday'), ('WED', 'Wednesday'),
        ('THU', 'Thursday'), ('FRI', 'Friday'), ('SAT', 'Saturday'),
    ]
    TYPE_CHOICES = [('class', 'Class'), ('exam', 'Exam'), ('lab', 'Lab')]

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    day = models.CharField(max_length=3, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=100)
    entry_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='class')
    academic_year = models.CharField(max_length=9)
    semester = models.IntegerField()
    level = models.IntegerField(default=100)

    class Meta:
        db_table = 'timetables'
        ordering = ['day', 'start_time']

    def __str__(self):
        return f"{self.course.code} - {self.day} {self.start_time}"


class Document(models.Model):
    """Student uploaded documents for AI processing"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents/%Y/%m/')
    file_type = models.CharField(max_length=10, blank=True)
    summary = models.TextField(blank=True)
    key_points = models.JSONField(default=list)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    class Meta:
        db_table = 'documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.student.user.user_id} - {self.title}"


class Batch(models.Model):
    """A student intake batch e.g. 2023/2024 Level 100"""
    name = models.CharField(max_length=100)  # e.g. "2023 Intake"
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='batches')
    admission_year = models.CharField(max_length=9)  # e.g. "2023/2024"
    expected_graduation_year = models.CharField(max_length=9, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'batches'
        ordering = ['-admission_year']
        unique_together = ['programme', 'admission_year']

    def __str__(self):
        return f"{self.programme.code} — {self.name} ({self.admission_year})"

    @property
    def student_count(self):
        return StudentProfile.objects.filter(
            programme=self.programme,
            academic_year=self.admission_year
        ).count()


class AcademicLevel(models.Model):
    """Configurable academic levels per programme"""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='levels')
    level = models.IntegerField()  # 100, 200, 300, 400
    label = models.CharField(max_length=50, blank=True)  # e.g. "Year 1", "Foundation"
    academic_year = models.CharField(max_length=9)  # e.g. "2024/2025"
    is_current = models.BooleanField(default=False)

    class Meta:
        db_table = 'academic_levels'
        unique_together = ['programme', 'level', 'academic_year']
        ordering = ['level']

    def __str__(self):
        return f"{self.programme.code} Level {self.level} ({self.academic_year})"

    @property
    def student_count(self):
        return StudentProfile.objects.filter(
            programme=self.programme,
            level=self.level,
            academic_year=self.academic_year
        ).count()
