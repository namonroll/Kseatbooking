# mail/urls.py
from django.urls import path
from .views import password_reset_view
from django.urls import path
from .views import password_reset_view

urlpatterns = [
   path('forget/', password_reset_view, name='password_reset'),
   path('forget/', password_reset_view, name='password_reset'),

]



