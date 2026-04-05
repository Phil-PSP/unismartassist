"""Notifications views"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Notification, Event, Announcement


@login_required
def notifications_view(request):
    """All notifications for the user"""
    notifications = Notification.objects.filter(user=request.user)
    events = Event.objects.filter(is_public=True).order_by('date')[:10]
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:5]
    context = {
        'notifications': notifications,
        'events': events,
        'announcements': announcements,
        'unread_count': notifications.filter(is_read=False).count(),
    }
    return render(request, 'notifications/notifications.html', context)


@login_required
@require_POST
def mark_read_view(request, notif_id):
    """Mark a notification as read"""
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.mark_read()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def mark_all_read_view(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})


@login_required
def unread_count_view(request):
    """API: Get unread notification count"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})
