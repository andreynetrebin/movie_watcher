import requests
import re
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django import forms
from .models import Movie, Genre, Country, Director, Writer
import os

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
        regex = r'^(https:\/\/www.kinopoisk.ru\/)([A-Za-z0-9-_]+)\/(\d{1,10})'
        match = re.search(regex, url.strip())
        if not match:
            raise forms.ValidationError(
                'The given URL does not match valid kinopoisk.'
            )
        else:
            kinopoisk_id = match.group(3)
            if Movie.objects.filter(kinopoisk_id=kinopoisk_id).exists():
                raise forms.ValidationError("Kinopoisk ID already exists in database")
            movie_url = f"https://kinopoiskapiunofficial.tech/api/v2.2/films/{kinopoisk_id}"
            movie_staff_url = f"https://kinopoiskapiunofficial.tech/api/v1/staff"
            movie_response = requests.get(movie_url, headers={
                'X-API-KEY': 'e2563c11-1959-48d4-803f-03caeec73ee7',
                "Content-Type": "application/json",
                         })
            movie_staff_response = requests.get(movie_staff_url, headers={
                'X-API-KEY': 'e2563c11-1959-48d4-803f-03caeec73ee7',
                "Content-Type": "application/json",
                         }, params={"filmId":  kinopoisk_id}
                                    )
            # "countries": [{"country": "США"}
            movie_data = movie_response.json()
            movie_staff_data = movie_staff_response.json()
            # dirpath = os.path.abspath(os.path.dirname(__file__))
            # with open(os.path.join(dirpath, f"{kinopoisk_id}_staff.json"), "w") as f:
            #     f.write(response.text)
            self.cleaned_data.update(
                {
                    "kinopoisk_id": kinopoisk_id,
                    "title": movie_data["nameRu"],
                    "title_original": movie_data["nameOriginal"],
                    # "genre": ", ".join([item["genre"] for item in movie_data["genres"]]),
                    "countries": [item["country"] for item in movie_data["countries"]],
                    "genres": [item["genre"] for item in movie_data["genres"]],
                    "directors": [
                        {"staff_id": item["staffId"], "name": item["nameRu"]} for item in movie_staff_data if item["professionKey"].upper() == "DIRECTOR"
                    ],
                    "writers": [
                        {"staff_id": item["staffId"], "name": item["nameRu"]} for item in movie_staff_data if
                        item["professionKey"].upper() == "WRITER"
                    ],
                    # "": [item["genre"] for item in movie_data["genres"]],
                    "year": movie_data["year"],
                    "duration": movie_data["filmLength"],
                    "kinopoisk_url": movie_data["webUrl"],
                    "url": movie_data["webUrl"],
                    "description": movie_data["description"],
                    "poster_movie_url": movie_data["posterUrl"],
                    "movie_data": movie_data,
                    "movie_staff_data": movie_staff_data,

                })

        # return api_url



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