from django.conf import settings
from django.urls import reverse
from django.db import models
from movies.models import Movie

class MovieList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    movies = models.ManyToManyField(Movie, related_name='movie_lists')
    points = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    users_like = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_lists', blank=True)
    is_public = models.BooleanField(default=False)  # Новое поле для публичности списка

    def __str__(self):
        return self.title

    def add_points(self, points):
        self.points += points
        self.save()

    def get_absolute_url(self):
        return reverse('lists:movie_list_detail', kwargs={'list_id': self.id})