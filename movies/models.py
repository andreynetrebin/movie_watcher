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
    title_original = models.CharField(max_length=200, null=True, blank=True)
    year = models.IntegerField()
    duration = models.IntegerField()
    kinopoisk_id = models.IntegerField()
    kinopoisk_url = models.URLField()
    slug = models.SlugField(max_length=200, blank=True)
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
    users_dislike = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='movies_dislike',
        blank=True
    )
    total_likes = models.PositiveIntegerField(default=0)
    total_dislikes = models.PositiveIntegerField(default=0)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.title)}_{self.kinopoisk_id}"
        super().save(*args, **kwargs)

    def add_like(self, user):
        if user not in self.users_like.all():
            self.users_like.add(user)
            self.total_likes += 1
            self.save()
            # Удаляем пользователя из дизлайков, если он там есть
            if user in self.users_dislike.all():
                self.users_dislike.remove(user)
                if self.total_dislikes > 0:
                    self.total_dislikes -= 1  # Предполагается, что у вас есть поле total_dislikes
                self.save()
    def remove_like(self, user):
        if user in self.users_like.all():
            self.users_like.remove(user)
            if self.total_likes > 0:
                self.total_likes -= 1
            self.save()

    def add_dislike(self, user):
        if user not in self.users_dislike.all():
            self.users_dislike.add(user)
            # Удаляем пользователя из лайков, если он там есть
            if user in self.users_like.all():
                self.users_like.remove(user)
                if self.total_likes > 0:
                    self.total_likes -= 1
                self.save()


    def remove_dislike(self, user):
        if user in self.users_dislike.all():
            self.users_dislike.remove(user)
            # Предполагается, что у вас есть поле total_dislikes
            if self.total_dislikes > 0:
                self.total_dislikes -= 1
            self.save()


    class Meta:
        indexes = [
            models.Index(fields=['-created']),
            models.Index(fields=['-total_likes']),
            models.Index(fields=['-total_dislikes']),
    ]
        ordering = ['-created']


    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('movies:detail', args=[self.slug])


class Watched(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    # watched = models.BooleanField(default=False)  # Поле для хранения статуса просмотра

    class Meta:
        unique_together = ('user', 'movie')  # Ограничение на уникальность

class WishList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('user', 'movie')  # Ограничение на уникальность



class Comment(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return f'Comment by {self.author} on {self.post}'

class MovieList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    movies = models.ManyToManyField(Movie, related_name='movie_lists')
    points = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    users_like = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_movie_lists', blank=True)

    def __str__(self):
        return self.title

    def add_points(self, points):
        self.points += points
        self.save()