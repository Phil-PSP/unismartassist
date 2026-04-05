"""
WebSocket Consumer for real-time chat
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    """Handles WebSocket connections for the chatbot"""

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_name = f"chat_{self.user.id}"
        self._session_id = None  # Will be set by init message
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()
        # No welcome message here — the template handles the greeting

    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        """Handle incoming message from WebSocket"""
        try:
            data = json.loads(text_data)
            msg_type = data.get('type', 'message')
            message = data.get('message', '').strip()
            session_id = data.get('session_id')

            # Init message — just sets the session, no response needed
            if msg_type == 'init':
                self._session_id = session_id
                return

            if not message:
                return

            # Use session_id from init or from this message
            effective_session_id = session_id or getattr(self, '_session_id', None)

            # Echo user message back
            await self.send(text_data=json.dumps({
                'type': 'user_message',
                'message': message,
                'timestamp': timezone.now().isoformat(),
            }))

            # Process with chatbot engine
            response_data = await self.process_message(message, effective_session_id)

            # Send bot response
            await self.send(text_data=json.dumps({
                'type': 'bot_message',
                'message': response_data['response'],
                'intent': response_data.get('intent', ''),
                'mode': response_data.get('mode', 'general'),
                'message_id': response_data.get('message_id'),
                'timestamp': timezone.now().isoformat(),
            }))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format.',
            }))

    @database_sync_to_async
    def process_message(self, message, session_id=None):
        """Process message synchronously in thread pool"""
        from .nlp_engine import ChatbotEngine
        from .models import ChatSession, ChatMessage

        # Strictly use the provided session_id — never fall back to a random one
        session = None
        if session_id:
            session = ChatSession.objects.filter(id=session_id, user=self.user).first()

        if not session:
            # Create a new session only if none was found
            session = ChatSession.objects.create(user=self.user)

        # Save user message
        ChatMessage.objects.create(session=session, sender='user', message=message)

        # Run chatbot engine
        engine = ChatbotEngine(self.user, session=session)
        result = engine.process(message, session.context)

        # Update session context
        session.context['last_intent'] = result.get('intent')
        session.context['last_message'] = message
        if result.get('mode'):
            session.mode = result['mode']
        session.save()

        # Save bot response
        bot_msg = ChatMessage.objects.create(
            session=session,
            sender='bot',
            message=result['response'],
            intent=result.get('intent', ''),
            confidence=result.get('confidence', 0.0),
        )

        self.user.add_points(1, 'Chatbot interaction')
        result['message_id'] = bot_msg.id
        result['session_id'] = session.id
        return result

    async def chat_message(self, event):
        """Handle messages sent to the group"""
        await self.send(text_data=json.dumps(event))
