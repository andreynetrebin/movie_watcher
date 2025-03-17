import requests
import re
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django import forms
from .models import Movie, Genre, Country, Director, Writer, Comment
from decouple import config
import os
from datetime import datetime

class MovieBulkCreateForm(forms.Form):
    urls = forms.CharField(widget=forms.Textarea, label="Список URL (по одному на строку)")

class MovieCreateForm(forms.ModelForm):

    url = forms.CharField(label="url kinopoisk")
    class Meta:
        model = Movie
        fields = ['url']

    def __init__(self, *args, **kwargs):
        self.source = kwargs.pop('source', None)  # Извлекаем source из kwargs
        super().__init__(*args, **kwargs)

    def clean_url(self):
        url = self.cleaned_data['url']

        pattern = r'^https://www\.kinopoisk\.ru/(film|series)/(\d+)/.*$'
        match = re.match(pattern, url)
        if not match:
            raise forms.ValidationError(
                'Url не валидный, ожидается url в формате https://www.kinopoisk.ru/film/{id фильма}/*'
            )
        else:
            kinopoisk_id = match.group(2)
            existing_movie = Movie.objects.filter(kinopoisk_id=kinopoisk_id).first()
            if existing_movie:
                if self.source == 'website':
                    return {
                        'exists': True,
                        'movie': existing_movie,
                    }
                elif self.source == 'telegram':
                    return {
                        'exists': True,
                        'kinopoisk_id': kinopoisk_id,
                    }

            movie_url = f"https://kinopoiskapiunofficial.tech/api/v2.2/films/{kinopoisk_id}"
            movie_staff_url = f"https://kinopoiskapiunofficial.tech/api/v1/staff"
            try:
                movie_response = requests.get(movie_url, headers={
                    'X-API-KEY': config('X-API-KEY'),
                    "Content-Type": "application/json",
                })
                movie_data = movie_response.json()
                if 'message' in movie_data and 'You exceeded the quota' in movie_data['message']:
                    raise forms.ValidationError("Превышена квота запросов к API Кинопоиска. Попробуйте выполнить на следующий день")
            except Exception as e:
                raise forms.ValidationError("Ошибка при запросе к API Кинопоиска")

            # Обработка movie_data
            if 'type' in movie_data and movie_data["type"] == "FILM" and not movie_data.get("serial"):
                type_movie = "FILM"
            elif 'type' in movie_data and movie_data["type"] in ["TV_SERIES", "MINI_SERIES"] and movie_data.get("serial"):
                type_movie = "TV_SERIES"
            else:
                raise forms.ValidationError(
                    'Похоже, что по Вашему url и не сериал и не фильм, а Иное. Иное добавлено не будет'
                )

            # Обработка данных о съемочной группе
            try:
                movie_staff_response = requests.get(movie_staff_url, headers={
                    'X-API-KEY': config('X-API-KEY2'),
                    "Content-Type": "application/json",
                }, params={"filmId": kinopoisk_id})
                movie_staff_data = movie_staff_response.json()
                if 'message' in movie_staff_data and 'You exceeded the quota' in movie_staff_data['message']:
                    raise forms.ValidationError("Превышена квота запросов к API Кинопоиска. Попробуйте выполнить на следующий день")
            except Exception as e:
                raise forms.ValidationError("Ошибка при запросе к API Кинопоиска")
            # Установка года, если он None
            year = movie_data.get("year")
            if year is None:
                year = datetime.now().year  # Устанавливаем текущий год
            # Заполнение cleaned_data
            self.cleaned_data.update(
                {
                    "kinopoisk_id": kinopoisk_id,
                    "title": movie_data["nameRu"],
                    "title_original": movie_data["nameOriginal"],
                    "countries": [item["country"] for item in movie_data["countries"]],
                    "genres": [item["genre"] for item in movie_data["genres"]],
                    "directors": [
                        {"staff_id": item["staffId"], "name": item["nameRu"]}
                        for item in movie_staff_data
                        if isinstance(item, dict) and item.get("professionKey", "").upper() == "DIRECTOR" and item.get("nameRu")
                    ],
                    "writers": [
                        {"staff_id": item["staffId"], "name": item["nameRu"]}
                        for item in movie_staff_data
                        if isinstance(item, dict) and item.get("professionKey", "").upper() == "WRITER" and item.get("nameRu")
                    ],
                    "year": year,
                    "duration": movie_data["filmLength"],
                    "kinopoisk_url": movie_data["webUrl"],
                    "url": movie_data["webUrl"],
                    "description": movie_data["description"],
                    "poster_movie_url": movie_data["posterUrl"],
                    "movie_data": movie_data,
                    "movie_staff_data": movie_staff_data,
                    "type_movie": type_movie,
                }
            )

    def save(self, force_insert=False, force_update=False, commit=True):
        movie = super().save(commit=False)  # Создаем объект Movie, но не сохраняем его в БД
        kinopoisk_id = self.cleaned_data["kinopoisk_id"]
        poster_movie_url = self.cleaned_data["poster_movie_url"]

        # Получаем изображение
        poster_image = requests.get(poster_movie_url)
        extension = poster_movie_url.rsplit('.', 1)[1].lower()
        image_name = f'{kinopoisk_id}.{extension}'

        # Сохраняем изображение
        movie.poster.save(
            image_name,
            ContentFile(poster_image.content),  # Убедитесь, что это возвращает байтовый объект
            save=False
        )

        # Заполняем остальные поля
        movie.title = self.cleaned_data["title"]
        movie.title_original = self.cleaned_data["title_original"]
        movie.year = self.cleaned_data["year"]
        movie.duration = self.cleaned_data["duration"]
        movie.kinopoisk_id = self.cleaned_data["kinopoisk_id"]
        movie.kinopoisk_url = self.cleaned_data["kinopoisk_url"]
        movie.url = self.cleaned_data["url"]
        movie.description = self.cleaned_data["description"]
        movie.movie_json = self.cleaned_data["movie_data"]
        movie.movie_staff_json = self.cleaned_data["movie_staff_data"]
        movie.type_movie = self.cleaned_data["type_movie"]

        if commit:
            movie.save()  # Сохраняем объект в БД
        return movie

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['body'].widget.attrs.update({'class': 'form-control'})
