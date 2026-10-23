from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('login/verify/', views.mfa_verify_view, name='mfa_verify'),
    path('login/resend-otp/', views.mfa_resend_view, name='mfa_resend'),
    path('mfa/toggle/', views.mfa_toggle_view, name='mfa_toggle'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
]
