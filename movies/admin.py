from django.contrib import admin

from .models import Movie


@admin.register(Movie)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'poster', 'created']
    list_filter = ['created']
