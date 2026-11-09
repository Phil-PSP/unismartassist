from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.students.models import Course, CourseRegistration, Department, StudentProfile
from .models import Exam, ExamAttempt


class ExamAuthorizationTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name="Computing",
            code="CMP",
            faculty="Engineering",
        )
        self.course = Course.objects.create(
            code="CSC101",
            name="Introduction to Computing",
            department=self.department,
            credit_hours=3,
            level=100,
            semester=1,
        )
        self.student = User.objects.create_user(
            user_id="EXAM/STUDENT/01",
            email="exam-student@example.com",
            password="Strong-Test-Password-2026!",
            first_name="Exam",
            last_name="Student",
            role=User.STUDENT,
        )
        self.profile = StudentProfile.objects.create(
            user=self.student,
            level=100,
            semester=1,
            academic_year="2025/2026",
        )
        self.exam = Exam.objects.create(
            title="CSC101 Practice",
            course=self.course,
            created_by=self.student,
            is_active=True,
            is_published=True,
            max_attempts=1,
        )
        self.start_url = reverse("exams:start_exam", args=[self.exam.pk])

    def test_start_exam_rejects_get(self):
        self.client.force_login(self.student)
        response = self.client.get(self.start_url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(ExamAttempt.objects.filter(exam=self.exam).count(), 0)

    def test_unregistered_student_cannot_start_exam(self):
        self.client.force_login(self.student)
        response = self.client.post(self.start_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ExamAttempt.objects.filter(exam=self.exam).count(), 0)

    def test_registered_student_can_start_exam(self):
        CourseRegistration.objects.create(
            student=self.profile,
            course=self.course,
            academic_year="2025/2026",
            semester=1,
            is_active=True,
        )
        self.client.force_login(self.student)
        response = self.client.post(self.start_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ExamAttempt.objects.filter(exam=self.exam, student=self.student).count(), 1)

    def test_non_student_cannot_start_exam(self):
        staff = User.objects.create_user(
            user_id="EXAM/STAFF/01",
            email="exam-staff@example.com",
            password="Strong-Test-Password-2026!",
            first_name="Exam",
            last_name="Staff",
            role=User.STAFF,
        )
        self.client.force_login(staff)
        response = self.client.post(self.start_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ExamAttempt.objects.filter(exam=self.exam).count(), 0)

    def test_submit_exam_rejects_get(self):
        attempt = ExamAttempt.objects.create(
            exam=self.exam,
            student=self.student,
            attempt_number=1,
            status="in_progress",
        )
        self.client.force_login(self.student)
        response = self.client.get(
            reverse("exams:submit_exam", args=[attempt.pk])
        )
        self.assertEqual(response.status_code, 405)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "in_progress")


    def test_students_cannot_view_results_before_staff_release(self):
        attempt = ExamAttempt.objects.create(
            exam=self.exam,
            student=self.student,
            attempt_number=1,
            status="graded",
            score=80,
            percentage=80,
            passed=True,
        )
        self.client.force_login(self.student)
        result_url = reverse("exams:exam_result", args=[attempt.pk])
        response = self.client.get(result_url)
        self.assertEqual(response.status_code, 302)

        self.exam.results_released = True
        self.exam.save(update_fields=["results_released"])
        response = self.client.get(result_url)
        self.assertEqual(response.status_code, 200)
