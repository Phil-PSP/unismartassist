from django.urls import path
from . import api_views

urlpatterns = [
    path('token/', api_views.TokenObtainWithMFAView.as_view(), name='token_obtain'),
    path('token/verify/', api_views.TokenVerifyMFAView.as_view(), name='token_verify_mfa'),
    path('token/refresh/', api_views.TokenRefreshAPIView.as_view(), name='token_refresh'),
    path('profile/', api_views.ProfileAPIView.as_view(), name='api_profile'),
    path('leaderboard/', api_views.LeaderboardAPIView.as_view(), name='api_leaderboard'),
]
