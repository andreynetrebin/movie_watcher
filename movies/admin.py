from django.contrib import admin

from .models import Movie, Watched, Comment


@admin.register(Movie)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'poster', 'created']
    list_filter = ['created']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'movie', 'created_on', 'active']
    list_filter = ['active', 'created_on']
    search_fields = ['body']

@admin.register(Watched)
class WatchedAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie']
    list_filter = ['user']
    search_fields = ['movie']