"""Activity logging middleware"""
from .models import ActivityLog


class ActivityLogMiddleware:
    """Log user page visits automatically"""
    EXCLUDED_PATHS = ['/static/', '/media/', '/admin/jsi18n/']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Log only authenticated GET requests to main pages
        if (request.user.is_authenticated and
                request.method == 'GET' and
                not any(request.path.startswith(p) for p in self.EXCLUDED_PATHS)):
            try:
                ActivityLog.objects.create(
                    user=request.user,
                    action='page_visit',
                    description=request.path,
                    ip_address=self.get_client_ip(request),
                )
            except Exception:
                pass  # Never let logging break the request
        return response

    def get_client_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0]
        return request.META.get('REMOTE_ADDR')
