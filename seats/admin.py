from django.contrib import admin
from .models import Seat, Reservation, Report 

admin.site.register(Seat)
admin.site.register(Reservation)
# Register your models here.
admin.site.register(Report)
