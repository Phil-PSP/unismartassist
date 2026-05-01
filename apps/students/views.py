"""Student views - results, GPA, timetable, documents"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import StudentProfile, Result, GPARecord, Timetable, Course, Document
from .forms import DocumentUploadForm
from .services import DocumentProcessor, GPAAnalyzer


def student_required(view_func):
    """Decorator: only students can access"""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_student:
            messages.error(request, 'Access denied. Students only.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@student_required
def results_view(request):
    """View student results per semester"""
    profile = get_object_or_404(StudentProfile, user=request.user)
    results = Result.objects.filter(student=profile).select_related('course')
    # Group by academic year and semester
    grouped = {}
    for r in results:
        key = f"{r.academic_year} - Semester {r.semester}"
        grouped.setdefault(key, []).append(r)

    gpa_records = GPARecord.objects.filter(student=profile)
    context = {
        'profile': profile,
        'grouped_results': grouped,
        'gpa_records': gpa_records,
        'cumulative_gpa': profile.cumulative_gpa,
    }
    return render(request, 'students/results.html', context)


@student_required
def timetable_view(request):
    """View class and exam timetable"""
    profile = get_object_or_404(StudentProfile, user=request.user)
    # Get courses the student is registered for
    registered_courses = profile.registrations.filter(
        is_active=True,
        academic_year=profile.academic_year,
        semester=profile.semester,
    ).values_list('course_id', flat=True)

    timetable = Timetable.objects.filter(
        course_id__in=registered_courses,
        academic_year=profile.academic_year,
        semester=profile.semester,
    ).select_related('course')

    # Organize by day
    days_order = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
    schedule = {day: [] for day in days_order}
    for entry in timetable:
        schedule[entry.day].append(entry)

    context = {
        'schedule': schedule,
        'days_order': days_order,
        'profile': profile,
    }
    return render(request, 'students/timetable.html', context)


@student_required
def gpa_dashboard_view(request):
    """GPA trends and academic insights"""
    profile = get_object_or_404(StudentProfile, user=request.user)
    analyzer = GPAAnalyzer(profile)
    context = {
        'profile': profile,
        'gpa_trend': analyzer.get_trend_data(),
        'weak_subjects': analyzer.get_weak_subjects(),
        'strong_subjects': analyzer.get_strong_subjects(),
        'improvement_tips': analyzer.get_improvement_tips(),
        'performance_by_course': analyzer.get_performance_by_course(),
    }
    return render(request, 'students/gpa_dashboard.html', context)


@student_required
def documents_view(request):
    """Upload and manage documents"""
    profile = get_object_or_404(StudentProfile, user=request.user)
    form = DocumentUploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.student = profile
        doc.file_type = doc.file.name.split('.')[-1].lower()
        doc.save()
        # Process document (synchronously if Celery not available)
        from .tasks import process_document
        try:
            process_document.delay(doc.id)
        except AttributeError:
            process_document(doc.id)
        messages.success(request, 'Document uploaded. Processing in background...')
        request.user.add_points(5, 'Document uploaded')
        return redirect('documents')

    documents = Document.objects.filter(student=profile)
    return render(request, 'students/documents.html', {'form': form, 'documents': documents})


@student_required
def document_detail_view(request, doc_id):
    """View document summary and key points"""
    profile = get_object_or_404(StudentProfile, user=request.user)
    doc = get_object_or_404(Document, id=doc_id, student=profile)
    return render(request, 'students/document_detail.html', {'doc': doc})


@login_required
def api_gpa_trend(request):
    """API: GPA trend data for charts"""
    if not request.user.is_student:
        return JsonResponse({'error': 'Students only'}, status=403)
    profile = get_object_or_404(StudentProfile, user=request.user)
    records = GPARecord.objects.filter(student=profile).order_by('academic_year', 'semester')
    data = {
        'labels': [f"{r.academic_year} S{r.semester}" for r in records],
        'values': [float(r.gpa) for r in records],
    }
    return JsonResponse(data)


@login_required
def api_today_schedule(request):
    """API: Today's class schedule"""
    if not request.user.is_student:
        return JsonResponse({'schedule': []})
    profile = get_object_or_404(StudentProfile, user=request.user)
    today = timezone.now().strftime('%A')[:3].upper()
    registered = profile.registrations.filter(is_active=True).values_list('course_id', flat=True)
    entries = Timetable.objects.filter(
        course_id__in=registered, day=today,
        academic_year=profile.academic_year,
    ).select_related('course').order_by('start_time')
    data = [{
        'course': e.course.name,
        'code': e.course.code,
        'start': e.start_time.strftime('%H:%M'),
        'end': e.end_time.strftime('%H:%M'),
        'venue': e.venue,
        'type': e.entry_type,
    } for e in entries]
    return JsonResponse({'schedule': data})
