"""ASGI config for KAAF - supports HTTP and WebSocket"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import apps.chatbot.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kaaf.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(apps.chatbot.routing.websocket_urlpatterns)
        )
    ),
})
