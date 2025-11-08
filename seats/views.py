# SeatBooking/seats/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta, datetime 
from django.core.mail import send_mail
from .models import Seat, Reservation, Report 
from .forms import ReportForm 

from django.conf import settings #



@login_required
def welcome(request): # 即時座位圖 / 預約系統主頁
    now = timezone.now()

    overlapping_reservations = Reservation.objects.filter(
        status='reserved', # 'reserved'正在進行的預約
        start_time__lte=now,
        end_time__gte=now
    ).select_related('seat')

    reserved_seat_ids = [res.seat_id for res in overlapping_reservations]
    seats = Seat.objects.all()

    context = {
        'seats': seats,
        'reserved_seat_ids': reserved_seat_ids,
        'now': timezone.localtime(now), # 本地時間
        'page_title': '即時座位圖'
    }
    return render(request, 'seats/welcome.html', context)

@login_required
def seat_map(request): # 查詢特定時間點的座位圖
    date_str = request.GET.get('date')
    time_str = request.GET.get('time')

    seats = Seat.objects.all()
    reserved_seat_ids = []

    if date_str and time_str:
        try:
            selected_datetime_naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            if settings.USE_TZ:
                selected_datetime = timezone.make_aware(selected_datetime_naive, timezone.get_current_timezone())
            else:
                selected_datetime = selected_datetime_naive

            overlapping_reservations = Reservation.objects.filter(
                status='reserved',
                start_time__lte=selected_datetime,
                end_time__gt=selected_datetime
            ).select_related('seat')
            reserved_seat_ids = [res.seat_id for res in overlapping_reservations]
        except ValueError:
            messages.error(request, "日期或時間格式無效。")
        except Exception as e:
             print(f"Error filtering seats in seat_map: {e}")
             messages.error(request, "查詢座位時發生錯誤。")

    date_options = [(date.today() + timedelta(days=i)).isoformat() for i in range(7)]
    time_slots = [f'{h:02}:00' for h in range(8, 24)]

    context = {
        'seats': seats,
        'reserved_seat_ids': reserved_seat_ids,
        'date_options': date_options,
        'time_slots': time_slots,
        'selected_date': date_str,
        'selected_time': time_str,
        'page_title': '查詢特定時間座位'
    }
    return render(request, 'seats/seat_map.html', context)

@login_required
def res_time(request): # 選擇預約時間範圍以查看可用座位
    date_str = request.GET.get('date')
    start_str = request.GET.get('start_time')
    end_str = request.GET.get('end_time')

    seats = Seat.objects.all()
    reserved_seat_ids = []
    user_reserved_seat_ids = [] # 當前使用者在該時段已預約的座位

    date_options = [(date.today() + timedelta(days=i)).isoformat() for i in range(7)]
    time_slots = [f'{h:02}:00' for h in range(8, 24)]

    if date_str and start_str and end_str:
        try:
            start_dt_naive = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
            end_dt_naive = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M")

            if settings.USE_TZ:
                current_tz = timezone.get_current_timezone()
                start_dt = timezone.make_aware(start_dt_naive, current_tz)
                end_dt = timezone.make_aware(end_dt_naive, current_tz)
            else:
                start_dt = start_dt_naive
                end_dt = end_dt_naive

            if start_dt >= end_dt:
                messages.error(request, "開始時間必須早於結束時間。")
            else:
                overlapping_reservations = Reservation.objects.filter(
                    status='reserved',
                    start_time__lt=end_dt,
                    end_time__gt=start_dt
                )
                reserved_seat_ids = list(overlapping_reservations.values_list('seat_id', flat=True))

                user_reservations_in_range = overlapping_reservations.filter(user=request.user)
                user_reserved_seat_ids = list(user_reservations_in_range.values_list('seat_id', flat=True))
        except ValueError:
            messages.error(request, "日期或時間格式無效。")
        except Exception as e:
            print(f"Error filtering seats in res_time: {e}")
            messages.error(request, "查詢座位時發生錯誤。")

    context = {
        'seats': seats,
        'reserved_seat_ids': reserved_seat_ids,
        'user_reserved_seat_ids': user_reserved_seat_ids,
        'date_options': date_options,
        'time_slots': time_slots,
        'selected_date': date_str,
        'selected_start_time': start_str,
        'selected_end_time': end_str,
        'page_title': '選擇預約時段與座位'
    }
    return render(request, 'seats/res_time.html', context)

@login_required
def make_reservation(request): # 處理預約請求
    if request.method == 'POST':
        seat_id = request.POST.get('seat_id')
        date_str = request.POST.get('date')
        start_str = request.POST.get('start_time')
        end_str = request.POST.get('end_time')

        redirect_url_base = reverse('seats:res_time')
        query_params = {}
        if date_str: query_params['date'] = date_str
        if start_str: query_params['start_time'] = start_str
        if end_str: query_params['end_time'] = end_str
        redirect_url_with_params = redirect_url_base
        if query_params:
            from urllib.parse import urlencode
            redirect_url_with_params += '?' + urlencode(query_params)

        if not seat_id:
            messages.error(request, "請先選擇座位")
            return redirect(redirect_url_with_params)
        try:
            seat = get_object_or_404(Seat, id=seat_id)
            start_dt_naive = datetime.strptime(f"{date_str} {start_str}", '%Y-%m-%d %H:%M')
            end_dt_naive = datetime.strptime(f"{date_str} {end_str}", '%Y-%m-%d %H:%M')

            if settings.USE_TZ:
                current_tz = timezone.get_current_timezone()
                start_dt = timezone.make_aware(start_dt_naive, current_tz)
                end_dt = timezone.make_aware(end_dt_naive, current_tz)
            else:
                start_dt = start_dt_naive
                end_dt = end_dt_naive

            if start_dt >= end_dt:
                 messages.error(request, "開始時間必須早於結束時間。")
                 return redirect(redirect_url_with_params)
            if start_dt < timezone.now():
                 messages.error(request, "無法預約過去的時間。")
                 return redirect(redirect_url_with_params)

            conflict_on_seat = Reservation.objects.filter(
                seat=seat,
                status='reserved',
                start_time__lt=end_dt,
                end_time__gt=start_dt
            ).exists()
            if conflict_on_seat:
                messages.error(request, "此座位在該時段已被預約，請重新選擇。")
                return redirect(redirect_url_with_params)

            user_already_booked_in_range = Reservation.objects.filter(
                user=request.user,
                status='reserved',
                start_time__lt=end_dt,
                end_time__gt=start_dt
            ).exists()
            if user_already_booked_in_range:
                messages.warning(request, "您已在此時段有其他預約。每位用戶同一時間只能預約一個座位。")
                return redirect(redirect_url_with_params)

            Reservation.objects.create(
                seat=seat,
                user=request.user,
                start_time=start_dt,
                end_time=end_dt,
                status='reserved'
            )
            messages.success(request, f"座位 {seat.name} 預約成功！ ({date_str} {start_str}~{end_str})")
            return redirect(reverse('seats:records')) # 預約成功後跳轉到個人紀錄頁面
        except Seat.DoesNotExist:
             messages.error(request, "找不到選取的座位。")
        except ValueError:
             messages.error(request, "日期或時間格式無效。")
        except Exception as e:
            print(f"Error making reservation: {e}")
            messages.error(request, f"預約時發生錯誤：{str(e)}")
        return redirect(redirect_url_with_params)
    return redirect(reverse('seats:res_time'))


# 個人預約紀錄
@login_required
def records(request):
    user = request.user
    user_reservations = Reservation.objects.filter(user=user).order_by('-start_time')
    submitted_reports = Report.objects.filter(reporter=user).order_by('-submitted_at')
    reports_about_user = Report.objects.filter(reported_user=user).order_by('-submitted_at')

    context = {
        'reservations': user_reservations,
        'submitted_reports': submitted_reports,
        'reports_about_user': reports_about_user,
        'page_title': '我的個人紀錄',
        'timezone_now': timezone.now() # 為了模板中比較時間 (取消按鈕是否顯示)
    }
    return render(request, 'seats/records.html', context)


# 取消預約
@login_required
def cancel_reservation_by_id(request, reservation_id):
    redirect_url = reverse('seats:records')

    if request.method == 'POST':
        try:
            reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
            if reservation.status == 'reserved':
                if reservation.start_time > timezone.now():
                    reservation.status = 'cancelled'
                    reservation.save()
                    messages.success(request, f"您的預約 (座位 {reservation.seat.name}, {reservation.start_time.strftime('%Y-%m-%d %H:%M')}) 已成功取消。")
                else:
                    messages.warning(request, "此預約已開始或已結束，無法取消。")
            else:
                messages.warning(request, "此預約 ({}) 無法取消或已被取消。".format(reservation.get_status_display()))
        except Exception as e:
            print(f"Error cancelling reservation by ID (ID: {reservation_id}): {e}")
            messages.error(request, f"取消預約時發生錯誤，請稍後再試。")
    else:
        messages.error(request, "無效的取消請求方式。")

    return redirect(redirect_url)



# --- (可選) 提交針對特定預約的檢舉 (如果 urls.py 中有 'submit_report' 指向這裡) ---
@login_required
def submit_report(request, reservation_id):
    try:
        reservation_to_report = get_object_or_404(Reservation, id=reservation_id)
    except Reservation.DoesNotExist:
        messages.error(request, "找不到要檢舉的預約記錄。")
        return redirect(reverse('seats:welcome')) # 或其他錯誤提示頁

    if request.method == 'POST':
        form = ReportForm(request.POST) # 假設 ReportForm 能處理這種情況
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.reservation = reservation_to_report # 關聯到特定預約
            report.seat = reservation_to_report.seat # 自動帶入座位
            report.reported_user = reservation_to_report.user # 自動帶入被檢舉人
            # 你可能還想預填 reported_date 和 reported_time
            report.save()
            
            # ✅ 發送提醒郵件
            if report.reported_user and report.reported_user.email:
                subject = "您在 K 書中心被提醒"
                message = (
                    f"您好，\n\n"
                    f"您在 {report.reported_date} {report.reported_time} 被其他使用者提醒。\n"
                    f"座位編號：{report.seat.name if report.seat else '未指定'}\n"
                    f"提醒原因：{report.reason}\n\n"
                    f"如有疑問，請洽管理員。"
                )
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [report.reported_user.email],
                    fail_silently=True,
                )
            messages.success(request, f"針對預約 (ID: {reservation_id}) 的檢舉已成功提交。")
            return redirect(reverse('seats:records'))
        else:
            messages.error(request, "提交檢舉失敗，請檢查表單內容。")
    else:
        # GET 請求時，可以預填表單
        initial_data = {
            'seat': reservation_to_report.seat,
            # 'reported_user_username': reservation_to_report.user.username, # 如果 ReportForm 使用 username
            'reported_date': reservation_to_report.start_time.date(),
            'reported_time': reservation_to_report.start_time.time(),
        }
        form = ReportForm(initial=initial_data)

    context = {
        'form': form,
        'reservation_to_report': reservation_to_report,
        'page_title': f'檢舉預約 (座位 {reservation_to_report.seat.name})'
    }
    return render(request, 'seats/submit_report_form.html', context) 



@login_required
def original_cancel_reservation(request):
    if request.method == 'POST':

        messages.info(request, "原始取消表單功能正在處理...") # 訊息
        return redirect(reverse('seats:res_time')) # 跳轉
    return redirect(reverse('seats:res_time'))


@login_required
def dashboard(request): # <--- 確保函數名是 dashboard
    context = {
        'page_title': '國立中央大學 K書中心 ',
        'welcome_message': f'歡迎回來, {request.user.username if request.user.is_authenticated else "挑戰者"}!'
    }
    return render(request, 'seats/dashboard.html', context)

@login_required 
def faq_view(request):
    context = {
        'page_title': "常見問答",
        'welcome_message': "以下是您可能會遇到的問題與解答。",
    }
    return render(request, 'seats/faq.html', context)


def rules_view(request):
    """
    處理「預約辦法」頁面的請求。
    """
    context = {
        'page_title': "預約辦法",
        'welcome_message': "本辦法由國立中央大學圖書館制定，旨在維護 K 書中心（以下簡稱「本中心」）的閱覽秩序，作為閱覽規範及執行公務的依據。", 
    }
    return render(request, 'seats/rules.html', context)

# records換頁
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Reservation, Report # Assuming these are your models
from django.utils import timezone

# Helper function to paginate a queryset
def get_paginated_queryset(request, queryset, page_param='page', items_per_page=10):
    paginator = Paginator(queryset, items_per_page)
    page_number = request.GET.get(page_param)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page_obj = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver last page of results.
        page_obj = paginator.page(paginator.num_pages)
    return page_obj

@login_required
def records(request):
    user = request.user
    
    # 1. Paginate Reservations
    all_reservations = Reservation.objects.filter(user=user).order_by('-start_time')
    reservations = get_paginated_queryset(request, all_reservations, 'res_page', 10)

    # 2. Paginate Submitted Reports by the user
    all_submitted_reports = Report.objects.filter(reporter=user).order_by('-submitted_at')
    submitted_reports = get_paginated_queryset(request, all_submitted_reports, 'sub_page', 10)

    # 3. Paginate Reports About User
    # Assuming Report.reported_user is a ForeignKey to User
    all_reports_about_user = Report.objects.filter(reported_user=user).order_by('-submitted_at')
    reports_about_user = get_paginated_queryset(request, all_reports_about_user, 'rep_page', 10)


    context = {
        'page_title': '個人紀錄',
        'reservations': reservations, # Paginated object
        'submitted_reports': submitted_reports, # Paginated object
        'reports_about_user': reports_about_user, # Paginated object
        'timezone_now': timezone.now(), # Pass current timezone-aware datetime
    }
    return render(request, 'seats/records.html', context)


import requests

def send_report_email(to_email, report_time, seat, reason):
    return requests.post(
        "https://api.mailgun.net/v3/YOUR_DOMAIN_NAME/messages",
        auth=("api", "e71583bb-453d328c"),
        data={
            "from": "<admin@sandbox189cab16c1bb4b3db7f5f9b3b95728f5.mail.org>",
            "to": [to_email],
            "subject": "提醒通知",
            "text": f"你好，你在 {report_time}、{seat} 被檢舉/提醒，\n被檢舉/提醒原因：{reason}"
        }
    )


#new remind
# SeatBooking/seats/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta, datetime
from django.core.mail import send_mail
from .models import Seat, Reservation, Report # 確保 Report, Reservation 模型已導入
from .forms import ReportForm # 確保 ReportForm 已導入
from django.db.models import Q # 用於複雜查詢



# 檢舉
@login_required
def reminds(request):
    seats = Seat.objects.all()
    date_options = [(date.today() + timedelta(days=i)).isoformat() for i in range(7)]
    time_slots = [f'{h:02}:00' for h in range(8, 24)]

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user # 提交檢舉的人是當前用戶

            # 獲取表單提交的座位、日期和時間
            reported_seat = form.cleaned_data.get('seat')
            reported_date = form.cleaned_data.get('reported_date')
            reported_time = form.cleaned_data.get('reported_time')

            # 合併日期和時間，並轉換為時區感知 datetime 物件
            if reported_date and reported_time:
                event_datetime_naive = datetime.combine(reported_date, reported_time)
                if settings.USE_TZ:
                    current_tz = timezone.get_current_timezone()
                    event_datetime = timezone.make_aware(event_datetime_naive, current_tz)
                else:
                    event_datetime = event_datetime_naive
            else:
                messages.error(request, "檢舉事件日期和時間是必填的。")
                # 重新渲染表單並顯示錯誤
                context = {
                    'form': form,
                    'seats': seats,
                    'date_options': date_options,
                    'time_slots': time_slots,
                    'page_title': '提交檢舉/提醒'
                }
                return render(request, 'seats/reminds.html', context)

            target_reservation = Reservation.objects.filter(
                seat=reported_seat,
                start_time__lte=event_datetime,
                end_time__gt=event_datetime, # 結束時間必須晚於事件時間點
                status='reserved' # 確保是已預約的狀態
            ).order_by('-start_time').first() # 如果有多個，取最近開始的

            if target_reservation:
                report.reported_user = target_reservation.user # 設定被檢舉人
                report.reported_reservation = target_reservation # 關聯到被檢舉的預約
                messages.info(request, f"系統已自動識別被檢舉者為 {target_reservation.user.username}。")
            else:
                # 如果沒有找到對應的預約
                report.reported_user = None # 如果沒有找到，設為 None
                report.reported_reservation = None # 如果沒有找到，設為 None
                messages.warning(request, "未找到在該座位和時間點的有效預約，無法自動識別被檢舉者。")

            report.save() # 儲存 report 物件

            # 發送提醒郵件
            # 現在檢查 report.reported_user 是否存在 (因為可能沒找到對應預約)
            if report.reported_user and report.reported_user.email:
                subject = "您在 K 書中心被提醒"
                message = (
                    f"您好，\n\n"
                    f"您在 {report.reported_date.strftime('%Y-%m-%d')} {report.reported_time.strftime('%H:%M')} 被其他使用者提醒。\n"
                    f"座位編號：{report.seat.name if report.seat else '未指定'}\n"
                    f"提醒原因：{report.reason}\n\n"
                    f"此提醒由系統自動發送，如有疑問，請洽管理員。"
                )
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [report.reported_user.email],
                        fail_silently=False, # 為了除錯，這裡可以暫時設為 False，出錯時會拋出異常
                    )
                    messages.success(request, f"您的檢舉已成功提交，並已向 {report.reported_user.username} 發送提醒郵件！")
                except Exception as e:
                    print(f"Error sending email: {e}")
                    messages.warning(request, f"檢舉已提交，但發送提醒郵件失敗：{e}")
            else:
                messages.success(request, "您的檢舉已成功提交，但未能發送提醒郵件（可能未找到被檢舉者或其郵箱）。")

            return redirect(reverse('seats:reminds'))

        else: # 表單驗證失敗
            for field, errs in form.errors.items():
                for err in errs:
                    field_label = form.fields[field].label if field in form.fields else field.capitalize()
                    messages.error(request, f"{field_label}：{err}")
            for err in form.non_field_errors():
                messages.error(request, err)
            
            context = {
                'form': form,
                'seats': seats,
                'date_options': date_options,
                'time_slots': time_slots,
                'page_title': '提交檢舉/提醒'
            }
            return render(request, 'seats/reminds.html', context)
    else: # GET request
        form = ReportForm(initial={'reported_date': date.today()})
    
    context = {
        'form': form,
        'seats': seats,
        'date_options': date_options,
        'time_slots': time_slots,
        'page_title': '提交檢舉/提醒'
    }
    return render(request, 'seats/reminds.html', context)

