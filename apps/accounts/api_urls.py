from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import api_views

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', api_views.ProfileAPIView.as_view(), name='api_profile'),
    path('leaderboard/', api_views.LeaderboardAPIView.as_view(), name='api_leaderboard'),
]
