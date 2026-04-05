from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ActivityLog, PointTransaction


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['user_id', 'get_full_name', 'email', 'role', 'points', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['user_id', 'first_name', 'last_name', 'email']
    ordering = ['user_id']
    fieldsets = (
        (None, {'fields': ('user_id', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar')}),
        ('Role & Status', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Gamification', {'fields': ('points', 'study_streak', 'last_study_date')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('user_id', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'description', 'timestamp']
    list_filter = ['action']
    search_fields = ['user__user_id', 'action']
    readonly_fields = ['timestamp']


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'reason', 'created_at']
    readonly_fields = ['created_at']
