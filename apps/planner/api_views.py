from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Task


class TasksAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(user=request.user, is_completed=False).order_by('due_date')
        data = [{
            'id': t.id, 'title': t.title, 'priority': t.priority,
            'due_date': str(t.due_date) if t.due_date else None,
            'type': t.task_type, 'is_overdue': t.is_overdue,
        } for t in tasks]
        return Response({'tasks': data})

    def post(self, request):
        from .forms import TaskForm
        form = TaskForm(request.data)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            return Response({'id': task.id, 'title': task.title}, status=201)
        return Response(form.errors, status=400)
