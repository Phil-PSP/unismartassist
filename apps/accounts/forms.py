"""Authentication forms"""
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from PIL import Image
from .models import User


class LoginForm(forms.Form):
    user_id = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        cleaned = super().clean()
        user_id = cleaned.get('user_id')
        password = cleaned.get('password')
        if user_id and password:
            user = authenticate(username=user_id, password=password)
            if not user:
                raise forms.ValidationError('Invalid ID or password. Please try again.')
            if not user.is_active:
                raise forms.ValidationError('Your account has been deactivated.')
            cleaned['user'] = user
        return cleaned


class UserProfileForm(forms.ModelForm):
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if not avatar:
            return avatar
        if avatar.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Profile image must not exceed 5 MB.')
        try:
            image = Image.open(avatar)
            if image.format not in {'JPEG', 'PNG', 'GIF', 'WEBP'}:
                raise forms.ValidationError('Upload a JPG, PNG, GIF or WEBP image.')
            image.verify()
        except (OSError, ValueError):
            raise forms.ValidationError('The uploaded profile image is invalid.')
        finally:
            avatar.seek(0)
        return avatar

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'personal_email', 'phone', 'avatar', 'preferred_language']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'personal_email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'e.g. yourname@gmail.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'preferred_language': forms.Select(attrs={'class': 'form-input'}),
        }
        labels = {
            'personal_email': 'Personal Email (for OTP / MFA)',
        }


class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    user_id = forms.CharField(max_length=20)
    email = forms.EmailField()
    phone = forms.CharField(max_length=15, required=False)
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    def clean_user_id(self):
        uid = self.cleaned_data['user_id'].strip()
        if User.objects.filter(user_id=uid).exists():
            raise forms.ValidationError('This ID is already registered.')
        return uid

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get('password')
        cpw = cleaned.get('confirm_password')
        if pw and cpw and pw != cpw:
            raise forms.ValidationError('Passwords do not match.')
        if pw:
            try:
                validate_password(pw)
            except ValidationError as exc:
                self.add_error('password', exc)
        return cleaned


class ChangePasswordForm(forms.Form):
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    def clean(self):
        cleaned = super().clean()
        new = cleaned.get('new_password')
        confirm = cleaned.get('confirm_password')
        if new and confirm and new != confirm:
            raise forms.ValidationError('New passwords do not match.')
        if new:
            try:
                validate_password(new, user=self.user)
            except ValidationError as exc:
                self.add_error('new_password', exc)
        return cleaned
