from django.conf import settings
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
    FILM = 'FILM'
    TV_SERIES = 'TV_SERIES'
    TYPE_CHOICES = [
        (FILM, 'Film'),
        (TV_SERIES, 'TV Series'),
    ]

    title = models.CharField(max_length=200)
    title_original = models.CharField(max_length=200, null=True, blank=True)
    year = models.IntegerField()
    duration = models.IntegerField(null=True, blank=True)
    kinopoisk_id = models.IntegerField()
    kinopoisk_url = models.URLField()
    slug = models.SlugField(max_length=200, blank=True)
    poster = models.ImageField(upload_to='images/%Y/%m/%d/')
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    movie_json = models.JSONField(blank=True)
    movie_staff_json = models.JSONField(blank=True)

    genres = models.ManyToManyField(Genre, related_name='movies_genre')
    countries = models.ManyToManyField(Country, related_name='movies_country')
    directors = models.ManyToManyField(Director, related_name='movies_director')
    writers = models.ManyToManyField(Writer, related_name='movies_writer')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='movies_add', on_delete=models.SET_NULL,
                             null=True)
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
    total_views = models.PositiveIntegerField(default=0)

    # Новое поле для типа фильма
    type_movie = models.CharField(max_length=10, choices=TYPE_CHOICES, default=FILM)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.title)}_{self.kinopoisk_id}"
        super().save(*args, **kwargs)

    # Метод для увеличения количества просмотров
    def increment_views(self):
        self.total_views += 1
        self.save()

    # Метод для уменьшения количества просмотров
    def decrement_views(self):
        if self.total_views > 0:
            self.total_views -= 1
            self.save()

    def add_like(self, user):
        if self.has_liked(user):  # Проверяем, есть ли уже лайк
            self.remove_like(user)  # Снимаем лайк
        else:
            self.users_like.add(user)  # Добавляем пользователя в лайки
            self.total_likes += 1  # Увеличиваем счетчик лайков
            self.save()  # Сохраняем изменения

    def add_dislike(self, user):
        if self.has_disliked(user):  # Проверяем, есть ли уже дизлайк
            self.remove_dislike(user)  # Снимаем дизлайк
        else:
            self.users_dislike.add(user)  # Добавляем пользователя в дизлайки
            self.total_dislikes += 1  # Увеличиваем счетчик дизлайков
            self.save()  # Сохраняем изменения

    def remove_like(self, user):
        if self.has_liked(user):  # Проверяем, есть ли лайк
            self.users_like.remove(user)  # Удаляем пользователя из лайков
            if self.total_likes > 0:
                self.total_likes -= 1  # Уменьшаем счетчик лайков
            self.save()  # Сохраняем изменения

    def remove_dislike(self, user):
        if self.has_disliked(user):  # Проверяем, есть ли дизлайк
            self.users_dislike.remove(user)  # Удаляем пользователя из дизлайков
            if self.total_dislikes > 0:
                self.total_dislikes -= 1  # Уменьшаем счетчик дизлайков
            self.save()  # Сохраняем изменения
    def has_liked(self, user):
        return self.users_like.filter(id=user.id).exists()

    def has_disliked(self, user):
        return self.users_dislike.filter(id=user.id).exists()


    class Meta:
        indexes = [
            models.Index(fields=['-created']),
            models.Index(fields=['-total_views']),
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

