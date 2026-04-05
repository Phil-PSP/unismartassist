"""Staff Models - Workplan, Teaching Schedule"""
from django.db import models
from apps.accounts.models import User
from apps.students.models import Course, Department


class StaffProfile(models.Model):
    RANK_CHOICES = [
        ('lecturer', 'Lecturer'),
        ('senior_lecturer', 'Senior Lecturer'),
        ('associate_prof', 'Associate Professor'),
        ('professor', 'Professor'),
        ('teaching_assistant', 'Teaching Assistant'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    rank = models.CharField(max_length=30, choices=RANK_CHOICES, default='lecturer')
    office = models.CharField(max_length=100, blank=True)
    office_hours = models.CharField(max_length=200, blank=True)
    specialization = models.CharField(max_length=200, blank=True)
    courses_assigned = models.ManyToManyField(Course, blank=True, related_name='instructors')

    class Meta:
        db_table = 'staff_profiles'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.rank}"


class WorkPlan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='workplans')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    week_start = models.DateField()
    week_end = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workplans'
        ordering = ['-week_start']

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.title}"
