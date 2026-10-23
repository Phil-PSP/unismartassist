"""
Management command to seed test exam data
Usage: python manage.py seed_exams
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.exams.models import ExamCategory, Exam, Question, QuestionOption
from apps.students.models import Course
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Seeds the database with sample exam data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding exam data...')
        
        # Get or create admin user
        admin = User.objects.filter(role=User.ADMIN).first()
        if not admin:
            # Try to get staff user
            admin = User.objects.filter(role=User.STAFF).first()
        if not admin:
            # Try superuser
            admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.ERROR('No admin/staff user found!'))
            return
        
        # Get some courses
        courses = Course.objects.all()[:3]
        if not courses:
            self.stdout.write(self.style.ERROR('No courses found! Run seed_data first.'))
            return
        
        # Create categories
        categories_data = [
            {'name': 'Mid-Semester Exam', 'description': 'Mid-semester assessments'},
            {'name': 'Final Exam', 'description': 'End of semester examinations'},
            {'name': 'Quiz', 'description': 'Short quizzes and tests'},
            {'name': 'Practice Test', 'description': 'Practice exams for revision'},
        ]
        
        categories = []
        for cat_data in categories_data:
            cat, created = ExamCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories.append(cat)
            if created:
                self.stdout.write(f'  ✓ Created category: {cat.name}')

        
        # Create sample exams
        now = timezone.now()
        
        for i, course in enumerate(courses):
            # Create a practice exam
            exam = Exam.objects.create(
                title=f"{course.code} Practice Test",
                course=course,
                category=categories[3],  # Practice Test
                exam_type='practice',
                difficulty='medium',
                description=f"Practice test for {course.name}",
                instructions="Answer all questions. Each question carries equal marks.",
                duration_minutes=45,
                start_time=now - timedelta(days=7),
                end_time=now + timedelta(days=30),
                total_marks=20,
                pass_mark=10,
                shuffle_questions=True,
                shuffle_options=True,
                show_results_immediately=True,
                allow_review=True,
                max_attempts=3,
                created_by=admin,
                is_active=True,
                is_published=True
            )
            
            # Add questions
            questions_data = [
                {
                    'text': f'What is the primary focus of {course.name}?',
                    'options': [
                        ('Understanding core concepts', True),
                        ('Memorizing facts', False),
                        ('Copying from textbooks', False),
                        ('Guessing answers', False),
                    ]
                },
                {
                    'text': f'Which of the following is a key topic in {course.code}?',
                    'options': [
                        ('Advanced techniques', True),
                        ('Unrelated subjects', False),
                        ('Random topics', False),
                        ('None of the above', False),
                    ]
                },
                {
                    'text': 'True or False: Regular practice improves understanding.',
                    'options': [
                        ('True', True),
                        ('False', False),
                    ]
                },
                {
                    'text': f'What is the best way to prepare for {course.code} exams?',
                    'options': [
                        ('Study consistently and practice problems', True),
                        ('Cram the night before', False),
                        ('Skip lectures', False),
                        ('Copy from friends', False),
                    ]
                },
            ]
            
            for q_idx, q_data in enumerate(questions_data, 1):
                question = Question.objects.create(
                    exam=exam,
                    question_text=q_data['text'],
                    question_type='true_false' if len(q_data['options']) == 2 else 'multiple_choice',
                    marks=5,
                    order=q_idx
                )
                
                for opt_idx, (opt_text, is_correct) in enumerate(q_data['options'], 1):
                    QuestionOption.objects.create(
                        question=question,
                        option_text=opt_text,
                        is_correct=is_correct,
                        order=opt_idx
                    )
            
            self.stdout.write(f'  ✓ Created exam: {exam.title} with {exam.total_questions} questions')
        
        # Create a quiz
        if courses:
            quiz = Exam.objects.create(
                title=f"{courses[0].code} Quick Quiz",
                course=courses[0],
                category=categories[2],  # Quiz
                exam_type='quiz',
                difficulty='easy',
                description="Quick quiz to test your knowledge",
                instructions="Answer all questions within the time limit.",
                duration_minutes=15,
                start_time=now,
                end_time=now + timedelta(days=7),
                total_marks=10,
                pass_mark=5,
                shuffle_questions=True,
                shuffle_options=True,
                show_results_immediately=True,
                allow_review=True,
                max_attempts=2,
                created_by=admin,
                is_active=True,
                is_published=True
            )
            
            # Add 2 quick questions
            q1 = Question.objects.create(
                exam=quiz,
                question_text="What does GPA stand for?",
                question_type='multiple_choice',
                marks=5,
                order=1
            )
            QuestionOption.objects.create(question=q1, option_text="Grade Point Average", is_correct=True, order=1)
            QuestionOption.objects.create(question=q1, option_text="General Performance Assessment", is_correct=False, order=2)
            QuestionOption.objects.create(question=q1, option_text="Graded Point Analysis", is_correct=False, order=3)
            
            q2 = Question.objects.create(
                exam=quiz,
                question_text="Is regular attendance important for academic success?",
                question_type='true_false',
                marks=5,
                order=2
            )
            QuestionOption.objects.create(question=q2, option_text="True", is_correct=True, order=1)
            QuestionOption.objects.create(question=q2, option_text="False", is_correct=False, order=2)
            
            self.stdout.write(f'  ✓ Created quiz: {quiz.title} with {quiz.total_questions} questions')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully seeded exam data!'))
        self.stdout.write(self.style.SUCCESS(f'   Total exams: {Exam.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'   Total questions: {Question.objects.count()}'))
