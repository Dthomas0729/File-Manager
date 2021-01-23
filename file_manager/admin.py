from django.contrib import admin

from .models import Customer, RentalOrder

# Register your models here.
admin.site.register(Customer)
admin.site.register(RentalOrder)