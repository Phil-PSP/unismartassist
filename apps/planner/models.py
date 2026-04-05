"""
Planner Models - Tasks, Study Timer, Productivity
"""
from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    TYPE_CHOICES = [
        ('assignment', 'Assignment'),
        ('study', 'Study Session'),
        ('exam_prep', 'Exam Preparation'),
        ('project', 'Project'),
        ('personal', 'Personal'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='study')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)
    due_time = models.TimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    points_reward = models.IntegerField(default=10)

    class Meta:
        db_table = 'tasks'
        ordering = ['due_date', 'priority']

    def __str__(self):
        return f"{self.user.user_id} - {self.title}"

    def complete(self):
        """Mark task as complete and award points"""
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save()
            self.user.add_points(self.points_reward, f'Completed task: {self.title}')
            # Update study streak
            self._update_streak()

    def _update_streak(self):
        """Update user's study streak"""
        from datetime import date
        today = date.today()
        user = self.user
        if user.last_study_date == today:
            return  # Already counted today
        if user.last_study_date and (today - user.last_study_date).days == 1:
            user.study_streak += 1
        else:
            user.study_streak = 1
        user.last_study_date = today
        user.save(update_fields=['study_streak', 'last_study_date'])

    @property
    def is_overdue(self):
        if self.due_date and not self.is_completed:
            return self.due_date < timezone.now().date()
        return False


class StudySession(models.Model):
    """Track study timer sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=100, blank=True)
    duration_minutes = models.IntegerField(default=25)  # Pomodoro default
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    class Meta:
        db_table = 'study_sessions'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.user_id} - {self.subject} ({self.duration_minutes}min)"

    def finish(self):
        """Complete a study session and award points"""
        self.ended_at = timezone.now()
        self.completed = True
        self.save()
        points = max(5, self.duration_minutes // 5)
        self.user.add_points(points, f'Study session: {self.subject or "General"}')
