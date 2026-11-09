"""Accounts views - login, logout, profile, MFA"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.cache import cache
import hashlib
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.db import transaction
import re
from .forms import LoginForm, UserProfileForm, ChangePasswordForm, SignupForm
from .models import ActivityLog, User
from .mfa import issue_otp, verify_otp


def login_view(request):
    """Handle login — with optional MFA"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    rate_key = 'login-failures:' + hashlib.sha256(ip_address.encode('utf-8')).hexdigest()
    if request.method == 'POST' and cache.get(rate_key, 0) >= 10:
        form = LoginForm(request.POST)
        form.add_error(None, 'Too many failed login attempts. Please wait 15 minutes before trying again.')
        return render(request, 'accounts/login.html', {'form': form}, status=429)

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cache.delete(rate_key)
        user = form.cleaned_data['user']

        if user.mfa_enabled:
            # Generate OTP and store in session
            try:
                issue_otp(user, enforce_cooldown=True)
            except ValueError:
                messages.warning(request, 'Please wait before requesting another verification code.')
                return redirect('login')
            except Exception:
                messages.error(request, 'Unable to send a verification code. Please try again later.')
                return redirect('login')
            request.session['mfa_user_id'] = user.id
            request.session['mfa_started_at'] = timezone.now().timestamp()
            request.session['mfa_next'] = request.GET.get('next', '')
            request.session.save()
            return redirect('mfa_verify')

        # No MFA — log in directly
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        ActivityLog.objects.create(
            user=user, action='login',
            description='User logged in',
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        messages.success(request, f'Welcome back, {user.first_name}!')
        next_url = request.GET.get('next', '')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return redirect(next_url)
        return redirect('dashboard')

    if request.method == 'POST':
        if not cache.add(rate_key, 1, timeout=900):
            try:
                cache.incr(rate_key)
            except ValueError:
                cache.set(rate_key, 1, timeout=900)
    return render(request, 'accounts/login.html', {'form': form})


@require_POST
def mfa_resend_view(request):
    """Resend OTP to the user's email."""
    user_id = request.session.get('mfa_user_id')
    if not user_id:
        return redirect('login')
    try:
        user = User.objects.get(id=user_id, is_active=True, mfa_enabled=True)
    except User.DoesNotExist:
        request.session.pop('mfa_user_id', None)
        request.session.pop('mfa_started_at', None)
        request.session.pop('mfa_next', None)
        return redirect('login')

    try:
        issue_otp(user, enforce_cooldown=True)
    except ValueError:
        messages.warning(request, 'Please wait at least 60 seconds before requesting another code.')
        return redirect('mfa_verify')
    except Exception:
        messages.error(request, 'Unable to send a new code. Please try again later.')
        return redirect('mfa_verify')
    request.session['mfa_resent'] = True
    request.session['mfa_started_at'] = timezone.now().timestamp()
    request.session.save()
    return redirect('mfa_verify')


def mfa_verify_view(request):
    """Verify OTP for MFA login."""
    user_id = request.session.get('mfa_user_id')
    if not user_id:
        return redirect('login')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('login')

    if not user.is_active or not user.mfa_enabled:
        request.session.pop('mfa_user_id', None)
        request.session.pop('mfa_started_at', None)
        request.session.pop('mfa_next', None)
        return redirect('login')

    started_at = request.session.get('mfa_started_at')
    try:
        challenge_expired = not started_at or timezone.now().timestamp() - float(started_at) > 600
    except (TypeError, ValueError):
        challenge_expired = True
    if challenge_expired:
        request.session.pop('mfa_user_id', None)
        request.session.pop('mfa_started_at', None)
        request.session.pop('mfa_next', None)
        return redirect('login')

    error = None
    if request.method == 'POST':
        valid, error = verify_otp(user, request.POST.get('otp', ''))
        if valid:
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            request.session.pop('mfa_user_id', None)
            request.session.pop('mfa_started_at', None)
            request.session.pop('mfa_resent', None)
            next_url = request.session.pop('mfa_next', '')
            ActivityLog.objects.create(user=user, action='login', description='User logged in with MFA', ip_address=request.META.get('REMOTE_ADDR'))
            messages.success(request, 'Welcome back, {}!'.format(user.first_name))
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(next_url)
            return redirect('dashboard')

    otp_email = user.personal_email if user.personal_email else user.email
    email_hint = '{}***@{}'.format(otp_email[:3], otp_email.split('@')[1]) if '@' in otp_email else '***'
    resent = request.session.pop('mfa_resent', False)
    return render(request, 'accounts/mfa_verify.html', {'user': user, 'error': error, 'email_hint': email_hint, 'dev_otp': None, 'resent': resent})


@login_required
def mfa_toggle_view(request):
    """Enable or disable MFA for the current user."""
    user = request.user
    if request.method == 'POST':
        action = request.POST.get('action')
        if action in ['enable', 'disable'] and not user.check_password(request.POST.get('password', '')):
            messages.error(request, 'Enter your current password to change MFA settings.')
            return redirect('profile')
        if action == 'enable' and not user.mfa_enabled:
            user.mfa_enabled = True
            user.save(update_fields=['mfa_enabled'])
            messages.success(request, 'Two-factor authentication enabled. An OTP will be sent to your email on each login.')
        elif action == 'disable' and user.mfa_enabled:
            user.mfa_enabled = False
            user.mfa_secret = ''
            user.mfa_secret_expires = None
            user.mfa_attempts = 0
            user.mfa_last_sent_at = None
            user.save(update_fields=['mfa_enabled', 'mfa_secret', 'mfa_secret_expires', 'mfa_attempts', 'mfa_last_sent_at'])
            messages.success(request, 'Two-factor authentication disabled.')
        return redirect('profile')
    return redirect('profile')


def signup_view(request):
    """Collect a registration request; an administrator must verify identity before activation."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    from apps.students.models import StudentProfile, Programme

    intake_choices = [
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
        intake = request.POST.get('intake', 'september')
        if intake not in dict(intake_choices):
            form.add_error(None, 'Select a valid intake type.')

        try:
            level = int(request.POST.get('level') or (200 if intake == 'direct_entry' else 100))
        except (TypeError, ValueError):
            level = 0
        if level not in {100, 200, 300, 400}:
            form.add_error(None, 'Select a valid academic level.')

        programme_id = request.POST.get('programme')
        try:
            programme = Programme.objects.get(pk=int(programme_id)) if programme_id else None
        except (TypeError, ValueError, Programme.DoesNotExist):
            programme = None
        if not programme:
            form.add_error(None, 'Select a valid programme.')

        academic_year = request.POST.get('academic_year', '')
        match = re.fullmatch(r'(20\d{2})/(20\d{2})', academic_year)
        if not match or int(match.group(2)) != int(match.group(1)) + 1:
            form.add_error(None, 'Enter a valid academic year, for example 2026/2027.')

        preferred_language = request.POST.get('preferred_language', 'English')
        if preferred_language not in dict(User.LANGUAGE_CHOICES):
            preferred_language = 'English'

        if not form.errors:
            d = form.cleaned_data
            with transaction.atomic():
                user = User.objects.create_user(
                    user_id=d['user_id'],
                    email=d['email'],
                    first_name=d['first_name'],
                    last_name=d['last_name'],
                    phone=d.get('phone', ''),
                    role=User.STUDENT,
                    is_active=False,
                    password=d['password'],
                    preferred_language=preferred_language,
                )
                StudentProfile.objects.create(
                    user=user,
                    programme=programme,
                    level=level,
                    academic_year=academic_year,
                )
                ActivityLog.objects.create(
                    user=user,
                    action='signup',
                    description=f'New student registration pending verification — {intake} intake',
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
            messages.info(
                request,
                'Your registration has been received. An administrator must verify your student identity before your account is activated.',
            )
            return redirect('login')

    from collections import defaultdict
    grouped_programmes = defaultdict(list)
    for programme in programmes:
        grouped_programmes[programme.department.faculty].append(programme)

    return render(request, 'accounts/signup.html', {
        'form': form,
        'grouped_programmes': dict(grouped_programmes),
        'intake_choices': intake_choices,
        'current_year': '2026/2027',
        'academic_years': ['2026/2027', '2025/2026', '2024/2025'],
    })

@require_POST
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
    form = ChangePasswordForm(request.POST or None, user=request.user)
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
