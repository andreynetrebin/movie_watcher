from django.contrib import admin
from .models import Profile, Contact

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'date_of_birth', 'photo']
    raw_id_fields = ['user']

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['user_from', 'user_to', 'created']
    list_filter = ['created']
    search_fields = ['user_from__username', 'user_to__username']
    raw_id_fields = ['user_from', 'user_to']