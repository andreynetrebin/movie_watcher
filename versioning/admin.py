from django.contrib import admin

from .models import Version

@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ['version_number', 'release_date', 'changes']
    list_filter = ['release_date']
