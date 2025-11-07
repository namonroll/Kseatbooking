# seats/urls.py
from django.urls import path
from . import views

app_name = 'seats' # 確保 app 命名空間已設定

urlpatterns = [
    path('', views.welcome, name='welcome'),                    # 主頁/歡迎頁
    path('seat_map/', views.seat_map, name='seat_map'),        # 座位圖查詢
    path('res_time/', views.res_time, name='res_time'),        # 選擇預約時間
    path('make_reservation/', views.make_reservation, name='make_reservation'),     # 建立預約
    path('records/', views.records, name='records'),                               # 預約記錄
    path('cancel_reservation/<int:reservation_id>/', views.cancel_reservation_by_id, name='cancel_reservation'),  
    path('reminds/', views.reminds, name='reminds'),                              # 提醒頁面/提交檢舉表單
    path('report/<int:reservation_id>/', views.submit_report, name='submit_report'),
    path('dashboard/', views.dashboard, name='dashboard'),  # 提交針對特定預約的檢舉
    path('faq/', views.faq_view, name='faq'),
    path('rules/', views.rules_view, name='rules'),

]