"""Planner views - tasks, study timer"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
import json
from .models import Task, StudySession
from .forms import TaskForm


@login_required
def planner_view(request):
    """Main planner page"""
    tasks = Task.objects.filter(user=request.user)
    pending = tasks.filter(is_completed=False).order_by('due_date', 'priority')
    completed = tasks.filter(is_completed=True).order_by('-completed_at')[:10]
    overdue = [t for t in pending if t.is_overdue]

    context = {
        'pending_tasks': pending,
        'completed_tasks': completed,
        'overdue_tasks': overdue,
        'total_points': request.user.points,
        'streak': request.user.study_streak,
    }
    return render(request, 'planner/planner.html', context)


@login_required
def add_task_view(request):
    """Add a new task"""
    form = TaskForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.user = request.user
        task.save()
        messages.success(request, 'Task added successfully!')
        return redirect('planner')
    return render(request, 'planner/add_task.html', {'form': form})


@login_required
@require_POST
def complete_task_view(request, task_id):
    """Mark task as complete"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.complete()
    return JsonResponse({
        'status': 'ok',
        'points_earned': task.points_reward,
        'total_points': request.user.points,
        'streak': request.user.study_streak,
    })


@login_required
@require_POST
def delete_task_view(request, task_id):
    """Delete a task"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return JsonResponse({'status': 'ok'})


@login_required
def study_timer_view(request):
    """Study timer / Pomodoro page"""
    recent_sessions = StudySession.objects.filter(user=request.user, completed=True)[:10]
    total_minutes = sum(s.duration_minutes for s in recent_sessions)
    context = {
        'recent_sessions': recent_sessions,
        'total_study_minutes': total_minutes,
        'streak': request.user.study_streak,
    }
    return render(request, 'planner/study_timer.html', context)


@login_required
@require_POST
def start_session_view(request):
    """Start a study session"""
    try:
        data = json.loads(request.body)
        session = StudySession.objects.create(
            user=request.user,
            subject=data.get('subject', ''),
            duration_minutes=data.get('duration', 25),
        )
        return JsonResponse({'session_id': session.id, 'status': 'started'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def finish_session_view(request, session_id):
    """Finish a study session"""
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    session.finish()
    return JsonResponse({
        'status': 'ok',
        'points_earned': max(5, session.duration_minutes // 5),
        'total_points': request.user.points,
    })
