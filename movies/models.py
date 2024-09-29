from django.conf import settings
from django.db import models
from django.urls import reverse
from pytils.translit import slugify

class Genre(models.Model):
    name = models.CharField(max_length=200, unique=True)
    def __str__(self):
        return self.name

    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)

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
    title_original = models.CharField(max_length=200)
    # genre = models.CharField(max_length=200)
    year = models.IntegerField()
    duration = models.IntegerField()
    # director = models.CharField(max_length=200)
    kinopoisk_id = models.IntegerField()
    kinopoisk_url = models.URLField()
    slug = models.SlugField(max_length=200, blank=True)
    # url = models.URLField(max_length=2000)
    poster = models.ImageField(upload_to='images/%Y/%m/%d/')
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    movie_json = models.JSONField(blank=True)
    movie_staff_json = models.JSONField(blank=True)

    genres = models.ManyToManyField(Genre, related_name='movies_genre')
    countries = models.ManyToManyField(Country, related_name='movies_country')
    directors = models.ManyToManyField(Director, related_name='movies_director')
    writers = models.ManyToManyField(Writer, related_name='movies_writer')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='movies_add', on_delete=models.DO_NOTHING)
    users_like = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='movies_like',
        blank=True
    )


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.title)}_{self.kinopoisk_id}"
        super().save(*args, **kwargs)


    class Meta:
        indexes = [
            models.Index(fields=['-created']),
    ]
        ordering = ['-created']


    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('movies:detail', args=[self.slug])

