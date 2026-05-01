"""Accounts views - login, logout, profile, MFA"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import random
from .forms import LoginForm, UserProfileForm, ChangePasswordForm, SignupForm
from .models import ActivityLog, User


def _generate_otp():
    return str(random.randint(100000, 999999))


def _send_otp_email(user, otp):
    from django.core.mail import send_mail
    try:
        send_mail(
            subject='KAAF University — Your Login OTP',
            message=(
                f"Hello {user.first_name},\n\n"
                f"Your one-time password (OTP) for KAAF University login is:\n\n"
                f"  {otp}\n\n"
                f"This code expires in 10 minutes. Do not share it with anyone.\n\n"
                f"If you did not request this, please ignore this email.\n\n"
                f"KAAF University Smart Assistant"
            ),
            from_email='noreply@kaafuni.edu.gh',
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:
        pass


def login_view(request):
    """Handle login — with optional MFA"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.cleaned_data['user']

        if user.mfa_enabled:
            # Generate OTP and store in session
            otp = _generate_otp()
            user.mfa_secret = otp
            user.mfa_secret_expires = timezone.now() + timedelta(minutes=10)
            user.save(update_fields=['mfa_secret', 'mfa_secret_expires'])
            _send_otp_email(user, otp)
            request.session['mfa_user_id'] = user.id
            return redirect('mfa_verify')

        # No MFA — log in directly
        login(request, user)
        ActivityLog.objects.create(
            user=user, action='login',
            description='User logged in',
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        messages.success(request, f'Welcome back, {user.first_name}!')
        return redirect(request.GET.get('next', 'dashboard'))

    return render(request, 'accounts/login.html', {'form': form})


def mfa_verify_view(request):
    """Verify OTP for MFA login."""
    user_id = request.session.get('mfa_user_id')
    if not user_id:
        return redirect('login')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('login')

    error = None
    if request.method == 'POST':
        otp_entered = request.POST.get('otp', '').strip()
        if (user.mfa_secret == otp_entered and
                user.mfa_secret_expires and
                timezone.now() <= user.mfa_secret_expires):
            # Clear OTP
            user.mfa_secret = ''
            user.mfa_secret_expires = None
            user.save(update_fields=['mfa_secret', 'mfa_secret_expires'])
            del request.session['mfa_user_id']
            login(request, user)
            ActivityLog.objects.create(
                user=user, action='login',
                description='User logged in with MFA',
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('dashboard')
        elif user.mfa_secret_expires and timezone.now() > user.mfa_secret_expires:
            error = 'OTP has expired. Please log in again.'
            del request.session['mfa_user_id']
            return redirect('login')
        else:
            error = 'Invalid OTP. Please try again.'

    return render(request, 'accounts/mfa_verify.html', {
        'user': user, 'error': error,
        'email_hint': f"{user.email[:3]}***@{user.email.split('@')[1]}"
    })


@login_required
def mfa_toggle_view(request):
    """Enable or disable MFA for the current user."""
    user = request.user
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'enable' and not user.mfa_enabled:
            user.mfa_enabled = True
            user.save(update_fields=['mfa_enabled'])
            messages.success(request, 'Two-factor authentication enabled. An OTP will be sent to your email on each login.')
        elif action == 'disable' and user.mfa_enabled:
            user.mfa_enabled = False
            user.mfa_secret = ''
            user.save(update_fields=['mfa_enabled', 'mfa_secret'])
            messages.success(request, 'Two-factor authentication disabled.')
        return redirect('profile')
    return redirect('profile')


def signup_view(request):
    """Self-registration for new students."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    from apps.students.models import StudentProfile, Programme, Department

    # Real KAAF intake types
    INTAKE_CHOICES = [
        ('february', 'February Intake'),
        ('september', 'September Intake'),
        ('sandwich', 'Sandwich Programme'),
        ('summer', 'Summer School'),
        ('direct_entry', 'Direct Entry (Level 200/300)'),
        ('access_course', 'Access Course (Nursing)'),
    ]

    programmes = Programme.objects.select_related('department').order_by('department__faculty', 'name')

    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        user = User.objects.create_user(
            user_id=d['user_id'],
            email=d['email'],
            first_name=d['first_name'],
            last_name=d['last_name'],
            phone=d.get('phone', ''),
            role=User.STUDENT,
            password=d['password'],
            preferred_language=request.POST.get('preferred_language', 'English'),
        )
        # Determine level from form or intake type
        intake = request.POST.get('intake', 'september')
        level_from_form = request.POST.get('level')
        if level_from_form:
            level = int(level_from_form)
        else:
            level = 200 if intake == 'direct_entry' else 100

        programme_id = request.POST.get('programme')
        academic_year = request.POST.get('academic_year', '2024/2025')

        StudentProfile.objects.create(
            user=user,
            programme_id=programme_id if programme_id else None,
            level=level,
            academic_year=academic_year,
        )
        ActivityLog.objects.create(
            user=user, action='signup',
            description=f'New student registered — {intake} intake',
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        login(request, user)
        messages.success(request, f'Welcome to KAAF University, {user.first_name}! 🎉')
        return redirect('dashboard')

    # Group programmes by faculty for the dropdown
    from collections import defaultdict
    grouped_programmes = defaultdict(list)
    for p in programmes:
        grouped_programmes[p.department.faculty].append(p)

    return render(request, 'accounts/signup.html', {
        'form': form,
        'grouped_programmes': dict(grouped_programmes),
        'intake_choices': INTAKE_CHOICES,
        'current_year': '2024/2025',
        'academic_years': ['2024/2025', '2025/2026', '2023/2024'],
    })


def logout_view(request):
    """Handle logout"""
    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user,
            action='logout',
            description='User logged out',
        )
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def profile_view(request):
    """View and update user profile"""
    form = UserProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password_view(request):
    """Change user password"""
    form = ChangePasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = request.user
        if not user.check_password(form.cleaned_data['old_password']):
            messages.error(request, 'Current password is incorrect.')
        else:
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def leaderboard_view(request):
    """Gamification leaderboard"""
    from .models import User
    top_users = User.objects.filter(is_active=True).order_by('-points')[:20]
    return render(request, 'accounts/leaderboard.html', {'top_users': top_users})
