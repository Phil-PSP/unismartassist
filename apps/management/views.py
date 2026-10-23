"""Admin Management Views — Announcements, Users, Results, Groups"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
import json, csv
from io import TextIOWrapper

from apps.accounts.models import User
from apps.notifications.models import Notification, Announcement, Event
from apps.students.models import (
    StudentProfile, Course, Result, Department,
    Programme, CourseRegistration, GPARecord
)


def admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'admin':
            messages.error(request, 'Admin access required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Overview ──────────────────────────────────────────────────────────────────

@admin_required
def overview_view(request):
    context = {
        'total_users': User.objects.filter(is_active=True).count(),
        'total_students': User.objects.filter(role='student', is_active=True).count(),
        'total_staff': User.objects.filter(role='staff', is_active=True).count(),
        'total_announcements': Announcement.objects.filter(is_active=True).count(),
        'total_results': Result.objects.count(),
        'recent_announcements': Announcement.objects.order_by('-created_at')[:5],
    }
    return render(request, 'management/overview.html', context)


# ── Announcements ─────────────────────────────────────────────────────────────

@admin_required
def announcements_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        target = request.POST.get('target', 'all')
        if title and content:
            ann = Announcement.objects.create(
                title=title, content=content,
                target=target, created_by=request.user
            )
            # Push as notification to targeted users
            _send_announcement_notifications(ann)
            messages.success(request, f'Announcement "{title}" sent successfully.')
        else:
            messages.error(request, 'Title and content are required.')
        return redirect('admin_announcements')

    announcements = Announcement.objects.select_related('created_by').order_by('-created_at')
    return render(request, 'management/announcements.html', {
        'announcements': announcements,
        'target_choices': Announcement.TARGET_CHOICES,
    })


@admin_required
@require_POST
def delete_announcement_view(request, ann_id):
    ann = get_object_or_404(Announcement, id=ann_id)
    ann.delete()
    return JsonResponse({'status': 'ok'})


@admin_required
@require_POST
def toggle_announcement_view(request, ann_id):
    ann = get_object_or_404(Announcement, id=ann_id)
    ann.is_active = not ann.is_active
    ann.save(update_fields=['is_active'])
    return JsonResponse({'status': 'ok', 'is_active': ann.is_active})


def _send_announcement_notifications(ann):
    """Create Notification records for targeted users."""
    target = ann.target
    if target == 'all':
        users = User.objects.filter(is_active=True)
    elif target == 'students':
        users = User.objects.filter(role='student', is_active=True)
    elif target == 'staff':
        users = User.objects.filter(role='staff', is_active=True)
    elif target.startswith('level_'):
        level = int(target.split('_')[1])
        student_ids = StudentProfile.objects.filter(level=level).values_list('user_id', flat=True)
        users = User.objects.filter(id__in=student_ids, is_active=True)
    else:
        users = User.objects.none()

    notifs = [
        Notification(
            user=u, title=ann.title,
            message=ann.content[:300],
            notification_type='announcement'
        ) for u in users
    ]
    Notification.objects.bulk_create(notifs, ignore_conflicts=True)


# ── User Management ───────────────────────────────────────────────────────────

@admin_required
def users_view(request):
    role_filter = request.GET.get('role', '')
    search = request.GET.get('q', '').strip()
    dept_filter = request.GET.get('dept', '')
    level_filter = request.GET.get('level', '')
    year_filter = request.GET.get('year', '')
    faculty_filter = request.GET.get('faculty', '')
    sort = request.GET.get('sort', '-date_joined')

    # Allowed sort fields
    SORT_OPTIONS = {
        'user_id': 'user_id',
        '-user_id': '-user_id',
        'name': 'first_name',
        '-name': '-first_name',
        'date_joined': 'date_joined',
        '-date_joined': '-date_joined',
    }
    order_by = SORT_OPTIONS.get(sort, '-date_joined')

    users = User.objects.filter(is_active=True)

    if role_filter:
        users = users.filter(role=role_filter)
    if search:
        users = (users.filter(user_id__icontains=search) |
                 users.filter(first_name__icontains=search) |
                 users.filter(last_name__icontains=search) |
                 users.filter(email__icontains=search))

    # Student-specific filters (join through StudentProfile)
    if dept_filter or level_filter or year_filter or faculty_filter:
        from apps.students.models import StudentProfile
        profiles = StudentProfile.objects.all()
        if level_filter:
            profiles = profiles.filter(level=level_filter)
        if year_filter:
            profiles = profiles.filter(academic_year=year_filter)
        if dept_filter:
            profiles = profiles.filter(programme__department__id=dept_filter)
        if faculty_filter:
            profiles = profiles.filter(programme__department__faculty__icontains=faculty_filter)
        student_user_ids = profiles.values_list('user_id', flat=True)
        users = users.filter(id__in=student_user_ids)

    users = users.order_by(order_by).select_related('student_profile__programme__department')

    # Data for filter dropdowns
    from apps.students.models import Department
    departments = Department.objects.order_by('name')
    faculties = Department.objects.values_list('faculty', flat=True).distinct().order_by('faculty')
    academic_years = StudentProfile.objects.values_list(
        'academic_year', flat=True).distinct().order_by('-academic_year') if 'StudentProfile' in dir() else []

    # Import StudentProfile if not already
    from apps.students.models import StudentProfile
    academic_years = StudentProfile.objects.values_list(
        'academic_year', flat=True).distinct().order_by('-academic_year')

    total = users.count()

    return render(request, 'management/users.html', {
        'users': users[:200],
        'role_filter': role_filter,
        'search': search,
        'dept_filter': dept_filter,
        'level_filter': level_filter,
        'year_filter': year_filter,
        'faculty_filter': faculty_filter,
        'sort': sort,
        'total': total,
        'departments': departments,
        'faculties': faculties,
        'academic_years': academic_years,
        'levels': [100, 200, 300, 400],
    })


@admin_required
def add_user_view(request):
    if request.method == 'POST':
        try:
            user_id = request.POST['user_id'].strip()
            email = request.POST['email'].strip()
            first_name = request.POST['first_name'].strip()
            last_name = request.POST['last_name'].strip()
            role = request.POST['role']
            password = request.POST['password']

            if User.objects.filter(user_id=user_id).exists():
                messages.error(request, f'User ID {user_id} already exists.')
                return redirect('admin_add_user')
            if User.objects.filter(email=email).exists():
                messages.error(request, f'Email {email} already in use.')
                return redirect('admin_add_user')

            user = User.objects.create_user(
                user_id=user_id, email=email,
                first_name=first_name, last_name=last_name,
                role=role, password=password,
                is_staff=(role == 'admin'),
            )

            # Auto-create student profile
            if role == 'student':
                programme_id = request.POST.get('programme')
                level = int(request.POST.get('level', 100))
                StudentProfile.objects.create(
                    user=user,
                    programme_id=programme_id if programme_id else None,
                    level=level,
                )

            messages.success(request, f'User {user.get_full_name()} ({user_id}) created.')
            return redirect('admin_users')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    programmes = Programme.objects.select_related('department').all()
    return render(request, 'management/add_user.html', {'programmes': programmes})


@admin_required
@require_POST
def toggle_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        return JsonResponse({'error': 'Cannot deactivate yourself'}, status=400)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    return JsonResponse({'status': 'ok', 'is_active': user.is_active})


@admin_required
@require_POST
def reset_password_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    data = json.loads(request.body)
    new_password = data.get('password', '').strip()
    if len(new_password) < 6:
        return JsonResponse({'error': 'Password must be at least 6 characters'}, status=400)
    user.set_password(new_password)
    user.save()
    return JsonResponse({'status': 'ok'})


# ── Results Upload ────────────────────────────────────────────────────────────

@admin_required
def results_view(request):
    courses = Course.objects.select_related('department').order_by('code')
    students = StudentProfile.objects.select_related('user', 'programme').order_by('user__user_id')
    recent_results = Result.objects.select_related(
        'student__user', 'course'
    ).order_by('-uploaded_at')[:20]
    return render(request, 'management/results.html', {
        'courses': courses,
        'students': students,
        'recent_results': recent_results,
    })


@admin_required
@require_POST
def upload_result_view(request):
    """Upload a single result manually."""
    try:
        student_id = request.POST['student_id']
        course_id = request.POST['course_id']
        score = float(request.POST['score'])
        academic_year = request.POST.get('academic_year', '2024/2025')
        semester = int(request.POST.get('semester', 1))
        remarks = request.POST.get('remarks', '')

        student = get_object_or_404(StudentProfile, id=student_id)
        course = get_object_or_404(Course, id=course_id)

        result, created = Result.objects.update_or_create(
            student=student, course=course,
            academic_year=academic_year, semester=semester,
            defaults={'score': score, 'grade': '', 'remarks': remarks}
        )

        # Notify student
        Notification.objects.create(
            user=student.user,
            title='Result Published',
            message=f'Your result for {course.name} ({course.code}) has been published. Score: {score}',
            notification_type='announcement'
        )

        action = 'Updated' if not created else 'Uploaded'
        messages.success(request, f'{action}: {student.user.user_id} — {course.code}: {result.grade} ({score})')
    except Exception as e:
        messages.error(request, f'Error: {e}')
    return redirect('admin_results')


@admin_required
@require_POST
def bulk_upload_results_view(request):
    """Bulk upload results via CSV file.
    CSV format: student_id,course_code,score,academic_year,semester
    """
    csv_file = request.FILES.get('csv_file')
    if not csv_file:
        messages.error(request, 'No file uploaded.')
        return redirect('admin_results')

    try:
        f = TextIOWrapper(csv_file.file, encoding='utf-8-sig')
        reader = csv.DictReader(f)
        success, errors = 0, []

        with transaction.atomic():
            for i, row in enumerate(reader, 1):
                try:
                    student = StudentProfile.objects.get(user__user_id=row['student_id'].strip())
                    course = Course.objects.get(code=row['course_code'].strip().upper())
                    score = float(row['score'])
                    year = row.get('academic_year', '2024/2025').strip()
                    sem = int(row.get('semester', 1))

                    Result.objects.update_or_create(
                        student=student, course=course,
                        academic_year=year, semester=sem,
                        defaults={'score': score, 'grade': ''}
                    )
                    success += 1
                except Exception as e:
                    errors.append(f'Row {i}: {e}')

        msg = f'{success} results uploaded.'
        if errors:
            msg += f' {len(errors)} errors: ' + '; '.join(errors[:3])
        messages.success(request, msg)
    except Exception as e:
        messages.error(request, f'File error: {e}')

    return redirect('admin_results')


# ── Groups / Cohorts ──────────────────────────────────────────────────────────

@admin_required
def groups_view(request):
    departments = Department.objects.all()
    programmes = Programme.objects.select_related('department').all()
    # Group students by level + programme
    cohorts = StudentProfile.objects.select_related(
        'user', 'programme', 'programme__department'
    ).order_by('programme__name', 'level')

    # Build cohort summary
    from collections import defaultdict
    cohort_map = defaultdict(list)
    for sp in cohorts:
        key = f"{sp.programme.name if sp.programme else 'Unknown'} — Level {sp.level}"
        cohort_map[key].append(sp)

    return render(request, 'management/groups.html', {
        'cohort_map': dict(cohort_map),
        'departments': departments,
        'programmes': programmes,
    })


@admin_required
@require_POST
def send_group_notification_view(request):
    """Send a notification to a specific cohort (programme + level)."""
    programme_id = request.POST.get('programme_id')
    level = request.POST.get('level')
    title = request.POST.get('title', '').strip()
    message = request.POST.get('message', '').strip()

    if not title or not message:
        messages.error(request, 'Title and message required.')
        return redirect('admin_groups')

    students = StudentProfile.objects.filter(is_active=True if hasattr(StudentProfile, 'is_active') else True)
    if programme_id:
        students = students.filter(programme_id=programme_id)
    if level:
        students = students.filter(level=int(level))

    notifs = [
        Notification(
            user=sp.user, title=title, message=message,
            notification_type='announcement'
        ) for sp in students.select_related('user')
    ]
    Notification.objects.bulk_create(notifs, ignore_conflicts=True)
    messages.success(request, f'Notification sent to {len(notifs)} students.')
    return redirect('admin_groups')


# ── Events ────────────────────────────────────────────────────────────────────

@admin_required
def events_view(request):
    if request.method == 'POST':
        try:
            Event.objects.create(
                title=request.POST['title'],
                description=request.POST.get('description', ''),
                event_type=request.POST.get('event_type', 'academic'),
                date=request.POST['date'],
                end_date=request.POST.get('end_date') or None,
                location=request.POST.get('location', ''),
                created_by=request.user,
            )
            messages.success(request, 'Event created.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_events')

    events = Event.objects.select_related('created_by').order_by('-date')
    return render(request, 'management/events.html', {
        'events': events,
        'event_types': Event.EVENT_TYPES,
    })


@admin_required
@require_POST
def delete_event_view(request, event_id):
    get_object_or_404(Event, id=event_id).delete()
    return JsonResponse({'status': 'ok'})


# ── Programmes ────────────────────────────────────────────────────────────────

@admin_required
def programmes_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'add_department':
                Department.objects.create(
                    name=request.POST['dept_name'],
                    code=request.POST['dept_code'].upper(),
                    faculty=request.POST['faculty'],
                )
                messages.success(request, 'Department created.')
            elif action == 'add_programme':
                Programme.objects.create(
                    name=request.POST['prog_name'],
                    code=request.POST['prog_code'].upper(),
                    department_id=request.POST['department'],
                    duration_years=int(request.POST.get('duration', 4)),
                )
                messages.success(request, 'Programme created.')
            elif action == 'delete_programme':
                Programme.objects.filter(id=request.POST['prog_id']).delete()
                messages.success(request, 'Programme deleted.')
            elif action == 'delete_department':
                Department.objects.filter(id=request.POST['dept_id']).delete()
                messages.success(request, 'Department deleted.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_programmes')

    departments = Department.objects.prefetch_related('programme_set').all()
    programmes = Programme.objects.select_related('department').all()
    return render(request, 'management/programmes.html', {
        'departments': departments,
        'programmes': programmes,
    })


# ── Batches ───────────────────────────────────────────────────────────────────

@admin_required
def batches_view(request):
    from apps.students.models import Batch
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'add':
                admission_year = request.POST['admission_year']
                programme_id = request.POST['programme']
                prog = Programme.objects.get(id=programme_id)
                # Auto-calculate graduation year
                start = int(admission_year.split('/')[0])
                grad_year = f"{start + prog.duration_years}/{start + prog.duration_years + 1}"
                Batch.objects.create(
                    name=request.POST['name'],
                    programme_id=programme_id,
                    admission_year=admission_year,
                    expected_graduation_year=grad_year,
                )
                messages.success(request, 'Batch created.')
            elif action == 'delete':
                Batch.objects.filter(id=request.POST['batch_id']).delete()
                messages.success(request, 'Batch deleted.')
            elif action == 'toggle':
                b = Batch.objects.get(id=request.POST['batch_id'])
                b.is_active = not b.is_active
                b.save()
                messages.success(request, 'Batch updated.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_batches')

    batches = Batch.objects.select_related('programme__department').order_by('-admission_year')
    programmes = Programme.objects.select_related('department').all()
    return render(request, 'management/batches.html', {
        'batches': batches,
        'programmes': programmes,
    })


# ── Academic Levels ───────────────────────────────────────────────────────────

@admin_required
def levels_view(request):
    from apps.students.models import AcademicLevel
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'add':
                AcademicLevel.objects.update_or_create(
                    programme_id=request.POST['programme'],
                    level=int(request.POST['level']),
                    academic_year=request.POST['academic_year'],
                    defaults={
                        'label': request.POST.get('label', ''),
                        'is_current': request.POST.get('is_current') == 'on',
                    }
                )
                messages.success(request, 'Academic level saved.')
            elif action == 'delete':
                AcademicLevel.objects.filter(id=request.POST['level_id']).delete()
                messages.success(request, 'Level deleted.')
            elif action == 'set_current':
                lvl = AcademicLevel.objects.get(id=request.POST['level_id'])
                # Unset others for same programme
                AcademicLevel.objects.filter(programme=lvl.programme, level=lvl.level).update(is_current=False)
                lvl.is_current = True
                lvl.save()
                messages.success(request, 'Current level updated.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_levels')

    levels = AcademicLevel.objects.select_related('programme__department').order_by('programme__name', 'level')
    programmes = Programme.objects.select_related('department').all()
    return render(request, 'management/levels.html', {
        'levels': levels,
        'programmes': programmes,
    })


# ── Group Chats ───────────────────────────────────────────────────────────────

@admin_required
def group_chats_view(request):
    from apps.chatbot.models import GroupChat
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'create':
                group = GroupChat.objects.create(
                    name=request.POST['name'],
                    description=request.POST.get('description', ''),
                    chat_type=request.POST.get('chat_type', 'class'),
                    created_by=request.user,
                    programme_id=request.POST.get('programme') or None,
                    level=int(request.POST['level']) if request.POST.get('level') else None,
                    academic_year=request.POST.get('academic_year', ''),
                )
                count = group.auto_add_members()
                messages.success(request, f'Group "{group.name}" created with {count} members.')
            elif action == 'delete':
                GroupChat.objects.filter(id=request.POST['group_id']).delete()
                messages.success(request, 'Group deleted.')
            elif action == 'toggle':
                g = GroupChat.objects.get(id=request.POST['group_id'])
                g.is_active = not g.is_active
                g.save()
                messages.success(request, 'Group updated.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_group_chats')

    groups = GroupChat.objects.select_related('created_by', 'programme').prefetch_related('members').order_by('-created_at')
    programmes = Programme.objects.all()
    return render(request, 'management/group_chats.html', {
        'groups': groups,
        'programmes': programmes,
        'chat_types': GroupChat.TYPE_CHOICES,
    })


@admin_required
@require_POST
def send_group_chat_message_view(request, group_id):
    """Admin broadcasts a message to a group chat."""
    from apps.chatbot.models import GroupChat, GroupMessage
    from apps.notifications.models import Notification
    group = get_object_or_404(GroupChat, id=group_id)
    message = request.POST.get('message', '').strip()
    if not message:
        return JsonResponse({'error': 'Message required'}, status=400)

    GroupMessage.objects.create(group=group, sender=request.user, message=message)

    # Notify all members
    notifs = [
        Notification(
            user=m, title=f'[{group.name}] New message',
            message=f'{request.user.get_full_name()}: {message[:150]}',
            notification_type='announcement'
        ) for m in group.members.filter(is_active=True)
    ]
    Notification.objects.bulk_create(notifs, ignore_conflicts=True)
    return JsonResponse({'status': 'ok', 'count': len(notifs)})


# ── PDF Student Import ────────────────────────────────────────────────────────

@admin_required
def import_students_view(request):
    """Upload one or more PDFs containing student lists and bulk-create accounts."""
    programmes = Programme.objects.select_related('department').order_by('name')

    if request.method == 'POST':
        from .pdf_import import (
            extract_text_from_pdf, parse_students_from_text,
            find_programme, generate_email,
        )

        pdf_files = request.FILES.getlist('pdf_files')
        default_level = int(request.POST.get('default_level', 100))
        default_programme_id = request.POST.get('default_programme') or None
        default_password = request.POST.get('default_password', 'kaaf2024')

        default_programme = None
        if default_programme_id:
            try:
                default_programme = Programme.objects.get(id=default_programme_id)
            except Programme.DoesNotExist:
                pass

        all_programmes = list(programmes)
        created_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []
        preview = []

        for pdf_file in pdf_files:
            try:
                text = extract_text_from_pdf(pdf_file)
                students, meta = parse_students_from_text(
                    text,
                    default_level=default_level,
                    default_programme=default_programme.name if default_programme else None,
                )

                if not students:
                    errors.append(f"'{pdf_file.name}': No students found. Check PDF format.")
                    continue

                with transaction.atomic():
                    for s in students:
                        try:
                            # Use school student number as user_id
                            user_id = s['student_no']
                            email = generate_email(s['first_name'], s['last_name'], user_id)

                            # Resolve programme from PDF metadata
                            programme = find_programme(
                                s['programme_hint'],
                                s['programme_code'],
                                all_programmes
                            ) or default_programme

                            # Create or update user
                            user, created = User.objects.get_or_create(
                                user_id=user_id,
                                defaults={
                                    'email': email,
                                    'first_name': s['first_name'],
                                    'last_name': s['last_name'],
                                    'role': User.STUDENT,
                                }
                            )
                            if created:
                                user.set_password(default_password)
                                user.save()
                                created_count += 1
                            else:
                                # Update name if changed
                                user.first_name = s['first_name']
                                user.last_name = s['last_name']
                                user.save(update_fields=['first_name', 'last_name'])
                                updated_count += 1

                            # Create or update student profile
                            profile, _ = StudentProfile.objects.update_or_create(
                                user=user,
                                defaults={
                                    'programme': programme,
                                    'level': s['level'],
                                    'academic_year': s['academic_year'],
                                    'semester': s['semester'],
                                }
                            )

                            preview.append({
                                'user_id': user_id,
                                'name': f"{s['first_name']} {s['last_name']}",
                                'level': s['level'],
                                'programme': programme.name if programme else '—',
                                'academic_year': s['academic_year'],
                                'created': created,
                            })

                        except Exception as e:
                            skipped_count += 1
                            errors.append(f"{s.get('student_no','?')} {s.get('first_name','')} {s.get('last_name','')}: {e}")

            except Exception as e:
                errors.append(f"File '{pdf_file.name}': {e}")

        if created_count:
            messages.success(request, f'✅ {created_count} new students imported. Default password: "{default_password}"')
        if updated_count:
            messages.info(request, f'🔄 {updated_count} existing students updated.')
        if skipped_count:
            messages.warning(request, f'⚠️ {skipped_count} entries skipped.')
        for err in errors[:10]:
            messages.error(request, err)

        return render(request, 'management/import_students.html', {
            'programmes': programmes,
            'preview': preview,
            'created_count': created_count,
            'updated_count': updated_count,
            'skipped_count': skipped_count,
            'errors': errors,
        })

    return render(request, 'management/import_students.html', {
        'programmes': programmes,
    })
