# mail/forms.py

from django import forms
from django.core.exceptions import ValidationError

class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email'})
    )
    verification_code = forms.CharField(
        max_length=6,
        required=False,  # 因為寄送驗證碼時不需要填驗證碼
        widget=forms.TextInput(attrs={'placeholder': '驗證碼'})
    )
    password = forms.CharField(
        required=False,  # 同樣是第二階段才需要填
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password'}),
        min_length=8,
        error_messages={'min_length': '密碼至少要 8 個字元喔！'}
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        min_length=8,
        error_messages={'min_length': '密碼至少要 8 個字元喔！'}
    )

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('password')
        cpw = cleaned_data.get('confirm_password')
        if pw and cpw and pw != cpw:
            raise ValidationError("兩次輸入的密碼不一致。")
        return cleaned_data
