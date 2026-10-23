"""
Examination System Views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, HttpResponse
from .models import Exam, ExamAttempt, Answer, Question, PastQuestionFile, ExamCategory
import random


@login_required
def exam_list(request):
    """List all available exams for the student"""
    if request.user.role != 'student':
        messages.error(request, "Only students can access exams.")
        return redirect('dashboard')
    
    # Get student's registered courses
    student_profile = request.user.student_profile
    registered_courses = student_profile.registrations.filter(
        is_active=True
    ).values_list('course_id', flat=True)
    
    # Get available exams
    now = timezone.now()
    exams = Exam.objects.filter(
        course_id__in=registered_courses,
        is_published=True,
        is_active=True
    ).select_related('course').annotate(
        attempts_count=Count('attempts', filter=Q(attempts__student=request.user))
    )
    
    # Categorize exams
    available_exams = []
    upcoming_exams = []
    past_exams = []
    
    for exam in exams:
        if exam.end_time and now > exam.end_time:
            past_exams.append(exam)
        elif exam.start_time and now < exam.start_time:
            upcoming_exams.append(exam)
        else:
            available_exams.append(exam)
    
    context = {
        'available_exams': available_exams,
        'upcoming_exams': upcoming_exams,
        'past_exams': past_exams,
    }
    return render(request, 'exams/exam_list.html', context)



@login_required
def exam_detail(request, exam_id):
    """Show exam details and allow student to start"""
    exam = get_object_or_404(Exam, id=exam_id, is_published=True)
    
    # Check if student is registered for this course (skip for AI-generated exams)
    if request.user.role == 'student':
        # AI-generated exams are available to all students
        is_ai_exam = exam.category and exam.category.name == "AI Generated"
        
        if not is_ai_exam:
            is_registered = request.user.student_profile.registrations.filter(
                course=exam.course, is_active=True
            ).exists()
            
            if not is_registered:
                messages.error(request, "You are not registered for this course.")
                return redirect('exams:exam_list')
    
    # Get student's attempts
    attempts = ExamAttempt.objects.filter(
        exam=exam, student=request.user
    ).order_by('-attempt_number')
    
    can_attempt = (
        exam.is_available and
        attempts.count() < exam.max_attempts
    )
    
    context = {
        'exam': exam,
        'attempts': attempts,
        'can_attempt': can_attempt,
        'attempts_left': exam.max_attempts - attempts.count(),
    }
    return render(request, 'exams/exam_detail.html', context)


@login_required
def start_exam(request, exam_id):
    """Start a new exam attempt"""
    exam = get_object_or_404(Exam, id=exam_id, is_published=True)
    
    if not exam.is_available:
        messages.error(request, "This exam is not currently available.")
        return redirect('exams:exam_detail', exam_id=exam_id)
    
    # Check attempts
    attempts_count = ExamAttempt.objects.filter(
        exam=exam, student=request.user
    ).count()
    
    if attempts_count >= exam.max_attempts:
        messages.error(request, "You have reached the maximum number of attempts.")
        return redirect('exams:exam_detail', exam_id=exam_id)
    
    # Create new attempt
    attempt = ExamAttempt.objects.create(
        exam=exam,
        student=request.user,
        attempt_number=attempts_count + 1,
        status='in_progress'
    )
    
    return redirect('exams:take_exam', attempt_id=attempt.id)


@login_required
def take_exam(request, attempt_id):
    """Take the exam"""
    attempt = get_object_or_404(
        ExamAttempt, id=attempt_id, student=request.user, status='in_progress'
    )
    
    exam = attempt.exam
    
    # Check if time expired
    time_elapsed = (timezone.now() - attempt.started_at).total_seconds() / 60
    if time_elapsed > exam.duration_minutes:
        attempt.status = 'expired'
        attempt.save()
        messages.warning(request, "Time expired! Your exam has been auto-submitted.")
        return redirect('exams:submit_exam', attempt_id=attempt.id)
    
    # Get questions
    questions = exam.questions.prefetch_related('options').all()
    if exam.shuffle_questions:
        questions = list(questions)
        random.shuffle(questions)
    
    # Get existing answers
    existing_answers = {
        ans.question_id: ans for ans in attempt.answers.select_related('selected_option')
    }
    
    context = {
        'attempt': attempt,
        'exam': exam,
        'questions': questions,
        'existing_answers': existing_answers,
        'time_remaining': exam.duration_minutes - int(time_elapsed),
    }
    return render(request, 'exams/take_exam.html', context)



@login_required
def save_answer(request, attempt_id):
    """AJAX endpoint to save an answer"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, student=request.user, status='in_progress')
    
    question_id = request.POST.get('question_id')
    option_id = request.POST.get('option_id')
    answer_text = request.POST.get('answer_text', '')
    
    question = get_object_or_404(Question, id=question_id, exam=attempt.exam)
    
    # Create or update answer
    answer, created = Answer.objects.get_or_create(
        attempt=attempt,
        question=question,
        defaults={'answer_text': answer_text}
    )
    
    if option_id:
        from .models import QuestionOption
        option = get_object_or_404(QuestionOption, id=option_id, question=question)
        answer.selected_option = option
        answer.check_answer()  # Auto-check for multiple choice
    else:
        answer.answer_text = answer_text
    
    answer.save()
    
    return JsonResponse({'success': True, 'saved': True})


@login_required
def submit_exam(request, attempt_id):
    """Submit the exam"""
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, student=request.user)
    
    if attempt.status != 'in_progress':
        messages.info(request, "This exam has already been submitted.")
        return redirect('exams:exam_result', attempt_id=attempt.id)
    
    # Calculate time taken
    time_taken = (timezone.now() - attempt.started_at).total_seconds() / 60
    attempt.time_taken_minutes = int(time_taken)
    attempt.submitted_at = timezone.now()
    attempt.status = 'submitted'
    
    # Auto-grade multiple choice, true/false, and fill_blank questions
    for answer in attempt.answers.all():
        if answer.question.question_type in ['multiple_choice', 'true_false', 'fill_blank']:
            answer.check_answer()
    
    # Calculate score
    attempt.calculate_score()
    attempt.status = 'graded'
    attempt.save()
    
    messages.success(request, "Exam submitted successfully!")
    
    if attempt.exam.show_results_immediately:
        return redirect('exams:exam_result', attempt_id=attempt.id)
    else:
        messages.info(request, "Your results will be available after grading.")
        return redirect('exams:exam_list')


@login_required
def exam_result(request, attempt_id):
    """View exam results"""
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, student=request.user)
    
    if attempt.status == 'in_progress':
        messages.warning(request, "Please submit the exam first.")
        return redirect('exams:take_exam', attempt_id=attempt.id)
    
    # Get answers with questions
    answers = attempt.answers.select_related(
        'question', 'selected_option'
    ).prefetch_related('question__options')
    
    context = {
        'attempt': attempt,
        'answers': answers,
        'can_review': attempt.exam.allow_review,
    }
    return render(request, 'exams/exam_result.html', context)



@login_required
def past_questions_list(request):
    """List all past question papers"""
    course_filter = request.GET.get('course')
    year_filter = request.GET.get('year')
    
    past_questions = PastQuestionFile.objects.filter(
        is_active=True
    ).select_related('course')
    
    if course_filter:
        past_questions = past_questions.filter(course_id=course_filter)
    if year_filter:
        past_questions = past_questions.filter(academic_year=year_filter)
    
    # Get unique years and courses for filters
    years = PastQuestionFile.objects.values_list('academic_year', flat=True).distinct()
    
    if request.user.role == 'student':
        # Get student's courses
        from apps.students.models import Course
        try:
            student_profile = request.user.student_profile
            courses = Course.objects.filter(
                courseregistration__student=student_profile,
                courseregistration__is_active=True
            ).distinct()
        except:
            courses = Course.objects.none()
    else:
        from apps.students.models import Course
        courses = Course.objects.all()
    
    context = {
        'past_questions': past_questions,
        'years': sorted(years, reverse=True),
        'courses': courses,
    }
    return render(request, 'exams/past_questions_list.html', context)


@login_required
def download_past_question(request, file_id):
    """Download a past question file"""
    past_question = get_object_or_404(PastQuestionFile, id=file_id, is_active=True)
    
    # Increment download count
    past_question.downloads += 1
    past_question.save()
    
    # Serve file
    response = HttpResponse(past_question.file, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{past_question.title}.{past_question.file_type}"'
    return response


# Admin views
@login_required
def upload_past_question(request):
    """Admin/Staff upload past question"""
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, "You don't have permission to upload past questions.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        from .forms import PastQuestionUploadForm
        form = PastQuestionUploadForm(request.POST, request.FILES)
        if form.is_valid():
            past_question = form.save(commit=False)
            past_question.uploaded_by = request.user
            past_question.save()
            messages.success(request, "Past question uploaded successfully!")
            return redirect('exams:past_questions_list')
    else:
        from .forms import PastQuestionUploadForm
        form = PastQuestionUploadForm()
    
    return render(request, 'exams/upload_past_question.html', {'form': form})



# ─── AI EXAM GENERATION VIEWS ────────────────────────────────────────────────

@login_required
def ai_exam_generator(request):
    """AI-powered exam generation interface"""
    if request.method == 'POST':
        topic = request.POST.get('topic', '').strip()
        course_code = request.POST.get('course_code', 'AI-GEN').strip()
        num_questions = int(request.POST.get('num_questions', 10))
        difficulty = request.POST.get('difficulty', 'medium')
        duration = int(request.POST.get('duration', 30))
        
        # Question types
        question_types = []
        if request.POST.get('multiple_choice'):
            question_types.append('multiple_choice')
        if request.POST.get('true_false'):
            question_types.append('true_false')
        if request.POST.get('fill_blank'):
            question_types.append('fill_blank')
        
        if not question_types:
            question_types = ['multiple_choice']
        
        if not topic:
            messages.error(request, "Please provide a topic for the exam.")
            return redirect('exams:ai_exam_generator')
        
        # Validate inputs
        if num_questions < 1 or num_questions > 200:
            messages.error(request, "Number of questions must be between 1 and 200.")
            return redirect('exams:ai_exam_generator')
        
        if duration < 5 or duration > 180:
            messages.error(request, "Duration must be between 5 and 180 minutes.")
            return redirect('exams:ai_exam_generator')
        
        try:
            from .ai_exam_generator import AIExamGenerator
            generator = AIExamGenerator()
            
            # Generate exam
            exam = generator.generate_exam(
                topic=topic,
                course_code=course_code,
                num_questions=num_questions,
                difficulty=difficulty,
                question_types=question_types,
                duration_minutes=duration,
                user=request.user
            )
            
            messages.success(request, f"✨ AI generated your exam: {exam.title}")
            return redirect('exams:exam_detail', exam_id=exam.id)
            
        except Exception as e:
            messages.error(request, f"Failed to generate exam: {str(e)}")
            return redirect('exams:ai_exam_generator')
    
    # GET request - show form
    context = {
        'page_title': 'AI Exam Generator',
    }
    return render(request, 'exams/ai_exam_generator.html', context)


@login_required
def my_ai_exams(request):
    """List all AI-generated exams for the current user"""
    ai_category = ExamCategory.objects.filter(name="AI Generated").first()
    
    if ai_category:
        exams = Exam.objects.filter(
            category=ai_category,
            is_published=True,
            is_active=True
        ).select_related('course').annotate(
            attempts_count=Count('attempts', filter=Q(attempts__student=request.user))
        ).order_by('-created_at')
    else:
        exams = Exam.objects.none()
    
    context = {
        'exams': exams,
        'page_title': 'My AI-Generated Exams',
    }
    return render(request, 'exams/my_ai_exams.html', context)


# ─── BULK QUESTION UPLOAD ────────────────────────────────────────────────────

@login_required
def bulk_question_upload(request):
    """Admin/Staff bulk upload questions via CSV or JSON"""
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, "You don't have permission to upload questions.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        from .forms import BulkQuestionUploadForm
        form = BulkQuestionUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            exam = form.cleaned_data['exam']
            file = form.cleaned_data['file']
            file_format = form.cleaned_data['file_format']
            
            try:
                if file_format == 'csv':
                    questions_created, errors = form.process_csv(file, exam)
                else:
                    questions_created, errors = form.process_json(file, exam)
                
                if questions_created > 0:
                    messages.success(request, f"✅ Successfully created {questions_created} questions!")
                
                if errors:
                    for error in errors[:5]:  # Show first 5 errors
                        messages.warning(request, error)
                    if len(errors) > 5:
                        messages.warning(request, f"... and {len(errors) - 5} more errors")
                
                return redirect('exams:exam_detail', exam_id=exam.id)
                
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
    else:
        from .forms import BulkQuestionUploadForm
        form = BulkQuestionUploadForm()
    
    context = {
        'form': form,
        'page_title': 'Bulk Question Upload',
    }
    return render(request, 'exams/bulk_question_upload.html', context)


@login_required
def download_question_template(request, format_type='csv'):
    """Download template file for bulk question upload"""
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, "You don't have permission to download templates.")
        return redirect('dashboard')
    
    if format_type == 'csv':
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'question_text',
            'question_type',
            'marks',
            'order',
            'options',
            'correct_answers',
            'expected_answer'
        ])
        
        # Write example rows
        writer.writerow([
            'What is the capital of France?',
            'multiple_choice',
            '2',
            '1',
            'London|Paris|Berlin|Madrid',
            '1',
            ''
        ])
        writer.writerow([
            'Python is a programming language.',
            'true_false',
            '1',
            '2',
            'True|False',
            '0',
            ''
        ])
        writer.writerow([
            'The capital of France is _____.',
            'fill_blank',
            '1',
            '3',
            '',
            '',
            'Paris'
        ])
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="question_template.csv"'
        return response
    
    else:  # JSON
        import json
        
        template = {
            "questions": [
                {
                    "question_text": "What is the capital of France?",
                    "question_type": "multiple_choice",
                    "marks": 2,
                    "order": 1,
                    "options": [
                        {"text": "London", "is_correct": False},
                        {"text": "Paris", "is_correct": True},
                        {"text": "Berlin", "is_correct": False},
                        {"text": "Madrid", "is_correct": False}
                    ]
                },
                {
                    "question_text": "Python is a programming language.",
                    "question_type": "true_false",
                    "marks": 1,
                    "order": 2,
                    "options": [
                        {"text": "True", "is_correct": True},
                        {"text": "False", "is_correct": False}
                    ]
                },
                {
                    "question_text": "The capital of France is _____.",
                    "question_type": "fill_blank",
                    "marks": 1,
                    "order": 3,
                    "expected_answer": "Paris"
                }
            ]
        }
        
        response = HttpResponse(
            json.dumps(template, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="question_template.json"'
        return response
