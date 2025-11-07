# userauth/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from userauth.forms import login_form, register_form
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.urls import reverse

def register_view(request):
    form = register_form(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            password = form.cleaned_data['password']

            password_policy_errors = []
            try:
                validate_password(password, user=None)
            except ValidationError as errs:
                password_policy_errors = errs.messages

            if password_policy_errors:
                for msg in password_policy_errors:
                    messages.error(request, f"密碼強度不足：{msg}")
                print(f"DEBUG: Messages before rendering (policy error): {list(messages.get_messages(request))}") # Add this
                # No return here, let it fall through to the final render
            else:
                user = form.save(commit=False)
                user.set_password(password)
                user.save()
                messages.success(request, '帳號建立成功！請用新密碼登入。')
                print(f"DEBUG: Messages before redirect (success): {list(messages.get_messages(request))}") # Add this
                return redirect('login')
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    if field == '__all__':
                        messages.error(request, err)
                    else:
                        field_label = form.fields[field].label or field.capitalize()
                        messages.error(request, f"{field_label}：{err}")
            for err in form.non_field_errors():
                messages.error(request, err)
            print(f"DEBUG: Messages before rendering (form error): {list(messages.get_messages(request))}") # Add this

    print(f"DEBUG: Messages at final render: {list(messages.get_messages(request))}") # Add this
    return render(request, 'register.html', {'form': form})

# ... (views.py 的其他部分保持不變) ...

def login_view(request):
      form = login_form(request.POST or None)
      if request.method == 'POST' and form.is_valid():
          username = form.cleaned_data['username']
          password = form.cleaned_data['password']
          user = authenticate(request, username=username, password=password)
          if user:
              login(request, user)
              messages.success(request, f"歡迎回來，{username}！")
              print(f"DEBUG: Messages before redirect (login success): {list(messages.get_messages(request))}") # Add this
              return redirect(reverse('seats:dashboard'))
          else:
              messages.error(request, '使用者名稱或密碼無效。')
              print(f"DEBUG: Messages before rendering (login error): {list(messages.get_messages(request))}") # Add this

      if request.user.is_authenticated:
          return redirect(reverse('seats:dashboard'))

      print(f"DEBUG: Messages at final login render: {list(messages.get_messages(request))}") # Add this
      return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, "您已成功登出。") # 中文提示
        return redirect('login') 
    else:
        messages.info(request, "請使用登出按鈕來登出。") # 中文提示
        return redirect('login')

# @login_required
# def index_view(request):
#     return render(request, 'index.html', {'user': request.user})

