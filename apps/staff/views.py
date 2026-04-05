"""Staff views"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import StaffProfile, WorkPlan
from apps.students.models import Course, Result, StudentProfile


def staff_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_staff_member or request.user.is_admin):
            messages.error(request, 'Access denied. Staff only.')
            from django.shortcuts import redirect
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@staff_required
def staff_dashboard_view(request):
    """Staff dashboard"""
    profile = get_object_or_404(StaffProfile, user=request.user)
    courses = profile.courses_assigned.all()
    workplans = WorkPlan.objects.filter(staff=profile).order_by('-week_start')[:5]
    context = {
        'profile': profile,
        'courses': courses,
        'workplans': workplans,
    }
    return render(request, 'staff/dashboard.html', context)


@staff_required
def student_performance_view(request):
    """View student performance for assigned courses"""
    profile = get_object_or_404(StaffProfile, user=request.user)
    courses = profile.courses_assigned.all()
    performance_data = []
    for course in courses:
        results = Result.objects.filter(course=course).select_related('student__user')
        avg_score = sum(float(r.score or 0) for r in results) / max(len(results), 1)
        performance_data.append({
            'course': course,
            'results': results,
            'avg_score': round(avg_score, 2),
            'total_students': results.count(),
        })
    return render(request, 'staff/student_performance.html', {'performance_data': performance_data})
