from django.contrib import admin
from .models import StaffProfile, WorkPlan


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'rank', 'office']
    list_filter = ['rank', 'department']
    filter_horizontal = ['courses_assigned']


@admin.register(WorkPlan)
class WorkPlanAdmin(admin.ModelAdmin):
    list_display = ['staff', 'title', 'week_start', 'week_end', 'status']
    list_filter = ['status']
