"""Celery tasks for notifications, proactive nudges, and at-risk alerts"""
try:
    from celery import shared_task
except ImportError:
    # Celery not installed — create a no-op decorator so tasks can still be called directly
    def shared_task(func=None, **kwargs):
        if func is not None:
            return func
        def decorator(f):
            return f
        return decorator

from django.utils import timezone
import random


# ── Existing tasks ─────────────────────────────────────────────────────────────

@shared_task
def send_class_reminders():
    """Send reminders for classes starting in the next hour"""
    from apps.students.models import Timetable
    from .models import Notification

    now = timezone.now()
    one_hour_later = (now + timezone.timedelta(hours=1)).time()
    today = now.strftime('%A')[:3].upper()

    entries = Timetable.objects.filter(
        day=today, start_time__lte=one_hour_later, start_time__gt=now.time(),
    ).select_related('course')

    for entry in entries:
        for reg in entry.course.courseregistration_set.filter(is_active=True):
            Notification.objects.create(
                user=reg.student.user,
                title=f"Class Reminder: {entry.course.name}",
                message=f"Your {entry.course.name} class starts at {entry.start_time.strftime('%H:%M')} in {entry.venue}.",
                notification_type='class',
            )


@shared_task
def check_assignment_deadlines():
    """Alert students about upcoming assignment deadlines"""
    from apps.planner.models import Task
    from .models import Notification

    tomorrow = timezone.now().date() + timezone.timedelta(days=1)
    tasks = Task.objects.filter(
        due_date=tomorrow, is_completed=False, task_type='assignment',
    ).select_related('user')

    for task in tasks:
        Notification.objects.create(
            user=task.user,
            title=f"Assignment Due Tomorrow: {task.title}",
            message=f"Don't forget! '{task.title}' is due tomorrow.",
            notification_type='assignment',
        )


@shared_task
def send_daily_motivation():
    """Send daily motivational messages to all active students"""
    from apps.accounts.models import User
    from .models import Notification

    quotes = [
        "Every day is a new opportunity to learn something new. Make it count!",
        "Success is the sum of small efforts repeated day in and day out.",
        "The harder you work for something, the greater you'll feel when you achieve it.",
        "Don't stop when you're tired. Stop when you're done.",
        "Your future is created by what you do today, not tomorrow.",
        "Education is the passport to the future. — Malcolm X",
        "The beautiful thing about learning is that no one can take it away from you.",
        "Push yourself, because no one else is going to do it for you.",
    ]

    students = User.objects.filter(role='student', is_active=True)
    quote = random.choice(quotes)
    for student in students:
        Notification.objects.create(
            user=student, title="Daily Motivation 💪",
            message=quote, notification_type='motivation',
        )


@shared_task
def send_notification(user_id, title, message, notification_type='system'):
    """Generic task to send a notification to a user"""
    from apps.accounts.models import User
    from .models import Notification
    try:
        user = User.objects.get(id=user_id)
        Notification.objects.create(
            user=user, title=title, message=message,
            notification_type=notification_type,
        )
    except User.DoesNotExist:
        pass


# ── New proactive tasks ────────────────────────────────────────────────────────

@shared_task
def send_morning_briefing():
    """Send a morning briefing notification to all active students."""
    from apps.accounts.models import User
    from apps.students.models import Timetable
    from apps.planner.models import Task
    from .models import Notification, Event

    now = timezone.now()
    today = now.strftime('%A')[:3].upper()
    today_date = now.date()

    students = User.objects.filter(role='student', is_active=True).select_related('student_profile')
    for student in students:
        try:
            profile = student.student_profile
            registered = profile.registrations.filter(is_active=True).values_list('course_id', flat=True)
            classes = Timetable.objects.filter(
                course_id__in=registered, day=today,
                academic_year=profile.academic_year,
            ).count()
            pending = Task.objects.filter(user=student, is_completed=False).count()
            overdue = Task.objects.filter(
                user=student, is_completed=False, due_date__lt=today_date
            ).count()

            parts = []
            if classes:
                parts.append(f"📅 {classes} class{'es' if classes > 1 else ''} today")
            if overdue:
                parts.append(f"⚠️ {overdue} overdue task{'s' if overdue > 1 else ''}")
            elif pending:
                parts.append(f"✅ {pending} pending task{'s' if pending > 1 else ''}")

            msg = "Good morning! " + (" | ".join(parts) if parts else "Have a great day!") + " 💪"
            Notification.objects.create(
                user=student, title="☀️ Morning Briefing",
                message=msg, notification_type='system',
            )
        except Exception:
            continue


@shared_task
def check_at_risk_students():
    """Flag students with low GPA and notify their lecturers."""
    from apps.accounts.models import User
    from apps.students.models import StudentProfile
    from apps.staff.models import StaffProfile
    from .models import Notification

    at_risk = StudentProfile.objects.filter(
        cumulative_gpa__lt=2.0, user__is_active=True
    ).select_related('user', 'programme')

    for profile in at_risk:
        # Notify the student
        Notification.objects.get_or_create(
            user=profile.user,
            title="⚠️ Academic Alert",
            defaults={
                'message': (
                    f"Your current GPA is {profile.cumulative_gpa}, which is below the minimum of 2.0. "
                    f"Please speak with your academic adviser or visit the Student Affairs Office for support."
                ),
                'notification_type': 'system',
            }
        )

        # Notify staff assigned to this student's courses
        course_ids = profile.registrations.filter(is_active=True).values_list('course_id', flat=True)
        staff_profiles = StaffProfile.objects.filter(courses_assigned__in=course_ids).distinct()
        for sp in staff_profiles:
            Notification.objects.create(
                user=sp.user,
                title=f"⚠️ At-Risk Student: {profile.user.user_id}",
                message=(
                    f"{profile.user.get_full_name()} (Level {profile.level}) has a GPA of {profile.cumulative_gpa}. "
                    f"Consider reaching out to provide academic support."
                ),
                notification_type='system',
            )


@shared_task
def send_grade_submission_reminders():
    """Remind staff to submit grades before deadline."""
    from apps.accounts.models import User
    from .models import Notification

    # Send reminder to all staff 3 days before end of semester (simplified: send weekly)
    staff = User.objects.filter(role='staff', is_active=True)
    for s in staff:
        Notification.objects.create(
            user=s,
            title="📝 Grade Submission Reminder",
            message="Please ensure all student grades are submitted before the deadline. Log in to the Staff Dashboard to update grades.",
            notification_type='system',
        )


@shared_task
def check_leaderboard_shoutouts():
    """Send shoutout notifications for leaderboard milestones."""
    from apps.accounts.models import User, PointTransaction
    from .models import Notification

    milestones = [100, 250, 500, 1000, 2000]
    students = User.objects.filter(role='student', is_active=True)

    for student in students:
        for milestone in milestones:
            if student.points >= milestone:
                # Check if we already sent this milestone notification
                already_sent = Notification.objects.filter(
                    user=student,
                    title__contains=f"{milestone} points"
                ).exists()
                if not already_sent:
                    rank = User.objects.filter(
                        role='student', is_active=True, points__gt=student.points
                    ).count() + 1
                    Notification.objects.create(
                        user=student,
                        title=f"🏆 Milestone: {milestone} Points!",
                        message=(
                            f"Congratulations {student.first_name}! You've reached {milestone} points. "
                            f"You're currently ranked #{rank} on the leaderboard. Keep it up! 🔥"
                        ),
                        notification_type='motivation',
                    )


@shared_task
def update_all_user_memories():
    """Periodically update AI memory for all active students."""
    from apps.accounts.models import User
    from apps.chatbot.nlp_engine import update_user_memory

    students = User.objects.filter(role='student', is_active=True)
    for student in students:
        try:
            update_user_memory(student, None)
        except Exception:
            continue


@shared_task
def send_exam_countdown_alerts():
    """Alert students 7 days and 1 day before exams."""
    from .models import Event, Notification
    from apps.accounts.models import User

    today = timezone.now().date()
    for days_ahead in [7, 1]:
        target_date = today + timezone.timedelta(days=days_ahead)
        exams = Event.objects.filter(event_type='exam', date=target_date)
        for exam in exams:
            students = User.objects.filter(role='student', is_active=True)
            for student in students:
                label = "tomorrow" if days_ahead == 1 else "in 7 days"
                Notification.objects.create(
                    user=student,
                    title=f"⏳ Exam {label}: {exam.title}",
                    message=f"{exam.title} is {label} ({exam.date.strftime('%B %d')}). Location: {exam.location or 'TBA'}. Good luck! 📚",
                    notification_type='exam',
                )
