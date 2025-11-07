# SeatBooking/seats/forms.py

from django import forms
from .models import Seat, Report # 引入 Report 模型
from datetime import date, time

# 其他表單（例如 LoginForm, RegisterForm 等，如果放在這裡的話，保留）

class ReportForm(forms.ModelForm):
    # ModelForm 會自動為 seat, reported_date, reported_time, reason 創建字段
    # 如果你想自定義字段，可以在這裡重新定義，例如：
    # seat = forms.ModelChoiceField(queryset=Seat.objects.all(), required=False, label="被檢舉座位")
    # reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label="檢舉原因")

    class Meta:
        model = Report
        # fields 列表中包含用戶需要填寫的字段
        fields = ['seat', 'reported_date', 'reported_time', 'reason']
        widgets = {
            'seat': forms.Select(attrs={'class': 'form-select'}),
            'reported_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reported_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': '請說明檢舉原因 (例如：離位太久、太吵、佔用座位等)'}),
        }
        labels = {
            'seat': '被檢舉座位',
            'reported_date': '事件發生日期',
            'reported_time': '事件發生時間',
            'reason': '檢舉原因',
        }

    # 可以加入 clean 方法進行額外驗證
    # def clean_reason(self):
    #     reason = self.cleaned_data.get('reason')
    #     if not reason:
    #         raise forms.ValidationError("檢舉原因不能為空。")
    #     return reason


# seats/forms.py
from django import forms
from .models import Report, Seat # 確保導入 Seat
# from django.contrib.auth.models import User # 不再需要直接在此處導入 User

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        # 移除 'reported_user_username'
        # 移除 'reported_user' (因為我們在 view 中自動設定)
        # 移除 'reported_reservation' (因為我們在 view 中自動設定)
        fields = ['seat', 'reported_date', 'reported_time', 'reason']
        widgets = {
            'seat': forms.Select(attrs={'class': 'form-select'}),
            'reported_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reported_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'seat': '被檢舉座位',
            'reported_date': '事件發生日期',
            'reported_time': '事件發生時間',
            'reason': '檢舉原因',
        }
    
    # 移除 clean 方法，因為不再需要驗證 reported_user_username