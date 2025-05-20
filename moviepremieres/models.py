from django.db import models
from django.urls import reverse
from pytils.translit import slugify

class Genre(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Director(models.Model):
    name = models.CharField(max_length=200)
    staff_id = models.IntegerField(unique=True)

    def __str__(self):
        return self.name


class Writer(models.Model):
    name = models.CharField(max_length=200, unique=True)
    staff_id = models.IntegerField(unique=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=200)
    title_original = models.CharField(max_length=200, null=True, blank=True)
    year = models.IntegerField()
    duration = models.IntegerField(null=True, blank=True)
    kinopoisk_id = models.IntegerField()
    kinopoisk_url = models.URLField()
    slug = models.SlugField(max_length=200, blank=True)
    poster = models.ImageField(upload_to='premieres/%Y/%m/%d/')
    created = models.DateTimeField(auto_now_add=True)
    genres = models.ManyToManyField(Genre, related_name='movies_genre')
    countries = models.ManyToManyField(Country, related_name='movies_country')
    directors = models.ManyToManyField(Director, related_name='movies_director')
    writers = models.ManyToManyField(Writer, related_name='movies_writer')
    premiere_date = models.DateField(null=True, blank=True)  # Новое поле для даты премьеры

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.title)}_{self.kinopoisk_id}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('moviepremieres:detail', args=[self.slug])
