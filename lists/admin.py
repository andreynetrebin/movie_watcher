from django.contrib import admin
from .models import MovieList

class MovieListAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_public', 'created', 'points')  # Поля, которые будут отображаться в списке
    list_filter = ('is_public', 'user')  # Фильтры для боковой панели
    search_fields = ('title',)  # Поля, по которым можно будет искать

    # Если хотите, чтобы можно было редактировать поля в форме
    fields = ('title', 'user', 'movies', 'is_public', 'points')  # Поля для редактирования
    readonly_fields = ('points',)  # Поля, которые будут только для чтения

admin.site.register(MovieList, MovieListAdmin)