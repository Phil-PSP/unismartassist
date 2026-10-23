from django.apps import AppConfig


class ExamsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.exams'
    verbose_name = 'Examination System'
    
    def ready(self):
        """Import admin when app is ready"""
        # Force import of admin module
        try:
            import apps.exams.admin
            print("✅ Exams admin module loaded successfully")
        except Exception as e:
            print(f"❌ Error loading exams admin: {e}")
