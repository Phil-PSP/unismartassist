"""Celery tasks for student app"""
try:
    from celery import shared_task
except ImportError:
    def shared_task(func=None, **kwargs):
        if func is not None:
            return func
        def decorator(f):
            return f
        return decorator


@shared_task
def process_document(document_id):
    """Process uploaded document in background"""
    from .models import Document
    from .services import DocumentProcessor
    try:
        doc = Document.objects.get(id=document_id)
        processor = DocumentProcessor(doc)
        processor.process()
    except Document.DoesNotExist:
        pass
    except Exception as e:
        print(f"Document processing error: {e}")


@shared_task
def recalculate_all_gpas():
    """Recalculate GPA for all students (admin task)"""
    from .models import StudentProfile
    for profile in StudentProfile.objects.all():
        profile.calculate_cumulative_gpa()
