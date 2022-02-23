from django.contrib import admin

from .models import Customer, RentalOrder, Item, ItemType, Location

# Register your models here.
admin.site.register(Customer)
admin.site.register(RentalOrder)
admin.site.register(Item)
admin.site.register(ItemType)
admin.site.register(Location)