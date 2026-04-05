"""Context processor to inject recent chat sessions into every template."""


def chat_sessions(request):
    if not request.user.is_authenticated:
        return {}
    try:
        from .models import ChatSession
        sessions = ChatSession.objects.filter(
            user=request.user
        ).order_by('-last_activity')[:8]
        return {'chat_sessions': sessions}
    except Exception:
        return {'chat_sessions': []}


def admin_nav(request):
    """Inject admin nav items for the sidebar."""
    if not request.user.is_authenticated or not request.user.is_admin:
        return {}
    return {
        'admin_nav_items': [
            ('admin_users',       'Users',        '👥'),
            ('admin_add_user',    'Add User',     '➕'),
            ('admin_announcements','Announcements','📢'),
            ('admin_results',     'Results',      '📊'),
            ('admin_groups',      'Groups',       '🏫'),
            ('admin_group_chats', 'Group Chats',  '💬'),
            ('admin_programmes',  'Programmes',   '🎓'),
            ('admin_batches',     'Batches',      '📋'),
            ('admin_levels',      'Levels',       '📈'),
            ('admin_events',      'Events',       '📅'),
        ]
    }
