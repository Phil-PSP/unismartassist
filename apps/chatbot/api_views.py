from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ChatSession, ChatMessage
from .nlp_engine import ChatbotEngine


class ChatAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = 'chat'
    MAX_MESSAGE_LENGTH = 4000

    def post(self, request):
        message = request.data.get('message', '')
        session_id = request.data.get('session_id')
        if not isinstance(message, str):
            return Response({'error': 'Message must be text.'}, status=400)
        message = message.strip()
        if not message:
            return Response({'error': 'Message required'}, status=400)
        if len(message) > self.MAX_MESSAGE_LENGTH:
            return Response({'error': 'Message is too long.'}, status=413)

        if session_id and not isinstance(session_id, str):
            return Response({'error': 'Invalid session ID.'}, status=400)
        if session_id:
            try:
                session = ChatSession.objects.filter(id=session_id, user=request.user).first()
            except (TypeError, ValueError):
                return Response({'error': 'Invalid session ID.'}, status=400)
        else:
            session = ChatSession.objects.filter(user=request.user, is_active=True).first()
        if not session:
            session = ChatSession.objects.create(user=request.user)

        ChatMessage.objects.create(session=session, sender='user', message=message)
        engine = ChatbotEngine(request.user)
        result = engine.process(message, session.context)
        session.context['last_intent'] = result.get('intent')
        session.save()
        bot_msg = ChatMessage.objects.create(
            session=session, sender='bot',
            message=result['response'],
            intent=result.get('intent', ''),
            confidence=result.get('confidence', 0.0),
        )
        return Response({
            'response': result['response'],
            'intent': result.get('intent'),
            'session_id': session.id,
            'message_id': bot_msg.id,
        })


class ChatHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session_id = request.query_params.get('session_id')
        if session_id:
            try:
                messages = ChatMessage.objects.filter(
                    session_id=session_id, session__user=request.user
                ).order_by('timestamp')
            except (TypeError, ValueError):
                return Response({'error': 'Invalid session ID.'}, status=400)
        else:
            session = ChatSession.objects.filter(user=request.user, is_active=True).first()
            messages = ChatMessage.objects.filter(session=session).order_by('timestamp') if session else []
        data = [{'sender': m.sender, 'message': m.message, 'timestamp': m.timestamp} for m in messages]
        return Response({'messages': data})
