"""Authentication forms"""
from django import forms
from django.contrib.auth import authenticate
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
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar', 'preferred_language']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'preferred_language': forms.Select(attrs={'class': 'form-input'}),
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
        if pw and len(pw) < 6:
            raise forms.ValidationError('Password must be at least 6 characters.')
        return cleaned


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    def clean(self):
        cleaned = super().clean()
        new = cleaned.get('new_password')
        confirm = cleaned.get('confirm_password')
        if new and confirm and new != confirm:
            raise forms.ValidationError('New passwords do not match.')
        return cleaned
