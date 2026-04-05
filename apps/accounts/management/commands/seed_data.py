"""
Management command to seed sample data for testing
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, time, timedelta
import random


class Command(BaseCommand):
    help = 'Seed the database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        self._create_departments()
        self._create_programmes()
        self._create_courses()
        self._create_users()
        self._create_timetables()
        self._create_results()
        self._create_events()
        self._create_notifications()
        self._create_tasks()
        self.stdout.write(self.style.SUCCESS('✅ Database seeded successfully!'))
        self.stdout.write('\nDemo Login Credentials:')
        self.stdout.write('  Student: STU/2021/001 / password123')
        self.stdout.write('  Staff:   STF/2020/001 / password123')
        self.stdout.write('  Admin:   ADM/001 / admin123')

    def _create_departments(self):
        from apps.students.models import Department
        depts = [
            ('CS', 'Computer Science', 'Faculty of Science'),
            ('MATH', 'Mathematics', 'Faculty of Science'),
            ('ENG', 'English', 'Faculty of Arts'),
            ('BUS', 'Business Administration', 'Faculty of Business'),
            ('EDUC', 'Education', 'Faculty of Education'),
        ]
        for code, name, faculty in depts:
            Department.objects.get_or_create(code=code, defaults={'name': name, 'faculty': faculty})
        self.stdout.write('  ✓ Departments created')

    def _create_programmes(self):
        from apps.students.models import Programme, Department
        cs = Department.objects.get(code='CS')
        bus = Department.objects.get(code='BUS')
        Programme.objects.get_or_create(code='BSC-CS', defaults={'name': 'BSc Computer Science', 'department': cs})
        Programme.objects.get_or_create(code='BBA', defaults={'name': 'Bachelor of Business Admin', 'department': bus})
        self.stdout.write('  ✓ Programmes created')

    def _create_courses(self):
        from apps.students.models import Course, Department
        cs = Department.objects.get(code='CS')
        courses = [
            ('CS101', 'Introduction to Programming', 3, 100, 1),
            ('CS102', 'Discrete Mathematics', 3, 100, 1),
            ('CS201', 'Data Structures & Algorithms', 3, 200, 1),
            ('CS202', 'Database Systems', 3, 200, 2),
            ('CS301', 'Software Engineering', 3, 300, 1),
            ('CS302', 'Computer Networks', 3, 300, 2),
            ('CS401', 'Artificial Intelligence', 3, 400, 1),
            ('CS402', 'Final Year Project', 6, 400, 2),
        ]
        for code, name, credits, level, sem in courses:
            Course.objects.get_or_create(code=code, defaults={
                'name': name, 'department': cs,
                'credit_hours': credits, 'level': level, 'semester': sem,
            })
        self.stdout.write('  ✓ Courses created')

    def _create_users(self):
        from apps.accounts.models import User
        from apps.students.models import StudentProfile, Programme, CourseRegistration, Course
        from apps.staff.models import StaffProfile
        from apps.students.models import Department

        # Admin
        admin, _ = User.objects.get_or_create(user_id='ADM/001', defaults={
            'email': 'admin@kaaf.edu.gh', 'first_name': 'System', 'last_name': 'Admin',
            'role': 'admin', 'is_staff': True, 'is_superuser': True,
        })
        admin.set_password('admin123')
        admin.save()

        # Students
        programme = Programme.objects.get(code='BSC-CS')
        student_data = [
            ('STU/2021/001', 'Kwame', 'Asante', 'kwame@kaaf.edu.gh'),
            ('STU/2021/002', 'Ama', 'Mensah', 'ama@kaaf.edu.gh'),
            ('STU/2022/001', 'Kofi', 'Boateng', 'kofi@kaaf.edu.gh'),
        ]
        for uid, fn, ln, email in student_data:
            user, created = User.objects.get_or_create(user_id=uid, defaults={
                'email': email, 'first_name': fn, 'last_name': ln, 'role': 'student',
                'points': random.randint(50, 500), 'study_streak': random.randint(0, 15),
            })
            if created:
                user.set_password('password123')
                user.save()
            profile, _ = StudentProfile.objects.get_or_create(user=user, defaults={
                'programme': programme, 'level': 300, 'semester': 1,
                'academic_year': '2024/2025',
            })
            # Register for courses
            courses = Course.objects.filter(level=300, semester=1)
            for course in courses:
                CourseRegistration.objects.get_or_create(
                    student=profile, course=course,
                    defaults={'academic_year': '2024/2025', 'semester': 1}
                )

        # Staff
        dept = Department.objects.get(code='CS')
        staff_user, created = User.objects.get_or_create(user_id='STF/2020/001', defaults={
            'email': 'staff@kaaf.edu.gh', 'first_name': 'Dr. Emmanuel', 'last_name': 'Owusu',
            'role': 'staff', 'is_staff': True,
        })
        if created:
            staff_user.set_password('password123')
            staff_user.save()
        staff_profile, _ = StaffProfile.objects.get_or_create(user=staff_user, defaults={
            'department': dept, 'rank': 'senior_lecturer',
            'office': 'Block A, Room 201', 'office_hours': 'Mon-Fri 10am-12pm',
        })
        courses = Course.objects.filter(level=300)
        staff_profile.courses_assigned.set(courses)

        self.stdout.write('  ✓ Users created')

    def _create_timetables(self):
        from apps.students.models import Timetable, Course
        entries = [
            ('CS301', 'MON', time(8, 0), time(10, 0), 'LH 101'),
            ('CS302', 'MON', time(12, 0), time(14, 0), 'LH 203'),
            ('CS301', 'WED', time(8, 0), time(10, 0), 'LH 101'),
            ('CS302', 'WED', time(14, 0), time(16, 0), 'LH 203'),
            ('CS301', 'FRI', time(10, 0), time(12, 0), 'LH 101'),
        ]
        for code, day, start, end, venue in entries:
            try:
                course = Course.objects.get(code=code)
                Timetable.objects.get_or_create(
                    course=course, day=day, academic_year='2024/2025', semester=1,
                    defaults={'start_time': start, 'end_time': end, 'venue': venue, 'level': 300}
                )
            except Course.DoesNotExist:
                pass
        self.stdout.write('  ✓ Timetables created')

    def _create_results(self):
        from apps.accounts.models import User
        from apps.students.models import StudentProfile, Result, Course, GPARecord
        scores = [
            ('CS201', 78), ('CS202', 85), ('CS301', 72), ('CS302', 90),
        ]
        for user in User.objects.filter(role='student'):
            try:
                profile = user.student_profile
                for code, score in scores:
                    try:
                        course = Course.objects.get(code=code)
                        Result.objects.get_or_create(
                            student=profile, course=course,
                            academic_year='2023/2024', semester=2,
                            defaults={'score': score + random.randint(-10, 10)}
                        )
                    except Course.DoesNotExist:
                        pass
                # Create GPA record
                profile.calculate_cumulative_gpa()
                GPARecord.objects.get_or_create(
                    student=profile, academic_year='2023/2024', semester=2,
                    defaults={'gpa': profile.cumulative_gpa, 'total_credits': 12}
                )
            except Exception:
                pass
        self.stdout.write('  ✓ Results created')

    def _create_events(self):
        from apps.accounts.models import User
        from apps.notifications.models import Event
        admin = User.objects.filter(role='admin').first()
        events = [
            ('Mid-Semester Examinations', 'exam', date.today() + timedelta(days=14), 'Main Hall'),
            ('SRC Week Celebration', 'src', date.today() + timedelta(days=21), 'Campus Grounds'),
            ('Faculty Meeting', 'faculty', date.today() + timedelta(days=7), 'Conference Room A'),
            ('Independence Day Holiday', 'holiday', date.today() + timedelta(days=30), 'N/A'),
            ('Graduation Ceremony', 'academic', date.today() + timedelta(days=60), 'Auditorium'),
        ]
        for title, etype, edate, location in events:
            Event.objects.get_or_create(title=title, defaults={
                'event_type': etype, 'date': edate, 'location': location,
                'created_by': admin,
            })
        self.stdout.write('  ✓ Events created')

    def _create_notifications(self):
        from apps.accounts.models import User
        from apps.notifications.models import Notification
        for user in User.objects.filter(role='student'):
            notifs = [
                ('Exam Reminder', 'Your mid-semester exams start in 2 weeks. Start preparing now!', 'exam'),
                ('Assignment Due', 'CS301 Software Engineering assignment is due in 3 days.', 'assignment'),
                ('Daily Motivation', 'Success is not final, failure is not fatal. Keep going!', 'motivation'),
            ]
            for title, msg, ntype in notifs:
                Notification.objects.get_or_create(
                    user=user, title=title,
                    defaults={'message': msg, 'notification_type': ntype}
                )
        self.stdout.write('  ✓ Notifications created')

    def _create_tasks(self):
        from apps.accounts.models import User
        from apps.planner.models import Task
        for user in User.objects.filter(role='student'):
            tasks = [
                ('Complete CS301 Assignment', 'assignment', 'high', date.today() + timedelta(days=3)),
                ('Study for Algorithms Exam', 'exam_prep', 'high', date.today() + timedelta(days=7)),
                ('Read Chapter 5 - Networks', 'study', 'medium', date.today() + timedelta(days=2)),
                ('Group Project Meeting', 'project', 'medium', date.today() + timedelta(days=5)),
            ]
            for title, ttype, priority, due in tasks:
                Task.objects.get_or_create(
                    user=user, title=title,
                    defaults={'task_type': ttype, 'priority': priority, 'due_date': due}
                )
        self.stdout.write('  ✓ Tasks created')
