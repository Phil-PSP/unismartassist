"""Chatbot views"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .models import ChatSession, ChatMessage, ChatFeedback
from .nlp_engine import ChatbotEngine


@login_required
def chat_view(request):
    """Main chat interface"""
    session_id = request.GET.get('session')

    if session_id:
        session = ChatSession.objects.filter(id=session_id, user=request.user).first()
        if not session:
            session = ChatSession.objects.create(user=request.user)
        messages = ChatMessage.objects.filter(session=session).order_by('timestamp')[:50]
    else:
        # Always start fresh — create a new session
        session = ChatSession.objects.create(user=request.user)
        messages = []

    # Role-aware starter prompts
    user = request.user
    if user.is_student:
        starter_prompts = [
            {'icon': '📊', 'label': 'What is my GPA?', 'text': 'What is my GPA?'},
            {'icon': '📅', 'label': 'Show my timetable', 'text': 'Show my timetable'},
            {'icon': '🎓', 'label': 'Scholarship info', 'text': 'Scholarship information'},
            {'icon': '💪', 'label': 'Motivate me', 'text': 'Motivate me'},
        ]
    elif user.is_staff_member:
        starter_prompts = [
            {'icon': '👨‍🏫', 'label': 'My profile', 'text': 'My staff profile'},
            {'icon': '📊', 'label': 'Student performance', 'text': 'Student performance tips'},
            {'icon': '💡', 'label': 'Study tips', 'text': 'Study tips for students'},
            {'icon': '📅', 'label': 'Upcoming events', 'text': 'Upcoming events'},
        ]
    else:
        starter_prompts = [
            {'icon': '📊', 'label': 'System overview', 'text': 'What can you do?'},
            {'icon': '📅', 'label': 'Upcoming events', 'text': 'Upcoming events'},
            {'icon': '📋', 'label': 'Help', 'text': 'help'},
            {'icon': '📞', 'label': 'Contacts', 'text': 'Contact details'},
        ]

    context = {
        'session': session,
        'messages': messages,
        'session_id': session.id,
        'starter_prompts': starter_prompts,
    }
    return render(request, 'chatbot/chat.html', context)


@login_required
@require_POST
def send_message_view(request):
    """HTTP fallback for chat (non-WebSocket)"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not message:
        return JsonResponse({'error': 'Empty message'}, status=400)

    # Get session
    if session_id:
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    else:
        session = ChatSession.objects.filter(user=request.user, is_active=True).first()
        if not session:
            session = ChatSession.objects.create(user=request.user)

    # Save user message
    ChatMessage.objects.create(session=session, sender='user', message=message)

    # Process
    # FORCE ONLINE MODE FOR NGROK - Remove this line to restore offline detection
    offline = False  # data.get('offline', False)
    engine = ChatbotEngine(request.user, session=session, offline=offline)
    result = engine.process(message, session.context)

    # Update session
    session.context['last_intent'] = result.get('intent')
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

    request.user.add_points(1, 'Chatbot interaction')

    return JsonResponse({
        'response': result['response'],
        'intent': result.get('intent'),
        'mode': result.get('mode', 'general'),
        'message_id': bot_msg.id,
        'session_id': session.id,
    })


@login_required
@require_POST
def feedback_view(request):
    """Submit feedback for a bot message"""
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        rating = data.get('rating')
        comment = data.get('comment', '')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    msg = get_object_or_404(ChatMessage, id=message_id, session__user=request.user, sender='bot')
    ChatFeedback.objects.update_or_create(
        message=msg,
        defaults={'rating': rating, 'comment': comment}
    )
    return JsonResponse({'status': 'ok'})


@login_required
def chat_history_view(request):
    """View chat history"""
    sessions = ChatSession.objects.filter(user=request.user).order_by('-last_activity')[:10]
    return render(request, 'chatbot/history.html', {'sessions': sessions})


@login_required
def new_session_view(request):
    """Start a new chat session"""
    session = ChatSession.objects.create(user=request.user)
    return JsonResponse({'session_id': session.id})


@login_required
@require_POST
def delete_session_view(request, session_id):
    """Delete a single chat session and all its messages"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.delete()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def delete_all_sessions_view(request):
    """Delete all chat sessions for the current user"""
    ChatSession.objects.filter(user=request.user).delete()
    return JsonResponse({'status': 'ok'})
