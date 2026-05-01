"""Analytics & Dashboard views"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from apps.accounts.models import User, ActivityLog
from apps.chatbot.models import ChatMessage, ChatSession
from apps.notifications.models import Notification, Event


@login_required
def dashboard_view(request):
    """Main dashboard - role-based content"""
    user = request.user
    context = {'user': user}

    if user.is_student:
        context.update(_student_dashboard_data(user))
    elif user.is_staff_member:
        context.update(_staff_dashboard_data(user))
    elif user.is_admin:
        context.update(_admin_dashboard_data())

    # Common data
    context['unread_notifications'] = Notification.objects.filter(
        user=user, is_read=False
    ).count()
    context['upcoming_events'] = Event.objects.filter(
        date__gte=timezone.now().date()
    ).order_by('date')[:3]

    return render(request, 'analytics/dashboard.html', context)


def _student_dashboard_data(user):
    """Dashboard data for students"""
    defaults = {
        'profile': None,
        'today_classes': [],
        'pending_tasks': 0,
        'overdue_count': 0,
        'gpa': '0.00',
        'points': user.points,
        'streak': user.study_streak,
    }
    try:
        profile = user.student_profile
        from apps.students.models import Timetable
        today = timezone.now().strftime('%A')[:3].upper()
        registered = profile.registrations.filter(is_active=True).values_list('course_id', flat=True)
        today_classes = list(Timetable.objects.filter(
            course_id__in=registered, day=today,
            academic_year=profile.academic_year,
        ).select_related('course').order_by('start_time'))

        from apps.planner.models import Task
        all_pending = Task.objects.filter(user=user, is_completed=False)
        pending_tasks = all_pending.count()
        overdue_count = sum(1 for t in all_pending if t.is_overdue)

        defaults.update({
            'profile': profile,
            'today_classes': today_classes,
            'pending_tasks': pending_tasks,
            'overdue_count': overdue_count,
            'gpa': profile.cumulative_gpa,
        })
    except Exception:
        pass
    return defaults


def _staff_dashboard_data(user):
    """Dashboard data for staff"""
    try:
        profile = user.staff_profile
        return {
            'staff_profile': profile,
            'courses_count': profile.courses_assigned.count(),
        }
    except Exception:
        return {}


def _admin_dashboard_data():
    """Dashboard data for admins"""
    from datetime import timedelta
    from django.db.models import Count
    from apps.students.models import StudentProfile, Result
    from apps.chatbot.models import ChatFeedback

    today = timezone.now().date()

    total_students = User.objects.filter(role='student', is_active=True).count()
    total_staff = User.objects.filter(role='staff', is_active=True).count()
    total_chats = ChatMessage.objects.count()
    active_sessions = ChatSession.objects.filter(is_active=True).count()
    total_users = User.objects.filter(is_active=True).count()

    # New users this week
    week_ago = today - timedelta(days=7)
    new_users_week = User.objects.filter(date_joined__date__gte=week_ago).count()

    # Chat messages today
    chats_today = ChatMessage.objects.filter(timestamp__date=today, sender='user').count()

    # AI feedback stats
    good_feedback = ChatFeedback.objects.filter(rating=3).count()
    bad_feedback = ChatFeedback.objects.filter(rating=1).count()
    total_feedback = good_feedback + bad_feedback
    satisfaction = round((good_feedback / total_feedback * 100) if total_feedback else 0)

    # Recent users
    recent_users = User.objects.filter(is_active=True).order_by('-date_joined')[:8]

    # Recent activity
    recent_activity = ActivityLog.objects.select_related('user').order_by('-timestamp')[:12]

    # Top chatters
    top_chatters = ChatMessage.objects.filter(sender='user').values(
        'session__user__first_name', 'session__user__last_name',
        'session__user__user_id', 'session__user__role'
    ).annotate(msg_count=Count('id')).order_by('-msg_count')[:5]

    # Chat usage last 7 days
    chat_labels, chat_data = [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = ChatMessage.objects.filter(timestamp__date=day, sender='user').count()
        chat_labels.append(day.strftime('%b %d'))
        chat_data.append(count)

    # User role breakdown
    role_counts = {
        'students': total_students,
        'staff': total_staff,
        'admins': User.objects.filter(role='admin').count(),
    }

    # Unread notifications count
    total_unread_notifs = Notification.objects.filter(is_read=False).count()

    return {
        'total_students': total_students,
        'total_staff': total_staff,
        'total_chats': total_chats,
        'active_sessions': active_sessions,
        'total_users': total_users,
        'new_users_week': new_users_week,
        'chats_today': chats_today,
        'satisfaction': satisfaction,
        'good_feedback': good_feedback,
        'bad_feedback': bad_feedback,
        'recent_users': recent_users,
        'recent_activity': recent_activity,
        'top_chatters': top_chatters,
        'chat_labels': chat_labels,
        'chat_data': chat_data,
        'role_counts': role_counts,
        'total_unread_notifs': total_unread_notifs,
    }


@login_required
def analytics_api_view(request):
    """API: Analytics data for charts"""
    if not request.user.is_admin:
        return JsonResponse({'error': 'Admin only'}, status=403)

    # Chat usage over last 7 days
    from datetime import timedelta
    today = timezone.now().date()
    labels = []
    chat_counts = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = ChatMessage.objects.filter(
            timestamp__date=day, sender='user'
        ).count()
        labels.append(day.strftime('%b %d'))
        chat_counts.append(count)

    # User role distribution
    role_data = {
        'students': User.objects.filter(role='student').count(),
        'staff': User.objects.filter(role='staff').count(),
        'admins': User.objects.filter(role='admin').count(),
    }

    return JsonResponse({
        'chat_usage': {'labels': labels, 'data': chat_counts},
        'user_roles': role_data,
    })
