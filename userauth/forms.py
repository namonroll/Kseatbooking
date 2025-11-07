from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class register_form(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}))

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm = self.cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            raise ValidationError("Passwords do not match.")
        return confirm

class login_form(forms.Form):
    username = forms.CharField(
        label='Username',
        max_length=10,
        widget=forms.TextInput(attrs={
            'placeholder': 'Username',
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
        })
    )

from django import forms
from django.core.exceptions import ValidationError



