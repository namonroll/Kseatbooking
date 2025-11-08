from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class Seat(models.Model):
    name = models.CharField(max_length=20, unique=True)  # 座位編號
    x = models.IntegerField(default=0)  # 選座位定位
    y = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('reserved', '已預約'),
        ('cancelled', '已取消'),
    ]

    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='reserved')
    created_at = models.DateTimeField(auto_now_add=True)  # 建立記錄的時間

    def __str__(self):
        return f"{self.seat.name} - {self.user.username} ({self.start_time} ~ {self.end_time})"

# seats/models.py

from django.db import models
from django.contrib.auth.models import User
from datetime import datetime 

class Seat(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name="座位編號")
    x = models.IntegerField(default=0, verbose_name="X 座標")
    y = models.IntegerField(default=0, verbose_name="Y 座標")

    def __str__(self):
        return self.name

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('reserved', '已預約'),
        ('cancelled', '已取消'),
        ('completed', '已完成'), # 建議增加 'completed' 狀態
    ]

    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, verbose_name="預約座位")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="預約使用者")
    start_time = models.DateTimeField(verbose_name="開始時間")
    end_time = models.DateTimeField(verbose_name="結束時間")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='reserved', verbose_name="狀態")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        username_str = self.user.username if self.user else "Unknown User"
        return f"{self.seat.name} - {username_str} ({self.start_time.strftime('%Y-%m-%d %H:%M')} ~ {self.end_time.strftime('%Y-%m-%d %H:%M')})"

class Report(models.Model):
    STATUS_CHOICES = [
        ('pending', '待處理'),
        ('resolved', '已處理'),
        ('dismissed', '已駁回'),
        ('confirmed', '已確認'), # 可以增加一個明確的確認狀態
    ]

    seat = models.ForeignKey(Seat, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="被檢舉座位")
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made', verbose_name="檢舉人")
    
    reported_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_against', verbose_name="被檢舉人")
    

    reported_reservation = models.ForeignKey(
        'Reservation', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        verbose_name="被檢舉的預約"
    )
    
    reported_date = models.DateField(null=True, blank=True, verbose_name="發生日期")
    reported_time = models.TimeField(null=True, blank=True, verbose_name="發生時間")
    reason = models.TextField(verbose_name="檢舉原因")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="處理狀態")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="提交時間")
    admin_notes = models.TextField(null=True, blank=True, verbose_name="管理員備註")

    def __str__(self):
        seat_name = self.seat.name if self.seat else "未知座位"
        date_str = self.reported_date.isoformat() if self.reported_date else "未知日期"
        time_str = self.reported_time.strftime('%H:%M') if self.reported_time else "未知時間"
        reported_user_str = self.reported_user.username if self.reported_user else "N/A"
        return f"檢舉 ({self.get_status_display()}) - 座位: {seat_name}, 時間: {date_str} {time_str}, 被檢舉人: {reported_user_str}"

    class Meta:
        verbose_name = "檢舉"
        verbose_name_plural = "檢舉"
        ordering = ['-submitted_at'] # 保持排序
