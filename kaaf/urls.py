"""KAAF University Chatbot - URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('offline/', TemplateView.as_view(template_name='offline.html'), name='offline'),
    path('accounts/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.analytics.urls')),
    path('students/', include('apps.students.urls')),
    path('staff/', include('apps.staff.urls')),
    path('chatbot/', include('apps.chatbot.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('planner/', include('apps.planner.urls')),
    path('manage/', include('apps.management.urls')),
    # REST API
    path('api/accounts/', include('apps.accounts.api_urls')),
    path('api/students/', include('apps.students.api_urls')),
    path('api/chatbot/', include('apps.chatbot.api_urls')),
    path('api/notifications/', include('apps.notifications.api_urls')),
    path('api/planner/', include('apps.planner.api_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
