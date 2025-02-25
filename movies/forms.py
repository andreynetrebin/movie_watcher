import requests
import re
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django import forms
from .models import Movie, Genre, Country, Director, Writer, Comment
from decouple import config
import os

class MovieBulkCreateForm(forms.Form):
    urls = forms.CharField(widget=forms.Textarea, label="Список URL (по одному на строку)")

class MovieCreateForm(forms.ModelForm):

    url = forms.CharField(label="url kinopoisk")
    class Meta:
        model = Movie
        fields = ['url']
        # widgets = {
        #     'url': forms.HiddenInput,
        # }

    # https://www.kinopoisk.ru/film/441406/
    # https://www.kinopoisk.ru/series/257386/

    def clean_url(self):
        url = self.cleaned_data['url']

        pattern = r'^https://www\.kinopoisk\.ru/(film|series)/(\d+)/.*$'
        # Проверка соответствия шаблону
        match = re.match(pattern, url)
        if not match:
            raise forms.ValidationError(
                'Url не валидный, ожидается url в формате https://www.kinopoisk.ru/film/{id фильма}/*'
            )
        else:
            kinopoisk_id = match.group(2)
            print(f"kinopoisk_id - {kinopoisk_id}")
            if Movie.objects.filter(kinopoisk_id=kinopoisk_id).exists():
                raise forms.ValidationError(f"С id {kinopoisk_id} фильм уже есть в базе")

            movie_url = f"https://kinopoiskapiunofficial.tech/api/v2.2/films/{kinopoisk_id}"
            movie_staff_url = f"https://kinopoiskapiunofficial.tech/api/v1/staff"
            try:
                movie_response = requests.get(movie_url, headers={
                    'X-API-KEY': config('X-API-KEY'),
                    "Content-Type": "application/json",
                })
            except Exception as e:
                print(f"Error - {e}")
                movie_response = None

            print(f"movie_response - {movie_response.json()}")
            movie_data = movie_response.json()
            print(f"movie_data - {movie_data}")
            try:
                if 'You exceeded the quota' in movie_data['message']:
                    print(f"if You exceeded the quota")
                    raise forms.ValidationError("Превышена квота запросов к API Кинопоиска. Попробуйте выполнить на следующий день")
            except:
                print(f"else You exceeded the quota")
                if movie_data["type"] == "FILM" and movie_data["serial"] is False:
                    type_movie = "FILM"
                elif movie_data["type"] == "TV_SERIES" and movie_data["serial"] is True:
                    type_movie = "TV_SERIES"
                else:
                    raise forms.ValidationError(
                        'Похоже, что по Вашему url и не сериал и не фильм. Ничего добавлено не будет'
                    )
                try:
                    movie_staff_response = requests.get(movie_staff_url, headers={
                    'X-API-KEY': config('X-API-KEY2'),
                    "Content-Type": "application/json",
                    }, params={"filmId": kinopoisk_id})
                except Exception as e:
                    print(f"Error - {e}")
                    movie_staff_response = None

                movie_staff_data = movie_staff_response.json()
                try:
                    if 'You exceeded the quota' in movie_staff_data['message']:
                        raise forms.ValidationError(
                        "Превышена квота запросов к API Кинопоиска. Попробуйте выполнить на следующий день")
                except:
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
                                if item["professionKey"].upper() == "DIRECTOR" and item["nameRu"]
                            ],
                            "writers": [
                                {"staff_id": item["staffId"], "name": item["nameRu"]}
                                for item in movie_staff_data
                                if item["professionKey"].upper() == "WRITER" and item["nameRu"]
                            ],
                            "year": movie_data["year"],
                            "duration": movie_data["filmLength"],
                            "kinopoisk_url": movie_data["webUrl"],
                            "url": movie_data["webUrl"],
                            "description": movie_data["description"],
                            "poster_movie_url": movie_data["posterUrl"],
                            "movie_data": movie_data,
                            "movie_staff_data": movie_staff_data,
                            "type_movie": type_movie,
                        })


    def save(self, force_insert=False, force_update=False, commit=True):
        movie = super().save(commit=False)
        kinopoisk_id = self.cleaned_data["kinopoisk_id"]
        poster_movie_url = self.cleaned_data["poster_movie_url"]

        # posterUrlPreview
        poster_image = requests.get(poster_movie_url)
        extension = poster_movie_url.rsplit('.', 1)[1].lower()
        image_name = f'{kinopoisk_id}.{extension}'
        # print(response.text)

        movie.poster.save(
            image_name,
            ContentFile(poster_image.content),
            save=False
        )

        if commit:
            movie.save()
        return movie


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['body'].widget.attrs.update({'class': 'form-control'})
