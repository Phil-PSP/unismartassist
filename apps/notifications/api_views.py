from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Notification, Event


class NotificationsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
        data = [{
            'id': n.id, 'title': n.title, 'message': n.message,
            'type': n.notification_type, 'is_read': n.is_read,
            'created_at': n.created_at.isoformat(),
        } for n in notifs]
        return Response({'notifications': data, 'unread': sum(1 for n in notifs if not n.is_read)})


class EventsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.filter(date__gte=timezone.now().date()).order_by('date')[:10]
        data = [{
            'id': e.id, 'title': e.title, 'date': str(e.date),
            'type': e.event_type, 'location': e.location,
        } for e in events]
        return Response({'events': data})
