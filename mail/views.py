# mail/views.py
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from .forms import PasswordResetForm
from django.contrib.auth.models import User
import random

def password_reset_view(request):
    form = PasswordResetForm() # 在 GET 請求前先初始化一個空的 form
    current_stage = 'email' # 預設階段為 Email 輸入

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        action = request.POST.get('action')

        if action == 'send_code':
            # 只驗證 Email 欄位，因為其他欄位可能還沒有資料
            if form.is_valid():
                email = form.cleaned_data['email']
                # 檢查 Email 是否存在於資料庫
                if not User.objects.filter(email=email).exists():
                    messages.error(request, '該電子郵件地址不存在。')
                    current_stage = 'email' # 保持在 Email 階段
                else:
                    code = str(random.randint(100000, 999999))
                    request.session['verification_code'] = code
                    request.session['reset_email'] = email
                    # 標記使用者已經在驗證碼階段
                    request.session['reset_stage'] = 'verification'

                    try:
                        send_mail(
                            subject='您的 驗證碼',
                            message=f'您好，您的驗證碼是：{code}',
                            from_email=None,  # 如果 settings 裡有 DEFAULT_FROM_EMAIL，可以設 None
                            recipient_list=[email],
                            fail_silently=False,
                        )
                        # 成功寄出郵件的泡泡提示
                        messages.success(request, '驗證碼已寄出，請至信箱查看。')
                        current_stage = 'verification' # 進入驗證碼階段
                    except Exception as e:
                        messages.error(request, f'驗證碼寄送失敗: {e}')
                        current_stage = 'email' # 寄送失敗，保持在 Email 階段
            else:
                messages.error(request, '請輸入正確的 Email。')
                current_stage = 'email' # 保持在 Email 階段

        elif action == 'verify_code':
            # 只驗證 Email 和 verification_code 欄位
            if form.is_valid(): # 這裡可能只驗證了填入的欄位
                email = form.cleaned_data['email'] # 從表單獲取
                code = form.cleaned_data['verification_code'] # 從表單獲取
                session_code = request.session.get('verification_code')
                session_email = request.session.get('reset_email')

                # 確保 Email 和驗證碼有被填寫
                if not email or not code:
                    messages.error(request, '請輸入電子郵件和驗證碼。')
                    current_stage = 'verification'
                elif email != session_email:
                    messages.error(request, 'Email 與發送驗證碼的 Email 不符。')
                    current_stage = 'verification'
                elif code != session_code:
                    messages.error(request, '驗證碼錯誤。')
                    current_stage = 'verification'
                else:
                    # 驗證成功，進入密碼重設階段
                    messages.success(request, '驗證碼正確，請輸入新密碼。')
                    request.session['reset_stage'] = 'password' # 標記使用者進入密碼重設階段
                    current_stage = 'password' # 進入密碼階段
            else:
                # 表單驗證失敗，保持在驗證碼階段
                messages.error(request, '驗證碼格式不正確。')
                current_stage = 'verification' # 保持在驗證碼階段

        elif action == 'reset_password':
            # 驗證所有欄位
            if form.is_valid():
                email = form.cleaned_data['email']
                code = form.cleaned_data['verification_code'] # 雖然這裡可能不會顯示，但 Form 會要求
                password = form.cleaned_data['password']
                confirm = form.cleaned_data['confirm_password']
                session_code = request.session.get('verification_code')
                session_email = request.session.get('reset_email')

                # 在重設密碼前再次檢查驗證碼和 Email 的匹配
                if email != session_email or code != session_code:
                    messages.error(request, '驗證碼或 Email 不符，請重新驗證。')
                    current_stage = 'verification' # 如果不符，退回驗證碼階段
                elif password != confirm:
                    messages.error(request, '兩次輸入的密碼不一致。')
                    current_stage = 'password' # 保持在密碼階段
                else: # 所有檢查都通過，可以重設密碼了
                    try:
                        user = User.objects.get(email=email)
                        user.set_password(password)
                        user.save()

                        messages.success(request, '密碼重設成功！請用新密碼登入。')
                        # 清除 session 中的驗證碼和 Email 相關資訊
                        request.session.pop('verification_code', None)
                        request.session.pop('reset_email', None)
                        request.session.pop('reset_stage', None)
                        return redirect('login') # 重新導向到登入頁面
                    except User.DoesNotExist:
                        messages.error(request, '系統錯誤：找不到對應的使用者帳戶。')
                        current_stage = 'password'
                    except Exception as e:
                        messages.error(request, f'密碼重設失敗發生錯誤: {e}')
                        import traceback
                        traceback.print_exc()
                        current_stage = 'password'
            else:
                messages.error(request, '請確認所有欄位都正確填寫。')
                current_stage = 'password' # 如果表單驗證失敗，保持在密碼階段
    else: # GET 請求
        # 初始化 Form，確保所有欄位都存在，但可能為空
        form = PasswordResetForm()
        # 清除舊的 session 狀態，確保每次新進入頁面都從第一階段開始
        request.session.pop('verification_code', None)
        request.session.pop('reset_email', None)
        request.session.pop('reset_stage', None)
        current_stage = 'email' # 預設為 Email 階段

    # 確保表單的 email 和 verification_code 欄位能從 session 帶入，以便前端判斷
    if 'reset_email' in request.session:
        form.fields['email'].initial = request.session['reset_email']
    # 注意：這裡 verification_code 不會從 session initial，因為是使用者輸入的

    return render(request, 'mail/forget.html', {'form': form, 'current_stage': current_stage})