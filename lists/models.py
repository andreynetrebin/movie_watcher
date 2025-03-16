from django.conf import settings
from django.db import models
from movies.models import Movie

class MovieList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    movies = models.ManyToManyField(Movie, related_name='movie_lists')
    points = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    users_like = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_lists', blank=True)

    def __str__(self):
        return self.title

    def add_points(self, points):
        self.points += points
        self.save()