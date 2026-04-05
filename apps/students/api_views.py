from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import StudentProfile, Result, Timetable, GPARecord


class ResultsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_student:
            return Response({'error': 'Students only'}, status=403)
        profile = get_object_or_404(StudentProfile, user=request.user)
        results = Result.objects.filter(student=profile).select_related('course')
        data = [{
            'course': r.course.name, 'code': r.course.code,
            'score': float(r.score or 0), 'grade': r.grade,
            'grade_points': float(r.grade_points),
            'semester': r.semester, 'year': r.academic_year,
        } for r in results]
        return Response({'results': data, 'cumulative_gpa': float(profile.cumulative_gpa)})


class TimetableAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_student:
            return Response({'error': 'Students only'}, status=403)
        profile = get_object_or_404(StudentProfile, user=request.user)
        registered = profile.registrations.filter(is_active=True).values_list('course_id', flat=True)
        entries = Timetable.objects.filter(
            course_id__in=registered,
            academic_year=profile.academic_year,
        ).select_related('course').order_by('day', 'start_time')
        data = [{
            'course': e.course.name, 'code': e.course.code,
            'day': e.day, 'start': str(e.start_time), 'end': str(e.end_time),
            'venue': e.venue, 'type': e.entry_type,
        } for e in entries]
        return Response({'timetable': data})


class GPAAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_student:
            return Response({'error': 'Students only'}, status=403)
        profile = get_object_or_404(StudentProfile, user=request.user)
        records = GPARecord.objects.filter(student=profile).order_by('academic_year', 'semester')
        data = [{'year': r.academic_year, 'semester': r.semester, 'gpa': float(r.gpa)} for r in records]
        return Response({'gpa_history': data, 'cumulative_gpa': float(profile.cumulative_gpa)})
