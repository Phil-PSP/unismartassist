"""
Chatbot Models - Chat sessions, messages, feedback
"""
from django.db import models
from apps.accounts.models import User


class ChatSession(models.Model):
    """A conversation session"""
    MODES = [
        ('academic', 'Academic Mode'),
        ('motivation', 'Motivation Mode'),
        ('mental_health', 'Mental Health Mode'),
        ('productivity', 'Productivity Mode'),
        ('general', 'General Mode'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    mode = models.CharField(max_length=20, choices=MODES, default='general')
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    context = models.JSONField(default=dict)  # Store conversation context

    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.user.user_id} - Session {self.id}"


class ChatMessage(models.Model):
    """Individual chat messages"""
    SENDER_CHOICES = [('user', 'User'), ('bot', 'Bot')]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=5, choices=SENDER_CHOICES)
    message = models.TextField()
    intent = models.CharField(max_length=50, blank=True)
    confidence = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.sender}] {self.message[:50]}"


class ChatFeedback(models.Model):
    """User feedback on bot responses"""
    RATING_CHOICES = [(1, '👎 Bad'), (2, '😐 Okay'), (3, '👍 Good')]

    message = models.OneToOneField(ChatMessage, on_delete=models.CASCADE, related_name='feedback')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_feedback'

    def __str__(self):
        return f"Feedback {self.rating} for message {self.message.id}"


class GroupChat(models.Model):
    """Admin-created group chats for classes/cohorts"""
    TYPE_CHOICES = [
        ('class', 'Class Group'),
        ('programme', 'Programme Group'),
        ('level', 'Level Group'),
        ('batch', 'Batch Group'),
        ('general', 'General'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    chat_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='class')
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_groups'
    )
    members = models.ManyToManyField(
        'accounts.User', related_name='group_chats', blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional filters for auto-membership
    programme = models.ForeignKey(
        'students.Programme', on_delete=models.SET_NULL, null=True, blank=True
    )
    level = models.IntegerField(null=True, blank=True)
    academic_year = models.CharField(max_length=9, blank=True)

    class Meta:
        db_table = 'group_chats'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def auto_add_members(self):
        """Auto-add students matching programme/level/year filters."""
        from apps.students.models import StudentProfile
        from apps.accounts.models import User
        qs = StudentProfile.objects.filter(user__is_active=True)
        if self.programme:
            qs = qs.filter(programme=self.programme)
        if self.level:
            qs = qs.filter(level=self.level)
        if self.academic_year:
            qs = qs.filter(academic_year=self.academic_year)
        user_ids = qs.values_list('user_id', flat=True)
        self.members.add(*User.objects.filter(id__in=user_ids))
        return self.members.count()


class GroupMessage(models.Model):
    """Messages within a group chat"""
    group = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='group_messages'
    )
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_pinned = models.BooleanField(default=False)

    class Meta:
        db_table = 'group_messages'
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.group.name}] {self.sender.user_id}: {self.message[:50]}"
