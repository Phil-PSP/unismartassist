from django.urls import path
from . import views

urlpatterns = [
    path('', views.overview_view, name='admin_overview'),
    path('announcements/', views.announcements_view, name='admin_announcements'),
    path('announcements/<int:ann_id>/delete/', views.delete_announcement_view, name='admin_delete_announcement'),
    path('announcements/<int:ann_id>/toggle/', views.toggle_announcement_view, name='admin_toggle_announcement'),
    path('users/', views.users_view, name='admin_users'),
    path('users/add/', views.add_user_view, name='admin_add_user'),
    path('users/<int:user_id>/toggle/', views.toggle_user_view, name='admin_toggle_user'),
    path('users/<int:user_id>/reset-password/', views.reset_password_view, name='admin_reset_password'),
    path('results/', views.results_view, name='admin_results'),
    path('results/upload/', views.upload_result_view, name='admin_upload_result'),
    path('results/bulk-upload/', views.bulk_upload_results_view, name='admin_bulk_upload'),
    path('groups/', views.groups_view, name='admin_groups'),
    path('groups/notify/', views.send_group_notification_view, name='admin_group_notify'),
    path('events/', views.events_view, name='admin_events'),
    path('events/<int:event_id>/delete/', views.delete_event_view, name='admin_delete_event'),
    # New
    path('programmes/', views.programmes_view, name='admin_programmes'),
    path('batches/', views.batches_view, name='admin_batches'),
    path('levels/', views.levels_view, name='admin_levels'),
    path('group-chats/', views.group_chats_view, name='admin_group_chats'),
    path('group-chats/<int:group_id>/message/', views.send_group_chat_message_view, name='admin_group_chat_message'),
    path('import-students/', views.import_students_view, name='admin_import_students'),
]
