"""
Accounts Models - Custom User with role-based access
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, user_id, email, password=None, **extra_fields):
        if not user_id:
            raise ValueError('User ID is required')
        email = self.normalize_email(email)
        user = self.model(user_id=user_id, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.ADMIN)
        return self.create_user(user_id, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    STUDENT = 'student'
    STAFF = 'staff'
    ADMIN = 'admin'
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (STAFF, 'Staff'),
        (ADMIN, 'Admin'),
    ]

    user_id = models.CharField(max_length=20, unique=True)  # e.g. STU/2021/001
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    # Gamification
    points = models.IntegerField(default=0)
    study_streak = models.IntegerField(default=0)
    last_study_date = models.DateField(null=True, blank=True)

    # Preferences
    LANGUAGE_CHOICES = [
        ('English', 'English'),
        ('Twi', 'Twi'),
        ('Ga', 'Ga'),
        ('Hausa', 'Hausa'),
        ('Pidgin', 'Pidgin'),
    ]
    preferred_language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='English')

    objects = UserManager()

    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'

    def __str__(self):
        return f"{self.get_full_name()} ({self.user_id})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_student(self):
        return self.role == self.STUDENT

    @property
    def is_staff_member(self):
        return self.role == self.STAFF

    @property
    def is_admin(self):
        return self.role == self.ADMIN

    def add_points(self, amount, reason=''):
        """Add gamification points"""
        self.points += amount
        self.save(update_fields=['points'])
        PointTransaction.objects.create(user=self, amount=amount, reason=reason)


class ActivityLog(models.Model):
    """Track all user activity for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activity_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.user_id} - {self.action} at {self.timestamp}"


class PointTransaction(models.Model):
    """Track gamification point transactions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_transactions')
    amount = models.IntegerField()
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'point_transactions'
        ordering = ['-created_at']


class UserMemory(models.Model):
    """Persistent AI memory per user — survives across sessions."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ai_memory')
    summary = models.TextField(blank=True)          # AI-generated summary of the user
    goals = models.TextField(blank=True)            # User's stated academic goals
    weak_subjects = models.JSONField(default=list)  # Courses with low grades
    strong_subjects = models.JSONField(default=list)
    mood_trend = models.CharField(max_length=20, blank=True)  # 'improving', 'declining', 'stable'
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_memory'

    def __str__(self):
        return f"Memory: {self.user.user_id}"


class MoodCheckIn(models.Model):
    """Weekly mood tracking for student wellbeing."""
    MOOD_CHOICES = [
        (5, '😄 Great'),
        (4, '🙂 Good'),
        (3, '😐 Okay'),
        (2, '😔 Low'),
        (1, '😢 Struggling'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_checkins')
    mood = models.IntegerField(choices=MOOD_CHOICES)
    note = models.TextField(blank=True)
    flagged = models.BooleanField(default=False)  # True if mood <= 2 for 3+ consecutive days
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mood_checkins'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.user_id} — mood {self.mood} at {self.created_at.date()}"


class StudyBuddy(models.Model):
    """Study buddy matching between students in the same course."""
    STATUS_CHOICES = [('pending', 'Pending'), ('active', 'Active'), ('ended', 'Ended')]
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buddy_requests')
    buddy = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buddy_received', null=True, blank=True)
    course = models.ForeignKey('students.Course', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'study_buddies'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.requester.user_id} ↔ {self.buddy.user_id if self.buddy else 'unmatched'}"
