from django import forms
from django.contrib.auth.forms import AuthenticationForm


class CustomLoginForm(AuthenticationForm):
    """Custom login form with enhanced styling"""
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-slate-300 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400 focus:outline-none transition',
            'placeholder': 'Username',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-slate-300 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400 focus:outline-none transition',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        })
    )


