from django.contrib import admin
from .models import *

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ['userID', 'name']
    list_display_links = ['userID', 'name']

admin.site.register(User, UserAdmin)