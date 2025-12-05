from django.contrib import admin
from .models import *
from django.contrib.auth.models import User

# Register your models here.

admin.site.register(TableCategory)
admin.site.register(Table)
admin.site.register(MenuCategory)
admin.site.register(MenuItem)


admin.site.register(Bill)
admin.site.register(BillItem)
admin.site.register(Kot)

from django.contrib import admin

# Change the text shown on the browser tab
admin.site.site_title = "The golden spoon admin"

# Change the big header text at the top of the admin site
admin.site.site_header = "The Golden Spoon Administration"

# Change the title on the admin homepage
admin.site.index_title = "Welcome to the Admin of Golden Spoon"
